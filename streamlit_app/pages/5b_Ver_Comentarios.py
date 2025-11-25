# streamlit_app/pages/5b_📖_Ver_Comentarios.py
import json
import requests
import pandas as pd
from ast import literal_eval
from pathlib import Path
import streamlit as st

from auth_helpers import get_backend_url, auth_headers  # 👈 NO importamos require_login

# ✅ set_page_config primero
st.set_page_config(page_title="Ver comentarios", page_icon="📖", layout="centered")

BACKEND_URL = get_backend_url()
DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "comments.csv"
DATA_PATH.parent.mkdir(parents=True, exist_ok=True)

PAGE_SELLER_PANEL = "2_Vendedor.py"
PAGE_MIS_PRODUCTOS = "7_Mis_Productos.py"

PAGE_NS = "ver_comments_v1"
def K(s: str) -> str:
    return f"{PAGE_NS}:{s}"

# ---------------------------
# Navegación segura
# ---------------------------
def safe_switch_page(*page_filenames: str):
    for filename in page_filenames:
        if filename.endswith(".py") and not filename.startswith("pages/"):
            main_path = Path(__file__).resolve().parents[1] / filename
            if main_path.exists():
                st.switch_page(filename)
                return
        page_path = Path(__file__).resolve().parent / filename
        if page_path.exists():
            st.switch_page(f"pages/{filename}")
            return
    st.warning("No se encontró la página destino. Revisá nombres exactos en /pages.")

# ---------------------------
# AUTH OPCIONAL (si hay token, lo usamos; si no, público)
# ---------------------------
def maybe_headers():
    """Devuelve headers con Bearer si hay token, sino {}."""
    tok = st.session_state.get("auth_token")
    return auth_headers() if tok else {}

user_obj = st.session_state.get("user") or st.session_state.get("auth_user") or {}
roles = (
    st.session_state.get("auth_roles")
    or st.session_state.get("roles")
    or user_obj.get("roles")
    or [user_obj.get("role")]
    or []
)
roles = [str(r).upper() for r in roles if r]

SELLER_ID = (
    st.session_state.get("auth_user_id")
    or st.session_state.get("user_id")
    or user_obj.get("user_id")
    or user_obj.get("id")
)

# Tomamos product_id de la URL (?id=...)
qp = st.query_params
pid_qs = qp.get("id") or qp.get("product_id")

if isinstance(pid_qs, list):
    pid_qs = pid_qs[0]

PRODUCT_ID = str(pid_qs or "").strip()

# ✅ fallback si no viene en la URL
if not PRODUCT_ID:
    PRODUCT_ID = str(st.session_state.get("last_product") or "").strip()

if not PRODUCT_ID:
    st.error("Falta product_id. Entrá desde un producto con el botón 'Ver comentarios'.")
    st.stop()


# ---------------------------
# Helpers backend
# ---------------------------
def normalize_list(data):
    if isinstance(data, dict):
        return data.get("items") or data.get("data") or []
    return data if isinstance(data, list) else []

def fetch_product(product_id: str) -> dict | None:
    """Trae producto real para cabecera."""
    try:
        r = requests.get(
            f"{BACKEND_URL}/products/{product_id}",
            headers=maybe_headers(),   # 👈 si no hay token, headers vacíos
            timeout=10
        )
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

def load_comments(product_id: str) -> list[dict]:
    """
    1) /products/{id}/comments (si existe)
    2) /comments?product_id={id}
    3) fallback CSV
    """
    # 1) endpoint anidado
    try:
        r = requests.get(
            f"{BACKEND_URL}/products/{product_id}/comments",
            headers=maybe_headers(),
            timeout=8
        )
        if r.status_code == 200:
            data = normalize_list(r.json())
            return _normalize_comments(data)
    except Exception:
        pass

    # 2) endpoint plano
    try:
        r = requests.get(
            f"{BACKEND_URL}/comments",
            params={"product_id": product_id},
            headers=maybe_headers(),
            timeout=8
        )
        if r.status_code == 200:
            data = normalize_list(r.json())
            return _normalize_comments(data)
    except Exception:
        pass

    # 3) Fallback CSV
    if DATA_PATH.exists():
        try:
            df = pd.read_csv(DATA_PATH)
            df = df[df["product_id"].astype(str) == str(product_id)]
            reviews = []
            for _, row in df.iterrows():
                crit_raw = row.get("criteria", "{}")
                try:
                    criteria = literal_eval(crit_raw)
                except Exception:
                    try:
                        criteria = json.loads(crit_raw)
                    except Exception:
                        criteria = {}
                reviews.append({
                    "user": row.get("user_name", "Anónimo"),
                    "rating": float(row.get("rating", 0.0)),
                    "comment": row.get("comment", ""),
                    "date": row.get("date", ""),
                    "criteria": criteria,
                })
            return reviews
        except Exception as e:
            st.warning(f"No se pudo leer comments.csv: {e}")

    return []

def _normalize_comments(data: list[dict]) -> list[dict]:
    normalized = []
    for it in data:
        normalized.append({
            "user": it.get("user_name") or it.get("user") or "Anónimo",
            "rating": float(it.get("rating", 0.0)),
            "comment": it.get("comment") or it.get("text") or "",
            "date": (it.get("date") or it.get("created_at") or "")[:10],
            "criteria": it.get("criteria", {}) or {},
        })
    return normalized

