# backend/app/deps.py
from typing import Generator

from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from jose import jwt

from .db import SessionLocal
from .models.models import User
from .security.tokens import SECRET_KEY, ALGORITHM  # 👈 mismo secret/algoritmo que los tokens


def get_db() -> Generator[Session, None, None]:
    """
    Crea y cierra la sesión de base de datos por request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    """
    Obtiene el usuario actual a partir del header Authorization: Bearer <token>.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falta token",
        )

    token = authorization.split(" ", 1)[1]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )

    uid = payload.get("sub")
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )

    user = db.query(User).filter(User.id == uid).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
        )

    return user


def current_admin_or_self(
    user_id: str,
    user: User = Depends(get_current_user),
) -> User:
    """
    Permite acceder si:
    - el usuario actual es ADMIN, o
    - es el mismo user_id que el del recurso.
    """
    codes = {
        ur.role.code
        for ur in getattr(user, "roles", [])
        if getattr(ur, "role", None)
    }

    if user.id == user_id or "ADMIN" in codes:
        return user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="No autorizado",
    )
def require_vendor(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency para rutas de vendedor (VENDEDOR).
    """
    roles = {
        ur.role.code
        for ur in getattr(current_user, "roles", [])
        if getattr(ur, "role", None)
    }

    if "VENDEDOR" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol VENDEDOR."
        )

    return current_user
