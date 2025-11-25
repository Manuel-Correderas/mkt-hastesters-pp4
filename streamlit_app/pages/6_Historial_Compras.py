# streamlit_app/pages/6_Historial_Compras.py
import requests
import streamlit as st
from pathlib import Path

from auth_helpers import get_backend_url, auth_headers, require_login

st.set_page_config(page_title="Historial de Compras (Cliente)", layout="centered")

BACKEND_URL = get_backend_url()

PAGE_NS = "historial_v1"
def K(s: str) -> str: return f"{PAGE_NS}:{s}"

# ---------------------------
# ACCESO / ROLES
# ---------------------------
require_login()

roles = st.session_state.get("auth_roles") or st.session_state.get("roles") or []
roles = [str(r).upper() for r in roles]
if "COMPRADOR" not in roles and "ADMIN" not in roles:
    st.warning("⚠️ No tenés permiso para ver el historial de compras.")
    st.stop()

USER_ID = (
    st.session_state.get("auth_user_id")
    or st.session_state.get("user_id")
    or st.session_state.get("user", {}).get("id")
    or ""
)
USER_NAME = (
    st.session_state.get("auth_user_name")
    or st.session_state.get("user_name")
    or st.session_state.get("user", {}).get("name")
    or "Cliente"
)

def safe_switch_page(page_filename: str):
    try:
        st.switch_page(f"pages/{page_filename}")
    except Exception:
        st.info("Volvé desde el menú lateral.")

def pesos(n: int | float) -> str:
    try:
        return f"${int(n):,}".replace(",", ".")
    except Exception:
        return f"${n}"

def fetch_orders(user_id: str):
    """
    Trae órdenes SOLO del comprador logueado.
    Espera que el backend filtre por user_id o por token.
    """
    try:
        r = requests.get(
            f"{BACKEND_URL}/orders",
            params={"user_id": user_id} if user_id else None,
            headers=auth_headers(),
            timeout=12
        )
        if r.status_code == 200:
            data = r.json()
            # soporta: []  o {"items":[...]} o {"orders":[...]}
            if isinstance(data, dict):
                return data.get("items") or data.get("orders") or data.get("data") or []
            return data if isinstance(data, list) else []
        if r.status_code in (401, 403):
            st.warning("Tu sesión no es válida. Volvé a iniciar sesión.")
            return []
        st.warning(f"No pude cargar órdenes (HTTP {r.status_code}).")
        return []
    except requests.RequestException as e:
        st.error(f"No se pudo conectar al backend: {e}")
        return []

# ================== Estilos ==================
st.markdown("""<style>
.stApp { background:#FF8C00; }
.panel{background:#f79b2f;border-radius:14px;padding:16px 18px;box-shadow:0 8px 18px rgba(0,0,0,.18);}
.hdr{text-align:center;font-weight:900;letter-spacing:.6px;color:#10203a;margin-bottom:12px;}
.badge{display:inline-block;background:#d6d6d6;color:#000;font-weight:900;border-radius:8px;padding:6px 10px;margin:4px 0;}
.list{background:#ffa84d;border-radius:10px;padding:10px;margin-top:8px;max-height:460px;overflow-y:auto;box-shadow: inset 0 1px 4px rgba(0,0,0,.12);}
.card{background:#fff5e6;border-radius:10px;padding:12px;box-shadow:0 2px 8px rgba(0,0,0,.12);margin-bottom:10px;}
.small{font-size:.86rem;color:#333;}
.btn-primary{background:#0b3a91 !important;color:#fff !important;border:none !important;border-radius:8px !important;padding:8px 14px !important;font-weight:900 !important;}
.btn-secondary{background:#936037 !important;color:#fff !important;border:none !important;border-radius:8px !important;padding:8px 14px !important;font-weight:900 !important;}
.client-header{background:#ff9b2f;padding:12px;border-radius:8px;margin-bottom:15px;text-align:center;}
</style>""", unsafe_allow_html=True)

# ================== Encabezado ==================
st.markdown('<div class="hdr"><h3>🧾 HISTORIAL DE COMPRAS</h3></div>', unsafe_allow_html=True)
st.markdown('<div class="panel">', unsafe_allow_html=True)

orders = fetch_orders(USER_ID)

# Cabecera cliente + resumen
total_gasto = 0
try:
    total_gasto = sum(float(o.get("total_amount", o.get("total", 0)) or 0) for o in orders)
except Exception:
    total_gasto = 0

