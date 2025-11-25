##backend/app/crud/user_crud.py
from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import HTTPException
from ..models.models import (
    User,
    Role,
    UserRole,
    Address,
    BankingInfo,
    CryptoWallet,
    Order,
)
from ..security import hash_password, verify_password
from ..schemas.user_schemas import UserCreate, AddressIn, CryptoWalletIn


# --------- Lecturas básicas ---------
def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    # Preferible a query(...).get(): Session.get usa PK directo y es el recomendado
    return db.get(User, user_id)

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


# --------- Alta simple (si la usás en algún lado) ---------
def create_user(
    db: Session,
    *,
    nombre: str,
    apellido: str,
    email: str,
    password: str,
    tipo_doc: str,
    nro_doc: str,
    acepta_terminos: bool,
) -> User:
    u = User(
        nombre=nombre,
        apellido=apellido,
        email=email,
        password_hash=hash_password(password),
        tipo_doc=tipo_doc,
        nro_doc=nro_doc,
        acepta_terminos=acepta_terminos,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u
###test
def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Devuelve el usuario si el email existe y la password coincide.
    Caso contrario, devuelve None.
    """
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

# --------- Roles ---------
def assign_roles(db: Session, user_id: str, role_codes: List[str]) -> None:
    """Reasigna roles por code (borra los actuales y setea los nuevos)."""
    user = get_user_by_id(db, user_id)
    if not user:
        return
    # limpiar actuales
    for ur in list(user.roles):
        db.delete(ur)
    # asignar nuevos
    roles = db.query(Role).filter(Role.code.in_(role_codes)).all()
    for r in roles:
        db.add(UserRole(user_id=user.id, role_id=r.id))
    db.commit()


# --------- Seed de roles base ---------
def seed_roles(db: Session) -> None:
    base = {"COMPRADOR": "Comprador", "VENDEDOR": "Vendedor", "ADMIN": "Administrador"}
    for code, nombre in base.items():
        if not db.query(Role).filter_by(code=code).first():
            db.add(Role(code=code, nombre=nombre))
    db.commit()


# --------- Upserts auxiliares ---------
def upsert_address(db: Session, user_id: str, addr_in: Optional[AddressIn]) -> None:
    if not addr_in:
        return
    addr = db.query(Address).filter_by(user_id=user_id, tipo=addr_in.tipo).one_or_none()
    if addr:
        # actualizar campos
        for f in ("calle_y_numero", "ciudad", "provincia", "pais", "cp"):
            setattr(addr, f, getattr(addr_in, f))
    else:
        db.add(Address(user_id=user_id, **addr_in.model_dump()))


def upsert_wallets(db: Session, user_id: str, wallets: Optional[List[CryptoWalletIn]]) -> None:
    if not wallets:
        return
    for w in wallets:
        row = (
            db.query(CryptoWallet)
            .filter_by(user_id=user_id, red=w.red)
            .one_or_none()
        )
        if row:
            row.address = w.address
        else:
            db.add(CryptoWallet(user_id=user_id, red=w.red, address=w.address))


# --------- Alta/Edición completas (pantalla de Streamlit) ---------
def create_user_full(db: Session, p: UserCreate) -> User:
   

    # validaciones
    if db.query(User).filter_by(email=p.email).first():
        raise HTTPException(status_code=409, detail="Email ya registrado")
    if db.query(User).filter_by(nro_doc=p.nro_doc).first():
        raise HTTPException(status_code=409, detail="Documento ya registrado")
    if "COMPRADOR" in p.roles and not p.domicilio_entrega:
        raise HTTPException(status_code=422, detail="COMPRADOR requiere domicilio de ENTREGA")
    if "VENDEDOR" in p.roles and (not p.banking or not p.wallets):
        raise HTTPException(status_code=422, detail="VENDEDOR requiere CBU/Alias y al menos una Wallet")

    u = User(
        nombre=p.nombre,
        apellido=p.apellido,
        tipo_doc=p.tipo_doc,
        nro_doc=p.nro_doc,
        email=p.email,
        tel=p.tel,
        palabra_seg=p.palabra_seg or "",
        password_hash=hash_password(p.password),
        acepta_terminos=p.acepta_terminos,
    )
    db.add(u)
    db.flush()  # genera u.id

    upsert_address(db, u.id, p.domicilio_envio)
    upsert_address(db, u.id, p.domicilio_entrega)

    if p.banking:
        b = db.query(BankingInfo).filter_by(user_id=u.id).one_or_none()
        if b:
            b.cbu_o_alias = p.banking.cbu_o_alias
        else:
            db.add(BankingInfo(user_id=u.id, cbu_o_alias=p.banking.cbu_o_alias))

    upsert_wallets(db, u.id, p.wallets)
    assign_roles(db, u.id, p.roles)

    db.commit()
    db.refresh(u)
    return u


def update_user_full(db: Session, user_id: str, p: UserCreate) -> User:
   

    u = db.get(User, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # actualizar básicos
    u.nombre, u.apellido = p.nombre, p.apellido
    u.tipo_doc, u.nro_doc = p.tipo_doc, p.nro_doc
    u.email, u.tel = p.email, p.tel
    u.palabra_seg = p.palabra_seg or ""
    u.acepta_terminos = p.acepta_terminos
    if p.password:
        u.password_hash = hash_password(p.password)

    upsert_address(db, u.id, p.domicilio_envio)
    upsert_address(db, u.id, p.domicilio_entrega)

    if p.banking:
        b = db.query(BankingInfo).filter_by(user_id=u.id).one_or_none()
        if b:
            b.cbu_o_alias = p.banking.cbu_o_alias
        else:
            db.add(BankingInfo(user_id=u.id, cbu_o_alias=p.banking.cbu_o_alias))

    upsert_wallets(db, u.id, p.wallets)
    assign_roles(db, u.id, p.roles)

    db.commit()
    db.refresh(u)
    return u

def delete_user_full(db: Session, user_id: str) -> bool:
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        return False

    # ---- borrar relaciones manualmente (si aplica) ----
    # roles
    for ur in list(u.roles or []):
        db.delete(ur)

    # domicilios
    for d in list(getattr(u, "domicilios", []) or []):
        db.delete(d)

    # wallets
    for w in list(getattr(u, "wallets", []) or []):
        db.delete(w)

    # banking (si es tabla aparte)
    b = getattr(u, "banking", None)
    if b:
        db.delete(b)

    # kyc files (si están en tabla aparte)
    for k in list(getattr(u, "kyc_files", []) or []):
        db.delete(k)

    db.delete(u)
    db.commit()
    return True