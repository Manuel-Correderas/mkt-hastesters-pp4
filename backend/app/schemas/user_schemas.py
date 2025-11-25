# backend/app/schemas/user_schemas.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Literal
from datetime import datetime

Red = Literal["BEP20","ERC20","TRC20","Polygon","Arbitrum"]
TipoDoc = Literal["DNI","LC","LE","CI","Pasaporte"]
TipoAddr = Literal["ENVIO","ENTREGA"]
RoleCode = Literal["COMPRADOR", "VENDEDOR", "ADMIN"]


class AddressIn(BaseModel):
    tipo: TipoAddr
    calle_y_numero: str
    ciudad: Optional[str] = ""
    provincia: Optional[str] = ""
    pais: Optional[str] = ""
    cp: Optional[str] = ""

class BankingIn(BaseModel):
    cbu_o_alias: str

class CryptoWalletIn(BaseModel):
    red: Red
    address: str

class UserCreate(BaseModel):
    nombre: str
    apellido: str
    tipo_doc: TipoDoc
    nro_doc: str
    email: EmailStr
    tel: Optional[str] = None
    palabra_seg: Optional[str] = None
    password: str = Field(min_length=6)
    acepta_terminos: bool

    domicilio_envio: Optional[AddressIn] = None
    domicilio_entrega: Optional[AddressIn] = None
    banking: Optional[BankingIn] = None
    wallets: Optional[List[CryptoWalletIn]] = None
    roles: List[RoleCode]

class UserOut(BaseModel):
    # En tu modelo SQLAlchemy usás id=str (uuid4 string) ⇒ mantenemos str
    id: str
    nombre: str
    apellido: str
    email: EmailStr
    roles: List[str]
    creado_en: datetime

    class Config:
        from_attributes = True
