# utils/theme.py
import streamlit as st

BLUE = "#0b3a91"

def paint_base(titulo: str = "", center: bool = False):
    st.set_page_config(page_title=titulo or "Panel", layout="centered")
    st.markdown("""
    <style>
      .ecom-card { background:#fff; border-radius:16px; padding:16px; box-shadow:0 6px 18px rgba(0,0,0,.18); }
      .btn { background:#0b3a91; color:#fff; border:none; border-radius:8px; padding:10px 16px; font-weight:700; }
    </style>
    """, unsafe_allow_html=True)
    if titulo:
        if center:
            st.markdown(f"<h2 style='text-align:center'>{titulo}</h2>", unsafe_allow_html=True)
        else:
            st.header(titulo)

def require_login():
    """Exige usuario en sesión y detiene la página si no existe."""
    if "user" not in st.session_state or st.session_state.user is None:
        st.warning("Debés iniciar sesión para acceder.")
        # Redirigí si querés:
        if st.button("Ir a Login"):
            st.switch_page("pages/0_Login.py")
        st.stop()

def has_role(*roles_permitidos: str) -> bool:
    """Devuelve True si el usuario tiene alguno de los roles permitidos."""
    user = st.session_state.get("user")
    if not user:
        return False
    user_roles = set(user.get("roles", []))
    return any(r in user_roles for r in roles_permitidos)
