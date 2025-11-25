# streamlit_app/pages/0c_👤_Alta_usuario.py
import requests
import streamlit as st
import base64, json

from auth_helpers import get_backend_url, auth_headers  # ✅ headers para PUT/KYC/DELETE

st.set_page_config(page_title="Alta / Edición de Usuario", layout="centered")

# ------------------- Config -------------------
BACKEND_URL = get_backend_url()

if "last_user_id" not in st.session_state:
    st.session_state["last_user_id"] = None

PAGE_NS = "alta_usuario_v2"
def K(s: str) -> str:
    return f"{PAGE_NS}:{s}"

# ------------------- Estilos -------------------
st.markdown(
    """
<style>
.stApp { background:#FF8C00; }
.panel{
  background: #f79b2f;
  border-radius: 12px;
  padding: 18px;
  box-shadow: 0 8px 18px rgba(0,0,0,.18);
}
.hdr{ font-size:1.25rem; font-weight:800; color:#1f2e5e; margin-bottom:8px; }
.lbl{ font-weight:700; color:#1f2e5e; }
.small{ color:#333; font-size:.9rem; }
.btn-azul{
  background:#0b3a91; color:#fff; border:none; border-radius:8px;
  padding:.65rem 1rem; font-weight:800; width:100%;
}
.btn-rojo{
  background:#b00020; color:#fff; border:none; border-radius:8px;
  padding:.65rem 1rem; font-weight:800; width:100%;
}
.warn{
  background: rgba(255,255,255,.35);
  border-left: 5px solid #b00020;
  padding: 10px 12px;
  border-radius: 8px;
  color:#3a0b0b;
  font-size:.95rem;
}
.btn-marron{
  background:#936037; color:#fff; border:none; border-radius:8px;
  padding:.65rem 1rem; font-weight:800; width:100%;
}
.divisor{ border-top:2px solid rgba(0,0,0,.1); margin:12px 0; }
</style>
""",
    unsafe_allow_html=True
)

# ------------------- Helpers backend -------------------

ROLE_MAP = {
    "COMPRADOR": "COMPRADOR",
    "VENDEDOR":  "VENDEDOR",
}

def _build_payload(
    nombre, apellido, tipo_doc, nro_doc, email, tel,
    palabra_seg, password, acepto,
    dom_env, dom_ent, alias_cbu, wallet, red,
    comprador_ck, vendedor_ck
):
    roles = []
    if comprador_ck:
        roles.append(ROLE_MAP["COMPRADOR"])
    if vendedor_ck:
        roles.append(ROLE_MAP["VENDEDOR"])
    if not roles:
        roles = [ROLE_MAP["COMPRADOR"]]

    domicilio_envio = None
    if dom_env.strip():
        domicilio_envio = {
            "tipo": "ENVIO",
            "calle_y_numero": dom_env.strip(),
            "ciudad": "",
            "provincia": "",
            "pais": "",
            "cp": ""
        }

    domicilio_entrega = None
    if dom_ent.strip():
        domicilio_entrega = {
            "tipo": "ENTREGA",
            "calle_y_numero": dom_ent.strip(),
            "ciudad": "",
            "provincia": "",
            "pais": "",
            "cp": ""
        }

    banking = {"cbu_o_alias": alias_cbu.strip()} if alias_cbu.strip() else None
    wallets = [{"red": red, "address": wallet.strip()}] if wallet.strip() else None

    payload = {
        "nombre": nombre.strip(),
        "apellido": apellido.strip(),
        "tipo_doc": tipo_doc,
        "nro_doc": nro_doc.strip(),
        "email": email.strip(),
        "tel": tel.strip() if tel else None,
        "palabra_seg": palabra_seg.strip() if palabra_seg else None,
        "password": password,
        "acepta_terminos": bool(acepto),
        "domicilio_envio": domicilio_envio,
        "domicilio_entrega": domicilio_entrega,
        "banking": banking,
        "wallets": wallets,

        "roles": roles,
        "role": roles[0],
    }
    return payload


def _post_user(payload):
    return requests.post(f"{BACKEND_URL}/users", json=payload, timeout=20)

def _put_user(user_id, payload):
    return requests.put(
        f"{BACKEND_URL}/users/{user_id}",
        json=payload,
        headers=auth_headers(),
        timeout=20
    )

def _upload_kyc(user_id, kyc_files):
    files = []
    for f in kyc_files:
        mime = getattr(f, "type", None) or "application/octet-stream"
        files.append(("files", (f.name, f.getvalue(), mime)))

    return requests.post(
        f"{BACKEND_URL}/users/{user_id}/kyc",
        files=files,
        headers=auth_headers(),
        timeout=60
    )

def _delete_user(user_id):
    return requests.delete(
        f"{BACKEND_URL}/users/{user_id}",
        headers=auth_headers(),
        timeout=20
    )

