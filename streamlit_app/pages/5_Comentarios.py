# streamlit_app/pages/5_Comentarios.py
import json
import requests
import pandas as pd
from datetime import datetime
from pathlib import Path
import streamlit as st

from auth_helpers import get_backend_url, auth_headers, require_login

st.set_page_config(page_title="Comentarios y Valoración", layout="centered")

# ----------------- Config -----------------
BACKEND_URL = get_backend_url()
DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "comments.csv"
DATA_PATH.parent.mkdir(parents=True, exist_ok=True)

qp = st.query_params
PRODUCT_ID = str(qp.get("id", "1"))

# ----------------- Acceso -----------------
require_login()

roles = st.session_state.get("auth_roles") or st.session_state.get("roles") or []
roles = [str(r).upper() for r in roles]
if "COMPRADOR" not in roles and "ADMIN" not in roles:
    st.warning("⚠️ No tenés permiso para comentar productos.")
    st.stop()

user_name = st.session_state.get("auth_user_name") or st.session_state.get("user_name") or "Anónimo"

def safe_switch_page(page_filename: str):
    try:
        st.switch_page(f"pages/{page_filename}")
    except Exception:
        st.info("Volvé desde el menú lateral.")

# ----------------- Estilos -----------------
st.markdown("""
<style>
.stApp { background:#FF8C00; }
.panel{
  background:#f79b2f; border-radius:12px; padding:16px 18px;
  box-shadow:0 8px 18px rgba(0,0,0,.18);
}
.hdr{
  text-align:center; font-weight:900; letter-spacing:.6px;
  color:#10203a; margin-bottom:10px;
}
.row{
  background:#ffa84d; border-radius:10px; padding:6px 8px; margin:6px 0;
  box-shadow:0 1px 4px rgba(0,0,0,.12);
}
.row .lbl{ color:#1b2749; font-weight:700; }
.counter{ display:flex; gap:6px; justify-content:flex-end; align-items:center; }
.counter .score{ background:#d6d6d6; color:#000; font-weight:900; border-radius:6px; padding:3px 8px; min-width:28px; text-align:center; }
.counter button{ font-weight:900; }
.badge{ display:inline-block; background:#d6d6d6; color:#000; font-weight:900; border-radius:8px; padding:6px 10px; margin:6px 0; }
.btn-primary{ background:#0b3a91 !important; color:#fff !important; border:none !important; border-radius:8px !important; padding:10px 18px !important; font-weight:900 !important; }
.btn-secondary{ background:#936037 !important; color:#fff !important; border:none !important; border-radius:8px !important; padding:10px 18px !important; font-weight:900 !important; }
.product-header { background:#ff9b2f; padding:12px; border-radius:8px; margin-bottom:15px; }
.comment-card{
  background:#fff5e6; border-radius:10px; padding:10px 12px; margin:8px 0;
  box-shadow:0 2px 6px rgba(0,0,0,.12);
}
.comment-card .name{ font-weight:900; color:#1f2e5e; }
.comment-card .date{ font-size:.85rem; color:#333; }
</style>
""", unsafe_allow_html=True)

# ----------------- Helpers producto -----------------
def api_get_product(pid: str):
    try:
        r = requests.get(f"{BACKEND_URL}/products/{pid}", timeout=8)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

product = api_get_product(PRODUCT_ID) or {}
product_info = {
    "name": product.get("name", "Producto"),
    "seller": product.get("seller_alias") or product.get("seller_name") or product.get("seller", "Vendedor"),
    "rating": float(product.get("rating", 0) or 0),
    "category": product.get("category", "-") or "-",
    "subcategory": product.get("subcategory", "-") or "-",
}

# ----------------- Cabecera -----------------
st.markdown('<div class="hdr"><h3>💬 COMENTARIOS Y VALORACIÓN</h3></div>', unsafe_allow_html=True)
st.markdown('<div class="panel">', unsafe_allow_html=True)

st.markdown("<div class='product-header'>", unsafe_allow_html=True)
st.write(f"**📦 PRODUCTO:** {product_info['name']}  \n**ID:** {PRODUCT_ID}")
st.caption(
    f"**🏪 VENDEDOR:** {product_info['seller']} • **⭐ VALORACIÓN:** {product_info['rating']}/10  \n"
    f"**📂 CATEGORÍA:** {product_info['category']}  \n"
    f"**🔍 SUBCATEGORÍA:** {product_info['subcategory']}"
)
st.markdown("</div>", unsafe_allow_html=True)

# ----------------- Criterios -----------------
criteria = [
    ("calidad_general", "⭐ CALIDAD GENERAL"),
    ("relacion_calidad_precio", "💰 RELACIÓN CALIDAD-PRECIO"),
    ("durabilidad", "🛡️ DURABILIDAD"),
    ("descripcion_fiel", "📝 DESCRIPCIÓN FIEL"),
    ("embalaje_recepcion", "📦 EMBALAJE / ESTADO AL RECIBIR"),
    ("satisfaccion_global", "😊 SATISFACCIÓN GLOBAL"),
    ("diseno_estetica", "🎨 DISEÑO Y ESTÉTICA"),
]

