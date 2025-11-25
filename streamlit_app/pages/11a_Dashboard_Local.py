# streamlit_app/pages/11a_Dashboard_Local.py
import streamlit as st
import pandas as pd
import requests
from datetime import date
from pathlib import Path

from auth_helpers import get_backend_url, require_login, auth_headers

st.set_page_config(page_title="Dashboard Local", layout="wide")

# =======================
# Helpers seguros (ANTES de usarlos)
# =======================
def safe_float(x, default=0.0):
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default

def money(x):
    return f"$ {int(safe_float(x)):,.0f}".replace(",", ".")

# =======================
# CONFIG / BACKEND
# =======================
BACKEND_URL = get_backend_url()

# =======================
# AUTH + USER DETECTION
# =======================
require_login()

# user_obj puede venir en distintos formatos según tu login
user_obj = st.session_state.get("user") or st.session_state.get("auth_user") or {}

# -----------------------
# Normalización de sesión
# -----------------------
# Si tu login devolvió premium/roles a nivel raíz (como tu backend),
# aseguramos que también existan dentro de user_obj
root_premium = st.session_state.get("premium")
root_roles = st.session_state.get("auth_roles") or st.session_state.get("roles")
root_user_id = st.session_state.get("auth_user_id")
root_user_name = st.session_state.get("auth_user_name")
root_email = st.session_state.get("auth_user_email")

if isinstance(user_obj, dict):
    if root_premium is not None and user_obj.get("premium") is None:
        user_obj["premium"] = root_premium
    if root_roles and not user_obj.get("roles"):
        user_obj["roles"] = root_roles
    if root_user_id and not (user_obj.get("id") or user_obj.get("user_id")):
        user_obj["id"] = root_user_id
    if root_user_name and not user_obj.get("nombre"):
        user_obj["nombre"] = root_user_name
    if root_email and not user_obj.get("email"):
        user_obj["email"] = root_email

# roles robustos
roles = (
    st.session_state.get("auth_roles")
    or st.session_state.get("roles")
    or user_obj.get("roles")
    or ([user_obj.get("role")] if user_obj.get("role") else [])
    or []
)
roles = [str(r).upper() for r in roles if r]

# ID único del usuario
USER_ID = (
    st.session_state.get("auth_user_id")
    or user_obj.get("user_id")
    or user_obj.get("id")
)

USER_NAME = (
    st.session_state.get("auth_user_name")
    or user_obj.get("nombre")
    or user_obj.get("email")
    or "Usuario"
)

USER_EMAIL = user_obj.get("email") or ""

# =======================
# Premium detection MUY flexible
# =======================
def is_premium_user():
    # 0) premium guardado en sesión (login)
    if safe_float(st.session_state.get("premium"), 0) >= 1:
        return True

    # 1) premium dentro del user_obj
    if safe_float(user_obj.get("premium"), 0) >= 1:
        return True

    # 2) compatibilidad con versiones viejas
    if any("PREMIUM" in r for r in roles):
        return True
    if user_obj.get("is_premium") is True:
        return True
    if str(user_obj.get("plan", "")).lower() == "premium":
        return True

    return False

IS_PREMIUM = is_premium_user()

# rol default para la vista
default_role = "VENDEDOR"
if any(r in roles for r in ["COMPRADOR", "BUYER", "1"]):
    default_role = "COMPRADOR"

# =======================
# API
# =======================
def api_get_local_dashboard(role_backend: str):
    endpoint = (
        f"{BACKEND_URL}/analytics/seller/dashboard"
        if role_backend == "VENDEDOR"
        else f"{BACKEND_URL}/analytics/buyer/dashboard"
    )
    try:
        r = requests.get(endpoint, headers=auth_headers(), timeout=10)
        if r.status_code == 200:
            return r.json() or {}
        if r.status_code in (401, 403):
            st.warning("🔒 Necesitás Premium para ver reportes avanzados.")
            return {}
        if r.status_code == 404:
            st.info("ℹ️ Analytics local no implementado en backend. Modo demo.")
            return {}
        st.warning(f"Analytics respondió {r.status_code}: {r.text}")
        return {}
    except Exception as e:
        st.warning(f"No se pudo conectar a analytics: {e}")
        return {}

# =======================
# Estilos
# =======================
st.markdown("""
<style>
.stApp { background:#FF8C00; }
.dashboard-panel {
    background:#f79b2f; border-radius:12px; padding:20px; margin-bottom:20px;
    box-shadow:0 8px 18px rgba(0,0,0,.18);
}
.metric-card {
    background:#fff5e6; border-radius:10px; padding:15px; text-align:center;
    box-shadow:0 2px 8px rgba(0,0,0,.12);
}
.badge-soft{
    background:#fff5e6; padding:6px 10px; border-radius:8px; font-weight:700; display:inline-block;
}
</style>
""", unsafe_allow_html=True)

