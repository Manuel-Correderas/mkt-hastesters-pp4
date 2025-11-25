# backend/app/routers/routes_premium.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..deps import get_db, get_current_user
from ..models.models import User

router = APIRouter(prefix="/premium", tags=["premium"])


# ======================================================
#  CONFIRMAR PAGO — activa premium del usuario
# ======================================================
@router.post("/confirm")
def confirm_premium_payment(
    payload: dict,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    tx_hash = payload.get("tx_hash")
    amount = payload.get("amount")
    network = payload.get("network")

    if not tx_hash:
        raise HTTPException(400, "Falta hash de transacción")
    if amount != 20:
        raise HTTPException(400, "Monto inválido. Debe ser 20 USDT")

    # Marcar el usuario como premium
    user.premium = 1
    db.add(user)
    db.commit()

    return {
        "status": "ok",
        "message": "Premium activado correctamente",
        "tx_hash": tx_hash,
        "network": network,
        "user_id": user.id
    }

# backend/app/routers/routes_premium.py
@router.get("/status")
def premium_status(
    user: User = Depends(get_current_user),
):
    return {"active": bool(user.premium)}