for key, _ in criteria:
    st.session_state.setdefault(f"rating_{key}", 9)

total_points = 0
for key, label in criteria:
    current = st.session_state[f"rating_{key}"]
    colA, colB = st.columns([3,2])
    with colA:
        st.markdown(f'<div class="row"><span class="lbl">{label}</span></div>', unsafe_allow_html=True)
    with colB:
        c1, c2, c3 = st.columns([1,1,2])
        with c1:
            if st.button("−", key=f"sub_{key}"):
                st.session_state[f"rating_{key}"] = max(1, current - 1)
                st.rerun()
        with c2:
            st.markdown(
                f"<div class='counter'><span class='score'>{st.session_state[f'rating_{key}']}</span></div>",
                unsafe_allow_html=True
            )
        with c3:
            if st.button("+", key=f"add_{key}"):
                st.session_state[f"rating_{key}"] = min(10, current + 1)
                st.rerun()
    total_points += st.session_state[f"rating_{key}"]

avg_score = round(total_points / len(criteria), 1)
st.markdown(f"<span class='badge'>🎯 PUNTUACIÓN FINAL: {avg_score}/10</span>", unsafe_allow_html=True)

# ----------------- Comentario libre -----------------
st.markdown("### 💭 TU COMENTARIO")
comment = st.text_area(
    "Compartí tu experiencia con este producto...",
    height=120,
    placeholder="¿Qué te pareció? ¿Recomendarías la compra? ¿Qué mejorarías?",
    label_visibility="collapsed"
)

# ----------------- Guardar comentario -----------------
def save_comment(payload: dict) -> bool:
    """Intenta enviar al backend; si falla, guarda en CSV. Devuelve True si se guardó."""
    # 1) Intento backend (con token)
    try:
        r = requests.post(
            f"{BACKEND_URL}/comments",
            json=payload,
            headers=auth_headers(),
            timeout=8
        )
        if r.status_code in (200, 201):
            return True
    except Exception:
        pass

    # 2) Fallback CSV
    try:
        if DATA_PATH.exists():
            df = pd.read_csv(DATA_PATH)
        else:
            df = pd.DataFrame(columns=["product_id","user_name","rating","criteria","comment","date"])

        row = {
            "product_id": payload["product_id"],
            "user_name": payload.get("user_name", "Anónimo"),
            "rating": payload["rating"],
            "criteria": json.dumps(payload["criteria"], ensure_ascii=False),
            "comment": payload["comment"],
            "date": datetime.now().strftime("%Y-%m-%d")
        }
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        df.to_csv(DATA_PATH, index=False, encoding="utf-8")
        return True
    except Exception as e:
        st.error(f"No se pudo guardar el comentario: {e}")
        return False

col_send, col_back = st.columns(2)

with col_send:
    if st.button("📤 ENVIAR VALORACIÓN", key="btn_send_valoracion"):
        payload = {
            "product_id": PRODUCT_ID,
            "user_name": user_name,
            "rating": float(avg_score),
            "criteria": {k: int(st.session_state[f"rating_{k}"]) for k, _ in criteria},
            "comment": comment.strip(),
        }
        if not payload["comment"]:
            st.warning("Escribí un comentario antes de enviar.")
        else:
            ok = save_comment(payload)
            if ok:
                st.success("✅ Valoración enviada correctamente.")
                st.rerun()

with col_back:
    if st.button("⬅️ VOLVER", key="btn_back"):
        safe_switch_page("1_Comprador.py")

st.markdown("</div>", unsafe_allow_html=True)

# ----------------- Mostrar comentarios existentes -----------------
def api_get_comments(pid: str):
    """Trae comentarios del backend; si no hay endpoint, devuelve None."""
    try:
        r = requests.get(f"{BACKEND_URL}/comments", params={"product_id": pid}, timeout=8)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, dict):
                return data.get("items") or data.get("comments") or []
            if isinstance(data, list):
                return data
    except Exception:
        pass
    return None

comments = api_get_comments(PRODUCT_ID)

if comments is None:
    # fallback CSV
    if DATA_PATH.exists():
        try:
            df = pd.read_csv(DATA_PATH)
            comments = df[df["product_id"].astype(str) == PRODUCT_ID].to_dict("records")
        except Exception:
            comments = []
    else:
        comments = []

st.markdown("### 📖 COMENTARIOS DEL PRODUCTO")
if not comments:
    st.info("Todavía no hay comentarios para este producto.")
else:
    # ordenamos por fecha si existe
    def _date_key(c):
        return c.get("date") or c.get("created_at") or ""
    comments = sorted(comments, key=_date_key, reverse=True)

    for c in comments[:50]:
        uname = c.get("user_name", "Anónimo")
        rating = c.get("rating", "-")
        text = c.get("comment", "")
        date = c.get("date") or c.get("created_at") or ""

        st.markdown(
            f"""
            <div class="comment-card">
              <div class="name">⭐ {rating}/10 — {uname}</div>
              <div class="date">{date}</div>
              <div>{text}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
