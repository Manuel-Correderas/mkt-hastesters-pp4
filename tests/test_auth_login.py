# tests/test_auth_login.py

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db import SessionLocal
from backend.app.models.models import User
from backend.app.security import hash_password  # usa el mismo scheme que verify_password

client = TestClient(app)


def crear_usuario_de_prueba():
    """
    Crea (o recrea) un usuario directamente en la base de datos
    para probar el login contra /auth/login.
    """
    db = SessionLocal()
    try:
        email = "login_test@mktlab.com"

        # Limpiar si ya existe
        existing = db.query(User).filter_by(email=email).first()
        if existing:
            db.delete(existing)
            db.commit()

        u = User(
            nombre="Login",
            apellido="Test",
            tipo_doc="DNI",
            nro_doc="99999999",
            email=email,
            tel="12345678",
            palabra_seg="gato",
            password_hash=hash_password("Test123!"),
            acepta_terminos=True,
            # opcional: asegurá defaults si tu modelo los tiene
            premium=0,
            dni_bloqueado=0,
        )
        db.add(u)
        db.commit()
        db.refresh(u)
        return u
    finally:
        db.close()


def test_login_exitoso():
    """
    Verifica que el login con credenciales correctas funcione contra /auth/login
    y que responda con el formato ACTUAL del router:

    {
        "ok": True,
        "access_token": "...",
        "token_type": "bearer",
        "user": {
            "id": "...",
            "email": "...",
            "roles": [...],
            "premium": 0,
            "dni_bloqueado": 0
        }
    }
    """
    crear_usuario_de_prueba()

    payload = {
        "email": "login_test@mktlab.com",
        "password": "Test123!",
    }
    resp = client.post("/auth/login", json=payload)

    # 1) Debe responder OK
    assert resp.status_code == 200, f"Status: {resp.status_code}, body: {resp.text}"

    data = resp.json()

    # 2) Debe marcar ok = True
    assert data.get("ok") is True

    # 3) Debe existir user y ser dict
    assert "user" in data and isinstance(data["user"], dict)

    user = data["user"]

    # 4) Debe devolver el mismo email (dentro de user)
    assert user.get("email") == payload["email"]

    # 5) Debe haber un id de usuario (UUID/str) dentro de user
    assert "id" in user and isinstance(user["id"], str)

    # 6) roles debe existir y ser lista (dentro de user)
    assert "roles" in user
    assert isinstance(user["roles"], list)

    # 7) premium y dni_bloqueado opcionales pero esperables
    assert "premium" in user
    assert isinstance(user["premium"], int)
    assert "dni_bloqueado" in user
    assert isinstance(user["dni_bloqueado"], int)

    # 8) Debe devolver access_token y token_type = bearer
    token = data.get("access_token")
    assert token and isinstance(token, str), f"access_token inválido: {token}"
    assert data.get("token_type", "").lower() == "bearer"


def test_login_password_incorrecta():
    """
    Verifica que con password incorrecta el login falle con 401.
    """
    crear_usuario_de_prueba()

    payload = {
        "email": "login_test@mktlab.com",
        "password": "MalaClave!",
    }
    resp = client.post("/auth/login", json=payload)

    assert resp.status_code == 401, f"Status: {resp.status_code}, body: {resp.text}"
