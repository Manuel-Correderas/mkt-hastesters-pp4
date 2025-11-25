# debug_imports.py

print("📦 Probando importar deps...")
from backend.app.deps import get_current_user
print("✅ deps importado OK")

print("📦 Probando importar security...")
from backend.app.security import hash_password
print("✅ security importado OK")

print("🎉 Todo se importó sin circular imports.")
