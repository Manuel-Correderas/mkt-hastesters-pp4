# backend/app/routers/routes_admin.py

from datetime import datetime, date, time, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from ..deps import get_db, get_current_user
from ..models.models import User, Order, Payment
from ..schemas.admin_schemas import AdminUserOut, AdminOrderOut


router = APIRouter(prefix="/admin", tags=["admin"])


# ============================
#  DEPENDENCIA: require_admin
# ============================
def require_admin(current_user: User = Depends(get_current_user)) -> User:
    roles = {
        ur.role.code
        for ur in getattr(current_user, "roles", [])
        if getattr(ur, "role", None)
    }
    if "ADMIN" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol ADMIN."
        )
    return current_user

AdminDep = Depends(require_admin)



# Se usa en los endpoints como parámetro `admin=AdminDep`
AdminDep = Depends(require_admin)


# ==============
#   USUARIOS
# ==============
@router.get("/users", response_model=List[AdminUserOut])
def list_users(
    estado: str | None = Query(None, description="ACTIVO / REVISION / BLOQUEADO"),
    solo_nuevos: bool = Query(False),
    dias: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db),
    admin=AdminDep,  # solo ADMIN
):
    q = db.query(User)

    if estado:
        q = q.filter(User.estado == estado)

    if solo_nuevos:
        corte = datetime.utcnow() - timedelta(days=dias)
        q = q.filter(User.creado_en >= corte)

    q = q.order_by(User.creado_en.desc())
    return q.all()


class EstadoUpdate(BaseModel):
    estado: str  # ACTIVO / REVISION / BLOQUEADO


@router.patch("/users/{user_id}/estado")
def update_user_estado(
    user_id: str,
    payload: EstadoUpdate,
    db: Session = Depends(get_db),
    admin=AdminDep,
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if payload.estado not in ("ACTIVO", "REVISION", "BLOQUEADO"):
        raise HTTPException(status_code=400, detail="Estado inválido")

    user.estado = payload.estado
    db.commit()
    db.refresh(user)
    return {"ok": True, "id": user.id, "estado": user.estado}


class DniBlockUpdate(BaseModel):
    dni_bloqueado: bool


@router.patch("/users/{user_id}/dni-block")
def update_user_dni_block(
    user_id: str,
    payload: DniBlockUpdate,
    db: Session = Depends(get_db),
    admin=AdminDep,
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    user.dni_bloqueado = 1 if payload.dni_bloqueado else 0
    db.commit()
    db.refresh(user)
    return {"ok": True, "id": user.id, "dni_bloqueado": bool(user.dni_bloqueado)}


# ==============
#   ÓRDENES
# ==============
@router.get("/orders", response_model=List[AdminOrderOut])
def list_orders(
    from_date: date,
    to_date: date,
    db: Session = Depends(get_db),
    admin=AdminDep,
):
    # incluir el día "hasta" completo
    start_dt = datetime.combine(from_date, time.min)
    end_dt = datetime.combine(to_date + timedelta(days=1), time.min)

    orders = (
        db.query(Order)
        .filter(Order.created_at >= start_dt, Order.created_at < end_dt)
        .options(joinedload(Order.payments))
        .all()
    )

    results: list[AdminOrderOut] = []

    for o in orders:
        payment: Payment | None = None
        if o.payments:
            payment = sorted(o.payments, key=lambda p: p.created_at)[-1]

        payment_status = payment.status if payment else None
        tx_ref = payment.tx_ref if payment else None

        user_email = None
        if o.user_id:
            user_email = db.query(User.email).filter(User.id == o.user_id).scalar()

        results.append(
            AdminOrderOut(
                id=o.id,
                created_at=o.created_at,
                user_id=o.user_id,
                user_email=user_email,
                total_amount=o.total_amount,
                payment_status=payment_status,
                tx_ref=tx_ref,
            )
        )

    return results
