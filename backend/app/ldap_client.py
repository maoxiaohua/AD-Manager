from dataclasses import dataclass
from ldap3 import Server, Connection, ALL, SIMPLE, SUBTREE, Tls, MODIFY_REPLACE
import json
import ssl
import logging

logger = logging.getLogger("ldap_client")


@dataclass
class LDAPConfig:
    server_url: str
    domain: str
    admin_username: str
    admin_password: str
    base_dn: str
    use_ssl: bool = True
    tls_validate: str = "CERT_NONE"  # CERT_NONE, CERT_OPTIONAL, or CERT_REQUIRED
    receive_timeout: int = 300
    page_size: int = 500


class LDAPClient:
    """Encapsulates raw LDAP operations with automatic connection management."""

    # LDAP Simple Paged Results control OID
    PAGED_RESULTS_OID = "1.2.840.113556.1.4.319"

    def __init__(self, config: LDAPConfig):
        self.config = config
        self._conn: Connection | None = None

    def __enter__(self):
        tls_mode = getattr(ssl, self.config.tls_validate, ssl.CERT_NONE)
        tls_config = Tls(validate=tls_mode)
        server = Server(self.config.server_url, get_info=ALL, use_ssl=self.config.use_ssl, tls=tls_config)

        if "\\" in self.config.admin_username:
            user = self.config.admin_username
        elif "@" in self.config.admin_username:
            user = self.config.admin_username
        else:
            user = f"{self.config.domain}\\{self.config.admin_username}"

        logger.debug(f"Connecting to {self.config.server_url} as {user}")
        self._conn = Connection(
            server, user=user, password=self.config.admin_password,
            authentication=SIMPLE, auto_bind=True,
            receive_timeout=self.config.receive_timeout,
        )
        logger.info("Connected to LDAP server")
        return self

    def __exit__(self, *args):
        if self._conn:
            try:
                self._conn.unbind()
            except Exception:
                pass

    # ── Paged Search (breaks 1000-result AD limit) ──

    def _paged_search(self, search_base: str, search_filter: str,
                      attributes: list[str], search_scope=SUBTREE) -> list[dict]:
        """Execute a paged LDAP search, collecting all pages."""
        all_entries = []
        cookie = None
        page_size = self.config.page_size

        while True:
            self._conn.search(
                search_base=search_base,
                search_filter=search_filter,
                attributes=attributes,
                search_scope=search_scope,
                paged_size=page_size,
                paged_cookie=cookie,
            )
            entries = self._parse_response()
            all_entries.extend(entries)

            # Get paging cookie for next page
            cookie = None
            try:
                controls = self._conn.result.get("controls", {})
                paged = controls.get(self.PAGED_RESULTS_OID, {})
                cookie = paged.get("value", {}).get("cookie")
            except Exception:
                pass

            if not cookie:
                break

        logger.info(f"Paged search: {len(all_entries)} total entries (base={search_base})")
        return all_entries

    # ── Entity Searches ──

    def search_computers(self, base_dn: str | None = None) -> list[dict]:
        base = base_dn or self.config.base_dn
        return self._paged_search(
            search_base=base,
            search_filter="(objectClass=computer)",
            attributes=[
                "name", "distinguishedName", "operatingSystem",
                "operatingSystemVersion", "description",
                "userAccountControl", "lastLogonTimestamp", "dNSHostName",
            ],
        )

    def search_users(self, base_dn: str | None = None, include_disabled: bool = False) -> list[dict]:
        base = base_dn or self.config.base_dn
        filter_parts = ["(&(objectClass=user)(objectCategory=person)"]
        if not include_disabled:
            filter_parts.append("(!(userAccountControl:1.2.840.113556.1.4.803:=2))")
        filter_parts.append(")")
        return self._paged_search(
            search_base=base,
            search_filter="".join(filter_parts),
            attributes=[
                "sAMAccountName", "displayName", "mail",
                "department", "distinguishedName", "userAccountControl",
                "lockoutTime", "badPwdCount", "badPasswordTime",
            ],
        )

    def search_groups(self, base_dn: str | None = None) -> list[dict]:
        base = base_dn or self.config.base_dn
        return self._paged_search(
            search_base=base,
            search_filter="(objectClass=group)",
            attributes=[
                "sAMAccountName", "displayName", "distinguishedName",
                "groupType", "description", "mail",
            ],
        )

    def get_group_members(self, group_dn: str) -> list[str]:
        """Return all member DNs for a group (handles nested range retrieval)."""
        members = []
        range_start = 0

        while True:
            attr_name = f"member;range={range_start}-*" if range_start > 0 else "member"
            self._conn.search(
                search_base=group_dn,
                search_filter="(objectClass=*)",
                attributes=[attr_name],
                search_scope=SUBTREE,
            )
            entries = self._parse_response()
            if not entries:
                break

            attrs = entries[0].get("attributes", {})
            values: list[str] = []
            matched_attr = None
            for k, v in attrs.items():
                if k.lower().startswith("member"):
                    values = v if isinstance(v, list) else [v]
                    matched_attr = k
                    break

            if not values:
                break
            members.extend(values)

            if matched_attr and "range=" in matched_attr:
                try:
                    range_part = matched_attr.split("range=")[1]
                    end_str = range_part.split("-")[1]
                    if end_str == "*":
                        range_start = int(range_part.split("-")[0].split(";")[-1]) + len(values)
                    else:
                        break
                except (IndexError, ValueError):
                    break
            else:
                break

        return list(set(members))

    # ── Location / Site Discovery ──

    def discover_locations(self) -> list[dict]:
        """
        Discover city-level OUs under the configured location base OU.
        Returns empty list if LOCATION_BASE_OU is not configured.
        """
        from app.config import settings
        if not settings.LOCATION_BASE_OU:
            return []
        location_base = f"{settings.LOCATION_BASE_OU},{self.config.base_dn}"
        result = []
        seen = set()

        # Step 1: Find regions (one level under OU=locations)
        regions = self._paged_search(
            search_base=location_base,
            search_filter="(objectClass=organizationalUnit)",
            attributes=["name", "distinguishedName"],
            search_scope=SUBTREE,
        )

        for e in regions:
            attrs = e.get("attributes", e)
            dn = attrs.get("distinguishedName", "")
            # Parse: OU=City,OU=Region,OU=locations,DC=... or deeper
            parts = [p.strip() for p in dn.split(",")]
            ou_parts = [p.replace("OU=", "") for p in parts if p.startswith("OU=")]

            # City is the 3rd OU from the end (city, region, locations)
            # e.g. [..., City, Region, locations] → index -3
            # But skip entries that have "DC=" before we find 3 OUs
            if len(ou_parts) >= 2 and "locations" in ou_parts:
                loc_idx = ou_parts.index("locations")
                if loc_idx >= 2:
                    # Structure: ..., City, Region, locations
                    city = ou_parts[loc_idx - 2]
                    region = ou_parts[loc_idx - 1]
                    key = f"{city}|{region}"
                    if key not in seen and city not in ("locations",):
                        seen.add(key)
                        city_dn = f"OU={city},OU={region},{settings.LOCATION_BASE_OU},{self.config.base_dn}"
                        result.append({"city": city, "region": region, "base_dn": city_dn})

        return sorted(result, key=lambda x: x["city"])

    def unlock_user(self, user_dn: str) -> bool:
        """Unlock a locked AD user by clearing lockoutTime."""
        try:
            self._conn.modify(
                user_dn,
                {"lockoutTime": [(MODIFY_REPLACE, ["0"])]},
            )
            if self._conn.result["result"] == 0:
                logger.debug(f"Unlocked user: {user_dn}")
                return True
            else:
                description = self._conn.result.get("description", "unknown error")
                logger.error(f"Failed to unlock user: {description}")
                return False
        except Exception as e:
            logger.error(f"Failed to unlock user: {e}")
            raise

    # ── Utility ──

    @staticmethod
    def decode_group_type(group_type_raw: int) -> tuple[str, str]:
        gt = int(group_type_raw) if group_type_raw else 0
        is_security = bool(gt & 0x80000000)
        scope_bits = gt & 0x0000000F
        scope_map = {1: "domain_local", 2: "global", 4: "universal"}
        return ("security" if is_security else "distribution",
                scope_map.get(scope_bits, "global"))

    def test_connection(self) -> bool:
        try:
            with self:
                return True
        except Exception:
            return False

    @staticmethod
    def discover_from_domain(domain: str) -> dict:
        domain = domain.strip().lower()
        server_url = None
        ad_domain = domain

        try:
            import dns.resolver
            answers = dns.resolver.resolve(f"_ldap._tcp.{domain}", "SRV")
            if answers:
                target = str(answers[0].target).rstrip(".")
                port = answers[0].port
                server_url = f"ldaps://{target}:{port}"
        except Exception:
            pass

        if not server_url:
            parts = domain.split(".")
            for i in range(len(parts) - 2):
                candidate = ".".join(parts[i+1:])
                try:
                    import dns.resolver
                    answers = dns.resolver.resolve(f"_ldap._tcp.{candidate}", "SRV")
                    if answers:
                        target = str(answers[0].target).rstrip(".")
                        port = answers[0].port
                        server_url = f"ldaps://{target}:{port}"
                        ad_domain = candidate
                        break
                except Exception:
                    continue

        if not server_url:
            parts = domain.split(".")
            if len(parts) > 2:
                ad_domain = ".".join(parts[-(min(3, len(parts))):])
            server_url = f"ldaps://{ad_domain}:636"

        dc_parts = [f"DC={part}" for part in ad_domain.split(".") if part]
        base_dn = ",".join(dc_parts)

        return {
            "server_url": server_url,
            "base_dn": base_dn,
            "domain": ad_domain.upper(),
        }

    def _parse_response(self) -> list[dict]:
        try:
            result_code = self._conn.result.get("result", -1) if self._conn.result else -1
            if result_code != 0 and result_code != -1:
                description = self._conn.result.get("description", "unknown error")
                logger.warning(f"LDAP result={result_code}: {description}")
            entries = json.loads(self._conn.response_to_json()).get("entries", [])
            return entries
        except Exception as e:
            logger.warning(f"LDAP parse error: {e}")
            try:
                return list(self._conn.entries) if hasattr(self._conn, "entries") and self._conn.entries else []
            except Exception:
                return []
