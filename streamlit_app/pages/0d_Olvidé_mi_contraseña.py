# streamlit_app/pages/0d_Olvidé_mi_contraseña.py
import requests
import streamlit as st
from auth_helpers import get_backend_url

st.set_page_config(page_title="Olvidé mi contraseña - Ecom MKT Lab", layout="centered")
BACKEND_URL = get_backend_url()

PAGE_NS = "forgot_v1"
def K(s: str) -> str:
    return f"{PAGE_NS}:{s}"

# estilos
st.markdown("""
<style>
.stApp { background:#FF8C00; }
.card{
  background:#fff; border-radius:18px; padding:28px;
  box-shadow:0 8px 22px rgba(0,0,0,.25);
}
.logo-box{
  background:#fff; border-radius:18px; padding:18px 22px;
  margin-bottom:18px; text-align:center;
}
.logo-title{ font-size:1.8rem; font-weight:800; color:#1f2e5e; }
.logo-sub{ font-size:.9rem; color:#666; }
</style>
""", unsafe_allow_html=True)

# estado
st.session_state.setdefault(K("step"), 1)
st.session_state.setdefault(K("email"), "")
st.session_state.setdefault(K("temp_pwd"), "")  # 👈 guardamos temporal

def forgot_start(email, celular, palabra):
    r = requests.post(
        f"{BACKEND_URL}/auth/forgot/start",
        json={"email": email, "celular": celular, "palabra": palabra},
        timeout=15
    )
    if r.status_code == 200:
        data = r.json() if r.headers.get("content-type","").startswith("application/json") else {}
        temp_pwd = data.get("temp_password")  # 👈 viene del backend

        st.session_state[K("email")] = email
        st.session_state[K("temp_pwd")] = temp_pwd or ""
        st.session_state[K("step")] = 2

        if temp_pwd:
            st.success("Contraseña temporal generada ✅")
            st.info(f"Tu contraseña temporal es: **{temp_pwd}** (vence en 15 minutos)")
        else:
            st.success("Si el email existe, se generó una contraseña temporal.")
    else:
        st.error(f"Error {r.status_code}: {r.text}")

def forgot_finish(email, code, new_password):
    r = requests.post(
        f"{BACKEND_URL}/auth/forgot/finish",
        json={"email": email, "code": code, "new_password": new_password},
        timeout=15
    )
    if r.status_code == 200:
        st.success("Contraseña actualizada. Ahora podés iniciar sesión.")
        if st.button("Ir al Login", use_container_width=True, key=K("to_login")):
            st.switch_page("pages/0_Login.py")
    else:
        st.error(f"Error {r.status_code}: {r.text}")

# UI
col = st.columns([1, 2, 1])[1]
with col:
    st.markdown("""
    <div class="logo-box">
        <div class="logo-title">🛒 Ecom MKT Lab</div>
        <div class="logo-sub">Soluciones de Marketing Digital y Comercio Electrónico</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🔑 Olvidé mi contraseña")

    step = st.session_state[K("step")]

    if step == 1:
        with st.form(K("form_start"), clear_on_submit=False):
            email = st.text_input("Email registrado", key=K("email_input"))
            celular = st.text_input("Celular/Móvil (opcional)", key=K("cel"))
            palabra = st.text_input("Palabra de seguridad (opcional)", type="password", key=K("pal"))
            enviar = st.form_submit_button("ENVIAR")

        if enviar:
            email_norm = (email or "").strip().lower()
            if not email_norm:
                st.error("Ingresá tu email registrado.")
            else:
                try:
                    forgot_start(email_norm, celular, palabra)
                except Exception as e:
                    st.error(f"No se pudo conectar al backend: {e}")

    elif step == 2:
        st.caption(f"Email: {st.session_state[K('email')]}")
        # si por alguna razón querés mostrarla de nuevo:
        if st.session_state[K("temp_pwd")]:
            st.info(f"Temporal: **{st.session_state[K('temp_pwd')]}**")

        with st.form(K("form_finish"), clear_on_submit=False):
            code = st.text_input(
                "Contraseña temporal",
                value=st.session_state[K("temp_pwd")],  # 👈 prellenamos
                key=K("code")
            )
            new_password = st.text_input("Nueva contraseña", type="password", key=K("newpwd"))
            confirmar = st.form_submit_button("CONFIRMAR")

        if confirmar:
            if not code or not new_password:
                st.error("Ingresá la contraseña temporal y la nueva contraseña.")
            elif len(new_password) < 6:
                st.error("La nueva contraseña debe tener al menos 6 caracteres.")
            else:
                try:
                    forgot_finish(st.session_state[K("email")], code, new_password)
                except Exception as e:
                    st.error(f"No se pudo conectar al backend: {e}")

    colA, colB = st.columns(2)
    if colA.button("Volver al Login", key=K("back_login"), use_container_width=True):
        st.switch_page("pages/0_Login.py")
    if colB.button("Cancelar", key=K("cancel"), use_container_width=True):
        st.session_state[K("step")] = 1
        st.session_state[K("email")] = ""
        st.session_state[K("temp_pwd")] = ""

    st.markdown('</div>', unsafe_allow_html=True)

with st.expander("ℹ️ Ayuda y seguridad"):
    st.markdown("""
- Por seguridad, no confirmamos si un email existe o no.
- La **contraseña temporal** expira en **15 minutos**.
""")
