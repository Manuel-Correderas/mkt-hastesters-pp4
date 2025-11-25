# streamlit_app/pages/0_Login.py
import os
import requests
import streamlit as st
from auth_helpers import get_backend_url, set_auth_session  # <-- NUEVO

st.set_page_config(page_title="Login - Ecom MKT Lab", layout="centered")

BACKEND_URL = get_backend_url()
PAGE_NS = "login_v1"
def K(s: str) -> str: return f"{PAGE_NS}:{s}"

# ---------- Estilos ----------
st.markdown("""
<style>
.stApp {background:#FF8C00;}
.login-card{
  background:#fff; border-radius:18px; padding:32px 28px;
  box-shadow:0 8px 22px rgba(0,0,0,.25);
}
.btn{
  background:#0b3a91; color:#fff; border:none; border-radius:8px;
  padding:10px 16px; font-weight:700; width:100%;
}
.logo-box{ 
  background:#fff; border-radius:18px; padding:18px 22px; 
  margin-bottom:20px; text-align:center;
  box-shadow:0 4px 14px rgba(0,0,0,.18);
}
.logo-title{ font-size:1.8rem; font-weight:800; color:#1f2e5e; }
.logo-sub{ font-size:.9rem; color:#666; }
</style>
""", unsafe_allow_html=True)

def do_login(email: str, password: str):
    try:
        r = requests.post(
            f"{BACKEND_URL}/auth/login",
            json={"email": email, "password": password},
            timeout=15
        )
        if r.status_code == 200:
            data = r.json()
            # 🔐 unificamos acá
            set_auth_session(data)
            return True, None
        elif r.status_code == 401:
            return False, "Credenciales inválidas"
        else:
            return False, f"Error {r.status_code}: {r.text}"
    except Exception as e:
        return False, f"No se pudo conectar al backend: {e}"

# ---------- UI ----------
st.write("")
col = st.columns([1,2,1])[1]
with col:
    st.markdown("""
        <div class="logo-box">
            <div class="logo-title">🛒 Ecom MKT Lab</div>
            <div class="logo-sub">Soluciones de Marketing Digital y Comercio Electrónico</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.markdown("### Iniciar sesión")

    email = st.text_input("Email", placeholder="tu@correo.com", key=K("email"))
    password = st.text_input("Contraseña", type="password", placeholder="••••••••", key=K("pwd"))

    st.write("")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("INGRESAR", use_container_width=True, key=K("ingresar")):
            if not email or not password:
                st.error("Completá email y contraseña.")
            else:
                ok, err = do_login(email, password)
                if ok:
                    st.success("Ingreso correcto ✅")
                    st.switch_page("Home.py")
                else:
                    st.error(err or "Error desconocido")

    with c2:
        if st.button("SALIR", use_container_width=True, key=K("salir")):
            st.switch_page("Home.py")

    with c3:
        # Eliminado el botón REGISTRARSE para no depender de 0b
        st.write("")

    st.write("")
    if st.button("He olvidado la contraseña", use_container_width=True, key=K("olvido")):
        st.switch_page("pages/0d_Olvidé_mi_contraseña.py")

    st.markdown('</div>', unsafe_allow_html=True)
