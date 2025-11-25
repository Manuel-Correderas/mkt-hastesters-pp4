# backend/app/routers/routes_auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from ..deps import get_db
from ..crud.user_crud import get_user_by_email
from ..security import verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginPayload(BaseModel):
    email: EmailStr
    password: str


@router.post("/login")
def login(payload: LoginPayload, db: Session = Depends(get_db)):
    user = get_user_by_email(db, payload.email)

    # ================
    # 1) Usuario existe
    # ================
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )

    # ================
    # 2) DNI BLOQUEADO
    # ================
    # IMPORTANTE: por defecto el campo es 0
    # Si está en 1 → NO puede loguearse
    if getattr(user, "dni_bloqueado", 0) == 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El DNI del usuario está bloqueado. No podés iniciar sesión."
        )

    # ================
    # 3) Crear token
    # ================
    access_token = create_access_token({"sub": user.id})

    return {
        "ok": True,
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "roles": [ur.role.code for ur in user.roles],
            "premium": int(user.premium or 0),
            "dni_bloqueado": int(user.dni_bloqueado or 0)
        }
    }
