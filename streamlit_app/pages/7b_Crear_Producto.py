# streamlit_app/pages/7b_✏️_Editar_Producto.py
import streamlit as st
import requests
from pathlib import Path

from auth_helpers import get_backend_url, require_login, auth_headers

# ⚠️ set_page_config SIEMPRE primero
st.set_page_config(page_title="Crear Producto (Vendedor)", page_icon="➕", layout="centered")

BACKEND_URL = get_backend_url()

PAGE_NS = "crearprod_v1"
def K(s: str) -> str:
    return f"{PAGE_NS}:{s}"

PAGE_MY_PRODUCTS = "7_Mis_Productos.py"
PAGE_SELLER_PANEL = "2_Vendedor.py"

# ---------------------------
# NAVEGACIÓN SEGURA CON FALLBACK
# ---------------------------
def safe_switch_page(*page_filenames: str):
    for filename in page_filenames:
        # page dentro de /pages
        page_path = Path(__file__).resolve().parent / filename
        if page_path.exists():
            st.switch_page(f"pages/{filename}")
            return
    st.warning("No se encontró ninguna página esperada en /pages. Revisá nombres exactos.")

# ---------------------------
# AUTH
# ---------------------------
require_login()

user_obj = st.session_state.get("user") or st.session_state.get("auth_user") or {}

roles = (
    st.session_state.get("auth_roles")
    or st.session_state.get("roles")
    or user_obj.get("roles")
    or [user_obj.get("role")]
    or []
)
roles = [str(r).upper() for r in roles if r]

if not any(r in roles for r in ["VENDEDOR", "SELLER", "ADMIN", "2"]):
    st.warning("⚠️ Solo vendedores/admin pueden crear productos.")
    st.stop()

SELLER_ID = (
    st.session_state.get("auth_user_id")
    or st.session_state.get("user_id")
    or user_obj.get("user_id")
    or user_obj.get("id")
)

SELLER_NAME = (
    st.session_state.get("auth_user_name")
    or st.session_state.get("user_name")
    or user_obj.get("email")
    or f"{user_obj.get('nombre','')}".strip()
    or "Mi Tienda"
)

if not SELLER_ID:
    st.error("No pude detectar tu ID de vendedor desde la sesión.")
    st.json(st.session_state)
    st.stop()

# ---------------------------
# HELPERS
# ---------------------------
def create_product(payload: dict):
    try:
        r = requests.post(
            f"{BACKEND_URL}/products",
            json=payload,
            headers=auth_headers(),
            timeout=12
        )
        return r
    except Exception as e:
        st.error(f"Error POST producto: {e}")
        return None

# ---------------------------
# UI
# ---------------------------
st.success(f"🏪 Creando producto como: **{SELLER_NAME}**")
st.caption(f"SELLER_ID: `{SELLER_ID}`")

st.markdown("## ➕ Crear nuevo producto")

with st.form("create_product_form"):
    st.markdown("### 📝 Información básica")

    name = st.text_input("Nombre del producto *", placeholder="Ej: Auriculares Bluetooth Pro")
    description = st.text_area("Descripción", placeholder="Contá qué incluye, materiales, garantía, etc.")
    features = st.text_area("Características técnicas", placeholder="Ej: Bluetooth 5.3, 20h batería, etc.")

    col1, col2 = st.columns(2)
    with col1:
        price = st.number_input("Precio (ARS) *", min_value=0, value=0, step=100)
        stock = st.number_input("Stock disponible *", min_value=0, value=0, step=1)
        condition = st.selectbox("Condición", ["NUEVO", "USADO"], index=0)
    with col2:
        category_id = st.text_input("category_id (UUID de categoría)", placeholder="Opcional en tu backend")
        subcategory = st.text_input("Subcategoría", placeholder="Ej: Audio, Periféricos")
        image_url = st.text_input("URL de imagen principal", placeholder="https://...")

    is_active = st.checkbox("Producto activo", value=True)

    st.markdown("### 💳 Configuración de pagos (opcional)")
    # estos codes coinciden con lo que ya te devuelve el backend
    pay_method = st.selectbox(
        "Método de pago",
        ["TRANSFER", "MP", "CARD", "CRYPTO"],
        index=0,
        help="TRANSFER=Transferencia, MP=MercadoPago, CARD=Tarjeta, CRYPTO=Cripto"
    )
    network = st.text_input("Red cripto (si aplica)", placeholder="TRON, BEP20, ERC20...")
    alias = st.text_input("Alias/CBU (si aplica)")
    wallet = st.text_input("Wallet (si aplica)")

    st.markdown("---")
    cbtn1, cbtn2, cbtn3 = st.columns(3)
    with cbtn1:
        submit = st.form_submit_button("✅ Crear producto", use_container_width=True)
    with cbtn2:
        clear = st.form_submit_button("🧹 Limpiar", use_container_width=True)
    with cbtn3:
        back = st.form_submit_button("⬅️ Volver", use_container_width=True)

if clear:
    st.rerun()

if back:
    safe_switch_page(PAGE_MY_PRODUCTS)

if submit:
    if not name.strip():
        st.error("El nombre es obligatorio.")
        st.stop()
    if price <= 0:
        st.error("El precio debe ser mayor a 0.")
        st.stop()

    payload = {
        "name": name.strip(),
        "description": description.strip() or None,
        "features": features.strip() or None,
        "price": int(price),
        "stock": int(stock),
        "condition": condition,
        "category_id": category_id.strip() or None,
        "subcategory": subcategory.strip() or None,
        "image_url": image_url.strip() or None,
        "is_active": bool(is_active),
        "pay_method": pay_method,
        "network": network.strip() or None,
        "alias": alias.strip() or None,
        "wallet": wallet.strip() or None,
        "seller_id": str(SELLER_ID),  # clave
    }

    r = create_product(payload)
    if r is None:
        st.stop()

    if r.status_code in (200, 201):
        st.success("🎉 Producto creado correctamente.")
        try:
            new_prod = r.json()
            st.json(new_prod)
        except Exception:
            pass

        st.session_state["last_created_product_id"] = None
        st.balloons()
        safe_switch_page(PAGE_MY_PRODUCTS)
    else:
        st.error(f"❌ No se pudo crear (HTTP {r.status_code}).")
        st.text(r.text)

st.markdown("---")
if st.button("📦 Ir a Mis Productos", use_container_width=True, key=K("go_my_products")):
    safe_switch_page(PAGE_MY_PRODUCTS)

if st.button("🏪 Volver al panel vendedor", use_container_width=True, key=K("go_seller_panel")):
    safe_switch_page(PAGE_SELLER_PANEL)