# ----------------- Estilos -----------------
st.markdown("""
<style>
.stApp { background:#FF8C00; }
.wrap{
  background:#f79b2f; border-radius:14px; padding:16px 18px;
  box-shadow:0 8px 18px rgba(0,0,0,.18);
}
.hdr{ text-align:center; font-weight:900; letter-spacing:.6px; color:#10203a; margin-bottom:8px; }
.sub{ font-size:.92rem; color:#162c56; }
.badge{ display:inline-block; background:#d6d6d6; color:#000; font-weight:900; border-radius:8px; padding:6px 10px; margin:6px 0; }
.list{ background:#ffa84d; border-radius:10px; padding:10px; margin-top:8px; max-height: 420px; overflow-y: auto; box-shadow: inset 0 1px 4px rgba(0,0,0,.12); }
.card{ background:#fff5e6; border-radius:10px; padding:10px 12px; box-shadow:0 2px 6px rgba(0,0,0,.12); margin-bottom:10px; }
.product-header { background:#ff9b2f; padding:12px; border-radius:8px; margin-bottom:15px; }
</style>
""", unsafe_allow_html=True)

# ----------------- Cabecera -----------------
st.markdown('<div class="hdr"><h3>📖 VER COMENTARIOS</h3></div>', unsafe_allow_html=True)
st.markdown('<div class="wrap">', unsafe_allow_html=True)

product = fetch_product(PRODUCT_ID) or {}

product_info = {
    "name": product.get("name", f"Producto {PRODUCT_ID}"),
    "seller": product.get("seller_name") or product.get("seller") or "-",
    "rating": product.get("rating", 0.0),
    "category": product.get("category_name") or product.get("category") or "-",
    "subcategory": product.get("subcategory") or "-",
    "image": product.get("image_url") or "",
    "seller_id": product.get("seller_id")
}

# ✅ Chequeo de pertenencia SOLO si está logueado como vendedor (público no)
is_logged = bool(st.session_state.get("auth_token"))
is_seller = any(r in roles for r in ["VENDEDOR", "SELLER"])
if is_logged and is_seller and "ADMIN" not in roles:
    if product_info["seller_id"] and SELLER_ID:
        if str(product_info["seller_id"]) != str(SELLER_ID):
            st.error("Este producto no pertenece a tu cuenta de vendedor.")
            st.stop()

c1, c2 = st.columns([4,1])
with c1:
    st.markdown("<div class='product-header'>", unsafe_allow_html=True)
    st.write(f"**📦 PRODUCTO:** {product_info['name']}  \n**ID:** {PRODUCT_ID}")
    st.markdown(
        f"<div class='sub'>"
        f"<b>🏪 VENDEDOR:</b> {product_info['seller']} • "
        f"<b>⭐ VALORACIÓN:</b> {product_info['rating']}/10<br>"
        f"<b>📂 CATEGORÍA:</b> {product_info['category']}<br>"
        f"<b>🔍 SUBCATEGORÍA:</b> {product_info['subcategory']}"
        f"</div>",
        unsafe_allow_html=True
    )
    st.markdown("</div>", unsafe_allow_html=True)

with c2:
    if product_info["image"]:
        st.image(product_info["image"], use_container_width=True)
    else:
        st.markdown(
            '<div style="background:#f8f9fa; border-radius:8px; padding:40px 20px; text-align:center; border:1px solid #ddd;">'
            '<span style="color:#666;">📸</span>'
            '</div>',
            unsafe_allow_html=True
        )

# ----------------- Datos -----------------
reviews = load_comments(PRODUCT_ID)

if reviews:
    avg_rating = round(sum(r["rating"] for r in reviews) / len(reviews), 1)
    total_reviews = len(reviews)
    st.markdown(
        f"<span class='badge'>📊 PUNTUACIÓN PROMEDIO: {avg_rating}/10 · {total_reviews} VALORACIONES</span>",
        unsafe_allow_html=True
    )
else:
    st.info("No hay comentarios registrados para este producto.")

# ----------------- Filtros -----------------
st.markdown("### 🔍 FILTRAR COMENTARIOS")
col_filter1, col_filter2, col_filter3 = st.columns([2,2,2])
with col_filter1:
    min_score = st.slider("Puntuación mínima", 0.0, 10.0, 0.0, 0.5)
with col_filter2:
    search_text = st.text_input("Buscar en comentarios", "")
with col_filter3:
    sort_order = st.toggle("Ordenar por más recientes", value=True)

# ----------------- Listado -----------------
st.markdown("### 💬 COMENTARIOS DE CLIENTES")
st.markdown('<div class="list">', unsafe_allow_html=True)

filtered = [
    x for x in reviews
    if x["rating"] >= min_score and search_text.lower() in (x["comment"] or "").lower()
]
if sort_order:
    filtered.sort(key=lambda x: x.get("date",""), reverse=True)

if not filtered:
    st.info("No hay comentarios que coincidan con los filtros aplicados.")
else:
    for i, review in enumerate(filtered, 1):
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f"**#{i} · ⭐ {review['rating']}/10**")
        st.caption(f"👤 por {review.get('user','Anónimo')} · 📅 {review.get('date','')}")
        st.write(f"_{review.get('comment','')}_")

        crit = review.get("criteria", {}) or {}
        if crit:
            st.caption("**Detalle de valoración:**")
            cols = st.columns(3)
            items = list(crit.items())
            for idx, (k, v) in enumerate(items):
                with cols[idx % 3]:
                    st.write(f"• {k.replace('_',' ').title()}: **{v}**")
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ----------------- Volver -----------------
st.write("")
if st.button("⬅️ VOLVER", key=K("btn_back"), use_container_width=True):
    safe_switch_page(PAGE_MIS_PRODUCTOS, PAGE_SELLER_PANEL)

st.markdown('</div>', unsafe_allow_html=True)
