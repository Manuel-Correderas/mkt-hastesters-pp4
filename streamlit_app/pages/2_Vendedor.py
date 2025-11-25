# streamlit_app/pages/2_Vendedor.py
import streamlit as st
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime

# ✅ SIEMPRE primero
st.set_page_config(page_title="Panel del Vendedor", page_icon="🏪", layout="centered")

from auth_helpers import get_backend_url, auth_headers, require_login


BACKEND_URL = get_backend_url()
PAGE_NS = "seller_panel_v1"
def K(s: str) -> str:
    return f"{PAGE_NS}:{s}"


# =====================================================
# 🔐 LOGIN + ROLES
# =====================================================
require_login()

roles = (
    st.session_state.get("auth_roles")
    or st.session_state.get("roles")
    or (st.session_state.get("user") or {}).get("roles")
    or [(st.session_state.get("user") or {}).get("role")]
    or []
)
roles = [str(r).upper() for r in roles if r]

if not any(r in roles for r in ["VENDEDOR", "SELLER", "ADMIN"]):
    st.warning("⚠️ No tenés permiso para acceder a este panel. Solo vendedores.")
    st.page_link("pages/0_Login.py", label="Ir a Login", icon="🔐")
    st.stop()

SELLER_ID = (
    st.session_state.get("auth_user_id")
    or st.session_state.get("user_id")
    or (st.session_state.get("user") or {}).get("user_id")
)

SELLER_NAME = (
    st.session_state.get("auth_user_name")
    or st.session_state.get("user_name")
    or (st.session_state.get("user") or {}).get("nombre")
    or (st.session_state.get("user") or {}).get("email")
    or "Vendedor"
)


# =====================================================
# 🎨 ESTILOS (simple premium)
# =====================================================
st.markdown("""
<style>
.stApp { background:#ff8c00; }
.panel-wrap{ max-width:520px; margin:0 auto; }
.logo-box{
  background:#fff;
  border-radius:18px;
  padding:14px;
  box-shadow:0 10px 20px rgba(0,0,0,.15);
  margin:10px 0 16px 0;
  text-align:center;
}
.btn-big .stButton>button{
  width:100%; border-radius:12px; padding:14px 12px;
  font-weight:900; font-size:1.05rem; border:none;
  background:#0b3a91; color:#fff;
  box-shadow:0 6px 14px rgba(0,0,0,.18);
}
.kpi-row{
  display:flex; gap:8px; margin:6px 0 10px 0;
}
.kpi{
  flex:1; background:#fff; border-radius:12px; padding:10px;
  text-align:center; box-shadow:0 6px 14px rgba(0,0,0,.12);
}
.kpi .v{ font-size:1.4rem; font-weight:900; color:#0b3a91; }
.kpi .l{ font-size:.78rem; font-weight:800; color:#444; text-transform:uppercase; }
.section{
  background:#fff; border-radius:12px; padding:12px 14px;
  box-shadow:0 6px 14px rgba(0,0,0,.12); margin-top:10px;
}
.badge{
  display:inline-block; padding:3px 8px; border-radius:999px;
  font-size:.75rem; font-weight:900;
}
.badge.PENDIENTE{ background:#fff3cd; color:#8a6d3b; }
.badge.PAGO_CONFIRMADO_COMPRADOR{ background:#cfe2ff; color:#084298; }
.badge.PAGO_CONFIRMADO_VENDEDOR{ background:#d1e7dd; color:#0f5132; }
.badge.DESPACHADO{ background:#e8f7ff; color:#0b5ed7; }
</style>
""", unsafe_allow_html=True)


# =====================================================
# 🔧 Helpers de datos
# =====================================================
def normalize_list(data):
    if isinstance(data, dict):
        return data.get("items") or data.get("data") or []
    return data if isinstance(data, list) else []

