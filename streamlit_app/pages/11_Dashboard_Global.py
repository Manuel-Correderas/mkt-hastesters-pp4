# streamlit_app/pages/0a_📊_Dashboard_Global.py
import streamlit as st
import pandas as pd
import requests
from datetime import timedelta, date

from auth_helpers import get_backend_url, auth_headers, require_login

st.set_page_config(page_title="Dashboard Global - MKT", layout="wide")
st.title("Dashboard Global")
st.caption("Resumen general de actividad, ventas y rendimiento.")

BACKEND_URL = get_backend_url()

# =======================
# AUTH
# =======================
require_login()  # ✅ faltaba

# =======================
# USER / PREMIUM
# =======================
user_obj = st.session_state.get("user") or st.session_state.get("auth_user") or {}
roles = (
    st.session_state.get("auth_roles")
    or st.session_state.get("roles")
    or user_obj.get("roles")
    or [user_obj.get("role")]
    or []
)
roles = [str(r).upper() for r in roles if r]

def safe_float(x, default=0.0):
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default

def is_premium_user():
    if safe_float(st.session_state.get("premium"), 0) >= 1:
        return True
    if safe_float(user_obj.get("premium"), 0) >= 1:
        return True
    if any("PREMIUM" in r for r in roles):
        return True
    if user_obj.get("is_premium") is True:
        return True
    if str(user_obj.get("plan", "")).lower() == "premium":
        return True
    return False

IS_PREMIUM = is_premium_user()

# =======================
# API
# =======================
def api_get_global_metrics():
    try:
        r = requests.get(
            f"{BACKEND_URL}/analytics/global",
            headers=auth_headers(),
            timeout=10
        )
        if r.status_code == 200:
            return r.json() or {}
        st.warning(f"/analytics/global -> {r.status_code}: {r.text}")
        return {}
    except Exception as e:
        st.warning(f"Error global metrics: {e}")
        return {}

def api_get_orders(from_date: date, to_date: date):
    try:
        params = {"from": from_date.isoformat(), "to": to_date.isoformat()}
        r = requests.get(
            f"{BACKEND_URL}/analytics/orders",
            params=params,
            headers=auth_headers(),
            timeout=15
        )
        if r.status_code == 200:
            return r.json() or []
        st.warning(f"/analytics/orders -> {r.status_code}: {r.text}")
        return []
    except Exception as e:
        st.warning(f"Error pidiendo órdenes: {e}")
        return []

def normalize_orders(df: pd.DataFrame) -> pd.DataFrame:
    """Adapta nombres de columnas comunes del backend a lo que usa el dashboard."""
    if df.empty:
        return df

    rename_map = {
        "created_at": "order_date",
        "date": "order_date",
        "seller": "seller_name",
        "seller_email": "seller_name",
        "product": "product_name",
        "title": "product_name",
        "quantity": "qty",
        "units": "qty",
        "total": "total_paid",
        "amount": "total_paid",
        "paid_total": "total_paid",
        "payment": "payment_method",
        "payment_type": "payment_method",
        "state": "status",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    # columnas mínimas aseguradas
    for col, default in {
        "order_date": pd.NaT,
        "seller_name": "Sin vendedor",
        "product_name": "Sin producto",
        "qty": 1,
        "total_paid": 0,
        "payment_method": "N/D",
        "status": "unknown",
    }.items():
        if col not in df.columns:
            df[col] = default

    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    df["qty"] = pd.to_numeric(df["qty"], errors="coerce").fillna(1)
    df["total_paid"] = pd.to_numeric(df["total_paid"], errors="coerce").fillna(0)
    return df

# =======================
# PREMIUM GATE
# =======================
if not IS_PREMIUM:
    st.info(
        """
        🔒 Este dashboard es parte de **Premium**.

        Beneficios:
        - 🔥 +20% visibilidad en Home  
        - 🛍️ Publicación de hasta 200 productos  
        - 📊 Reportes avanzados + exportaciones  
        - ⚡ Soporte prioritario  
        """
    )
    st.stop()

# =======================
# FILTROS
# =======================
st.sidebar.header("Filtros")
hoy = date.today()
desde = st.sidebar.date_input("Desde", hoy - timedelta(days=30))
hasta = st.sidebar.date_input("Hasta", hoy)

if isinstance(desde, list): desde = desde[0]
if isinstance(hasta, list): hasta = hasta[0]

# =======================
# DATA
# =======================
global_data = api_get_global_metrics()
orders_data = api_get_orders(desde, hasta)

df_orders = pd.DataFrame(orders_data) if orders_data else pd.DataFrame()
df_orders = normalize_orders(df_orders)

# =======================
# KPIs
# =======================
total_users = global_data.get("total_users", 0)
total_products = global_data.get("total_products", 0)

gmv = float(df_orders["total_paid"].sum()) if not df_orders.empty else 0.0
orders_count = len(df_orders)
aov = gmv / orders_count if orders_count else 0.0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Usuarios totales", f"{total_users:,}".replace(",", "."))
c2.metric("Productos publicados", f"{total_products:,}".replace(",", "."))
c3.metric("GMV (ventas cobradas)", f"$ {int(gmv):,}".replace(",", "."))
c4.metric("Ticket medio (AOV)", f"$ {int(aov):,}".replace(",", "."))

st.divider()

# =======================
# EVOLUCIÓN
# =======================
st.subheader("Evolución de ventas")

if not df_orders.empty and df_orders["order_date"].notna().any():
    df_orders["day"] = df_orders["order_date"].dt.floor("D")
    daily = df_orders.groupby("day", as_index=False).agg(
        gmv=("total_paid","sum"),
        orders=("order_date","count")
    )
    st.line_chart(daily.set_index("day")[["gmv","orders"]], height=260)
else:
    st.info("Sin datos en el rango seleccionado.")

# =======================
# RANKINGS
# =======================
colA, colB = st.columns(2)

with colA:
    st.subheader("Top vendedores por GMV")
    if not df_orders.empty:
        df_sellers = df_orders.groupby("seller_name", as_index=False)["total_paid"].sum()
        df_sellers = df_sellers.sort_values("total_paid", ascending=False).head(10)
        st.bar_chart(df_sellers.set_index("seller_name")["total_paid"], height=260)
    else:
        st.info("Sin datos de órdenes.")

with colB:
    st.subheader("Top productos por unidades")
    if not df_orders.empty:
        df_products = df_orders.groupby("product_name", as_index=False)["qty"].sum()
        df_products = df_products.sort_values("qty", ascending=False).head(10)
        st.bar_chart(df_products.set_index("product_name")["qty"], height=260)
    else:
        st.info("Sin datos de órdenes.")

st.divider()

# =======================
# CATÁLOGO Y PAGOS
# =======================
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Catálogo")
    st.write(f"• Sin stock: **{global_data.get('products_out_of_stock', 0)}**")
    st.write(f"• Con imagen: **{global_data.get('products_with_image', 0)}**")
    st.write("• Top categorías:")
    st.write(pd.Series(global_data.get("top_categories", [])))

with col2:
    st.subheader("Métodos de pago")
    if not df_orders.empty:
        st.bar_chart(df_orders["payment_method"].value_counts(), height=260)
    else:
        st.info("Sin datos de pagos.")

with col3:
    st.subheader("Calidad de órdenes")
    if not df_orders.empty:
        fail_rate = (df_orders["status"].astype(str).str.lower() == "failed").mean() * 100
        st.metric("Tasa de fallos de pago", f"{fail_rate:.1f}%")
    else:
        st.info("Sin estados de orden.")

st.caption("Panel Premium conectado al backend — datos reales desde FastAPI.")
