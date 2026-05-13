from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session, select

from app.config import get_settings
from app.db.models import User
from app.db.session import get_session
from app.services.role_config import ui_access_for_email

bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(*, subject: str, expires_minutes: int | None = None) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.jwt_expire_minutes
    )
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> str:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        sub = payload.get("sub")
        if not isinstance(sub, str):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return sub
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        ) from exc


def get_current_user(
    creds: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)],
    session: Annotated[Session, Depends(get_session)],
) -> User:
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    email = decode_token(creds.credentials)
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def get_current_user_optional(
    creds: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)],
    session: Annotated[Session, Depends(get_session)],
) -> Optional[User]:
    if creds is None or creds.scheme.lower() != "bearer":
        return None
    try:
        email = decode_token(creds.credentials)
    except HTTPException:
        return None
    return session.exec(select(User).where(User.email == email)).first()


def require_full_ui_access(
    current: Annotated[User, Depends(get_current_user)],
) -> User:
    """Manager/SME (per role_config.json) only — for session create and user listing."""
    _, access = ui_access_for_email(current.email)
    if access != "full":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager or SME access required for this action",
        )
    return current