def group_flat_order_items(rows):
    """
    Convierte filas planas de order_items -> órdenes con items[]
    """
    grouped = {}
    for r in rows:
        oid = r.get("order_id") or r.get("id")
        if not oid:
            continue

        grouped.setdefault(oid, {
            "id": oid,
            "created_at": r.get("created_at") or r.get("fecha") or "",
            "user_name": r.get("user_name") or r.get("buyer_name") or "",
            "payment_status": r.get("payment_status") or r.get("estado_pago") or "PENDIENTE",
            "status": r.get("status") or "PENDIENTE",
            "items": []
        })

        item = {
            "qty": r.get("qty") or r.get("quantity") or r.get("cantidad") or 1,
            "price": r.get("price") or r.get("unit_price") or r.get("unitPrice") or 0,
            "seller_id": r.get("seller_id") or r.get("sellerId"),
            "seller": r.get("seller") or r.get("seller_name"),
            "product": {
                "id": r.get("product_id") or r.get("producto_id"),
                "name": r.get("product_name") or r.get("name"),
                "seller_id": r.get("seller_id") or r.get("sellerId"),
                "seller": r.get("seller") or r.get("seller_name"),
            }
        }
        grouped[oid]["items"].append(item)

    return list(grouped.values())

def get_seller_products():
    # tus productos por seller_id
    try:
        r = requests.get(
            f"{BACKEND_URL}/products",
            params={"seller_id": SELLER_ID, "limit": 200},
            headers=auth_headers(),
            timeout=12
        )
        if r.status_code == 200:
            return normalize_list(r.json())
    except Exception:
        pass
    return []

def get_seller_orders():
    """
    Intenta:
      1) /orders?seller_id=SELLER_ID  (si backend soporta)
      2) /orders (global) y filtramos por items.seller_id o seller (nombre)
      3) /order_items (si backend expone) y agrupamos
    """
    # 1) directo con seller_id
    try:
        r = requests.get(
            f"{BACKEND_URL}/orders",
            params={"seller_id": SELLER_ID},
            headers=auth_headers(),
            timeout=12
        )
        if r.status_code == 200:
            data = normalize_list(r.json())
            if data:
                return data
    except Exception:
        pass

    # 2) global y filtro por items
    try:
        r = requests.get(f"{BACKEND_URL}/orders", headers=auth_headers(), timeout=12)
        if r.status_code == 200:
            data = normalize_list(r.json())
            # si vienen planas, agrupamos
            if data and "items" not in data[0] and ("order_id" in data[0] or "product_id" in data[0]):
                data = group_flat_order_items(data)

            filtered = []
            for o in data:
                items = o.get("items") or []
                for it in items:
                    prod = it.get("product") or {}
                    sid = it.get("seller_id") or prod.get("seller_id") or it.get("sellerId")
                    sname = it.get("seller") or prod.get("seller") or it.get("seller_name")

                    if (sid and str(sid) == str(SELLER_ID)) or (
                        sname and str(sname).strip().upper() == str(SELLER_NAME).strip().upper()
                    ):
                        filtered.append(o)
                        break
            if filtered:
                return filtered
    except Exception:
        pass

    # 3) order_items plano
    for endpoint in ["/order_items", "/order-items", "/orders/items"]:
        try:
            r = requests.get(f"{BACKEND_URL}{endpoint}", headers=auth_headers(), timeout=12)
            if r.status_code == 200:
                rows = normalize_list(r.json())
                if rows:
                    orders = group_flat_order_items(rows)
                    # filtramos por seller
                    filtered = []
                    for o in orders:
                        for it in o.get("items", []):
                            sid = it.get("seller_id")
                            sname = it.get("seller") or (it.get("product") or {}).get("seller")
                            if (sid and str(sid) == str(SELLER_ID)) or (
                                sname and str(sname).strip().upper() == str(SELLER_NAME).strip().upper()
                            ):
                                filtered.append(o)
                                break
                    return filtered
        except Exception:
            continue

    return []

