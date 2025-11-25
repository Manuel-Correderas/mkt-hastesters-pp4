from datetime import datetime, timedelta
from dotenv import load_dotenv
from pathlib import Path

# Cargar variables desde .env
ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ENV_PATH)

from .db import SessionLocal
from .models.models import (
    User, Role, UserRole,
    Product, Order, OrderItem, Payment
)
from .security import hash_password



def get_or_create_role(db, code: str, nombre: str):
    role = db.query(Role).filter_by(code=code).first()
    if role:
        return role
    role = Role(code=code, nombre=nombre)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def crear_roles_base(db):
    roles = {
        "ADMIN": "Administrador",
        "VENDEDOR": "Vendedor",
        "COMPRADOR": "Comprador",
    }
    res = {}
    for code, nombre in roles.items():
        res[code] = get_or_create_role(db, code, nombre)
    return res


def get_or_create_user(db, email: str, **kwargs):
    # 1) Buscar por email
    user = db.query(User).filter_by(email=email).first()
    if user:
        return user

    # 2) Si viene nro_doc, ver si ya existe alguien con ese doc
    nro_doc = kwargs.get("nro_doc")
    if nro_doc:
        existing_doc = db.query(User).filter_by(nro_doc=nro_doc).first()
        if existing_doc:
            # O lo reutilizás:
            return existing_doc
            # o lo borrás si es entorno de desarrollo:
            # db.delete(existing_doc)
            # db.commit()

    user = User(
        email=email,
        password_hash=hash_password(kwargs.pop("password")),
        nombre=kwargs.get("nombre", ""),
        apellido=kwargs.get("apellido", ""),
        tipo_doc=kwargs.get("tipo_doc", "DNI"),
        nro_doc=nro_doc or "00000000",
        tel=kwargs.get("tel", ""),
        palabra_seg=kwargs.get("palabra_seg", "gato"),
        acepta_terminos=kwargs.get("acepta_terminos", True),
        estado=kwargs.get("estado", "ACTIVO"),
        dni_bloqueado=kwargs.get("dni_bloqueado", 0),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user



def asignar_rol(db, user: User, role: Role):
    ya = db.query(UserRole).filter_by(user_id=user.id, role_id=role.id).first()
    if ya:
        return ya
    ur = UserRole(user_id=user.id, role_id=role.id)
    db.add(ur)
    db.commit()
    return ur


def crear_usuarios_y_roles(db):
    roles = crear_roles_base(db)

    # Admin
    admin = get_or_create_user(
        db,
        email="admin@mktlab.com",
        password="Admin123!",
        nombre="Admin",
        apellido="General",
        tipo_doc="DNI",
        nro_doc="10000000",
        tel="11111111",
        estado="ACTIVO",
    )
    asignar_rol(db, admin, roles["ADMIN"])

    # Vendedores
    vendor1 = get_or_create_user(
        db,
        email="vendedora.julia@mktlab.com",
        password="Julia123!",
        nombre="Julia",
        apellido="Pérez",
        tipo_doc="DNI",
        nro_doc="20000001",
        tel="22222222",
        estado="ACTIVO",
    )
    asignar_rol(db, vendor1, roles["VENDEDOR"])

    vendor2 = get_or_create_user(
        db,
        email="vendor.carlos@mktlab.com",
        password="Carlos123!",
        nombre="Carlos",
        apellido="López",
        tipo_doc="DNI",
        nro_doc="20000002",
        tel="22223333",
        estado="ACTIVO",
    )
    asignar_rol(db, vendor2, roles["VENDEDOR"])

    # Compradores
    buyer1 = get_or_create_user(
        db,
        email="cliente.lucas@mktlab.com",
        password="Lucas123!",
        nombre="Lucas",
        apellido="Gómez",
        tipo_doc="DNI",
        nro_doc="30000001",
        tel="33334444",
        estado="ACTIVO",
    )
    asignar_rol(db, buyer1, roles["COMPRADOR"])

    buyer2 = get_or_create_user(
        db,
        email="cliente.ana@mktlab.com",
        password="Ana123!",
        nombre="Ana",
        apellido="Martínez",
        tipo_doc="DNI",
        nro_doc="30000002",
        tel="33335555",
        estado="REVISION",
    )
    asignar_rol(db, buyer2, roles["COMPRADOR"])

    # Ejemplo de usuario bloqueado por DNI (para dashboard de seguridad)
    buyer_bloq = get_or_create_user(
        db,
        email="fraude.sospechoso@mktlab.com",
        password="Fraude123!",
        nombre="Sospechoso",
        apellido="Bloqueado",
        tipo_doc="DNI",
        nro_doc="39999999",
        tel="00000000",
        estado="BLOQUEADO",
        dni_bloqueado=1,
    )
    asignar_rol(db, buyer_bloq, roles["COMPRADOR"])

    return {
        "admin": admin,
        "vendor1": vendor1,
        "vendor2": vendor2,
        "buyer1": buyer1,
        "buyer2": buyer2,
        "buyer_bloq": buyer_bloq,
        "roles": roles,
    }


def crear_productos_demo(db, vendor1: User, vendor2: User):
    productos_exist = db.query(Product).count()
    if productos_exist > 0:
        return  # no duplicar

    p1 = Product(
        seller_id=vendor1.id,
        name="Auriculares Bluetooth Pro",
        description="Auriculares inalámbricos con cancelación de ruido.",
        price=45999,
        stock=25,
        condition="NUEVO",
        rating=8.7,
        sold_count=12,
        image_url="https://via.placeholder.com/300x200?text=Auriculares",
        category_id=None,
        subcategory="Audio",
        is_active=True,
        pay_method="CRYPTO",
        network="TRON",
        alias="julia.audios.mkt",
        wallet="TXYZ123456789",
    )
    p2 = Product(
        seller_id=vendor1.id,
        name="Mouse Gamer RGB",
        description="Mouse ergonómico con 6 botones y luces RGB.",
        price=19999,
        stock=40,
        condition="NUEVO",
        rating=9.1,
        sold_count=20,
        image_url="https://via.placeholder.com/300x200?text=Mouse",
        subcategory="Periféricos",
        is_active=True,
        pay_method="TRANSFER",
        network=None,
        alias=None,
        wallet=None,
    )
    p3 = Product(
        seller_id=vendor2.id,
        name="Notebook 15'' i5 16GB",
        description="Notebook para trabajo y estudio, pantalla 15 pulgadas.",
        price=499999,
        stock=5,
        condition="NUEVO",
        rating=9.3,
        sold_count=5,
        image_url="https://via.placeholder.com/300x200?text=Notebook",
        subcategory="Computadoras",
        is_active=True,
        pay_method="MP",
        network=None,
    )
    p4 = Product(
        seller_id=vendor2.id,
        name="Teclado Mecánico",
        description="Teclado mecánico con switches azules.",
        price=74999,
        stock=15,
        condition="NUEVO",
        rating=8.9,
        sold_count=8,
        image_url="https://via.placeholder.com/300x200?text=Teclado",
        subcategory="Periféricos",
        is_active=True,
        pay_method="CRYPTO",
        network="BTC",
        wallet="bc1qxxxxxx",
    )

    db.add_all([p1, p2, p3, p4])
    db.commit()
    return [p1, p2, p3, p4]


def crear_ordenes_demo(db, buyers, productos):
    # Si ya hay órdenes, no duplicamos
    if db.query(Order).count() > 0:
        return

    buyer1 = buyers["buyer1"]
    buyer2 = buyers["buyer2"]

    p1, p2, p3, p4 = productos

    # Orden de ayer para buyer1
    o1 = Order(
        user_id=buyer1.id,
        user_name=f"{buyer1.nombre} {buyer1.apellido}",
        status="Entregado",
        created_at=datetime.utcnow() - timedelta(days=1),
        total_amount= (1 * p1.price) + (2 * p2.price),
    )
    db.add(o1)
    db.flush()

    oi1 = OrderItem(
        order_id=o1.id,
        product_id=p1.id,
        product_name=p1.name,
        category=None,
        subcategory=p1.subcategory,
        seller=p1.seller.nombre if p1.seller else "Vendedor",
        company="Ecom MKT Lab",
        quantity=1,
        unit_price=p1.price,
    )
    oi2 = OrderItem(
        order_id=o1.id,
        product_id=p2.id,
        product_name=p2.name,
        category=None,
        subcategory=p2.subcategory,
        seller=p2.seller.nombre if p2.seller else "Vendedor",
        company="Ecom MKT Lab",
        quantity=2,
        unit_price=p2.price,
    )

    pay1 = Payment(
        order_id=o1.id,
        provider="MP",
        status="APROBADO",
        amount=o1.total_amount,
        tx_ref="MP-TEST-0001",
    )

    # Orden de hoy para buyer2
    o2 = Order(
        user_id=buyer2.id,
        user_name=f"{buyer2.nombre} {buyer2.apellido}",
        status="En camino",
        created_at=datetime.utcnow(),
        total_amount=(1 * p3.price) + (1 * p4.price),
    )
    db.add(o2)
    db.flush()

    oi3 = OrderItem(
        order_id=o2.id,
        product_id=p3.id,
        product_name=p3.name,
        category=None,
        subcategory=p3.subcategory,
        seller=p3.seller.nombre if p3.seller else "Vendedor",
        company="Ecom MKT Lab",
        quantity=1,
        unit_price=p3.price,
    )
    oi4 = OrderItem(
        order_id=o2.id,
        product_id=p4.id,
        product_name=p4.name,
        category=None,
        subcategory=p4.subcategory,
        seller=p4.seller.nombre if p4.seller else "Vendedor",
        company="Ecom MKT Lab",
        quantity=1,
        unit_price=p4.price,
    )

    pay2 = Payment(
        order_id=o2.id,
        provider="CRYPTO",
        status="APROBADO",
        amount=o2.total_amount,
        tx_ref="TX-CRYPTO-0001",
    )

    db.add_all([oi1, oi2, oi3, oi4, pay1, pay2])
    db.commit()


def main():
    db = SessionLocal()
    try:
        data_users = crear_usuarios_y_roles(db)
        productos = crear_productos_demo(db, data_users["vendor1"], data_users["vendor2"])
        crear_ordenes_demo(db, data_users, productos)
        print("✅ Datos de demo cargados correctamente.")
        print("  Admin: admin@mktlab.com / Admin123!")
        print("  Vendedor1: vendedora.julia@mktlab.com / Julia123!")
        print("  Vendedor2: vendor.carlos@mktlab.com / Carlos123!")
        print("  Comprador1: cliente.lucas@mktlab.com / Lucas123!")
        print("  Comprador2: cliente.ana@mktlab.com / Ana123!")
    finally:
        db.close()


if __name__ == "__main__":
    main()
