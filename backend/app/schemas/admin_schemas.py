# backend/app/schemas/admin_schemas.py
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr

class AdminUserOut(BaseModel):
    id: str
    nombre: str
    apellido: str
    email: EmailStr
    tipo_doc: str
    nro_doc: str
    estado: str
    dni_bloqueado: bool
    creado_en: datetime

    class Config:
        from_attributes = True


class AdminOrderOut(BaseModel):
    id: str
    created_at: datetime
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    total_amount: int
    payment_status: Optional[str] = None
    tx_ref: Optional[str] = None
