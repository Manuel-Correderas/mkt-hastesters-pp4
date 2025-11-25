# streamlit_app/pages/3_📦_Producto.py
import streamlit as st
import requests

from auth_helpers import get_backend_url, auth_headers

st.set_page_config(page_title="Producto", layout="wide")

BACKEND_URL = get_backend_url()
PAGE_NS = "product_view_v1"

def K(s: str) -> str:
    return f"{PAGE_NS}:{s}"


# =========================
# HELPERS
# =========================
def get_roles_upper():
    roles = st.session_state.get("auth_roles") or st.session_state.get("roles") or []
    return [str(r).upper() for r in roles]

def is_seller() -> bool:
    roles = get_roles_upper()
    return "VENDEDOR" in roles or "ADMIN" in roles

def is_admin() -> bool:
    roles = get_roles_upper()
    return "ADMIN" in roles

def can_edit_this_product(product: dict) -> bool:
    """
    True si:
      - es ADMIN, o
      - es VENDEDOR y el producto le pertenece
    """
    if not is_seller():
        return False
    if is_admin():
        return True

    logged_user_id = (
        st.session_state.get("auth_user_id")
        or st.session_state.get("user_id")
        or st.session_state.get("seller_id")
    )
    prod_seller_id = product.get("seller_id")

    if not logged_user_id or not prod_seller_id:
        return False

    return str(logged_user_id) == str(prod_seller_id)

def get_product_id_from_query() -> str | None:
    """
    Lee SOLO st.query_params.
    Acepta ?id=... o ?product_id=...
    """
    qp = st.query_params
    pid = qp.get("id") or qp.get("product_id")

    if isinstance(pid, list):
        pid = pid[0]

    if not pid:
        pid = st.session_state.get("product_id") or st.session_state.get("last_product")

    return str(pid) if pid else None

def require_login_for_cart() -> bool:
    if "auth_token" not in st.session_state:
        st.warning("Tenés que iniciar sesión para agregar productos al carrito.")
        st.page_link("pages/0_Login.py", label="Ir a Login", icon="🔐")
        return False
    return True

def pesos(n):
    try:
        return f"${int(n):,}".replace(",", ".")
    except Exception:
        return f"${n}"


# =========================
# ESTILOS
# =========================
st.markdown("""
<style>
.stApp { background:#f8fafc; }
.detail-wrapper{
  background:#ffffff; border-radius:18px; padding:20px;
  box-shadow:0 12px 30px rgba(15,23,42,.18);
}
.detail-name{ font-size:1.8rem; font-weight:900; color:#111827; margin-bottom:4px; }
.detail-price{ font-size:1.5rem; font-weight:800; color:#16a34a; margin-bottom:8px; }
.detail-meta{ font-size:.9rem; color:#6b7280; margin-bottom:4px; }
.detail-desc{ font-size:.95rem; color:#111827; margin-top:10px; }
.badge{
  display:inline-block; padding:4px 10px; border-radius:999px;
  font-size:.8rem; font-weight:800;
}
.badge.stock-ok{ background:#e8f6e8; color:#1e7e34; }
.badge.stock-low{ background:#fff8e5; color:#b58102; }
.badge.stock-out{ background:#fdecea; color:#c0392b; }
.actions-row{
  display:flex; gap:10px; margin-top:12px;
}
</style>
""", unsafe_allow_html=True)


# =========================
# CARGAR PRODUCTO
# =========================
pid = get_product_id_from_query()

if not pid:
    st.info("No se encontró un producto para mostrar. Volvé al Home y elegí uno.")
    st.stop()

producto = None
try:
    r = requests.get(f"{BACKEND_URL}/products/{pid}", timeout=15)
    if r.status_code == 200:
        producto = r.json()
    else:
        st.error(f"No se pudo cargar el producto (HTTP {r.status_code}): {r.text}")
except Exception as e:
    st.error(f"Error de conexión al backend: {e}")

if not producto:
    st.info("No se encontró el producto solicitado.")
    st.stop()


