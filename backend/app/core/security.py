from datetime import datetime, timedelta, timezone
import bcrypt
from jose import jwt, JWTError
from app.config import settings

ALGORITHM = "HS256"


def create_access_token() -> str:
    """Create a JWT for admin authentication.

    SECURITY NOTE: Tokens are transmitted via Bearer header and
    intended for intranet use. For internet-facing deployments,
    consider httpOnly cookies with CSRF protection.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"exp": expire, "sub": "admin", "iat": datetime.now(timezone.utc)}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())
