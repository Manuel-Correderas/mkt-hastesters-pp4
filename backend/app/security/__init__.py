# backend/app/security/__init__.py
import os
from dotenv import load_dotenv
from fastapi import HTTPException, status
from passlib.context import CryptContext

from ..models.models import User
from .tokens import create_access_token, SECRET_KEY, ALGORITHM

# ============================
# Cargar variables del .env
# ============================
load_dotenv()

# ============================
# Hasheo de contraseñas (UN SOLO SISTEMA)
# ============================
pwd_ctx = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(p: str) -> str:
    return pwd_ctx.hash(p)


def verify_password(p: str, h: str) -> bool:
    return pwd_ctx.verify(p, h)


# ============================
# Helper de rol VENDEDOR
# (NO usa Depends ni get_current_user)
# ============================
def require_vendor(user: User) -> None:
    codes = {
        ur.role.code
        for ur in getattr(user, "roles", [])
        if getattr(ur, "role", None)
    }

    if "VENDEDOR" not in codes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol VENDEDOR.",
        )


__all__ = [
    "hash_password",
    "verify_password",
    "require_vendor",
    "create_access_token",
    "SECRET_KEY",
    "ALGORITHM",
]
