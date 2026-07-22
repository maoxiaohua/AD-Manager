from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import create_access_token, verify_password, hash_password
from app.schemas.auth import LoginRequest, LoginResponse, VerifyResponse
from app.models import Setting
import time
from collections import defaultdict

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# In-memory rate limiting for login attempts
_failed_attempts: dict[str, list[float]] = defaultdict(list)
_MAX_ATTEMPTS = 5
_WINDOW_SECONDS = 300  # 5 minutes
_DELAY_SECONDS = 3


def get_admin_password_hash(db: Session) -> str:
    """Get admin password hash from settings, or seed default if not exists."""
    from app.config import settings as app_settings
    setting = db.query(Setting).filter(Setting.key == "admin_password_hash").first()
    if not setting:
        hashed = hash_password(app_settings.DEFAULT_ADMIN_PASSWORD)
        db.add(Setting(key="admin_password_hash", value=hashed))
        db.commit()
        return hashed
    return setting.value


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, req: Request, db: Session = Depends(get_db)):
    # Rate limiting: check recent failures
    client_ip = req.client.host if req.client else "unknown"
    now = time.time()
    attempts = [t for t in _failed_attempts[client_ip] if now - t < _WINDOW_SECONDS]
    _failed_attempts[client_ip] = attempts
    if len(attempts) >= _MAX_ATTEMPTS:
        time.sleep(_DELAY_SECONDS)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed attempts. Please wait and try again.",
        )

    password_hash = get_admin_password_hash(db)
    if not verify_password(request.password, password_hash):
        _failed_attempts[client_ip].append(now)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password",
        )
    token = create_access_token()
    return LoginResponse(access_token=token)


@router.get("/verify", response_model=VerifyResponse)
def verify(current_user: dict = Depends(get_current_user)):
    """Verify JWT token validity."""
    return VerifyResponse(valid=True)