st.markdown("<div class='client-header'>", unsafe_allow_html=True)
st.markdown(f"### 👤 {USER_NAME}")
st.markdown(f"**📊 RESUMEN:** {len(orders)} COMPRAS • 💵 {pesos(total_gasto)} TOTAL GASTADO")
st.markdown("</div>", unsafe_allow_html=True)

# ------------------ Filtros ------------------
st.markdown("### 🔍 BUSCAR EN MIS COMPRAS")
col_search, col_filter = st.columns([3, 1])
with col_search:
    search_query = st.text_input("", placeholder="Buscar por producto, empresa o vendedor...")
with col_filter:
    filter_status = st.selectbox("Estado", ["Todas", "Entregado", "En camino", "Pendiente", "Cancelado"])

# ================== Lista de Compras ==================
st.markdown('<div class="list">', unsafe_allow_html=True)

def order_matches(o: dict) -> bool:
    status = (o.get("status") or o.get("estado") or "").strip()
    if filter_status != "Todas" and status != filter_status:
        return False

    if not search_query:
        return True

    q = search_query.lower()
    for it in o.get("items", []) or o.get("productos", []):
        if any(q in str(x or "").lower() for x in [
            it.get("product_name"),
            it.get("name"),
            it.get("seller"),
            it.get("seller_name"),
            it.get("company")
        ]):
            return True
    return False

filtered = [o for o in orders if order_matches(o)]

if not filtered:
    st.info("No se encontraron compras que coincidan con los filtros.")
else:
    # orden más nuevo primero
    def _date_key(o):
        s = o.get("created_at") or o.get("date") or ""
        return s
    filtered = sorted(filtered, key=_date_key, reverse=True)

    for o in filtered:
        oid = str(o.get("id") or o.get("order_id") or "")
        st.markdown('<div class="card">', unsafe_allow_html=True)

        first = (o.get("items") or [{}])[0]
        product_name = first.get("product_name") or first.get("name") or "(sin ítems)"
        category = first.get("category") or "-"
        subcategory = first.get("subcategory") or "-"
        seller = first.get("seller") or first.get("seller_name") or "-"
        company = first.get("company") or "-"
        status = (o.get("status") or o.get("estado") or "-").strip()
        total = float(o.get("total_amount", o.get("total", 0)) or 0)

        created_at = o.get("created_at") or ""
        date_iso = created_at[:10] if created_at else "-"
        time_iso = created_at[11:16] if len(created_at) >= 16 else ""

        col_header1, col_header2 = st.columns([3, 1])
        with col_header1:
            st.markdown(f"**🛍️ {product_name}**")
            st.caption(f"📂 {category} • 🔍 {subcategory}")
        with col_header2:
            icon = "🟢" if status == "Entregado" else "🟡" if status == "En camino" else "🔴"
            st.markdown(f"**{icon} {status}**")

        col_details1, col_details2 = st.columns(2)
        with col_details1:
            st.markdown(f"""
            **📅 Fecha:** {date_iso} {time_iso}  
            **🏪 Vendedor:** {seller}  
            **🏢 Empresa:** {company}  
            **🧾 Orden:** {oid}
            """)
        with col_details2:
            try:
                qty_sum = sum(int(it.get("quantity", it.get("qty", 0)) or 0) for it in (o.get("items") or []))
            except Exception:
                qty_sum = "-"
            st.markdown(f"""
            **📦 Ítems:** {qty_sum}  
            **💵 Total Orden:** {pesos(total)}  
            **👤 Cliente:** {o.get("user_name") or USER_NAME}
            """)

        st.markdown(f"<span class='badge'>💵 TOTAL: {pesos(total)}</span>", unsafe_allow_html=True)

        # Acciones
        c1, c2, c3 = st.columns(3)
        with c1:
            st.button("📄 Ver Factura", key=K(f"invoice_{oid}"))
        with c2:
            st.button("📦 Seguir Envío", key=K(f"track_{oid}"))
        with c3:
            if st.button("⭐ Valorar", key=K(f"rate_{oid}")):
                # si querés que vaya directo a comentarios con id del producto:
                pid = first.get("product_id") or first.get("id")
                if pid:
                    st.query_params["id"] = str(pid)
                safe_switch_page("5_Comentarios.py")

        st.markdown("</div>", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)  # /list

# ================== Pie ==================
st.write("")
if st.button("⬅️ VOLVER AL PANEL", key=K("btn_back_hist"), use_container_width=True):
    safe_switch_page("1_Comprador.py")

st.markdown('</div>', unsafe_allow_html=True)  # /panel
