# streamlit_app/pages/9_📈_Historial_Ventas.py
import streamlit as st
import pandas as pd
import requests
from datetime import timedelta, date
from pathlib import Path

from auth_helpers import get_backend_url, require_login, auth_headers

# ===========================
# CONFIG
# ===========================
st.set_page_config(
    page_title="Historial de Ventas (Vendedor)",
    page_icon="📈",
    layout="centered"
)

BACKEND_URL = get_backend_url()

PAGE_NS = "sales_hist_v4"
def K(s: str): return f"{PAGE_NS}:{s}"

PAGE_SELLER_PANEL = "2_Vendedor.py"

def safe_switch_page(*pages):
    for p in pages:
        path = Path(__file__).resolve().parent / p
        if path.exists():
            st.switch_page(f"pages/{p}")
            return
    st.warning("No se encontró la página destino.")

# ===========================
# AUTH
# ===========================
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
    st.error("Solo vendedores/admin pueden ver este panel.")
    st.stop()

SELLER_ID = (
    st.session_state.get("auth_user_id")
    or user_obj.get("user_id")
    or user_obj.get("id")
)

SELLER_NAME = (
    st.session_state.get("auth_user_name")
    or user_obj.get("email")
    or user_obj.get("nombre")
    or "Mi Tienda"
)

if not SELLER_ID:
    st.error("No se encontró seller_id en sesión.")
    st.stop()

# ===========================
# ESTILOS
# ===========================
st.markdown("""
<style>
.stApp { background:#FF8C00; }
.panel { background:#f79b2f; border-radius:14px; padding:16px 18px; box-shadow:0 8px 18px rgba(0,0,0,.18); }
.hdr { text-align:center; font-weight:900; letter-spacing:.6px; color:#10203a; margin-bottom:12px; }
.list { background:#ffa84d; border-radius:10px; padding:10px; margin-top:8px; max-height: 460px; overflow-y:auto; }
.card { background:#fff5e6; border-radius:10px; padding:12px; box-shadow:0 2px 8px rgba(0,0,0,.12); margin-bottom:10px; }
.badge { display:inline-block; background:#d6d6d6; color:#000; font-weight:900; border-radius:8px; padding:6px 10px; margin:6px 0; }
</style>
""", unsafe_allow_html=True)

# ===========================
# FETCH REAL DE /sales/history
# ===========================
def fetch_sales(start: date, end: date, search: str):
    params = {
        "seller_id": SELLER_ID,
        "start": start.isoformat(),
        "end": end.isoformat()
    }
    if search:
        params["search"] = search

    try:
        r = requests.get(
            f"{BACKEND_URL}/sales/history",
            params=params,
            headers=auth_headers(),
            timeout=10
        )
        if r.status_code == 200:
            return r.json()
        st.error(f"/sales/history → {r.status_code}: {r.text}")
    except Exception as e:
        st.error(f"Error conectando a /sales/history: {e}")

    return []


# ===========================
# HEADER
# ===========================
st.markdown('<div class="hdr"><h3>📈 HISTORIAL DE VENTAS</h3></div>', unsafe_allow_html=True)
st.markdown('<div class="panel">', unsafe_allow_html=True)
st.markdown(
    f"<div class='seller-header'>🏪 {SELLER_NAME}<br><small>{SELLER_ID}</small></div>",
    unsafe_allow_html=True
)

# ===========================
# FILTROS
# ===========================
st.markdown("### 🔍 BUSCAR VENTAS")
c1, c2, c3 = st.columns([2, 1, 1])

with c1:
    search_query = st.text_input("", placeholder="Buscar producto, cliente, factura...")

with c2:
    date_filter = st.selectbox("Fecha", ["Últimos 7 días", "Este mes", "Últimos 3 meses", "Todo"])

with c3:
    status_filter = st.selectbox("Estado", ["Todos", "Entregados", "En camino", "Pendientes"])

hoy = date.today()
if date_filter == "Últimos 7 días":
    start_date = hoy - timedelta(days=7)
elif date_filter == "Este mes":
    start_date = hoy.replace(day=1)
elif date_filter == "Últimos 3 meses":
    start_date = hoy - timedelta(days=90)
else:
    start_date = hoy - timedelta(days=365)

end_date = hoy

# ===========================
# FETCH + PROCESADO
# ===========================
sales = fetch_sales(start_date, end_date, search_query)

df = pd.DataFrame(sales) if sales else pd.DataFrame()

if not df.empty:
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["date_str"] = df["date"].dt.strftime("%d/%m/%Y")
    df["time_str"] = df["date"].dt.strftime("%H:%M")

# Filtro por estado (backend devuelve status en mayúsculas)
status_map = {"Entregados": "DELIVERED", "En camino": "SHIPPED", "Pendientes": "PENDING"}

if status_filter != "Todos" and not df.empty:
    wanted = status_map.get(status_filter, status_filter).upper()
    df = df[df["status"].str.upper() == wanted]

# ===========================
# RESUMEN
# ===========================
total_ventas = len(df)
ingresos_totales = df["total"].sum() if total_ventas > 0 else 0

st.markdown(
    f"**📊 RESUMEN:** {total_ventas} ventas • "
    f"${ingresos_totales:,.0f} ingresos".replace(",", ".")
)

# ===========================
# LISTA
# ===========================
st.markdown('<div class="list">', unsafe_allow_html=True)

if df.empty:
    st.info("No hay ventas para los filtros seleccionados.")
else:
    for _, r in df.iterrows():
        st.markdown('<div class="card">', unsafe_allow_html=True)

        st.markdown(f"### 🛍️ {r['product_name']}")
        st.caption(f"📂 {r['category']}  •  🔍 {r['subcategory']}")

        status_color = "🟢" if r["status"]=="DELIVERED" else "🟡" if r["status"]=="SHIPPED" else "🔴"
        st.markdown(f"**{status_color} {r['status']}**")

        st.markdown(
            f"""
            **📅 Fecha:** {r['date_str']} {r['time_str']}  
            **👤 Cliente:** {r['client_name']}  
            **🏠 Dirección:** {r['client_address']}  
            **📦 Cantidad:** {r['quantity']}  
            **💰 Unitario:** ${r['unit_price']:,.0f}  
            **🧾 Factura:** {r['invoice']}  
            """.replace(",", ".")
        )

        st.markdown(
            f"<span class='badge'>💵 TOTAL: ${r['total']:,.0f}</span>".replace(",", "."),
            unsafe_allow_html=True
        )

        st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ===========================
# FOOTER
# ===========================
st.markdown("---")
if st.button("⬅️ VOLVER AL PANEL", use_container_width=True):
    safe_switch_page(PAGE_SELLER_PANEL)

st.markdown("</div>", unsafe_allow_html=True)