def _uid_from_token():
    """Lee el sub del JWT de auth_token."""
    tok = st.session_state.get("auth_token")
    if not tok:
        return None
    try:
        payload_part = tok.split(".")[1]
        payload_part += "=" * (-len(payload_part) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_part).decode("utf-8"))
        return payload.get("sub")
    except Exception:
        return None

def current_uid():
    """ID del usuario actual con fallback robusto."""
    return (
        st.session_state.get("user_id")
        or st.session_state.get("current_user_id")
        or st.session_state.get("last_user_id")
        or _uid_from_token()
    )

# ------------------- Defaults de roles -------------------
pref = st.session_state.get("pref_roles", {})
compr_def = pref.get("comprador", True)
vend_def  = pref.get("vendedor", False)

# ------------------- UI -------------------
col = st.columns([1,2,1])[1]
with col:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="hdr">🧑‍💻 Alta / Edición de Usuario</div>', unsafe_allow_html=True)

    # ----- Datos básicos -----
    c1, c2 = st.columns(2)
    with c1:
        nombre  = st.text_input("Nombre", key=K("nombre"))
        tipo_doc= st.selectbox("Tipo de Documento", ["DNI","LC","LE","CI","Pasaporte"], index=0, key=K("tipo_doc"))
        dom_env = st.text_input("Domicilio de envío", key=K("dom_env"))
        email   = st.text_input("Email", key=K("email"))
        tel     = st.text_input("Teléfono", key=K("tel"))
    with c2:
        apellido= st.text_input("Apellido", key=K("apellido"))
        nro_doc = st.text_input("N° Documento", key=K("nro_doc"))
        dom_ent = st.text_input("Domicilio de entrega", key=K("dom_ent"))
        cuit    = st.text_input("CUIT (solo visual, no se guarda aún)", key=K("cuit"))
        cuil    = st.text_input("CUIL (solo visual, no se guarda aún)", key=K("cuil"))

    st.markdown('<div class="divisor"></div>', unsafe_allow_html=True)

    # ----- Documentación KYC -----
    st.markdown('<span class="lbl">Adjuntar documentación (KYC)</span>', unsafe_allow_html=True)
    kyc_files = st.file_uploader(
        "Subí DNI/CUIT/comprobante (1 o más)",
        type=["png","jpg","jpeg","pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed",
        key=K("kyc")
    )

    st.markdown('<div class="divisor"></div>', unsafe_allow_html=True)

    # ----- Seguridad & Acceso -----
    c3, c4 = st.columns(2)
    with c3:
        palabra_seg = st.text_input("Palabra de seguridad", key=K("palabra"))
        password    = st.text_input("Contraseña", type="password", key=K("password"))
    with c4:
        alias_cbu = st.text_input("CBU/CBU Alias (banco)", key=K("cbu"))
        wallet    = st.text_input("Wallet pública (cripto)", key=K("wallet"))
        red       = st.selectbox("Red", ["BEP20","ERC20","TRC20","Polygon","Arbitrum"], index=0, key=K("red"))

    st.caption(
        "Estos datos bancarios/cripto se usarán para generar QR y recibir pagos. "
        "El usuario es responsable de su validez."
    )

    st.markdown('<div class="divisor"></div>', unsafe_allow_html=True)

    # ----- Roles -----
    st.markdown("**Roles del usuario** (podés marcar uno o ambos):")
    comprador_ck = st.checkbox("COMPRADOR", value=compr_def, key=K("role_compr"))
    vendedor_ck  = st.checkbox("VENDEDOR",  value=vend_def,  key=K("role_vend"))

    st.markdown('<div class="divisor"></div>', unsafe_allow_html=True)

    # ----- Términos -----
    acepto = st.checkbox("Acepto los términos de uso y privacidad", key=K("acepto"))

    st.markdown('<div class="divisor"></div>', unsafe_allow_html=True)

    # ----- Botones -----
    colA, colB, colC = st.columns(3)

    # ========== REGISTRAR ==========
    with colA:
        if st.button("REGISTRAR", use_container_width=True, key=K("btn_reg")):
            if not (nombre and apellido and email and nro_doc and password and acepto):
                st.error("Completá: Nombre, Apellido, Email, Documento, Contraseña y aceptá Términos.")
            else:
                payload = _build_payload(
                    nombre, apellido, tipo_doc, nro_doc, email, tel,
                    palabra_seg, password, acepto,
                    dom_env, dom_ent, alias_cbu, wallet, red,
                    comprador_ck, vendedor_ck
                )

                if ROLE_MAP["COMPRADOR"] in payload["roles"] and not payload["domicilio_entrega"]:
                    st.warning("COMPRADOR requiere domicilio de ENTREGA.")
                elif ROLE_MAP["VENDEDOR"] in payload["roles"] and (payload["banking"] is None or not payload["wallets"]):
                    st.warning("VENDEDOR requiere CBU/Alias y al menos una Wallet.")
                else:
                    try:
                        r = _post_user(payload)
                        if r.status_code == 201:
                            data = r.json() if r.headers.get("content-type","").startswith("application/json") else {}
                            new_id = data.get("id") or data.get("user_id")
                            st.session_state["last_user_id"] = new_id
                            st.success(f"Usuario creado ✅ ID: {new_id}")
                        else:
                            st.error(f"Error {r.status_code}: {r.text}")
                    except Exception as e:
                        st.error(f"Fallo conexión: {e}")

    # ========== ACTUALIZAR ==========
    with colB:
        if st.button("ACTUALIZAR", use_container_width=True, key=K("btn_upd")):
            if "auth_token" not in st.session_state:
                st.warning("Tenés que iniciar sesión para actualizar usuarios.")
                st.page_link("pages/0_Login.py", label="Ir al Login", icon="🔐")
            else:
                uid = current_uid()
                if not uid:
                    st.warning("No hay usuario en sesión. Logueate de nuevo.")
                else:
                    payload = _build_payload(
                        nombre, apellido, tipo_doc, nro_doc, email, tel,
                        palabra_seg, password, acepto,
                        dom_env, dom_ent, alias_cbu, wallet, red,
                        comprador_ck, vendedor_ck
                    )
                    try:
                        r = _put_user(uid, payload)
                        if r.status_code == 200:
                            st.success("Usuario actualizado ✅")
                        else:
                            st.error(f"Error {r.status_code}: {r.text}")
                    except Exception as e:
                        st.error(f"Fallo conexión: {e}")

    # ========== SUBIR KYC ==========
    with colC:
        if st.button("SUBIR KYC", use_container_width=True, key=K("btn_kyc")):
            if "auth_token" not in st.session_state:
                st.warning("Tenés que iniciar sesión para subir KYC.")
                st.page_link("pages/0_Login.py", label="Ir al Login", icon="🔐")
            else:
                uid = current_uid()
                if not uid:
                    st.warning("No hay usuario en sesión. Logueate de nuevo.")
                elif not kyc_files:
                    st.warning("Subí uno o más archivos.")
                else:
                    try:
                        r = _upload_kyc(uid, kyc_files)
                        if r.status_code == 200:
                            st.success("KYC subido ✅")
                        else:
                            st.error(f"Error {r.status_code}: {r.text}")
                    except Exception as e:
                        st.error(f"Fallo conexión: {e}")

    st.markdown('</div>', unsafe_allow_html=True)

# ==========================
# DESACTIVAR CUENTA
# ==========================
st.write("")
st.markdown("### 🗑️ Desactivar mi cuenta")
st.markdown(
    """
    <div class="warn">
    <b>Atención:</b> esta acción desactiva tu cuenta.  
    No podrás iniciar sesión ni aparecer en la plataforma.  
    (Solo podés hacerlo si estás logueado).
    </div>
    """,
    unsafe_allow_html=True
)

confirm_delete = st.checkbox(
    "Confirmo que quiero desactivar mi cuenta",
    key=K("confirm_delete")
)

if st.button(
    "DESACTIVAR MI CUENTA",
    use_container_width=True,
    disabled=not confirm_delete,
    key=K("btn_delete")
):
    if "auth_token" not in st.session_state:
        st.warning("Tenés que iniciar sesión para desactivar tu cuenta.")
        st.page_link("pages/0_Login.py", label="Ir al Login", icon="🔐")
    else:
        uid = current_uid()
        if not uid:
            st.warning("No hay usuario en sesión para desactivar.")
            st.info("Andá a Login y volvé a entrar.")
        else:
            try:
                r = _delete_user(uid)
                if r.status_code in (200, 204):
                    st.success("Cuenta desactivada ✅")

                    for k in list(st.session_state.keys()):
                        del st.session_state[k]

                    st.switch_page("pages/0_Login.py")
                else:
                    st.error(f"Error {r.status_code}: {r.text}")
            except Exception as e:
                st.error(f"Fallo conexión: {e}")

# ---- Ayuda contextual ----
with st.expander("ℹ️ Requisitos por rol"):
    st.write("""
- **COMPRADOR**
  - Datos personales, email y contraseña
  - **Domicilio de entrega** (obligatorio)
  - Aceptar Términos y Privacidad

- **VENDEDOR**
  - Todo lo anterior
  - **CBU/Alias bancario** y **Wallet pública** (obligatorio)
  - Adjuntar documentos **KYC** (DNI/CUIT/comprobante)

- **ADMIN**
  - No se auto-asigna desde esta pantalla. Solo puede asignarse desde JSON/Backend.
""")
