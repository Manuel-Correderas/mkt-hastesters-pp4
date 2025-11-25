# streamlit_app/pages/4b_💳_Checkout.py
import os
import requests
import streamlit as st
from dotenv import load_dotenv

from auth_helpers import get_backend_url, auth_headers, require_login

# =========================
# CONFIG GLOBAL
# =========================
load_dotenv()
st.set_page_config(page_title="Checkout - Ecom MKT Lab", layout="centered")

BACKEND_URL = get_backend_url()

# ============== HELPERS API ==============

def api_get_cart():
    """Trae el carrito actual del backend."""
    try:
        r = requests.get(
            f"{BACKEND_URL}/cart",
            headers=auth_headers(),
            timeout=10,
        )
        # muchos backends devuelven 204/404 si no hay carrito
        if r.status_code in (204, 404):
            return []
        if r.status_code == 200:
            return r.json()
        st.error(f"Error al obtener el carrito ({r.status_code}): {r.text}")
        return None
    except Exception as e:
        st.error(f"No se pudo conectar al backend: {e}")
        return None


def api_post_checkout(payload: dict):
    """Confirma la compra en el backend."""
    try:
        r = requests.post(
            f"{BACKEND_URL}/orders/checkout",
            json=payload,
            headers=auth_headers(),
            timeout=15,
        )
        return r
    except Exception as e:
        st.error(f"No se pudo conectar al backend: {e}")
        return None


def resumen_compra(items: list[dict]) -> str:
    """
    Arma un texto con lo comprado:
    '2x Zapatillas, 1x Remera'
    Soporta items planos o con product anidado.
    """
    parts = []
    for it in items:
        prod = it.get("product") or it.get("producto") or it
        name = prod.get("name") or it.get("product_name") or "Producto"
        qty = it.get("quantity", it.get("qty", it.get("cantidad", 1)))
        try:
            qty = int(qty or 1)
        except Exception:
            qty = 1
        parts.append(f"{qty}x {name}")
    return ", ".join(parts)


# ============== ESTILOS ==============
st.markdown("""
<style>
.stApp { background:#FF8C00; }
.panel {
  background:#f79b2f; border-radius:12px; padding:16px 18px;
  box-shadow:0 8px 18px rgba(0,0,0,.18);
}
.hdr { 
    text-align:center; 
    font-weight:900; 
    color:#10203a; 
    letter-spacing:.5px; 
    margin-bottom:15px;
}
.item {
  background:#fff5e6; border-radius:10px; padding:12px; margin-bottom:10px;
  box-shadow:0 2px 8px rgba(0,0,0,.12);
}
.badge {
  display:inline-block; background:#d6d6d6; color:#000; font-weight:900;
  border-radius:8px; padding:6px 10px; margin:6px 0;
}
.btn-primary { 
    background:#0b3a91 !important; 
    color:#fff !important; 
    border:none !important; 
    border-radius:8px !important; 
    padding:10px 18px !important; 
    font-weight:800 !important;
}
.btn-secondary { 
    background:#936037 !important; 
    color:#fff !important; 
    border:none !important; 
    border-radius:8px !important; 
    padding:10px 18px !important; 
    font-weight:800 !important;
}
.section-title {
    color:#1f2e5e;
    font-weight:800;
    margin:20px 0 10px 0;
    border-bottom:2px solid #0b3a91;
    padding-bottom:5px;
}
.qr-container {
    background:#ffffff;
    border-radius:10px;
    padding:20px;
    text-align:center;
    border:2px solid #0b3a91;
    margin:15px 0;
}
</style>
""", unsafe_allow_html=True)


# ============== CHEQUEO LOGIN ==============
require_login()

# ============== TRAER CARRITO DEL BACKEND ==============
cart = api_get_cart()

# ✅ Normalizamos carrito a lista de items sí o sí
if cart is None:
    raw_items = []
elif isinstance(cart, dict):
    raw_items = cart.get("items") or cart.get("cart_items") or cart.get("data") or []
elif isinstance(cart, list):
    raw_items = cart
else:
    raw_items = []

# ✅ si viene dict de items -> list
if isinstance(raw_items, dict):
    raw_items = list(raw_items.values())

# ✅ filtramos basura (qty 0 / None)
items = []
for it in (raw_items or []):
    q = it.get("quantity", it.get("qty", it.get("cantidad", 0)))
    try:
        q = int(q or 0)
    except Exception:
        q = 0
    if q > 0:
        items.append(it)

