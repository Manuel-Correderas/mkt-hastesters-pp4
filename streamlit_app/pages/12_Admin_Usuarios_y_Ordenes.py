# streamlit_app/pages/12_Admin_Usuarios_y_Ordenes.py
import streamlit as st
import requests
from datetime import date, timedelta

from auth_helpers import get_backend_url, auth_headers, require_admin

st.set_page_config(page_title="Panel Admin - Ecom MKT Lab", layout="wide")

BACKEND_URL = get_backend_url()
PAGE_NS = "admin_v1"
def K(s: str) -> str:
    return f"{PAGE_NS}:{s}"



# ============================
# Helpers de auth
# ============================
def auth_headers():
    tok = st.session_state.get("auth_token")
    return {"Authorization": f"Bearer {tok}"} if tok else {}


def require_admin():
    if "auth_token" not in st.session_state:
        st.warning("Tenés que iniciar sesión como administrador.")
        st.page_link("pages/0_Login.py", label="Ir a Login", icon="🔐")
        st.stop()

    roles = st.session_state.get("roles", [])
    if "ADMIN" not in roles:
        st.error("No tenés permisos para acceder a este panel.")
        st.stop()


# ============================
# Estilos
# ============================
st.markdown("""
<style>
.stApp { background:#f3f5fb; }

.admin-header {
  display:flex; align-items:center; justify-content:space-between;
  margin-bottom:12px;
}
.admin-title {
  font-size:1.4rem; font-weight:900; color:#0b3a91;
}
.admin-badge {
  background:#0b3a91; color:#fff; padding:4px 10px;
  border-radius:999px; font-size:0.8rem; font-weight:700;
}
.card {
  background:#ffffff;
  border-radius:14px;
  padding:14px 16px;
  box-shadow:0 8px 20px rgba(0,0,0,.07);
  margin-bottom:16px;
}
.card-title {
  font-weight:800;
  font-size:1rem;
  margin-bottom:4px;
  color:#1b2a4b;
}
.small-label {
  font-size:0.75rem; text-transform:uppercase;
  letter-spacing:.04em; color:#777;
}
.chip {
  display:inline-block;
  padding:2px 8px;
  border-radius:999px;
  font-size:0.75rem;
  font-weight:700;
}
.chip.ACTIVO { background:#e8f6e8; color:#1e7e34; }
.chip.REVISION { background:#fff8e5; color:#b58102; }
.chip.BLOQUEADO { background:#fdecea; color:#c0392b; }
.chip.DNI {
  background:#222; color:#fff;
}
.table-header {
  font-size:0.8rem;
  text-transform:uppercase;
  letter-spacing:.05em;
  color:#555;
  border-bottom:1px solid #e1e1e1;
  padding-bottom:4px;
  margin-bottom:4px;
}
</style>
""", unsafe_allow_html=True)


require_admin()

# ============================
# Header
# ============================
st.markdown(
    """
<div class="admin-header">
  <div class="admin-title">🛡️ Panel de Administración</div>
  <div class="admin-badge">Modo Supervisor</div>
</div>
""",
    unsafe_allow_html=True,
)

tab_users, tab_orders = st.tabs(["👤 Usuarios", "🧾 Órdenes"])


