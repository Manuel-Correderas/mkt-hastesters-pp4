# streamlit_app/Home.py



import os
import sys
import json
import time
import requests
import pandas as pd
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

# Cargar variables desde .env (en la raíz del proyecto)
load_dotenv()

st.set_page_config(page_title="Ecom MKT Lab - Home", page_icon="🛒", layout="wide")

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

PAGE_NS = "home_v1"
def K(s: str) -> str:
    return f"{PAGE_NS}:{s}"

# =========================
# ESTILOS — LIMPIO, SIN RECTÁNGULOS
# =========================
st.markdown("""
<style>
:root { --primary:#0b3a91; }
body, .stApp { background:#ffffff; }
.topbar { display:flex; flex-wrap:wrap; align-items:center; gap:10px; margin:8px 0 16px; }
.brand { font-weight:900; color:var(--primary); font-size:1.2rem; }
div[data-baseweb="input"] input { border-radius:10px; height:40px; border:2px solid var(--primary) !important; }
.stButton > button {
  background:#fff !important; color:var(--primary) !important;
  border:2px solid var(--primary) !important; border-radius:999px !important;
  padding:6px 12px !important; font-weight:800 !important; box-shadow:none !important; white-space:nowrap !important;
}
.card { background:transparent; border:none; box-shadow:none; border-radius:0; padding:0; margin-bottom:10px; display:flex; flex-direction:column; align-items:center; }
.card-img { width:100%; height:260px; object-fit:contain; background:transparent; display:block; }
.name { font-weight:900; color:var(--primary); margin:8px 0 4px; text-align:center; font-size:1rem; }
.price { color:#111; text-align:center; font-weight:800; font-size:1.05rem; margin:2px 0 6px; }
.meta { color:#444; text-align:center; font-size:.9rem; margin:0 0 8px; }
.cta { display:flex; justify-content:center; gap:6px; align-items:center; }
.qty-label { font-size:0.8rem; color:#555; text-align:center; margin-top:4px; }
</style>
""", unsafe_allow_html=True)


# =========================
# HELPERS
# =========================
def csv_path():
    for p in [
        Path(__file__).resolve().parents[1] / "data" / "products.csv",
        Path.cwd() / "data" / "products.csv",
        Path(__file__).resolve().parent / "data" / "products.csv",
    ]:
        if p.exists():
            return p
    return None

def money(v):
    try:
        return f"$ {int(float(v)):,}".replace(",", ".")
    except Exception:
        return "$ --"

def set_query_param_id(product_id: str | int):
    """Soporta Streamlit nuevo (st.query_params) y el experimental viejo."""
    try:
        st.query_params.clear()
        st.query_params["id"] = str(product_id)
    except Exception:
        try:
            st.experimental_set_query_params(id=str(product_id))
        except Exception:
            st.session_state["product_id"] = str(product_id)

def auth_headers():
    tok = st.session_state.get("auth_token")
    return {"Authorization": f"Bearer {tok}"} if tok else {}

def require_login_for_cart() -> bool:
    if "auth_token" not in st.session_state:
        st.warning("Tenés que iniciar sesión para agregar productos al carrito.")
        st.page_link("pages/0_Login.py", label="Ir al Login", icon="🔐")
        return False
    return True