# Si no hay items, mostramos vacío
if not items:
    st.markdown('<div class="hdr"><h3>💳 CHECKOUT</h3></div>', unsafe_allow_html=True)
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.info("Tu carrito está vacío. Volvé a la tienda para agregar productos.")
    if st.button("⬅️ VOLVER AL CARRITO", key="btn_back_empty", use_container_width=True):
        try:
            st.switch_page("pages/4_Mi_Carrito.py")
        except Exception:
            st.info("Volvé al carrito desde el menú lateral.")
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# =========================
# ARMAR TOTAL / CURRENCY
# =========================
if isinstance(cart, dict):
    currency = cart.get("currency", "ARS")
    total_pedido = cart.get("total")
else:
    currency = "ARS"
    total_pedido = None

if not total_pedido:
    total_pedido = sum(
        float(
            it.get("subtotal")
            or it.get("total")
            or it.get("quantity", it.get("qty", 1)) * it.get("unit_price", it.get("price", 0))
        )
        for it in items
    )

# config de pago si existe
payment_config = cart.get("payment", {}) if isinstance(cart, dict) else {}
first_item = items[0] if items else {}

default_pay_method = payment_config.get("pay_method") or first_item.get("pay_method") or "TRANSFERENCIA"
default_alias = payment_config.get("alias") or first_item.get("alias") or "HMVENTAS.GALICIA"
default_wallet = payment_config.get("wallet") or first_item.get("wallet") or "0x742d35Cc6634C0532925a3b8D..."
default_network = payment_config.get("network") or first_item.get("network") or "BEP-20"
default_bank = payment_config.get("bank_name") or first_item.get("bank_name") or "Galicia"
default_cbu = payment_config.get("cbu") or first_item.get("cbu") or "0070000000001234567890"
default_mp_link = payment_config.get("mp_link") or "https://mpago.la/1a2b3c4d"

# ============== RESUMEN DEL PEDIDO ==============
st.markdown('<div class="hdr"><h3>💳 CHECKOUT</h3></div>', unsafe_allow_html=True)
st.markdown('<div class="panel">', unsafe_allow_html=True)

st.markdown("### 📦 RESUMEN DE TU PEDIDO")

for it in items:
    prod = it.get("product") or it.get("producto") or it

    name = prod.get("name", "Producto sin nombre")
    seller = prod.get("seller_alias") or prod.get("seller_name") or prod.get("seller") or "Vendedor"
    quantity = int(it.get("quantity", it.get("qty", 1)) or 1)
    unit_price = float(prod.get("unit_price", prod.get("price", 0)) or 0)
    subtotal = float(it.get("subtotal", quantity * unit_price))
    category = prod.get("category", "Sin categoría")
    subcategory = prod.get("subcategory", "Sin subcategoría")
    image_url = prod.get("image_url") or prod.get("image") or ""

    col_item1, col_item2 = st.columns([3, 1])
    with col_item1:
        st.markdown('<div class="item">', unsafe_allow_html=True)
        st.markdown(f"**{name}**")
        st.markdown(f"Vendedor: {seller} • {category} • {subcategory}")
        st.markdown(
            f"Cantidad: {quantity} • Precio unitario: "
            f"${unit_price:,.0f}".replace(",", ".")
        )
        st.markdown(
            f'<span class="badge">Subtotal: ${subtotal:,.0f}</span>'.replace(",", "."),
            unsafe_allow_html=True
        )
        st.markdown('</div>', unsafe_allow_html=True)
    with col_item2:
        if image_url:
            try:
                st.image(image_url, use_container_width=True)
            except Exception:
                st.warning("Imagen no disponible")
        else:
            st.markdown(
                '<div style="background:#f8f9fa; border-radius:8px; padding:30px 15px; text-align:center; border:1px solid #ddd;">'
                '<span style="color:#666;">📸</span>'
                '</div>',
                unsafe_allow_html=True
            )

st.markdown(
    f"### 💰 TOTAL DEL PEDIDO: ${total_pedido:,.0f} {currency}".replace(",", ".")
)
st.markdown("</div>", unsafe_allow_html=True)

# ============== MÉTODO DE PAGO ==============
st.markdown('<div class="panel">', unsafe_allow_html=True)
st.markdown('<div class="section-title">💳 MÉTODO DE PAGO</div>', unsafe_allow_html=True)

method_map_backend_to_label = {
    "TRANSFERENCIA": "Transferencia Bancaria",
    "MERCADO_PAGO": "Mercado Pago",
    "TARJETA": "Tarjeta de Crédito",
    "CRYPTO": "Criptomonedas",
}
method_map_label_to_backend = {v: k for k, v in method_map_backend_to_label.items()}