def calculate_seller_metrics(products, orders):
    total_products = len(products)
    active_products = len([p for p in products if p.get("is_active", True)])
    total_sales = len(orders)
    total_revenue = 0.0

    for o in orders:
        # si la orden trae total_amount lo usamos, si no lo calculamos por items
        if o.get("total_amount") is not None or o.get("total") is not None:
            total_revenue += float(o.get("total_amount", o.get("total", 0)) or 0)
        else:
            s = 0.0
            for it in o.get("items", []):
                qty = float(it.get("qty", 1) or 1)
                price = float(it.get("price", 0) or 0)
                s += qty * price
            total_revenue += s

    return {
        "total_products": total_products,
        "active_products": active_products,
        "total_sales": total_sales,
        "total_revenue": total_revenue
    }

def safe_patch(urls: list[str], payload: dict | None = None):
    for u in urls:
        try:
            r = requests.patch(u, json=payload or {}, headers=auth_headers(), timeout=12)
            if r.status_code in (200, 204):
                return True, r.text
        except Exception:
            continue
    return False, "No existe endpoint PATCH compatible."


# =====================================================
# 🧾 DATA
# =====================================================
products = get_seller_products()
orders = get_seller_orders()
metrics = calculate_seller_metrics(products, orders)


# =====================================================
# 🟧 UI SIMPLE (como tu foto)
# =====================================================
st.markdown('<div class="panel-wrap">', unsafe_allow_html=True)

# Logo
st.markdown("""
<div class="logo-box">
  <h2 style="margin:0;color:#0b3a91;">Ecom MKT Lab</h2>
  <div style="font-weight:700;color:#333;">Soluciones de Marketing Digital y Comercio Electrónico</div>
  <div style="font-size:.9rem;color:#666;margin-top:6px;">👤 {seller}</div>
</div>
""".format(seller=SELLER_NAME), unsafe_allow_html=True)

# KPIs
st.markdown(f"""
<div class="kpi-row">
  <div class="kpi"><div class="l">Productos</div><div class="v">{metrics['total_products']}</div><div style="font-size:.8rem;">{metrics['active_products']} activos</div></div>
  <div class="kpi"><div class="l">Ventas</div><div class="v">{metrics['total_sales']}</div><div style="font-size:.8rem;">órdenes</div></div>
  <div class="kpi"><div class="l">Ingresos</div><div class="v">$ {metrics['total_revenue']:,.0f}</div><div style="font-size:.8rem;">total</div></div>
</div>
""", unsafe_allow_html=True)

# Botonera grande
st.markdown('<div class="btn-big">', unsafe_allow_html=True)

if st.button("VER MIS PRODUCTOS", key=K("ver_prod")):
    st.switch_page("pages/7_Mis_Productos.py")


if st.button("COMENTARIOS", key=K("comentarios")):
    st.switch_page("pages/5b_Ver_Comentarios.py")

if st.button("HISTORIAL DE VENTAS", key=K("ventas")):
    st.switch_page("pages/9_Historial_Ventas.py")

if st.button("FINANCIAS Y RENTABILIDAD", key=K("finanzas")):
    st.switch_page("pages/8_Finanzas_Rentab.py")


view = st.session_state.get("seller_view", "ventas")


# =====================================================
# 📌 SECCIONES (simples)
# =====================================================
if view == "ventas":
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.subheader("💰 Historial de Ventas")

    if not orders:
        st.info("Aún no tenés ventas registradas.")
    else:
        # a dataframe fácil
        rows = []
        for o in orders:
            oid = o.get("id") or o.get("order_id")
            created = o.get("created_at") or ""
            pay = o.get("payment_status") or "PENDIENTE"
            status = o.get("status") or "PENDIENTE"

            # total fallback
            total = o.get("total_amount") or o.get("total")
            if total is None:
                total = sum(
                    float(it.get("qty",1) or 1) * float(it.get("price",0) or 0)
                    for it in o.get("items", [])
                )

            rows.append({
                "orden_id": oid,
                "fecha": created[:19],
                "estado_pago": pay,
                "estado_envio": status,
                "total": float(total or 0)
            })

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown('</div>', unsafe_allow_html=True)


