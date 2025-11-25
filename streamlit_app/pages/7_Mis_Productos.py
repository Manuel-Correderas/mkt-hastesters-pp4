# streamlit_app/pages/7_Crear_Producto.py
import streamlit as st
import requests
from pathlib import Path

from auth_helpers import get_backend_url, require_login, auth_headers

# ⚠️ set_page_config SIEMPRE primero
st.set_page_config(page_title="Mis Productos (Vendedor)", page_icon="📦", layout="centered")

BACKEND_URL = get_backend_url()

PAGE_NS = "misprod_v4"
def K(s: str) -> str:
    return f"{PAGE_NS}:{s}"

# Ajustá nombres reales si difieren
PAGE_CREATE = "7b_Crear_Producto.py"   # tu página de crear
PAGE_SELLER_PANEL = "2_Vendedor.py"   # panel vendedor

# ---------------------------
# NAVEGACIÓN SEGURA CON FALLBACK
# ---------------------------
def safe_switch_page(*page_filenames: str):
    for filename in page_filenames:
        # main script (Home, etc)
        if filename.endswith(".py") and not filename.startswith("pages/"):
            main_path = Path(__file__).resolve().parents[1] / filename
            if main_path.exists():
                st.switch_page(filename)
                return
        # page dentro de /pages
        page_path = Path(__file__).resolve().parent / filename
        if page_path.exists():
            st.switch_page(f"pages/{filename}")
            return
    st.warning("No se encontró ninguna página esperada en /pages. Revisá nombres exactos.")

# ---------------------------
# AUTH  ✅ SIN CHEQUEAR RETORNO
# ---------------------------
require_login()

user_obj = st.session_state.get("user") or st.session_state.get("auth_user") or {}

# roles pueden estar en session_state.roles o en user.roles
roles = (
    st.session_state.get("auth_roles")
    or st.session_state.get("roles")
    or user_obj.get("roles")
    or [user_obj.get("role")]
    or []
)
roles = [str(r).upper() for r in roles if r]

# tu tabla roles tiene code: COMPRADOR/VENDEDOR/ADMIN
if not any(r in roles for r in ["VENDEDOR", "SELLER", "ADMIN", "2"]):
    st.warning("⚠️ Solo vendedores/admin pueden ver este panel.")
    st.stop()

# ---------------------------
# SELLER_ID robusto (solo UUID)
# ---------------------------
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
def pesos(n):
    try:
        return f"${int(float(n)):,.0f}".replace(",", ".")
    except Exception:
        return f"${n}"

def normalize_products(data):
    if isinstance(data, dict):
        return data.get("items") or data.get("data") or []
    return data if isinstance(data, list) else []

def fetch_my_products():
    try:
        r = requests.get(
            f"{BACKEND_URL}/products",
            params={"seller_id": SELLER_ID, "limit": 200},
            headers=auth_headers(),
            timeout=10
        )
        if r.status_code == 200:
            return normalize_products(r.json())
        st.error(f"/products respondió {r.status_code}: {r.text}")
    except Exception as e:
        st.error(f"Error conectando a /products: {e}")
    return []

def update_product(pid: str, payload: dict):
    try:
        return requests.put(
            f"{BACKEND_URL}/products/{pid}",
            json=payload,
            headers=auth_headers(),
            timeout=12
        )
    except Exception as e:
        st.error(f"Error PUT producto: {e}")
        return None

def delete_product(pid: str):
    try:
        return requests.delete(
            f"{BACKEND_URL}/products/{pid}",
            headers=auth_headers(),
            timeout=12
        )
    except Exception as e:
        st.error(f"Error DELETE producto: {e}")
        return None

# ---------------------------
# HEADER
# ---------------------------
st.success(f"🏪 Logueado como vendedor: **{SELLER_NAME}**")
st.caption(f"SELLER_ID: `{SELLER_ID}` • Roles: `{roles}`")

st.markdown("## 📦 Mis productos")

modo_edicion = st.toggle(
    "Modo edición rápida",
    value=True,
    help="Activalo para editar directamente acá mismo."
)

products = fetch_my_products()

if not products:
    st.warning("No tenés productos activos o no matchean con tu seller_id.")
    st.info("Si estás seguro que hay productos, revisá en DB que `products.seller_id` sea tu UUID.")
    if st.button("➕ Crear mi primer producto", key=K("go_create"), use_container_width=True):
        safe_switch_page(PAGE_CREATE)
    st.stop()