# =======================
# Encabezado + datos locales
# =======================
st.markdown('<div class="dashboard-panel">', unsafe_allow_html=True)
st.markdown("## 📊 DASHBOARD LOCAL")
st.markdown("**Panel de control y métricas de tu actividad**")
st.markdown(
    f"""
    <div class='badge-soft'>👤 {USER_NAME}</div>
    <div class='badge-soft'>🆔 {USER_ID or '-'}</div>
    <div class='badge-soft'>📧 {USER_EMAIL or '-'}</div>
    <div class='badge-soft'>⭐ Plan: {"PREMIUM" if IS_PREMIUM else "FREE"}</div>
    """,
    unsafe_allow_html=True
)
st.markdown('</div>', unsafe_allow_html=True)

# =======================
# Selector de Vista
# =======================
options = ["Vendedor", "Comprador"]
default_idx = 0 if default_role == "VENDEDOR" else 1

can_view_seller = any(r in roles for r in ["VENDEDOR", "SELLER", "ADMIN", "2"])
can_view_buyer  = any(r in roles for r in ["COMPRADOR", "BUYER", "1"])

if can_view_seller and can_view_buyer:
    st.markdown('<div class="dashboard-panel">', unsafe_allow_html=True)
    view_mode = st.radio(
        "👤 Ver como:",
        options,
        horizontal=True,
        index=default_idx,
        key="view_mode"
    )
    st.markdown('</div>', unsafe_allow_html=True)
elif can_view_seller:
    view_mode = "Vendedor"
elif can_view_buyer:
    view_mode = "Comprador"
else:
    st.error("No tenés rol válido para ver este dashboard.")
    st.stop()

role_for_backend = "VENDEDOR" if view_mode == "Vendedor" else "COMPRADOR"

# =======================
# Premium gate
# =======================
if not IS_PREMIUM:
    st.markdown('<div class="dashboard-panel">', unsafe_allow_html=True)
    st.markdown("### 🔒 Reportes avanzados Premium")
    st.markdown(
        """
        Este panel completo está disponible con **Premium**.  
        Beneficios:
        - 🔥 +20% visibilidad en Home  
        - 🛍️ Publicación de hasta 200 productos  
        - 📊 Reportes avanzados + exportaciones  
        - ⚡ Soporte prioritario  
        """
    )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="dashboard-panel">', unsafe_allow_html=True)
    st.markdown("### 📌 Resumen básico")

    if view_mode == "Vendedor":
        st.metric("🧾 Ventas (básico)", "Disponible en Premium")
        st.metric("📦 Pedidos (básico)", "Disponible en Premium")
    else:
        st.metric("🛍️ Compras (básico)", "Disponible en Premium")
        st.metric("📦 Pedidos (básico)", "Disponible en Premium")

    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# =======================
# Traer datos backend (premium)
# =======================
data = api_get_local_dashboard(role_for_backend) or {}
kpis = data.get("kpis") or {}
series = data.get("series") or {}
lists = data.get("lists") or {}

# =======================
# KPIs Principales
# =======================
st.markdown('<div class="dashboard-panel">', unsafe_allow_html=True)
st.markdown("### 📈 MÉTRICAS PRINCIPALES")

