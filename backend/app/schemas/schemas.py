##backend/app/schemas/schemas.py

from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List, Literal
from uuid import UUID
from datetime import datetime

Red = Literal["BEP20","ERC20","TRC20","Polygon","Arbitrum"]
TipoDoc = Literal["DNI","LC","LE","CI","Pasaporte"]
TipoAddr = Literal["ENVIO","ENTREGA"]

class AddressIn(BaseModel):
    tipo: TipoAddr
    calle_y_numero: str
    ciudad: Optional[str] = ""
    provincia: Optional[str] = ""
    pais: Optional[str] = ""
    cp: Optional[str] = ""

class CryptoWalletIn(BaseModel):
    red: Red
    address: str

class BankingInfoIn(BaseModel):
    cbu_o_alias: str

class UserCreate(BaseModel):
    nombre: str
    apellido: str
    tipo_doc: TipoDoc
    nro_doc: str
    email: EmailStr
    tel: Optional[str] = None
    palabra_seg: Optional[str] = None
    password: str
    acepta_terminos: bool
    domicilio_envio: Optional[AddressIn] = None
    domicilio_entrega: Optional[AddressIn] = None
    banking: Optional[BankingInfoIn] = None
    wallets: Optional[List[CryptoWalletIn]] = None
    roles: List[Literal["COMPRADOR","VENDEDOR"]] = ["COMPRADOR"]

    @field_validator("nro_doc")
    def validar_doc(cls, v):
        if not (6 <= len(v) <= 12): raise ValueError("Documento inválido")
        return v

    @field_validator("domicilio_envio")
    def validar_envio(cls, v):
        if v and v.tipo != "ENVIO": raise ValueError("domicilio_envio.tipo debe ser ENVIO")
        return v

    @field_validator("domicilio_entrega")
    def validar_entrega(cls, v):
        if v and v.tipo != "ENTREGA": raise ValueError("domicilio_entrega.tipo debe ser ENTREGA")
        return v

class UserOut(BaseModel):
    id: UUID
    nombre: str
    apellido: str
    email: EmailStr
    roles: List[str]
    creado_en: datetime
