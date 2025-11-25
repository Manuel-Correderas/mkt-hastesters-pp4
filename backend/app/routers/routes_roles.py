# backend/app/routers/routes_roles.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..deps import get_db, get_current_user
from ..models.models import Role   

# si tenés el helper para sembrar roles:
# from ..crud.user_crud import seed_roles

router = APIRouter(prefix="/roles", tags=["roles"])

@router.get("", response_model=list[dict])
def list_roles(db: Session = Depends(get_db)):
    """Lista todos los roles existentes."""
    rows = db.query(Role).order_by(Role.id.asc()).all()
    return [{"id": r.id, "code": r.code, "nombre": r.nombre} for r in rows]

# Endpoint opcional para sembrar roles base si aún no existen.
# Descomentalo si ya tenés seed_roles implementado.
# @router.post("/seed", status_code=201)
# def seed(db: Session = Depends(get_db)):
#     seed_roles(db)
#     return {"ok": True, "seeded": ["COMPRADOR", "VENDEDOR", "ADMIN"]}
