from db import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, DateTime, ForeignKey, UniqueConstraint, Integer
from uuid import uuid4
from datetime import datetime

def _id(): return str(uuid4())

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    nombre: Mapped[str] = mapped_column(String(80))
    apellido: Mapped[str] = mapped_column(String(80))
    tipo_doc: Mapped[str] = mapped_column(String(20))
    nro_doc: Mapped[str] = mapped_column(String(20), unique=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    tel: Mapped[str] = mapped_column(String(40), nullable=True)
    palabra_seg: Mapped[str] = mapped_column(String(120), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    acepta_terminos: Mapped[bool] = mapped_column(Boolean, default=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    actualizado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    addresses = relationship("Address", back_populates="user", cascade="all,delete-orphan")
    banking = relationship("BankingInfo", uselist=False, back_populates="user", cascade="all,delete-orphan")
    wallets = relationship("CryptoWallet", back_populates="user", cascade="all,delete-orphan")
    kyc_docs = relationship("KYCDocument", back_populates="user", cascade="all,delete-orphan")
    roles = relationship("UserRole", back_populates="user", cascade="all,delete-orphan")

class Address(Base):
    __tablename__ = "addresses"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    tipo: Mapped[str] = mapped_column(String(10))  # ENVIO/ENTREGA
    calle_y_numero: Mapped[str] = mapped_column(String(120))
    ciudad: Mapped[str] = mapped_column(String(80), default="")
    provincia: Mapped[str] = mapped_column(String(80), default="")
    pais: Mapped[str] = mapped_column(String(80), default="")
    cp: Mapped[str] = mapped_column(String(15), default="")
    user = relationship("User", back_populates="addresses")
    __table_args__ = (UniqueConstraint("user_id", "tipo", name="uq_address_user_tipo"),)

class BankingInfo(Base):
    __tablename__ = "banking_infos"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    cbu_o_alias: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    user = relationship("User", back_populates="banking")

class CryptoWallet(Base):
    __tablename__ = "crypto_wallets"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    red: Mapped[str] = mapped_column(String(20))
    address: Mapped[str] = mapped_column(String(120))
    __table_args__ = (UniqueConstraint("user_id","red", name="uq_wallet_user_red"),)
    user = relationship("User", back_populates="wallets")

class KYCDocument(Base):
    __tablename__ = "kyc_documents"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    tipo: Mapped[str] = mapped_column(String(20), default="OTRO")
    filename: Mapped[str] = mapped_column(String(180))
    mime: Mapped[str] = mapped_column(String(50))
    size_bytes: Mapped[int]
    storage_path: Mapped[str] = mapped_column(String(255))
    subido_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="kyc_docs")

class Role(Base):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)  # COMPRADOR/VENDEDOR/ADMIN
    nombre: Mapped[str] = mapped_column(String(40))

class UserRole(Base):
    __tablename__ = "user_roles"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    asignado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="roles")
    role = relationship("Role")