# ============================
#  TAB: USUARIOS
# ============================
with tab_users:
    st.markdown("### 👤 Movimientos de usuarios")

    col_f1, col_f2, col_f3 = st.columns([1, 1, 1.5])
    with col_f1:
        estado_filter = st.selectbox(
            "Estado",
            options=["TODOS", "ACTIVO", "REVISION", "BLOQUEADO"],
            index=0,
        )
    with col_f2:
        solo_nuevos = st.checkbox("Solo nuevos últimos días", value=True)
    with col_f3:
        dias = st.slider("Días (para nuevos)", min_value=1, max_value=30, value=7)

    params = {}
    if estado_filter != "TODOS":
        params["estado"] = estado_filter
    if solo_nuevos:
        params["solo_nuevos"] = "true"
        params["dias"] = dias

    try:
        resp = requests.get(
            f"{BACKEND_URL}/admin/users",
            params=params,
            headers=auth_headers(),
            timeout=20,
        )
        if resp.status_code != 200:
            st.error(f"Error al cargar usuarios (HTTP {resp.status_code}): {resp.text}")
        else:
            users = resp.json()
    except Exception as e:
        st.error(f"Error de conexión al backend: {e}")
        users = []

    total_users = len(users)
    col_u1, col_u2, col_u3 = st.columns(3)
    with col_u1:
        st.metric("Usuarios listados", total_users)
    with col_u2:
        bloqueados = sum(1 for u in users if u.get("estado") == "BLOQUEADO")
        st.metric("Bloqueados", bloqueados)
    with col_u3:
        dni_block = sum(1 for u in users if u.get("dni_bloqueado"))
        st.metric("DNI bloqueados", dni_block)

    st.markdown("<div class='table-header'>Listado</div>", unsafe_allow_html=True)

    for idx, u in enumerate(users):
        user_id = u["id"]
        nombre = u["nombre"]
        apellido = u["apellido"]
        email = u["email"]
        tipo_doc = u["tipo_doc"]
        nro_doc = u["nro_doc"]
        estado = u.get("estado", "ACTIVO")
        dni_bloqueado = u.get("dni_bloqueado", False)
        creado_en = u.get("creado_en", "")

        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            c1, c2, c3 = st.columns([3, 2, 3])

            with c1:
                st.markdown(
                    f"""
                    <div class="card-title">{apellido}, {nombre}</div>
                    <div class="small-label">{email}</div>
                    <div class="small-label">DOC: {tipo_doc} {nro_doc}</div>
                    <div class="small-label">Creado: {creado_en}</div>
                    """,
                    unsafe_allow_html=True,
                )

            with c2:
                st.markdown(
                    f'<span class="chip {estado}">{estado}</span>',
                    unsafe_allow_html=True,
                )
                if dni_bloqueado:
                    st.markdown(
                        '<span class="chip DNI">DNI BLOQUEADO</span>',
                        unsafe_allow_html=True,
                    )

            with c3:
                st.write("Acciones:")
                col_a1, col_a2, col_a3 = st.columns(3)

                # Cambiar estado
                with col_a1:
                    if st.button("🔍 Revisión", key=K(f"rev_{idx}")):
                        r = requests.patch(
                            f"{BACKEND_URL}/admin/users/{user_id}/estado",
                            json={"estado": "REVISION"},
                            headers=auth_headers(),
                            timeout=15,
                        )
                        if r.status_code == 200:
                            st.success("Usuario puesto en revisión.")
                            st.rerun()
                        else:
                            st.error(f"Error: {r.status_code} - {r.text}")

                with col_a2:
                    if st.button("✅ Activar", key=K(f"act_{idx}")):
                        r = requests.patch(
                            f"{BACKEND_URL}/admin/users/{user_id}/estado",
                            json={"estado": "ACTIVO"},
                            headers=auth_headers(),
                            timeout=15,
                        )
                        if r.status_code == 200:
                            st.success("Usuario activado.")
                            st.rerun()
                        else:
                            st.error(f"Error: {r.status_code} - {r.text}")

                with col_a3:
                    if st.button("⛔ Bloquear", key=K(f"blk_{idx}")):
                        r = requests.patch(
                            f"{BACKEND_URL}/admin/users/{user_id}/estado",
                            json={"estado": "BLOQUEADO"},
                            headers=auth_headers(),
                            timeout=15,
                        )
                        if r.status_code == 200:
                            st.success("Usuario bloqueado.")
                            st.rerun()
                        else:
                            st.error(f"Error: {r.status_code} - {r.text}")

                # Bloqueo de DNI
                st.write("")
                col_d1, col_d2 = st.columns([2, 2])
                with col_d1:
                    label_dni = "🔓 Desbloquear DNI" if dni_bloqueado else "🔒 Bloquear DNI"
                    if st.button(label_dni, key=K(f"dni_{idx}")):
                        nuevo_estado = not dni_bloqueado
                        r = requests.patch(
                            f"{BACKEND_URL}/admin/users/{user_id}/dni-block",
                            json={"dni_bloqueado": nuevo_estado},
                            headers=auth_headers(),
                            timeout=15,
                        )
                        if r.status_code == 200:
                            st.success("Estado de DNI actualizado.")
                            st.rerun()
                        else:
                            st.error(f"Error: {r.status_code} - {r.text}")

            st.markdown("</div>", unsafe_allow_html=True)
            st.write("")
