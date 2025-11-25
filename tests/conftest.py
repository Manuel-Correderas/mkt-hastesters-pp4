# tests/conftest.py
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Esto garantiza que pytest pueda importar backend.app.main SIEMPRE
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
