import streamlit as st
import pandas as pd
import requests
from datetime import date, timedelta
from pathlib import Path

from auth_helpers import get_backend_url, require_login, auth_headers

st.set_page_config(page_title="Finanzas y Rentabilidad", page_icon="💰", layout="wide")

BACKEND_URL = get_backend_url()

PAGE_NS = "finanzas_v2"
def K(s: str): return f"{PAGE_NS}:{s}"

# ==========================
# AUTH ✅
# ==========================
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
    st.warning("⚠️ Solo vendedores/admin pueden ver este panel.")
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

# =======================
# HEADER
# =======================
st.title("Finanzas y Rentabilidad")
st.caption("Dashboard financiero del vendedor con datos reales del backend.")
st.success(f"🏪 Vendedor: **{SELLER_NAME}**")
st.caption(f"SELLER_ID: `{SELLER_ID}`")

# =======================
# SIDEBAR – FILTROS
# =======================
st.sidebar.header("Filtros")

hoy = date.today()
inicio = hoy - timedelta(days=30)
rangos = st.sidebar.date_input("Rango de fechas", (inicio, hoy), format="DD/MM/YYYY")

moneda = st.sidebar.selectbox("Moneda", ["ARS", "USD"], index=0)
canales = st.sidebar.multiselect(
    "Canales",
    ["tienda", "marketplace", "instagram", "whatsapp"],
    default=["tienda"]
)

mostrar_iva = st.sidebar.toggle("Mostrar IVA (21%)", value=False)
top_n = st.sidebar.slider("Top productos", 3, 15, 8)

params = {
    "start": str(rangos[0]),
    "end": str(rangos[1]),
    "currency": moneda,
    "channels": ",".join(canales),
    # si más adelante querés filtrar por vendedor:
    # "seller_id": SELLER_ID
}

# =======================
# HELPERS ✅ ahora manda token
# =======================
def api_get(path: str, extra_params: dict | None = None):
    try:
        p = dict(params)
        if extra_params:
            p.update(extra_params)

        res = requests.get(
            f"{BACKEND_URL}{path}",
            params=p,
            headers=auth_headers(),  # ✅ CLAVE: mandar token
            timeout=10
        )
        if res.status_code == 200:
            return res.json()
        st.error(f"Error {res.status_code}: {res.text}")
        return None
    except Exception as e:
        st.error(f"No se pudo conectar al backend: {e}")
        return None

# =======================
# 1) KPIs
# =======================
st.subheader("📊 KPIs Financieros")

summary = api_get("/analytics/sales-summary") or {
    "total_sales": 0,
    "total_margin": 0,
    "ticket_avg": 0,
    "returns": 0
}

ventas = summary.get("total_sales", 0)
margen = summary.get("total_margin", 0)
ticket = summary.get("ticket_avg", 0)
devoluciones = summary.get("returns", 0)

if mostrar_iva:
    ventas *= 1.21
    margen *= 1.21

c1, c2, c3, c4 = st.columns(4)
c1.metric("Ventas", f"$ {ventas:,.0f}".replace(",", "."))
c2.metric(
    "Margen",
    f"$ {margen:,.0f}".replace(",", "."),
    delta=f"{(margen / ventas * 100) if ventas else 0:.1f}%"
)
c3.metric("Ticket Promedio", f"$ {ticket:,.0f}".replace(",", "."))
c4.metric("Devoluciones", devoluciones)

st.divider()

# =======================
# 2) Ventas diarias
# =======================
st.subheader("📈 Evolución diaria de ventas")

daily = api_get("/analytics/sales-daily")
if daily:
    df_daily = pd.DataFrame(daily)
    st.line_chart(df_daily, x="date", y="total")
else:
    st.info("No hay datos de ventas en este período.")

col1, col2 = st.columns(2)

# =======================
# 3) Margen por categoría
# =======================
with col1:
    st.subheader("📦 Margen por categoría")
    margins = api_get("/analytics/category-margins")
    if margins:
        df_margins = pd.DataFrame(margins)
        st.bar_chart(df_margins, x="category", y="margin")
    else:
        st.info("No hay datos para mostrar.")

# =======================
# 4) Top productos
# =======================
with col2:
    st.subheader("🏆 Top productos por ventas")
    top = api_get("/analytics/top-products", {"top": top_n})
    if top:
        df_top = pd.DataFrame(top)
        st.bar_chart(df_top, x="product", y="sales")
    else:
        st.info("Sin productos para mostrar.")

st.divider()

# =======================
# 5) Operaciones
# =======================
st.subheader("🧾 Detalle de operaciones")
ops = api_get("/analytics/operations")

if ops:
    df_ops = pd.DataFrame(ops)
    st.dataframe(df_ops, use_container_width=True)
else:
    st.info("No existen operaciones registradas en el período seleccionado.")