if view_mode == "Vendedor":
    ventas_totales = safe_float(kpis.get("total_sales"))
    pedidos = int(safe_float(kpis.get("orders_count")))
    rating = safe_float(kpis.get("rating"))
    devoluciones = int(safe_float(kpis.get("returns")))

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("💰 Ventas Totales", money(ventas_totales))
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("📦 Pedidos", f"{pedidos}")
        st.markdown('</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("⭐ Valoración", f"{rating:.1f}/10")
        st.markdown('</div>', unsafe_allow_html=True)
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("🔄 Devoluciones", f"{devoluciones}")
        st.markdown('</div>', unsafe_allow_html=True)

else:
    total_spent = safe_float(kpis.get("total_spent"))
    orders = int(safe_float(kpis.get("orders_count")))

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("🛍️ Compras Totales", money(total_spent))
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("📦 Pedidos", f"{orders}")
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# =======================
# Gráficos
# =======================
st.markdown('<div class="dashboard-panel">', unsafe_allow_html=True)
st.markdown("### 📊 EVOLUCIÓN TEMPORAL")

col_chart1, col_chart2 = st.columns(2)

if view_mode == "Vendedor":
    with col_chart1:
        st.markdown("**📈 Ventas Mensuales**")
        ventas_mensuales = series.get("monthly_sales", [])
        if ventas_mensuales:
            dfv = pd.DataFrame(ventas_mensuales)
            if {"period","total"} <= set(dfv.columns):
                st.line_chart(dfv.set_index("period")["total"], height=260)
            else:
                st.info("Formato inválido monthly_sales.")
        else:
            st.info("Sin datos mensuales.")

    with col_chart2:
        st.markdown("**📦 Pedidos por Categoría**")
        pedidos_cat = series.get("orders_by_category", [])
        if pedidos_cat:
            dfc = pd.DataFrame(pedidos_cat)
            if {"category","orders"} <= set(dfc.columns):
                st.bar_chart(dfc.set_index("category")["orders"], height=260)
            else:
                st.info("Formato inválido orders_by_category.")
        else:
            st.info("Sin datos por categoría.")

else:
    with col_chart1:
        st.markdown("**🛍️ Compras Mensuales**")
        compras_m = series.get("monthly_purchases", [])
        if compras_m:
            dfc = pd.DataFrame(compras_m)
            if {"period","amount"} <= set(dfc.columns):
                st.line_chart(dfc.set_index("period")["amount"], height=260)
            else:
                st.info("Formato inválido monthly_purchases.")
        else:
            st.info("Sin datos de compras mensuales.")

    with col_chart2:
        st.markdown("**🏪 Marcas favoritas**")
        top_brands = lists.get("top_brands", [])
        if top_brands:
            dfb = pd.DataFrame(top_brands)
            if {"name","orders"} <= set(dfb.columns):
                st.bar_chart(dfb.set_index("name")["orders"], height=260)
            else:
                st.info("Formato inválido top_brands.")
        else:
            st.info("Sin datos de marcas favoritas.")

st.markdown('</div>', unsafe_allow_html=True)

# =======================
# Top 3
# =======================
st.markdown('<div class="dashboard-panel">', unsafe_allow_html=True)

medals = ["🥇", "🥈", "🥉"]

if view_mode == "Vendedor":
    st.markdown("### 🏆 TOP PRODUCTOS MÁS VENDIDOS")
    top_products = lists.get("top_products") or []

    if not top_products:
        st.info("Sin top products.")
    else:
        cols = st.columns(3)
        for idx, p in enumerate(top_products[:3]):
            with cols[idx]:
                st.markdown(f"**{medals[idx]} {p.get('name','Producto')}**")
                st.markdown(f"💰 {money(p.get('price',0))} c/u")
                st.markdown(f"📦 {int(safe_float(p.get('sold',0)))} vendidos")
                st.markdown(f"⭐ {safe_float(p.get('rating')):.1f}/10")
else:
    st.markdown("### 🏆 TUS MARCAS FAVORITAS")
    top_brands = lists.get("top_brands") or []

    if not top_brands:
        st.info("Sin top brands.")
    else:
        cols = st.columns(3)
        for idx, b in enumerate(top_brands[:3]):
            with cols[idx]:
                st.markdown(f"**{medals[idx]} {b.get('name','Marca')}**")
                st.markdown(f"🛍️ {int(safe_float(b.get('orders',0)))} compras")
                st.markdown(f"💰 {money(b.get('spent',0))} gastado")
                st.markdown(f"⭐ {safe_float(b.get('rating')):.1f}/10")

st.markdown('</div>', unsafe_allow_html=True)

# =======================
# Actividad Reciente
# =======================
st.markdown('<div class="dashboard-panel">', unsafe_allow_html=True)
st.markdown("### 📋 ACTIVIDAD RECIENTE")

if view_mode == "Vendedor":
    recent_orders = lists.get("recent_orders") or []
    st.markdown("**Últimos Pedidos:**")
    if not recent_orders:
        st.info("Sin pedidos recientes.")
    else:
        for o in recent_orders:
            st.markdown(
                f"- **Pedido #{o.get('id','')}** - {o.get('product_name','')} "
                f"- {money(o.get('total',0))}"
            )
else:
    recent_purchases = lists.get("recent_purchases") or []
    st.markdown("**Tus Últimas Compras:**")
    if not recent_purchases:
        st.info("Sin compras recientes.")
    else:
        for c in recent_purchases:
            st.markdown(
                f"- **Compra #{c.get('id','')}** - {c.get('product_name','')} "
                f"- {money(c.get('total',0))}"
            )

st.markdown('</div>', unsafe_allow_html=True)
