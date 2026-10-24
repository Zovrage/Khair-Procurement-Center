import secrets

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models import User
from app.schemas.auth import LoginRequest, LoginResponse
from app.security import authenticate_user, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный логин или пароль")
    token = create_access_token(user.username)
    csrf_token = secrets.token_urlsafe(32)
    max_age = settings.access_token_expire_minutes * 60
    response.set_cookie(
        "khair_session",
        token,
        max_age=max_age,
        httponly=True,
        secure=settings.app_env == "production",
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        "khair_csrf",
        csrf_token,
        max_age=max_age,
        httponly=False,
        secure=settings.app_env == "production",
        samesite="strict",
        path="/",
    )
    return LoginResponse(username=user.username, full_name=user.full_name, role=user.role.value)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response, current_user: User = Depends(get_current_user)):
    response.delete_cookie("khair_session", path="/", httponly=True, samesite="lax")
    response.delete_cookie("khair_csrf", path="/", httponly=False, samesite="strict")


@router.get("/me")
def current_user_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "role": current_user.role.value,
    }