if view == "finanzas":
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.subheader("📊 Finanzas y rentabilidad")

    st.write(f"• Ingresos totales: **$ {metrics['total_revenue']:,.0f}**")
    st.write(f"• Órdenes totales: **{metrics['total_sales']}**")
    st.write(f"• Productos cargados: **{metrics['total_products']}**")

    st.caption("Más KPIs después (margen, tasa de conversión, top productos, etc.).")
    st.markdown('</div>', unsafe_allow_html=True)


# =====================================================
# ✅ Confirmaciones de pago (siempre visible abajo)
# =====================================================
st.markdown('<div class="section">', unsafe_allow_html=True)
st.subheader("✅ Confirmaciones de Pago")

if not orders:
    st.info("No hay órdenes para confirmar.")
else:
    def get_pay_status(o):
        return (
            o.get("payment_status")
            or o.get("pay_status")
            or o.get("estado_pago")
            or "PENDIENTE"
        )

    pendientes = [o for o in orders if get_pay_status(o) in ["PAGO_CONFIRMADO_COMPRADOR", "PENDIENTE_VENDEDOR", "PENDIENTE"]]

    if not pendientes:
        st.success("No tenés pagos pendientes.")
    else:
        for i, o in enumerate(pendientes):
            order_id = o.get("id") or o.get("order_id")
            created_at = (o.get("created_at") or "")[:19]
            pay_status = get_pay_status(o)

            # primer producto del pedido
            items = o.get("items") or []
            first = items[0] if items else {}
            prod = first.get("product") or first
            prod_name = prod.get("name") or first.get("product_name") or "Producto"
            qty = first.get("qty") or first.get("quantity") or 1
            price = first.get("price") or first.get("unit_price") or 0

            st.markdown(f"**Orden #{order_id}** • {created_at}<br/>🛍️ {prod_name} (x{qty}) — $ {float(price):,.0f}", unsafe_allow_html=True)
            st.markdown(f"<span class='badge {pay_status}'>{pay_status}</span>", unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                if st.button("Confirmar pago", key=K(f"confirm_{i}"), use_container_width=True):
                    ok, msg = safe_patch([
                        f"{BACKEND_URL}/seller/orders/{order_id}/confirm-payment",
                        f"{BACKEND_URL}/orders/{order_id}/seller-confirm-payment",
                        f"{BACKEND_URL}/orders/{order_id}/confirm-payment-seller",
                        f"{BACKEND_URL}/orders/{order_id}/payment/confirm-seller",
                    ], payload={"payment_status": "PAGO_CONFIRMADO_VENDEDOR"})
                    if ok:
                        st.success("Pago confirmado.")
                        st.rerun()
                    else:
                        st.warning(msg)

            with c2:
                if st.button("Marcar despachado", key=K(f"ship_{i}"), use_container_width=True):
                    ok, msg = safe_patch([
                        f"{BACKEND_URL}/seller/orders/{order_id}/ship",
                        f"{BACKEND_URL}/orders/{order_id}/ship",
                        f"{BACKEND_URL}/orders/{order_id}/status",
                    ], payload={"status": "DESPACHADO"})
                    if ok:
                        st.success("Orden despachada.")
                        st.rerun()
                    else:
                        st.warning(msg)

            st.markdown("---")

st.markdown('</div>', unsafe_allow_html=True)


# =====================================================
# 🚪 Logout
# =====================================================
st.markdown("---")
if st.button("🚪 Cerrar sesión", key=K("logout"), use_container_width=True):
    for k in [
        "auth_token", "auth_user_id", "auth_email", "auth_roles",
        "roles", "is_authenticated", "user", "user_id", "user_name",
        "auth_user_name", "seller_view"
    ]:
        st.session_state.pop(k, None)
    st.success("Sesión cerrada correctamente.")
    st.switch_page("pages/0_Login.py")

