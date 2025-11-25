##backend/app/models/models.py

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, DateTime, ForeignKey, UniqueConstraint, Integer, Text, Numeric
from uuid import uuid4
from datetime import datetime
from ..db import Base



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
    ##
    estado: Mapped[str] = mapped_column(String(20), default="ACTIVO")  
    # ACTIVO | REVISION | BLOQUEADO

    dni_bloqueado: Mapped[bool] = mapped_column(Boolean, default=False)
    addresses = relationship("Address", back_populates="user", cascade="all,delete-orphan")
    banking = relationship("BankingInfo", uselist=False, back_populates="user", cascade="all,delete-orphan")
    wallets = relationship("CryptoWallet", back_populates="user", cascade="all,delete-orphan")
    kyc_docs = relationship("KYCDocument", back_populates="user", cascade="all,delete-orphan")
    roles = relationship("UserRole", back_populates="user", cascade="all,delete-orphan")
    ##
    premium: Mapped[int] = mapped_column(Integer, default=0)
    # para recuperación de contraseña por código
    reset_code_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reset_code_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

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
##############
##############
##############
class Category(Base):
    __tablename__ = "categories"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    name: Mapped[str] = mapped_column(String(80), index=True)
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    parent = relationship("Category", remote_side=[id])
    products = relationship("Product", back_populates="category")

class Product(Base):
    __tablename__ = "products"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    seller_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    description: Mapped[str | None] = mapped_column(Text, default=None)
    price: Mapped[int] = mapped_column(Integer)                 # en centavos o entero ARS
    stock: Mapped[int] = mapped_column(Integer, default=0)
    condition: Mapped[str] = mapped_column(String(10), default="NUEVO")  # NUEVO/USADO
    rating: Mapped[float] = mapped_column(Numeric(3,1), default=0)       # 0..10
    sold_count: Mapped[int] = mapped_column(Integer, default=0)
    image_url: Mapped[str | None] = mapped_column(String(255), default=None)
    features: Mapped[str | None] = mapped_column(Text)


    # taxonomía sencilla
    category_id: Mapped[str | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    subcategory: Mapped[str | None] = mapped_column(String(80), nullable=True)

    # metadatos
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    seller = relationship("User", backref="products")
    category = relationship("Category", back_populates="products")
    images = relationship("ProductImage", back_populates="product", cascade="all,delete-orphan")
    comments = relationship("ProductComment", back_populates="product", cascade="all,delete-orphan")
    ####
    pay_method: Mapped[str | None] = mapped_column(String(40))
    network: Mapped[str | None] = mapped_column(String(40))
    alias: Mapped[str | None] = mapped_column(String(120))
    wallet: Mapped[str | None] = mapped_column(String(200))
#####

class ProductImage(Base):
    __tablename__ = "product_images"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    url: Mapped[str] = mapped_column(String(255))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    product = relationship("Product", back_populates="images")


class Cart(Base):
    __tablename__ = "carts"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    items = relationship("CartItem", back_populates="cart", cascade="all,delete-orphan")

class CartItem(Base):
    __tablename__ = "cart_items"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    cart_id: Mapped[str] = mapped_column(ForeignKey("carts.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[str] = mapped_column(String, index=True)
    name: Mapped[str] = mapped_column(String(180))
    price: Mapped[int] = mapped_column(Integer)                # entero ARS
    qty: Mapped[int] = mapped_column(Integer, default=1)
    image: Mapped[str | None] = mapped_column(String(255), default=None)
    seller: Mapped[str] = mapped_column(String(120))           # nombre vendedor snapshot
    stock_snapshot: Mapped[int] = mapped_column(Integer, default=0)

    cart = relationship("Cart", back_populates="items")

# --- AGREGAR ABAJO DE Comment ---
class Order(Base):
    __tablename__ = "orders"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    user_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="Entregado")  # Entregado|En camino|Pendiente
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    total_amount: Mapped[int] = mapped_column(Integer, default=0)

    items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )


    payments: Mapped[list["Payment"]] = relationship(
        "Payment", back_populates="order", cascade="all, delete-orphan"
    )


class OrderItem(Base):
    __tablename__ = "order_items"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    order_id: Mapped[str] = mapped_column(String(36), ForeignKey("orders.id"), nullable=False)

    product_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    product_name: Mapped[str] = mapped_column(String(160), nullable=False)
    category: Mapped[str | None] = mapped_column(String(64))
    subcategory: Mapped[str | None] = mapped_column(String(64))
    seller: Mapped[str | None] = mapped_column(String(120))
    seller_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    company: Mapped[str | None] = mapped_column(String(160))

    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_price: Mapped[int] = mapped_column(Integer, default=0)

    order: Mapped["Order"] = relationship("Order", back_populates="items")

class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(30), default="MP")    # MP/TARJETA/TRANSFER
    status: Mapped[str] = mapped_column(String(20), default="PENDIENTE")  # PENDIENTE/APROBADO/RECHAZADO
    amount: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ##
    # 👇 NUEVO
    tx_ref: Mapped[str | None] = mapped_column(String(80), default=None)
    order = relationship("Order", back_populates="payments")

class ProductComment(Base):
    __tablename__ = "product_comments"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    rating: Mapped[int] = mapped_column(Integer)  # 1..10
    text: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="comments")
    user = relationship("User", backref="product_comments")

Comment = ProductComment