# =========================
# BACKEND CALLS
# =========================
@st.cache_data(ttl=30)
def api_list_products(
    q: str | None = None,
    category_id: str | None = None,
    seller_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> pd.DataFrame:
    url = f"{BACKEND_URL}/products"
    params = {"limit": limit, "offset": offset}
    if q:
        params["q"] = q
    if category_id:
        params["category_id"] = category_id
    if seller_id:
        params["seller_id"] = seller_id
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json() or []
    df = pd.json_normalize(data)

    if "category_id" in df.columns and "category" not in df.columns:
        df["category"] = df["category_id"]
    df["image_url"] = df.get("image_url", "")
    df["description"] = df.get("description", "")
    df["name"] = df.get("name", "")
    df["price"] = df.get("price", 0).fillna(0)
    df["subcategory"] = df.get("subcategory", "")
    df["stock"] = df.get("stock", 0).fillna(0)
    df["seller_name"] = df.get("seller_name", "")
    return df

@st.cache_data(ttl=60)
def load_products_from_backend_or_csv(q: str | None) -> pd.DataFrame:
    # intento backend
    try:
        return api_list_products(q=q, limit=200, offset=0)
    except Exception as e:
        st.warning(f"No se pudo contactar el backend ({e}). Se usará demo CSV si existe.")
        p = csv_path()
        if p:
            df = pd.read_csv(p, encoding="utf-8-sig").fillna("")
            for c in ["name", "description", "category", "subcategory", "image_url"]:
                if c in df.columns:
                    df[c] = df[c].astype(str)
            if "stock" not in df.columns:
                df["stock"] = 0
            if "seller_name" not in df.columns and "seller" in df.columns:
                df["seller_name"] = df["seller"]
            return df

        # fallback absoluto
        return pd.DataFrame(
            [
                {
                    "id": 1,
                    "name": "Remera Básica Negra",
                    "price": 9999,
                    "category": "Indumentaria",
                    "subcategory": "Remeras",
                    "image_url": "https://i.imgur.com/pTgqgQw.png",
                    "description": "Remera algodón peinado color negro",
                    "stock": 10,
                    "seller_name": "Demo Seller",
                },
                {
                    "id": 2,
                    "name": "Jean Slim Azul",
                    "price": 25999,
                    "category": "Indumentaria",
                    "subcategory": "Pantalones",
                    "image_url": "https://i.imgur.com/8m7Zy0Z.png",
                    "description": "Jean slim fit azul clásico",
                    "stock": 5,
                    "seller_name": "Demo Seller",
                },
            ]
        )

# =========================
# TOPBAR (incluye CARRITO)
# =========================
st.markdown('<div class="topbar">', unsafe_allow_html=True)
c1, c2, c3 = st.columns([2, 4, 1])
with c1:
    st.markdown('<div class="brand">🛍️ Ecom MKT Lab</div>', unsafe_allow_html=True)
with c2:
    q = st.text_input("Buscar productos…", label_visibility="collapsed", key="q")
with c3:
    if st.button("🛒 Carrito"):
        st.switch_page("pages/4_Mi_Carrito.py")
st.markdown("</div>", unsafe_allow_html=True)

# =========================
# LISTADO + FILTROS (desde BACKEND)
# =========================
df = load_products_from_backend_or_csv(q).copy()

cats = ["Todos"] + sorted(
    df.get("category", pd.Series(dtype=str)).dropna().astype(str).unique().tolist()
)
subs = ["Todas"] + sorted(
    df.get("subcategory", pd.Series(dtype=str)).dropna().astype(str).unique().tolist()
)

sel_cat = st.session_state.get("sel_cat", "Todos")
sel_sub = st.session_state.get("sel_sub", "Todas")

st.caption("Categorías")
cat_cols = st.columns(max(1, len(cats)))
for i, c in enumerate(cats):
    with cat_cols[i]:
        if st.button(c, key=f"cat_{c}"):
            sel_cat = c
            st.session_state["sel_cat"] = c

st.caption("Subcategorías")
sub_cols = st.columns(max(1, len(subs)))
for i, s in enumerate(subs):
    with sub_cols[i]:
        if st.button(s, key=f"sub_{s}"):
            sel_sub = s
            st.session_state["sel_sub"] = s

view = df.copy()
if sel_cat != "Todos" and "category" in view.columns:
    view = view[view["category"] == sel_cat]
if sel_sub != "Todas" and "subcategory" in view.columns:
    view = view[view["subcategory"] == sel_sub]

# =========================
# GRID DE PRODUCTOS (Ver detalle + Añadir al carrito)
# =========================
st.markdown("## Productos Disponibles")
cols = st.columns(3)

if view.empty:
    st.info("No se encontraron productos.")
else:
    view = view.reset_index(drop=True)
    for i, row in view.iterrows():
        with cols[i % 3]:
            img = str(row.get("image_url", "")).strip()
            if not (img and img.startswith("http")):
                img = "https://via.placeholder.com/600x400.png?text=Sin+Imagen"

            pid = str(row.get("id", f"row-{i}"))
            pname = row.get("name", "Producto")
            pprice = row.get("price", 0)
            cat = row.get("category", "")
            sub = row.get("subcategory", "")
            seller = row.get("seller_name") or row.get("seller", "")

            # STOCK DIRECTO DESDE BACKEND (sin restar lo del carrito)
            stock_raw = row.get("stock", 0)
            try:
                stock = int(stock_raw)
            except Exception:
                stock = 0

            st.markdown(
                f"""
            <div class="card">
              <img class="card-img" src="{img}" alt="{pname}">
              <div class="name">{pname}</div>
              <div class="price">{money(pprice)}</div>
              <div class="meta">{cat} / {sub}</div>
              <div class="meta">Stock: {stock} — Vendedor: {seller}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Controles: Ver detalle + Cantidad + Añadir
            with st.container():
                # cantidad depende del stock actual
                max_qty = max(1, stock) if stock > 0 else 1
                qty = st.number_input(
                    "Cant.",
                    min_value=1,
                    max_value=max_qty,
                    value=1,
                    step=1,
                    key=K(f"qty_{pid}_{i}"),
                )

                cta = st.columns(2)
                with cta[0]:
                    if st.button("🔎 Ver detalle", key=K(f"det_{pid}_{i}")):
                        st.session_state["last_product"] = pid
                        set_query_param_id(pid)
                        st.switch_page("pages/3_Producto.py")
                with cta[1]:
                    if st.button("🛒 Añadir", key=K(f"add_{pid}_{i}")):
                        if stock <= 0:
                            st.error("No hay stock disponible para este producto.")
                        elif not require_login_for_cart():
                            # Ya mostró mensaje/link
                            pass
                        else:
                            try:
                                r = requests.post(
                                    f"{BACKEND_URL}/cart/items",
                                    json={"product_id": pid, "qty": int(qty)},
                                    headers=auth_headers(),
                                    timeout=10,
                                )
                                if r.status_code in (200, 201):
                                    st.success("Producto añadido al carrito ✅")
                                    # Si querés refrescar igual para recargar lista:
                                    if hasattr(st, "rerun"):
                                        st.rerun()
                                    else:
                                        st.experimental_rerun()
                                else:
                                    st.error(
                                        f"Error al agregar al carrito (HTTP {r.status_code}): {r.text}"
                                    )
                            except Exception as e:
                                st.error(f"No se pudo conectar al backend: {e}")