# ============================
#  TAB: ÓRDENES
# ============================
with tab_orders:
    st.markdown("### 🧾 Órdenes y transacciones")

    hoy = date.today()
    col_d1, col_d2, col_d3 = st.columns([1, 1, 1])
    with col_d1:
        from_date = st.date_input("Desde", value=hoy - timedelta(days=7))
    with col_d2:
        to_date = st.date_input("Hasta", value=hoy)
    with col_d3:
        if st.button("🔄 Actualizar", key=K("reload_orders")):
            st.experimental_rerun() if hasattr(st, "experimental_rerun") else st.rerun()

    params_o = {
        "from_date": from_date.isoformat(),
        "to_date": to_date.isoformat(),
    }

    try:
        resp_o = requests.get(
            f"{BACKEND_URL}/admin/orders",
            params=params_o,
            headers=auth_headers(),
            timeout=20,
        )
        if resp_o.status_code != 200:
            st.error(f"Error al cargar órdenes (HTTP {resp_o.status_code}): {resp_o.text}")
            orders = []
        else:
            orders = resp_o.json()
    except Exception as e:
        st.error(f"Error de conexión al backend: {e}")
        orders = []

    total_orders = len(orders)
    total_monto = sum(o.get("total_amount", 0) for o in orders)
    aprobadas = sum(1 for o in orders if o.get("payment_status") == "APROBADO")

    col_o1, col_o2, col_o3 = st.columns(3)
    with col_o1:
        st.metric("Órdenes", total_orders)
    with col_o2:
        st.metric("Total vendido", f"${total_monto:,.0f}".replace(",", "."))
    with col_o3:
        st.metric("Pagos aprobados", aprobadas)

    st.markdown("<div class='table-header'>Listado de órdenes</div>", unsafe_allow_html=True)

    for idx, o in enumerate(orders):
        order_id = o["id"]
        created_at = o.get("created_at", "")
        user_id = o.get("user_id", "")
        user_email = o.get("user_email", "")
        total_amount = o.get("total_amount", 0)
        payment_status = o.get("payment_status", "DESCONOCIDO")
        tx_ref = o.get("tx_ref", "")

        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            c1, c2, c3 = st.columns([3, 2, 2])

            with c1:
                st.markdown(
                    f"""
                    <div class="card-title">Orden #{order_id}</div>
                    <div class="small-label">Fecha: {created_at}</div>
                    <div class="small-label">Usuario ID: {user_id or "-"}<br/>
                    Email: {user_email or "-"}</div>
                    """,
                    unsafe_allow_html=True,
                )

            with c2:
                st.markdown(
                    f"""
                    <div class="small-label">Monto total</div>
                    <div style="font-size:1.1rem; font-weight:800;">${total_amount:,.0f}</div>
                    <div class="small-label">Estado pago: {payment_status}</div>
                    """.replace(",", "."),
                    unsafe_allow_html=True,
                )
                if tx_ref:
                    st.markdown(
                        f'<div class="small-label">Tx ID: {tx_ref}</div>',
                        unsafe_allow_html=True,
                    )

            with c3:
                st.write("Acciones:")

                # En una versión más avanzada, podrías traer detalle de items / revisar sospechas
                if st.button("Ver detalle", key=K(f"detail_{idx}")):
                    st.info("Acá podrías abrir otra página o modal con detalle de la orden (items, dirección, etc.).")

            st.markdown("</div>", unsafe_allow_html=True)
            st.write("")