# backend/app/security/tokens.py
from datetime import datetime, timedelta
from jose import jwt
import os

# Usamos SIEMPRE la misma clave y algoritmo en todo el sistema
SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 día

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Genera un JWT con los datos de `data` y expiración.
    En `sub` guardamos el user.id.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token
