# tests/test_smoke_areas.py
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health_ok():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert data.get("ok") is True


@pytest.mark.parametrize(
    "name, path",
    [
        ("roles", "/roles"),
        ("products", "/products"),
        ("orders", "/orders"),
        ("comments", "/comments"),
    ],
)
def test_list_endpoints_no_500(name, path):
    """
    Smoke test por área:
    - Llama a los list endpoints principales.
    - Falla si hay un 5xx (error de servidor).
    - Si responde 200, valida que sea una lista.
    """
    resp = client.get(path)

    # 1) Nunca debería haber error 5xx
    assert resp.status_code < 500, f"{name} devolvió {resp.status_code} con body: {resp.text}"

    # 2) Si la respuesta es OK, chequeamos tipo de dato
    if resp.status_code == 200:
        data = resp.json()
        assert isinstance(
            data, list
        ), f"Se esperaba una lista en {name}, pero vino: {type(data).__name__}"
