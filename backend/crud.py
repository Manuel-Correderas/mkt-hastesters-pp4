import os, secrets
from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile
from models import User, Address, BankingInfo, CryptoWallet, KYCDocument, Role, UserRole
from security import hash_password
from schemas import UserCreate, AddressIn, CryptoWalletIn

def seed_roles(db: Session):
    base = {"COMPRADOR":"Comprador","VENDEDOR":"Vendedor","ADMIN":"Administrador"}
    for code, nombre in base.items():
        if not db.query(Role).filter_by(code=code).first():
            db.add(Role(code=code, nombre=nombre))
    db.commit()

def upsert_address(db: Session, user_id: str, addr_in: AddressIn | None):
    if not addr_in: return
    addr = db.query(Address).filter_by(user_id=user_id, tipo=addr_in.tipo).one_or_none()
    if addr:
        for f in ("calle_y_numero","ciudad","provincia","pais","cp"):
            setattr(addr, f, getattr(addr_in, f))
    else:
        addr = Address(user_id=user_id, **addr_in.model_dump())
        db.add(addr)

def upsert_wallets(db: Session, user_id: str, wallets: List[CryptoWalletIn] | None):
    if not wallets: return
    for w in wallets:
        row = db.query(CryptoWallet).filter_by(user_id=user_id, red=w.red).one_or_none()
        if row: row.address = w.address
        else: db.add(CryptoWallet(user_id=user_id, red=w.red, address=w.address))

def assign_roles(db: Session, user_id: str, role_codes: List[str]):
    roles = db.query(Role).filter(Role.code.in_(role_codes)).all()
    # limpiar y setear (simple)
    db.query(UserRole).filter_by(user_id=user_id).delete()
    for r in roles:
        db.add(UserRole(user_id=user_id, role_id=r.id))

def create_user(db: Session, p: UserCreate) -> User:
    if db.query(User).filter_by(email=p.email).first():
        raise HTTPException(409, "Email ya registrado")
    if db.query(User).filter_by(nro_doc=p.nro_doc).first():
        raise HTTPException(409, "Documento ya registrado")

    if "COMPRADOR" in p.roles and not p.domicilio_entrega:
        raise HTTPException(422, "COMPRADOR requiere domicilio de ENTREGA")
    if "VENDEDOR" in p.roles and (not p.banking or not p.wallets):
        raise HTTPException(422, "VENDEDOR requiere CBU/Alias y al menos una Wallet")

    u = User(
        nombre=p.nombre, apellido=p.apellido,
        tipo_doc=p.tipo_doc, nro_doc=p.nro_doc,
        email=p.email, tel=p.tel, palabra_seg=p.palabra_seg or "",
        password_hash=hash_password(p.password),
        acepta_terminos=p.acepta_terminos
    )
    db.add(u); db.flush()  # genera u.id

    upsert_address(db, u.id, p.domicilio_envio)
    upsert_address(db, u.id, p.domicilio_entrega)

    if p.banking:
        from models import BankingInfo
        db.add(BankingInfo(user_id=u.id, cbu_o_alias=p.banking.cbu_o_alias))

    upsert_wallets(db, u.id, p.wallets)
    assign_roles(db, u.id, p.roles)
    db.commit(); db.refresh(u)
    return u

def update_user(db: Session, user_id: str, p: UserCreate) -> User:
    u = db.query(User).get(user_id)
    if not u: raise HTTPException(404, "Usuario no encontrado")

    # campos básicos
    u.nombre, u.apellido = p.nombre, p.apellido
    u.tipo_doc, u.nro_doc = p.tipo_doc, p.nro_doc
    u.email, u.tel = p.email, p.tel
    u.palabra_seg = p.palabra_seg or ""
    u.acepta_terminos = p.acepta_terminos
    if p.password: u.password_hash = hash_password(p.password)

    upsert_address(db, u.id, p.domicilio_envio)
    upsert_address(db, u.id, p.domicilio_entrega)

    # banking
    if p.banking:
        b = db.query(BankingInfo).filter_by(user_id=u.id).one_or_none()
        if b: b.cbu_o_alias = p.banking.cbu_o_alias
        else:
            db.add(BankingInfo(user_id=u.id, cbu_o_alias=p.banking.cbu_o_alias))

    upsert_wallets(db, u.id, p.wallets)
    assign_roles(db, u.id, p.roles)

    db.commit(); db.refresh(u)
    return u

def get_user_out(db: Session, user_id: str):
    u = db.query(User).get(user_id)
    if not u: raise HTTPException(404, "Usuario no encontrado")
    roles = [ur.role.code for ur in u.roles]
    return {"id": u.id, "nombre": u.nombre, "apellido": u.apellido, "email": u.email, "roles": roles, "creado_en": u.creado_en}

def save_kyc_files(db: Session, user_id: str, files: List[UploadFile]):
    base = os.path.join(".", "secure", "kyc", user_id)
    os.makedirs(base, exist_ok=True)
    saved = []
    for f in files:
        rand = secrets.token_hex(8)
        ext = os.path.splitext(f.filename)[1]
        disk_name = f"{rand}{ext or ''}"
        path = os.path.join(base, disk_name)
        with open(path, "wb") as out:
            out.write(f.file.read())
        doc = KYCDocument(
            user_id=user_id,
            tipo="OTRO",
            filename=f.filename,
            mime=f.content_type or "",
            size_bytes=os.path.getsize(path),
            storage_path=path
        )
        db.add(doc); saved.append(disk_name)
    db.commit()
    return {"archivos_guardados": saved}