default_label = method_map_backend_to_label.get(default_pay_method, "Transferencia Bancaria")
methods_labels = ["Transferencia Bancaria", "Mercado Pago", "Tarjeta de Crédito", "Criptomonedas"]
try:
    default_index = methods_labels.index(default_label)
except ValueError:
    default_index = 0

payment_method_label = st.radio(
    "Seleccioná tu método de pago:",
    methods_labels,
    index=default_index,
    horizontal=True
)
payment_method_backend = method_map_label_to_backend[payment_method_label]

if payment_method_label == "Transferencia Bancaria":
    st.markdown("#### 🏦 Transferencia Bancaria")
    col_bank1, col_bank2 = st.columns(2)
    with col_bank1:
        st.markdown("**Datos para transferencia:**")
        st.markdown(
            f"""
- **Banco:** {default_bank}
- **Titular:** {first_item.get("seller_name", "Ecom MKT Lab")}
- **CBU:** {default_cbu}
- **Alias:** {default_alias}
"""
        )
    with col_bank2:
        st.markdown('<div class="qr-container">', unsafe_allow_html=True)
        st.markdown("**📱 Código QR**")
        st.markdown(
            '<div style="background:#f8f9fa; border-radius:8px; padding:60px 30px; text-align:center; border:1px solid #ddd; margin:10px 0;">'
            '<span style="color:#666;">QR Code</span>'
            '</div>',
            unsafe_allow_html=True
        )
        st.markdown("Escaneá con tu app bancaria")
        st.markdown('</div>', unsafe_allow_html=True)

elif payment_method_label == "Mercado Pago":
    st.markdown("#### 📱 Mercado Pago")
    st.markdown(f"**🔗 Link de pago:** {default_mp_link}")
    st.markdown("**💡 Instrucciones:**")
    st.markdown("1. Hacé clic en el link de arriba")
    st.markdown("2. Completá los datos de tu tarjeta o cuenta de Mercado Pago")
    st.markdown("3. Confirmá el pago")

elif payment_method_label == "Tarjeta de Crédito":
    st.markdown("#### 💳 Tarjeta de Crédito")
    col_card1, col_card2 = st.columns(2)
    with col_card1:
        st.text_input("Número de tarjeta", placeholder="1234 5678 9012 3456")
        st.text_input("Nombre del titular", placeholder="Como figura en la tarjeta")
    with col_card2:
        col_exp, col_cvv = st.columns(2)
        with col_exp:
            st.text_input("Vencimiento", placeholder="MM/AA")
        with col_cvv:
            st.text_input("CVV", placeholder="123")
    st.markdown("💡 Pago procesado de forma segura (simulado)")

elif payment_method_label == "Criptomonedas":
    st.markdown("#### ₿ Criptomonedas")
    col_crypto1, col_crypto2 = st.columns(2)
    with col_crypto1:
        crypto_network = st.selectbox(
            "Red",
            ["BEP-20", "ERC-20", "TRC-20", "Polygon"],
            index=["BEP-20", "ERC-20", "TRC-20", "Polygon"].index(default_network)
            if default_network in ["BEP-20", "ERC-20", "TRC-20", "Polygon"] else 0
        )
        st.markdown(f"**Wallet:** {default_wallet}")
        st.markdown(f"**Monto aproximado en USDT:** {total_pedido/1000:.2f}")
    with col_crypto2:
        st.markdown('<div class="qr-container">', unsafe_allow_html=True)
        st.markdown("**📱 QR Cripto**")
        st.markdown(
            '<div style="background:#f8f9fa; border-radius:8px; padding:60px 30px; text-align:center; border:1px solid #ddd; margin:10px 0;">'
            '<span style="color:#666;">QR Code</span>'
            '</div>',
            unsafe_allow_html=True
        )
        st.markdown("Escaneá con tu wallet")
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ============== INFORMACIÓN DE ENVÍO ==============
st.markdown('<div class="panel">', unsafe_allow_html=True)
st.markdown('<div class="section-title">🚚 INFORMACIÓN DE ENVÍO</div>', unsafe_allow_html=True)

default_shipping_name = st.session_state.get("shipping_name") or st.session_state.get("user_name") or ""
default_shipping_address = st.session_state.get("shipping_address") or ""
default_shipping_phone = st.session_state.get("shipping_phone") or ""

