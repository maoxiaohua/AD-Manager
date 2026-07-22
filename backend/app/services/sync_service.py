from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from app.models import SyncLog, Setting, Computer, User, ADGroup, GroupMembership
from app.ldap_client import LDAPClient, LDAPConfig
from app.core.pagination import PaginatedResponse, PaginationParams
from fastapi import HTTPException, status
from math import ceil
import logging

logger = logging.getLogger("sync_service")


class SyncService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _val(attrs: dict, key: str, default=None):
        """Safely extract scalar value from ldap3 response, unwrapping lists."""
        v = attrs.get(key, default)
        if isinstance(v, list) and len(v) > 0:
            return v[0]
        if isinstance(v, list):
            return default
        return v if v is not None else default

    def run_ldap_sync(self) -> SyncLog:
        """Full LDAP sync pipeline. Returns the SyncLog record."""
        # ── Atomically claim the sync slot ──
        # INSERT a tentative "pending" record, then atomically promote it to
        # "running" only if no other "running" row exists.  This eliminates the
        # check-then-act race that could create duplicate running records.
        log = SyncLog(
            sync_type="ldap",
            status="pending",
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(log)
        self.db.flush()  # get the id without committing

        result = self.db.execute(
            text(
                "UPDATE sync_logs SET status='running' "
                "WHERE id=:our_id AND status='pending' "
                "AND NOT EXISTS (SELECT 1 FROM sync_logs WHERE status='running' AND sync_type=:sync_type AND id != :our_id)"
            ),
            {"our_id": log.id, "sync_type": "ldap"},
        )
        if result.rowcount == 0:
            # Another caller won the race
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A sync is already in progress",
            )

        self.db.commit()
        self.db.refresh(log)

        ldap_config = self._load_ldap_config()
        # Apply location filter: override base_dn if sync_location is set
        location = self._get_setting("sync_location")
        if location:
            ldap_config.base_dn = location
            logger.info(f"Location filter active: {location}")

        logger.info("Starting LDAP sync")
        logger.debug(f"Sync details: server={ldap_config.server_url}, base_dn={ldap_config.base_dn}")
        try:
            with LDAPClient(ldap_config) as client:
                logger.info("Syncing computers...")
                computer_count = self._sync_computers(client)
                logger.info(f"Computers synced: {computer_count}")

                logger.info("Syncing users...")
                user_count = self._sync_users(client)
                logger.info(f"Users synced: {user_count}")

                logger.info("Syncing groups...")
                group_count = self._sync_groups(client)
                logger.info(f"Groups synced: {group_count}")

                logger.info("Syncing group memberships...")
                membership_count = self._sync_group_memberships(client)
                logger.info(f"Memberships synced: {membership_count}")

            log.records_processed = (
                computer_count + user_count + group_count + membership_count
            )
            log.status = "success"
            log.completed_at = datetime.now(timezone.utc)
        except Exception as e:
            logger.error(f"Sync failed: {e}", exc_info=True)
            log.status = "failed"
            log.error_message = str(e)
            log.completed_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(log)
        return log

    def run_user_status_sync(self) -> SyncLog:
        """Sync only user account status (lock/unlock/disable). Lightweight — skips
        computers, groups, and memberships.  Designed for sub-hourly cadence."""
        # ── Atomically claim the sync slot (scoped to ldap_user_status type) ──
        log = SyncLog(
            sync_type="ldap_user_status",
            status="pending",
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(log)
        self.db.flush()

        result = self.db.execute(
            text(
                "UPDATE sync_logs SET status='running' "
                "WHERE id=:our_id AND status='pending' "
                "AND NOT EXISTS (SELECT 1 FROM sync_logs WHERE status='running' AND sync_type=:sync_type AND id != :our_id)"
            ),
            {"our_id": log.id, "sync_type": "ldap_user_status"},
        )
        if result.rowcount == 0:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user status sync is already in progress",
            )

        self.db.commit()
        self.db.refresh(log)

        ldap_config = self._load_ldap_config()
        location = self._get_setting("sync_location")
        if location:
            ldap_config.base_dn = location
            logger.info(f"User-status sync: location filter active: {location}")

        logger.info("Starting user-status sync")
        try:
            with LDAPClient(ldap_config) as client:
                user_count = self._sync_users(client, include_disabled=True)
                logger.info(f"User-status sync: {user_count} users updated")

            log.records_processed = user_count
            log.status = "success"
            log.completed_at = datetime.now(timezone.utc)
        except Exception as e:
            logger.error(f"User-status sync failed: {e}", exc_info=True)
            log.status = "failed"
            log.error_message = str(e)
            log.completed_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(log)
        return log

    def _sync_computers(self, client: LDAPClient) -> int:
        """Fetch computers from AD, upsert into local DB."""
        ad_entries = client.search_computers()
        count = 0
        for entry in ad_entries:
            attrs = entry.get("attributes", entry)
            dn = self._val(attrs, "distinguishedName", "")

            uac_raw = self._val(attrs, "userAccountControl", 0)
            try:
                uac = int(uac_raw)
            except (ValueError, TypeError):
                uac = 0
            status_val = "disabled" if (uac & 2) else "active"

            last_logon = self._val(attrs, "lastLogonTimestamp")
            if last_logon:
                try:
                    last_logon = self._filetime_to_datetime(int(last_logon))
                except (ValueError, TypeError):
                    last_logon = None

            existing = self.db.query(Computer).filter(Computer.distinguished_name == dn).first()
            if existing:
                existing.name = self._val(attrs, "name", existing.name)
                existing.ip_address = self._val(attrs, "dNSHostName", existing.ip_address)
                existing.operating_system = self._val(attrs, "operatingSystem", existing.operating_system)
                existing.os_version = self._val(attrs, "operatingSystemVersion", existing.os_version)
                existing.description = self._val(attrs, "description", existing.description)
                existing.status = status_val
                existing.last_logon_timestamp = last_logon
            else:
                computer = Computer(
                    name=self._val(attrs, "name", ""),
                    distinguished_name=dn,
                    ip_address=self._val(attrs, "dNSHostName"),
                    operating_system=self._val(attrs, "operatingSystem"),
                    os_version=self._val(attrs, "operatingSystemVersion"),
                    description=self._val(attrs, "description"),
                    status=status_val,
                    last_logon_timestamp=last_logon,
                )
                self.db.add(computer)
            count += 1

            if count % 100 == 0:
                self.db.commit()

        self.db.commit()
        return count

    @staticmethod
    def _decode_uac_flags(uac: int) -> list[str]:
        """Decode userAccountControl bitmask into human-readable flags."""
        flags = []
        if uac & 2:     flags.append("ACCOUNTDISABLE")
        if uac & 16:    flags.append("LOCKOUT")
        if uac & 32:    flags.append("PASSWD_NOTREQD")
        if uac & 64:    flags.append("PASSWD_CANT_CHANGE")
        if uac & 65536: flags.append("DONT_EXPIRE_PASSWORD")
        if uac & 8388608: flags.append("PASSWORD_EXPIRED")
        if uac & 2097152: flags.append("TRUSTED_TO_AUTH_FOR_DELEGATION")
        return flags

    def _sync_users(self, client: LDAPClient, include_disabled: bool = False) -> int:
        """Fetch AD users, upsert into local DB."""
        ad_entries = client.search_users(include_disabled=include_disabled)
        count = 0
        for entry in ad_entries:
            attrs = entry.get("attributes", entry)
            dn = self._val(attrs, "distinguishedName", "")

            existing = self.db.query(User).filter(User.distinguished_name == dn).first()
            # Decode userAccountControl
            uac = self._val(attrs, "userAccountControl")
            try:
                uac_int = int(uac) if uac else 0
            except (ValueError, TypeError):
                uac_int = 0
            if uac_int & 16:
                user_status = "locked"
            elif uac_int & 2:
                user_status = "disabled"
            else:
                user_status = "active"

            uac_flags = ", ".join(self._decode_uac_flags(uac_int))
            lockout_time_raw = self._val(attrs, "lockoutTime")
            lockout_time = None
            if lockout_time_raw:
                try:
                    lt_int = int(lockout_time_raw)
                    if lt_int != 0:
                        lockout_time = self._filetime_to_datetime(lt_int)
                except (ValueError, TypeError):
                    # ldap3 may auto-convert FILETIME to an ISO datetime string
                    try:
                        dt_str = str(lockout_time_raw).replace(" ", "T")
                        lockout_time = datetime.fromisoformat(dt_str)
                        # Treat Windows epoch (1601-01-01) as "not locked"
                        if lockout_time and lockout_time.year <= 1601:
                            lockout_time = None
                    except Exception:
                        pass

            # AD does not reliably set UAC LOCKOUT bit (16) for password-policy lockouts.
            # lockoutTime IS replicated (Win2003+) but may lag. badPasswordTime IS
            # replicated across all DCs — reliable cross-DC lockout signal.
            # badPwdCount is DC-local (NOT replicated) — use as threshold hint only.
            bad_pwd_raw = self._val(attrs, "badPwdCount")
            bad_pwd_count = None
            if bad_pwd_raw is not None:
                try:
                    bad_pwd_count = int(bad_pwd_raw)
                except (ValueError, TypeError):
                    pass

            bad_password_time_raw = self._val(attrs, "badPasswordTime")
            bad_password_time = None
            if bad_password_time_raw:
                try:
                    bpt_int = int(bad_password_time_raw)
                    if bpt_int != 0:
                        bad_password_time = self._filetime_to_datetime(bpt_int)
                except (ValueError, TypeError):
                    try:
                        dt_str = str(bad_password_time_raw).replace(" ", "T")
                        bad_password_time = datetime.fromisoformat(dt_str)
                        if bad_password_time and bad_password_time.year <= 1601:
                            bad_password_time = None
                    except Exception:
                        pass

            # Threshold: default AD lockout threshold, configurable
            from app.config import settings as app_settings
            lockout_threshold = app_settings.LOCKOUT_THRESHOLD
            if user_status == "active" and (
                lockout_time is not None
                or (bad_pwd_count is not None and bad_pwd_count >= lockout_threshold)
            ):
                user_status = "locked"

            if existing:
                existing.sam_account_name = self._val(attrs, "sAMAccountName", existing.sam_account_name)
                existing.display_name = self._val(attrs, "displayName", existing.display_name)
                existing.email = self._val(attrs, "mail", existing.email)
                existing.department = self._val(attrs, "department", existing.department)
                existing.user_account_control = uac_int
                existing.status = user_status
                existing.uac_flags = uac_flags
                existing.lockout_time = lockout_time
                existing.bad_pwd_count = bad_pwd_count
            else:
                user = User(
                    sam_account_name=self._val(attrs, "sAMAccountName", ""),
                    display_name=self._val(attrs, "displayName"),
                    email=self._val(attrs, "mail"),
                    department=self._val(attrs, "department"),
                    distinguished_name=dn,
                    user_account_control=uac_int,
                    status=user_status,
                    uac_flags=uac_flags,
                    lockout_time=lockout_time,
                    bad_pwd_count=bad_pwd_count,
                )
                self.db.add(user)
            count += 1

            if count % 100 == 0:
                self.db.commit()

        self.db.commit()
        return count

    def _sync_groups(self, client: LDAPClient) -> int:
        """Fetch AD groups, upsert into local DB."""
        ad_entries = client.search_groups()
        count = 0
        for entry in ad_entries:
            attrs = entry.get("attributes", entry)
            dn = self._val(attrs, "distinguishedName", "")

            group_type_raw = self._val(attrs, "groupType", 0)
            try:
                group_type_raw = int(group_type_raw)
            except (ValueError, TypeError):
                group_type_raw = 0
            group_type, group_scope = LDAPClient.decode_group_type(group_type_raw)

            existing = self.db.query(ADGroup).filter(ADGroup.distinguished_name == dn).first()
            if existing:
                existing.name = self._val(attrs, "sAMAccountName", existing.name)
                existing.display_name = self._val(attrs, "displayName", existing.display_name)
                existing.group_type = group_type
                existing.group_scope = group_scope
                existing.description = self._val(attrs, "description", existing.description)
                existing.email = self._val(attrs, "mail", existing.email)
                # NOTE: end_user_email and jira_ticket are local-only, never overwritten by sync
            else:
                new_group = ADGroup(
                    name=self._val(attrs, "sAMAccountName", ""),
                    display_name=self._val(attrs, "displayName"),
                    distinguished_name=dn,
                    group_type=group_type,
                    group_scope=group_scope,
                    description=self._val(attrs, "description"),
                    email=self._val(attrs, "mail"),
                )
                self.db.add(new_group)
            count += 1

            if count % 100 == 0:
                self.db.commit()

        self.db.commit()
        return count

    def _sync_group_memberships(self, client: LDAPClient) -> int:
        """Sync group memberships: delete-and-reinsert for each group."""
        groups = self.db.query(ADGroup).all()
        count = 0

        for group in groups:
            # Fetch members from LDAP FIRST to avoid data loss on error
            try:
                member_dns = client.get_group_members(group.distinguished_name)
            except Exception:
                logger.warning(f"Failed to fetch members for group {group.name}, skipping")
                continue

            # Only delete old memberships after successful LDAP fetch
            self.db.query(GroupMembership).filter(
                GroupMembership.group_id == group.id
            ).delete()

            for member_dn in member_dns:
                user = self.db.query(User).filter(
                    User.distinguished_name == member_dn
                ).first()

                membership = GroupMembership(
                    group_id=group.id,
                    user_id=user.id if user else None,
                    member_dn=member_dn,
                )
                self.db.add(membership)
                count += 1

            # Commit after each group to avoid partial-group data
            self.db.commit()
        return count

    def list_logs(
        self,
        params: PaginationParams,
        sync_type: str | None = None,
        status: str | None = None,
    ) -> PaginatedResponse:
        query = self.db.query(SyncLog)
        if sync_type:
            query = query.filter(SyncLog.sync_type == sync_type)
        if status:
            query = query.filter(SyncLog.status == status)

        query = query.order_by(SyncLog.started_at.desc())
        total = query.count()
        logs = query.offset((params.page - 1) * params.page_size).limit(params.page_size).all()
        return PaginatedResponse(
            items=logs,
            total=total,
            page=params.page,
            page_size=params.page_size,
            total_pages=max(1, ceil(total / params.page_size)),
        )

    def get_status(self):
        latest = self.db.query(SyncLog).order_by(SyncLog.started_at.desc()).first()
        running = self.db.query(SyncLog).filter(SyncLog.status == "running").first()
        return {
            "is_running": running is not None,
            "latest_sync": latest,
        }

    @staticmethod
    def _filetime_to_datetime(ft: int) -> datetime | None:
        """Convert Windows FILETIME (100-ns intervals since 1601-01-01) to datetime.
        Returns None for zero and never-expire sentinel values."""
        if ft == 0 or ft == 0x7FFFFFFFFFFFFFFF:
            return None
        return datetime(1601, 1, 1, tzinfo=timezone.utc) + timedelta(microseconds=ft // 10)

    def _load_ldap_config(self) -> LDAPConfig:
        """Read LDAP connection settings from the settings table."""
        settings = {s.key: s.value for s in self.db.query(Setting).filter(Setting.key.like("ldap_%")).all()}
        return LDAPConfig(
            server_url=settings.get("ldap_server_url", "ldaps://localhost:636"),
            domain=settings.get("ldap_domain", ""),
            admin_username=settings.get("ldap_admin_username", ""),
            admin_password=settings.get("ldap_admin_password", ""),
            base_dn=settings.get("ldap_base_dn", ""),
            use_ssl=settings.get("ldap_use_ssl", "true").lower() == "true",
            tls_validate=settings.get("ldap_tls_validate", "CERT_NONE"),
            receive_timeout=int(settings.get("ldap_receive_timeout", 300)),
            page_size=int(settings.get("ldap_page_size", 500)),
        )

    def _get_setting(self, key: str) -> str | None:
        s = self.db.query(Setting).filter(Setting.key == key).first()
        return s.value if s else None
