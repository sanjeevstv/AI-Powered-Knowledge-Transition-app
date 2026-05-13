from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.db.models import User
from app.db.session import get_session
from app.deps import (
    create_access_token,
    get_current_user,
    hash_password,
    require_full_ui_access,
    verify_password,
)
from app.schemas import LoginRequest, MeResponse, RegisterRequest, TokenResponse, UserPublic
from app.services.role_config import get_config_role_raw, ui_access_for_email

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, session: Session = Depends(get_session)) -> TokenResponse:
    user = session.exec(select(User).where(User.email == body.email)).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(subject=user.email)
    return TokenResponse(access_token=token)


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, session: Session = Depends(get_session)) -> UserPublic:
    exists = session.exec(select(User).where(User.email == body.email)).first()
    if exists:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        role=body.role,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return UserPublic.model_validate(user)


@router.get("/me", response_model=MeResponse)
def me(user: User = Depends(get_current_user)) -> MeResponse:
    _, ui_access = ui_access_for_email(user.email)
    return MeResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        config_role=get_config_role_raw(user.email),
        ui_access=ui_access,
    )


@router.get("/users", response_model=list[UserPublic])
def list_users(
    session: Session = Depends(get_session),
    _: User = Depends(require_full_ui_access),
) -> list[UserPublic]:
    """List users for assigning KT owners (requirements: assign KT owners)."""
    users = list(session.exec(select(User)).all())
    return [UserPublic.model_validate(u, from_attributes=True) for u in users]
