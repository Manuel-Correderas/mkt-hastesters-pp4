from datetime import datetime, timedelta
import secrets
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.db import get_db
from backend.app.models.models import User
from backend.app.security import hash_password, verify_password  # verify_password ya lo usás en login



router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/forgot/start")
def forgot_start(payload: dict, db: Session = Depends(get_db)):
    email = (payload.get("email") or "").strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="Email requerido")

    user = db.query(User).filter(User.email == email).first()

    # siempre 200 aunque no exista
    if not user:
        return {"ok": True}

    temp_password = secrets.token_urlsafe(6)

    # ✅ guardamos la TEMPORAL aparte, NO tocamos la real
    user.reset_code_hash = hash_password(temp_password)
    user.reset_code_expires_at = datetime.utcnow() + timedelta(minutes=15)

    db.commit()

    return {
        "ok": True,
        "temp_password": temp_password,
        "expires_in_minutes": 15
    }

@router.post("/forgot/finish")
def forgot_finish(payload: dict, db: Session = Depends(get_db)):
    email = (payload.get("email") or "").strip().lower()
    code = (payload.get("code") or "").strip()
    new_password = payload.get("new_password") or ""

    if not email or not code or not new_password:
        raise HTTPException(status_code=400, detail="Datos incompletos")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        return {"ok": True}

    if not user.reset_code_expires_at or user.reset_code_expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Contraseña temporal expirada")

    # ✅ validamos contra reset_code_hash, no contra password real
    if not user.reset_code_hash or not verify_password(code, user.reset_code_hash):
        raise HTTPException(status_code=400, detail="Contraseña temporal inválida")

    # setear nueva real
    user.password_hash = hash_password(new_password)

    # limpiar reset
    user.reset_code_expires_at = None
    user.reset_code_hash = None

    db.commit()
    return {"ok": True}