# ---------------------------
# LISTADO
# ---------------------------
for p in products:
    pid = p.get("id")
    name = p.get("name", "(sin nombre)")
    price = p.get("price", 0)
    stock = p.get("stock", 0)
    category_id = p.get("category_id") or ""
    subcategory = p.get("subcategory") or ""
    img = p.get("image_url") or ""
    description = p.get("description") or ""
    features = p.get("features") or ""
    is_active = bool(p.get("is_active", True))

    pay_method = p.get("pay_method") or ""
    network = p.get("network") or ""
    alias = p.get("alias") or ""
    wallet = p.get("wallet") or ""

    st.markdown("---")
    c1, c2 = st.columns([3, 1])

    with c1:
        st.markdown(f"### {name}")
        st.write(f"💲 {pesos(price)} • 📦 Stock: **{stock}**")
        st.caption(f"Categoría ID: {category_id or '-'} • Subcat: {subcategory or '-'}")
        st.caption(f"ID: {pid} • {'✅ Activo' if is_active else '⛔ Inactivo'}")

    with c2:
        if img:
            try:
                st.image(img, use_container_width=True)
            except Exception:
                st.write("📸")
        else:
            st.write("📸 sin imagen")

    if modo_edicion:
        with st.expander("✏️ Editar producto acá mismo", expanded=False):
            new_name = st.text_input("Nombre del producto", value=name, key=K(f"name_{pid}"))
            new_price = st.number_input("Precio (ARS)", min_value=0, value=int(price or 0), step=100, key=K(f"price_{pid}"))
            new_stock = st.number_input("Stock disponible", min_value=0, value=int(stock or 0), step=1, key=K(f"stock_{pid}"))

            new_category_id = st.text_input("category_id (UUID de categoría)", value=category_id, key=K(f"cat_{pid}"))
            new_subcat = st.text_input("Subcategoría", value=subcategory, key=K(f"sub_{pid}"))

            new_img = st.text_input("URL de imagen principal", value=img, key=K(f"img_{pid}"))
            new_desc = st.text_area("Descripción", value=description, key=K(f"desc_{pid}"))
            new_feat = st.text_area("Características", value=features, key=K(f"feat_{pid}"))

            new_active = st.checkbox("Producto activo", value=is_active, key=K(f"act_{pid}"))

            st.markdown("#### 💳 Datos de pago (opcionales)")
            new_pay_method = st.text_input("pay_method", value=pay_method, key=K(f"pm_{pid}"))
            new_network = st.text_input("network", value=network, key=K(f"net_{pid}"))
            new_alias = st.text_input("alias", value=alias, key=K(f"alias_{pid}"))
            new_wallet = st.text_input("wallet", value=wallet, key=K(f"wallet_{pid}"))

            b1, b2, b3 = st.columns(3)

            with b1:
                if st.button("💾 Guardar cambios", key=K(f"save_{pid}"), use_container_width=True):
                    payload = {
                        "name": new_name,
                        "price": int(new_price),
                        "stock": int(new_stock),
                        "category_id": new_category_id or None,
                        "subcategory": new_subcat or None,
                        "image_url": new_img or None,
                        "description": new_desc or None,
                        "features": new_feat or None,
                        "is_active": bool(new_active),
                        "pay_method": new_pay_method or None,
                        "network": new_network or None,
                        "alias": new_alias or None,
                        "wallet": new_wallet or None,
                    }
                    r = update_product(pid, payload)
                    if r and r.status_code == 200:
                        st.success("✅ Producto actualizado.")
                        st.rerun()
                    else:
                        st.error(f"❌ No se pudo actualizar. {(r.status_code if r else '')}")
                        if r:
                            st.text(r.text)

            with b2:
                label_toggle = "⛔ Desactivar" if is_active else "✅ Activar"
                if st.button(label_toggle, key=K(f"toggle_{pid}"), use_container_width=True):
                    r = update_product(pid, {"is_active": not is_active})
                    if r and r.status_code == 200:
                        st.success("✅ Estado actualizado.")
                        st.rerun()
                    else:
                        st.error(r.text if r else "Error actualizando estado")

            with b3:
                if st.button("🗑 Eliminar producto", key=K(f"del_{pid}"), use_container_width=True):
                    r = delete_product(pid)
                    if r and r.status_code in (200, 204):
                        st.success("✅ Producto eliminado.")
                        st.rerun()
                    else:
                        st.error(r.text if r else "Error eliminando producto")

st.markdown("### ➕ Nuevo producto")
if st.button("Crear producto", use_container_width=True, key=K("create_bottom")):
    safe_switch_page(PAGE_CREATE)

st.markdown("### ⬅️ Volver al panel vendedor")
if st.button("Volver", use_container_width=True, key=K("back_seller")):
    safe_switch_page(PAGE_SELLER_PANEL)