col_shipping1, col_shipping2 = st.columns(2)
with col_shipping1:
    shipping_name = st.text_input("Nombre completo", value=default_shipping_name)
    shipping_address = st.text_area("Dirección de envío", value=default_shipping_address)
with col_shipping2:
    shipping_phone = st.text_input("Teléfono de contacto", value=default_shipping_phone)
    shipping_notes = st.text_area("Instrucciones especiales", placeholder="Ej: Timbre azul, dejar con portero")

st.markdown("**📦 Método de envío:** Estándar (3-5 días hábiles)")
st.markdown("**💰 Costo de envío:** Gratis (compra mayor a $30.000)")

st.markdown("</div>", unsafe_allow_html=True)

# Guardar en sesión
st.session_state["shipping_name"] = shipping_name
st.session_state["shipping_address"] = shipping_address
st.session_state["shipping_phone"] = shipping_phone

# ============== CONFIRMACIÓN ==============
st.markdown('<div class="panel">', unsafe_allow_html=True)
st.markdown('<div class="section-title">✅ CONFIRMAR COMPRA</div>', unsafe_allow_html=True)

st.markdown("#### 📎 Comprobante de Pago")
proof_file = st.file_uploader(
    "Subí tu comprobante de pago (opcional)",
    type=["jpg", "png", "pdf"]
)

order_notes = st.text_area(
    "Notas para el vendedor",
    placeholder="Algún comentario especial sobre tu pedido..."
)

col_confirm1, col_confirm2 = st.columns(2)

with col_confirm1:
    if st.button("✅ CONFIRMAR PEDIDO", key="btn_confirm", use_container_width=True):
        # armamos items con product_id robusto
        payload_items = []
        for it in items:
            prod = it.get("product") or it.get("producto") or it
            pid = (
                it.get("product_id")
                or prod.get("id")
                or prod.get("_id")
            )
            qty = int(it.get("quantity", it.get("qty", 1)) or 1)
            payload_items.append({"product_id": pid, "quantity": qty})

        payload = {
            "payment_method": payment_method_backend,
            "currency": currency,
            "shipping": {
                "name": shipping_name,
                "address": shipping_address,
                "phone": shipping_phone,
                "notes": shipping_notes,
            },
            "notes": order_notes,
            "items": payload_items,
        }

        resp = api_post_checkout(payload)

        if resp is None:
            st.stop()

        compra_txt = resumen_compra(items)

        if resp.status_code in (200, 201):
            data_resp = resp.json()
            order_id = data_resp.get("order_id", data_resp.get("id", ""))

            nombres = []
            for it in items:
                prod = it.get("product") or it.get("producto") or it
                nombres.append(prod.get("name", "Producto"))

            # ✅ MENSAJE QUE QUERÍAS
            st.success(
                "✅ **Compra realizada**\n\n"
                f"🧾 Orden: **{order_id}**\n\n"
                "Compraste: " + ", ".join(nombres) + "\n\n"
                "📌 Pasamos a la **verificación** (admin y vendedor)."
            )
            st.balloons()

            # opcional: guardar número de orden en sesión
            st.session_state["last_order_id"] = order_id

        elif resp.status_code in (400, 422):
            try:
                detail = resp.json().get("detail", "Error de validación en el pedido.")
            except Exception:
                detail = "Error de validación en el pedido."
            st.error(f"No se pudo confirmar el pedido: {detail}")

        else:
            # 500 u otros -> igual mostramos compra + verificación
            st.warning(
                f"🛍️ **Has comprado:** {compra_txt}\n\n"
                "⚠️ **Tu pedido quedó en proceso de verificación.**\n"
                "El administrador y el vendedor van a validar el pago para liberar el producto."
            )
            st.caption(f"(Detalle técnico: {resp.text[:200]})")

with col_confirm2:
    if st.button("⬅️ VOLVER AL CARRITO", key="btn_back", use_container_width=True):
        try:
            st.switch_page("pages/4_Mi_Carrito.py")
        except Exception:
            st.info("Volvé al carrito desde el menú lateral.")

st.markdown("</div>", unsafe_allow_html=True)

# Información de contacto
with st.expander("📞 CONTACTO Y AYUDA"):
    st.markdown("""
    **¿Necesitás ayuda con tu compra?**
    
    📧 Email: soporte@ecommktlab.com  
    📞 Teléfono: +54 11 1234-5678  
    💬 WhatsApp: +54 9 11 8765-4321  
    
    **Horarios de atención:**  
    Lunes a Viernes: 9:00 - 18:00  
    Sábados: 9:00 - 13:00
    """)

