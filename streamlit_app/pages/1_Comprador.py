# streamlit_app/pages/1_Comprador.py
import streamlit as st
from pathlib import Path

from auth_helpers import get_backend_url, require_login

st.set_page_config(page_title="Panel del Comprador", layout="wide")

BACKEND_URL = get_backend_url()
PAGE_NS = "buyer_panel_v1"
def K(s: str) -> str:
    return f"{PAGE_NS}:{s}"


# ---------------------------
# NAVEGACIÓN SEGURA CON FALLBACK
# ---------------------------
def safe_switch_page(*page_filenames: str):
    """
    Recibe 1 o varios nombres de archivo.
    Intenta navegar al primero que exista dentro de /pages.
    Si le pasás "Home.py" navega al main directamente.
    """
    for filename in page_filenames:
        # Si es Home u otro main script
        if filename.endswith(".py") and not filename.startswith("pages/"):
            main_path = Path(__file__).resolve().parents[1] / filename  # streamlit_app/<filename>
            if main_path.exists():
                st.switch_page(filename)
                return
        # Si es una page
        page_path = Path(__file__).resolve().parent / filename  # streamlit_app/pages/<filename>
        if page_path.exists():
            st.switch_page(f"pages/{filename}")
            return

    st.warning("No se encontró ninguna de las páginas esperadas. Revisá nombres en /pages.")


# ---------------------------
# CONTROL DE ACCESO
# ---------------------------
require_login()

roles = st.session_state.get("auth_roles") or st.session_state.get("roles") or []
roles = [str(r).upper() for r in roles]

if "COMPRADOR" not in roles and "ADMIN" not in roles:
    st.warning("⚠️ No tenés permiso para acceder al panel de Comprador.")
    st.stop()

nombre = st.session_state.get("auth_user_name", "Cliente")


# ---------------------------
# ESTILOS
# ---------------------------
st.markdown("""
<style>
.stApp { background: linear-gradient(135deg,#fb923c,#f97316); font-family: Arial, sans-serif; }

/* Header */
.panel-header{
  background:rgba(255,255,255,0.15);
  padding:22px 24px;border-radius:16px;
  color:#111827;margin-bottom:18px;
  box-shadow:0 8px 18px rgba(0,0,0,.18);
}
.panel-header h1{
  margin:0;font-size:2rem;font-weight:900;color:#111827;
}
.panel-header small{color:#374151;font-size:.9rem;}
.badge-user{
  margin-top:10px;display:inline-block;
  padding:6px 14px;border-radius:999px;
  background:#111827;color:#facc15;
  font-weight:700;
}

/* Acciones rápidas */
.actions-box{
  margin-top:6px;
  background:#fffbeb;
  border-radius:14px;
  padding:14px 16px;
  box-shadow:0 8px 18px rgba(0,0,0,.12);
}
.actions-title{font-weight:800;color:#c2410c;margin-bottom:8px;}

.stButton>button{
  font-weight:800;
  border-radius:12px;
  padding:14px 14px;
  width:100%;
  border:none;
  box-shadow:0 3px 8px rgba(0,0,0,0.12);
}
</style>
""", unsafe_allow_html=True)


# ---------------------------
# HEADER
# ---------------------------
st.markdown(f"""
<div class="panel-header">
  <h1>🧑‍🤝‍🧑 Panel del Comprador</h1>
  <small>Accedé rápido a lo que necesitás para comprar y gestionar tus pedidos.</small><br/>
  <span class="badge-user">👤 {nombre}</span>
</div>
""", unsafe_allow_html=True)


# ---------------------------
# ACCIONES (ahora 5)
# ---------------------------
st.markdown('<div class="actions-box">', unsafe_allow_html=True)
st.markdown('<div class="actions-title">📌 Secciones</div>', unsafe_allow_html=True)

# 5 columnas (si se achica la pantalla, Streamlit las apila solo)
a1, a2, a3, a4, a5 = st.columns(5)

with a1:
    # ✅ Productos = catálogo general
    if st.button("🛍️ Productos", key=K("productos"), use_container_width=True):
        safe_switch_page("Home.py")

with a2:
    # Mi Carrito
    if st.button("🛒 Mi carrito", key=K("carrito"), use_container_width=True):
        safe_switch_page("4_Mi_Carrito.py")

with a3:
    # ✅ NUEVO: Mis pedidos / confirmar pago
    if st.button("📦 Mis pedidos", key=K("mis_pedidos"), use_container_width=True):
        safe_switch_page(
            # probá estos nombres, el primero que exista abre
            "7_📦_Mis_Pedidos.py",
            "7_📦_Mis_Pedidos_y_Pagos.py",
            "7_✅_Confirmar_Pago.py",
            "6_Historial_Compras.py",  # fallback final
        )

with a4:
    # Historial de compras
    if st.button("📜 Historial", key=K("historial"), use_container_width=True):
        safe_switch_page("6_Historial_Compras.py")

with a5:
    # Comentarios
    if st.button("💬 Mis comentarios", key=K("comentarios"), use_container_width=True):
        safe_switch_page("5_Comentarios.py")

st.markdown('</div>', unsafe_allow_html=True)


# ---------------------------
# FOOTER / SALIR
# ---------------------------
st.markdown("---")
if st.button("🚪 Cerrar sesión", key=K("logout"), use_container_width=True):
    for k in [
        "auth_token", "auth_user_id", "auth_email", "auth_roles",
        "roles", "is_authenticated", "auth_user_name",
        "user_id", "user_name"
    ]:
        st.session_state.pop(k, None)

    st.success("Sesión cerrada correctamente.")
    safe_switch_page("0_Login.py")
