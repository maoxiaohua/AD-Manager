from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import verify_token

security_scheme = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> dict:
    """Validates JWT and returns payload. Raises 401 if invalid or expired."""
    payload = verify_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload
