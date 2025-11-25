import requests
import streamlit as st

def api_get(path: str):
    API_BASE = st.secrets.get("API_BASE", "http://localhost:8000/api/v1")
    try:
        r = requests.get(f"{API_BASE}{path}", timeout=8)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.warning(f"⚠️ Error GET {path}: {e}")
        return None

def api_post(path: str, payload: dict):
    API_BASE = st.secrets.get("API_BASE", "http://localhost:8000/api/v1")
    try:
        r = requests.post(f"{API_BASE}{path}", json=payload, timeout=8)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.warning(f"⚠️ Error POST {path}: {e}")
        return None

def api_put(path: str, payload: dict):
    API_BASE = st.secrets.get("API_BASE", "http://localhost:8000/api/v1")
    try:
        r = requests.put(f"{API_BASE}{path}", json=payload, timeout=8)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.warning(f"⚠️ Error PUT {path}: {e}")
        return None
def get_api_base() -> str:
    try:
        return st.secrets["API_BASE"]
    except Exception:
        return "http://localhost:8000/api/v1"