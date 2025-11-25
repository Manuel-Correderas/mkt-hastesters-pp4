import streamlit as st
import requests

from io import BytesIO

from auth_helpers import get_backend_url, require_login, auth_headers

st.set_page_config(page_title="Pago Premium", layout="centered")
require_login()

BACKEND_URL = get_backend_url()

AMOUNT_USDT = 20
NETWORK = "Ethereum (ERC-20)"
ADDRESS = "0xdbf46c952b8026f0806aabfea09ab35a3f715d5d"

st.title("💎 Checkout Premium")
st.caption("Pago único para activar Premium en toda tu cuenta.")

# ---------------------------
# Mostrar datos del user logueado
# ---------------------------
user_obj = st.session_state.get("user") or st.session_state.get("auth_user") or {}
st.info(
    f"**Usuario:** {user_obj.get('nombre','')} {user_obj.get('apellido','')}  \n"
    f"**Email:** {user_obj.get('email','')}  \n"
    f"**User ID:** {user_obj.get('id','')}"
)

st.markdown("---")

# ---------------------------
# Instrucciones de pago
# ---------------------------
st.subheader("📌 Instrucciones")
st.markdown(
    f"""
**Monto:** `{AMOUNT_USDT} USDT`  
**Red:** `{NETWORK}`  
**Dirección:**  
`{ADDRESS}`  

👉 Enviá exactamente **20 USDT** por ERC-20 a esa dirección.
"""
)


# ---------------------------
# Cargar hash
# ---------------------------
st.subheader("✅ Confirmar pago")

tx_hash = st.text_input(
    "Pegá acá el hash de la transacción (0x...)",
    placeholder="0x...............................................................",
)

if st.button("Ya pagué — Activar Premium", type="primary", disabled=not tx_hash):
    payload = {
        "tx_hash": tx_hash.strip(),
        "network": "ethereum",
        "amount": AMOUNT_USDT,
    }
    try:
        r = requests.post(
            f"{BACKEND_URL}/premium/confirm",
            json=payload,
            headers=auth_headers(),
            timeout=10
        )
        if r.status_code == 200:
            st.success("🎉 Pago confirmado. Tu cuenta ya es Premium.")
            # refrescar estado local (opcional)
            st.session_state["premium_active"] = True
        else:
            st.error(f"No se pudo confirmar: {r.status_code} — {r.text}")
    except Exception as e:
        st.error(f"Error de conexión: {e}")

st.markdown("---")
st.caption("Una vez activado Premium, aplica a todos tus roles.")
