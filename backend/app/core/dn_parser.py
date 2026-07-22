"""Utilities for parsing AD Distinguished Names."""


def parse_dn(dn: str) -> dict:
    """
    Parse an AD Distinguished Name into components.

    Example: CN=PC01,OU=Workstations,OU=City,OU=Region,OU=locations,DC=company,DC=com
    Returns: {
        'cn': 'PC01',
        'ou_path': ['Workstations', 'City', 'Region', 'locations'],
        'site': 'City',       # city-level OU (above region)
        'region': 'Region',
        'department': 'Workstations',      # team/department OU (below city)
        'container': 'Workstations',
        'dc': ['company', 'com'],
    }
    """
    result = {
        "cn": "",
        "ou_path": [],
        "site": "",
        "region": "",
        "department": "",
        "container": "",
        "dc": [],
    }

    if not dn:
        return result

    parts = [p.strip() for p in dn.split(",")]

    for part in parts:
        if "=" not in part:
            continue
        key, _, value = part.partition("=")
        key = key.strip().upper()
        value = value.strip()

        if key == "CN":
            result["cn"] = value
        elif key == "OU":
            result["ou_path"].append(value)
        elif key == "DC":
            result["dc"].append(value)

    ous = result["ou_path"]
    # Site = OU at position before region, where region is before 'locations'
    # Pattern: OU=Department,OU=Site,OU=Region,OU=locations
    if "locations" in ous:
        loc_idx = ous.index("locations")
        if loc_idx >= 2:
            result["region"] = ous[loc_idx - 1] if loc_idx >= 1 else ""
            result["site"] = ous[loc_idx - 2] if loc_idx >= 2 else ""
            result["department"] = ous[loc_idx - 3] if loc_idx >= 3 else ""
        elif loc_idx >= 1:
            result["region"] = ous[loc_idx - 1]
            result["site"] = ""
    elif len(ous) >= 2:
        result["region"] = ous[-1] if ous else ""
        result["site"] = ous[-2] if len(ous) >= 2 else ""
        result["department"] = ous[-3] if len(ous) >= 3 else ""

    if ous:
        result["container"] = ous[0]

    return result
