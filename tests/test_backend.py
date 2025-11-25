# tests/test_backend.py
import os
# tests/test_backend.py
from backend.app.db import SessionLocal
from backend.app.models.models import User
from backend.app.security import hash_password

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)

# ⚠️ Usuario REAL que exista en tu base de datos
# Podés sobreescribirlos con variables de entorno si querés:
#   EMAIL_TEST=... PASS_TEST=...
EMAIL_TEST = os.getenv("EMAIL_TEST", "admin@ecomlab.com")
PASS_TEST = os.getenv("PASS_TEST", "123456")  # poné la contraseña real

def crear_usuario_real_para_tests():
    db = SessionLocal()
    try:
        email = "admin@ecomlab.com"

        existing = db.query(User).filter_by(email=email).first()
        if existing:
            db.delete(existing)
            db.commit()

        user = User(
            nombre="Admin",
            apellido="Test",
            tipo_doc="DNI",
            nro_doc="99999998",
            email=email,
            tel="555",
            palabra_seg="perro",
            password_hash=hash_password("123456"),  # 👈 COINCIDE CON EL TEST
            acepta_terminos=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()

# =========================
# PRUEBAS UNITARIAS (ENDPOINTS AISLADOS)
# =========================

def test_health_ok():
    """
    U1 - Verifica que la API responda en /health.
    En tu main devuelve {"ok": True}
    """
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert data.get("ok") is True


def test_login_invalid_credentials():
    """
    U2 - Login con credenciales inválidas -> 401.
    """
    payload = {"email": "no_existe@example.com", "password": "incorrecta"}
    resp = client.post("/auth/login", json=payload)
    assert resp.status_code == 401


def test_login_valid_returns_token():
    """
    U3 - Login con credenciales válidas devuelve access_token.
    """
    resp = client.post("/auth/login", json={"email": EMAIL_TEST, "password": PASS_TEST})
    assert resp.status_code == 200, f"Login falló: {resp.status_code} {resp.text}"
    data = resp.json()
    token = data.get("access_token")
    assert token, f"Respuesta de login sin access_token: {data}"
    assert data.get("token_type", "").lower() in ("bearer", "jwt", "")


def test_list_products_returns_list():
    """
    U4 - Listado de productos devuelve lista y campos básicos.
    """
    resp = client.get("/products", params={"limit": 5, "offset": 0})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)

    if data:  # si hay productos cargados
        p0 = data[0]
        assert "id" in p0
        assert "name" in p0
        assert "price" in p0
        assert "stock" in p0


# =========================
# HELPERS COMUNES PARA INTEGRACIÓN
# =========================

def login_and_get_token():
    """
    Helper: hace login con un usuario real y devuelve el token."""
    resp = client.post("/auth/login", json={"email": EMAIL_TEST, "password": PASS_TEST})
    assert resp.status_code == 200, f"Login falló: {resp.status_code} {resp.text}"
    data = resp.json()
    token = data.get("access_token")
    assert token, f"Respuesta de login sin access_token: {data}"
    return token


def get_first_product_id_with_stock():
    """
    Helper: toma el primer producto con stock > 0 (para usar en carrito).
    """
    resp = client.get("/products", params={"limit": 50, "offset": 0})
    assert resp.status_code == 200
    productos = resp.json()
    assert isinstance(productos, list), f"/products no devolvió lista: {productos}"
    assert productos, "No hay productos en la base de datos para probar."

    for p in productos:
        stock = p.get("stock", 0) or 0
        try:
            stock = int(stock)
        except Exception:
            stock = 0
        if stock > 0:
            return p["id"]

    raise AssertionError("No se encontró ningún producto con stock > 0 para test.")


# =========================
# PRUEBAS DE INTEGRACIÓN
# =========================

def test_cart_requires_auth():
    """
    I1 - /cart sin token debería devolver 401 (o 403).
    """
    resp = client.get("/cart")
    assert resp.status_code in (401, 403)


def test_integration_login_and_get_cart():
    """
    I2 - Flujo: login -> acceder a carrito.
    Sirve para detectar el problema de 'Token inválido' en /cart.
    """
    token = login_and_get_token()
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/cart", headers=headers)
    # Permitimos 200 (carrito con datos) o 204 (carrito vacío)
    assert resp.status_code in (200, 204), f"/cart devolvió {resp.status_code}: {resp.text}"


def test_integration_add_item_to_cart_and_list():
    """
    I3 - Flujo completo:
    - login
    - obtener producto con stock
    - agregar al carrito
    - leer carrito y verificar el ítem
    """
    token = login_and_get_token()
    headers = {"Authorization": f"Bearer {token}"}

    # 1) Buscamos un producto con stock
    product_id = get_first_product_id_with_stock()

    # 2) Agregamos 1 unidad al carrito
    payload = {"product_id": product_id, "qty": 1}
    resp_add = client.post("/cart/items", json=payload, headers=headers)
    assert resp_add.status_code in (200, 201), \
        f"No se pudo agregar al carrito: {resp_add.status_code} {resp_add.text}"

    # 3) Consultamos el carrito
    resp_cart = client.get("/cart", headers=headers)
    assert resp_cart.status_code == 200, \
        f"No se pudo obtener carrito: {resp_cart.status_code} {resp_cart.text}"
    data = resp_cart.json()

    # Asumimos que /cart devuelve algo tipo {"items":[...], "total": ...}
    items = data.get("items") if isinstance(data, dict) else data
    assert isinstance(items, list), f"Formato inesperado de /cart: {data}"

    # verificamos que esté el producto
    assert any(str(it.get("product_id")) == str(product_id) for it in items), \
        f"El producto {product_id} no aparece en el carrito: {items}"
# Crear usuario admin para las pruebas
crear_usuario_real_para_tests()