from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.dependencies import get_current_user
from app.services.settings_service import SettingsService
from app.ldap_client import LDAPClient
from app.schemas.setting import SettingsUpdateRequest, PasswordChangeRequest
from pydantic import BaseModel


class DiscoverRequest(BaseModel):
    domain: str

router = APIRouter(prefix="/api/settings", tags=["Settings"])


@router.get("/")
def get_settings(
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """Get all settings (sensitive values masked)."""
    return SettingsService(db).get_all_settings()


@router.put("/")
def update_settings(
    request: SettingsUpdateRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """Bulk update settings."""
    SettingsService(db).update_settings(request.settings)
    # Notify scheduler of schedule changes
    if "sync_schedule" in request.settings:
        from app.scheduler import update_schedule
        update_schedule(request.settings["sync_schedule"])
    if "sync_user_status_schedule" in request.settings:
        from app.scheduler import update_schedule
        update_schedule(
            request.settings["sync_user_status_schedule"],
            job_id="ldap_user_status_sync_job",
        )
    return {"message": "Settings updated successfully"}


@router.post("/change-password")
def change_password(
    request: PasswordChangeRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    SettingsService(db).change_password(request.current_password, request.new_password)
    return {"message": "Password changed successfully"}


@router.post("/discover-ad")
def discover_ad(
    request: DiscoverRequest,
    _: dict = Depends(get_current_user),
):
    """Auto-discover AD server URL and Base DN from a domain name."""
    domain = request.domain.strip()
    if not domain:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Domain is required")
    try:
        result = LDAPClient.discover_from_domain(domain)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Discovery failed: {str(e)}",
        )


@router.post("/test-connection")
def test_ldap_connection(
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """Test the LDAP connection using saved settings."""
    from app.services.settings_service import SettingsService
    svc = SettingsService(db)
    ldap_config_raw = svc.get_ldap_config()
    from app.ldap_client import LDAPConfig
    ldap_config = LDAPConfig(
        server_url=ldap_config_raw.get("server_url", ""),
        domain=ldap_config_raw.get("domain", ""),
        admin_username=ldap_config_raw.get("admin_username", ""),
        admin_password=ldap_config_raw.get("admin_password", ""),
        base_dn=ldap_config_raw.get("base_dn", ""),
        use_ssl=ldap_config_raw.get("use_ssl", "true").lower() == "true",
    )

    if not ldap_config.server_url or not ldap_config.admin_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LDAP settings not configured. Please save LDAP config first.",
        )

    try:
        with LDAPClient(ldap_config) as client:
            result = client.test_connection()
        if result:
            return {"status": "success", "message": f"Connected to {ldap_config.server_url}"}
        else:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Connection failed. Check server URL, credentials, and network.",
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Connection failed: {str(e)}",
        )


@router.post("/discover-locations")
def discover_locations(
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """Discover available sync locations (cities) from AD."""
    from app.services.settings_service import SettingsService
    svc = SettingsService(db)
    ldap_config_raw = svc.get_ldap_config()
    from app.ldap_client import LDAPConfig
    ldap_config = LDAPConfig(
        server_url=ldap_config_raw.get("server_url", ""),
        domain=ldap_config_raw.get("domain", ""),
        admin_username=ldap_config_raw.get("admin_username", ""),
        admin_password=ldap_config_raw.get("admin_password", ""),
        base_dn=ldap_config_raw.get("base_dn", ""),
        use_ssl=ldap_config_raw.get("use_ssl", "true").lower() == "true",
    )

    if not ldap_config.server_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LDAP settings not configured. Please save LDAP config first.",
        )

    try:
        with LDAPClient(ldap_config) as client:
            locations = client.discover_locations()
        return {"locations": locations}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Location discovery failed: {str(e)}",
        )