# Campos básicos
name = producto.get("name", "Producto")
price = producto.get("price", 0)
desc = producto.get("description", "")
cat = producto.get("category", "")
sub = producto.get("subcategory", "")
stock = int(producto.get("stock", 0) or 0)
seller_alias = producto.get("seller_alias") or producto.get("seller_name") or producto.get("seller", "")
rating = float(producto.get("rating", 0.0) or 0.0)
sold = int(producto.get("sold", 0) or 0)

img = str(producto.get("image_url", "") or "").strip()
if not (img and img.startswith("http")):
    img = "https://via.placeholder.com/600x400.png?text=Producto"


# =========================
# UI DETALLE
# =========================
col_img, col_info = st.columns([2, 3])

with col_img:
    st.image(img, use_container_width=True)

with col_info:
    st.markdown('<div class="detail-wrapper">', unsafe_allow_html=True)

    st.markdown(f'<div class="detail-name">{name}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="detail-price">{pesos(price)}</div>', unsafe_allow_html=True)

    st.markdown(
        f'<div class="detail-meta">Categoría: {cat or "-"} / {sub or "-"}</div>',
        unsafe_allow_html=True,
    )

    # Badge stock
    if stock <= 0:
        badge = "<span class='badge stock-out'>Sin stock</span>"
    elif stock < 5:
        badge = f"<span class='badge stock-low'>Stock bajo: {stock}</span>"
    else:
        badge = f"<span class='badge stock-ok'>Stock: {stock}</span>"
    st.markdown(badge, unsafe_allow_html=True)

    if seller_alias:
        st.markdown(
            f'<div class="detail-meta">Vendido por: <b>{seller_alias}</b></div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        f'<div class="detail-meta">⭐ {rating:.1f}/10 • 🎯 {sold} vendidos</div>',
        unsafe_allow_html=True,
    )

    if desc:
        st.markdown(
            '<div class="detail-desc"><b>Descripción</b><br/>' + desc + '</div>',
            unsafe_allow_html=True
        )

    st.markdown("---")

    # =========================
    # ACCIONES
    # =========================

    

   
    # =========================
    # VER COMENTARIOS (PÚBLICO)
    # =========================
    if st.button("📖 Ver comentarios del producto", use_container_width=True, key=K("go_comments")):
        # guardo fallback por si algo borra la URL
        st.session_state["last_product"] = pid

        # seteo query param antes de navegar
        st.query_params.clear()
        st.query_params["id"] = pid

        st.switch_page("pages/5b_Ver_Comentarios.py")




    # Agregar al carrito
    if stock <= 0:
        st.error("No hay stock disponible para este producto.")
    else:
        qty = st.number_input(
            "Cantidad",
            min_value=1,
            max_value=stock,
            value=1,
            step=1,
            key=K(f"qty_detail_{pid}")
        )
        if st.button("🛒 Añadir al carrito", key=K(f"add_cart_{pid}"), use_container_width=True):
            if require_login_for_cart():
                try:
                    r_cart = requests.post(
                        f"{BACKEND_URL}/cart/items",
                        json={"product_id": pid, "qty": int(qty)},
                        headers=auth_headers(),
                        timeout=10,
                    )
                    if r_cart.status_code in (200, 201):
                        st.success("Producto añadido al carrito ✅")
                        st.page_link("pages/4_Mi_Carrito.py", label="Ir al carrito", icon="🛒")
                    else:
                        st.error(f"Error al agregar al carrito (HTTP {r_cart.status_code}): {r_cart.text}")
                except Exception as e:
                    st.error(f"No se pudo conectar al backend: {e}")

    st.markdown('</div>', unsafe_allow_html=True)


# =========================
# BOTONES DE NAVEGACIÓN ABAJO
# =========================
st.write("")
c1, c2 = st.columns(2)

with c1:
    if st.button("⬅️ Volver al Home", use_container_width=True, key=K("back_home")):
        st.query_params.clear()
        st.switch_page("Home.py")

with c2:
    if st.button("🛒 Ir al Carrito", use_container_width=True, key=K("go_cart")):
        st.switch_page("pages/4_Mi_Carrito.py")
