# streamlit_app/pages/0b_Términos_y_Privacidad.py
import streamlit as st

st.set_page_config(page_title="Términos y Privacidad – Ecom MKT Lab", layout="centered")

# ---------- estilos ----------
st.markdown("""
<style>
/* fondo app */
.stApp { background:#FF8C00; }

/* contenedor “panel” con sombra suave, sin cajas blancas internas */
.panel{
  background: rgba(0,0,0,0.00); /* transparente para no sumar otro bloque */
  border-radius:12px;
  padding:18px;
}

/* título */
.hdr{
  font-size:1.25rem;
  font-weight:900;
  color:#1f2e5e;
  margin-bottom:10px;
  text-align:center;
}

/* área scrolleable SIN fondo blanco ni borde */
.scroll{
  max-height: 75vh;             /* un toque más alto ya que no hay botones */
  overflow-y: auto;
  background: transparent;      /* sin caja blanca */
  color:#10203a;                /* texto legible sobre naranja */
  border: none;                 /* sin borde */
  padding: 0;                   /* sin padding extra */
  font-size: 1rem;
  line-height: 1.5;
}

/* scrollbar discreto */
.scroll::-webkit-scrollbar { width: 8px; }
.scroll::-webkit-scrollbar-thumb {
  background: rgba(0,0,0,.25);
  border-radius: 8px;
}
.scroll::-webkit-scrollbar-track { background: transparent; }
</style>
""", unsafe_allow_html=True)

c = st.columns([1, 2, 1])[1]
with c:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown(
        '<div class="hdr">📄 Términos de Uso y Privacidad – Ecom MKT Lab</div>',
        unsafe_allow_html=True
    )

    # ---------- texto ----------
    st.markdown('<div class="scroll">', unsafe_allow_html=True)
    st.markdown("""
**1. Aceptación**  
Al registrarse y utilizar la plataforma, el usuario (comprador o vendedor) acepta estos Términos de Uso y la Política de Privacidad.

**2. Registro de usuarios**  
• Deben consignar datos verdaderos (nombre, documento, correo, teléfono).  
• El vendedor podrá adjuntar documentación adicional para verificar identidad (DNI/CUIT, comprobantes, CBU/alias, wallet).  
• Cada usuario es responsable de la confidencialidad de sus credenciales.

**3. Uso de la plataforma**  
• Los compradores pueden explorar productos, agregarlos al carrito y realizar pedidos.  
• Los vendedores pueden publicar y gestionar productos, stock y precios, y ver su historial de ventas.  
• Está prohibido el uso fraudulento o ilícito, o que afecte a terceros.

**4. Pagos y transacciones**  
• Los pagos se efectúan mediante integraciones externas (p.ej. Mercado Pago / transferencias / cripto).  
• Ecom MKT Lab **no almacena** datos sensibles de tarjetas ni credenciales bancarias.  
• Cada transacción genera un comprobante asociado a la orden.  
• Pueden aplicarse **comisiones** de servicio y de pasarela.

**5. Protección de datos personales**  
• Tratamos los datos con fines de autenticación, operación del servicio y prevención de fraude.  
• El acceso está restringido al personal autorizado.

**6. Documentación KYC**  
• El material aportado por vendedores se utiliza únicamente para verificación interna y cumplimiento legal.  
• Ecom MKT Lab puede solicitar documentación adicional si lo requiere la normativa vigente.

**7. Derechos de los usuarios**  
• Podrán solicitar rectificación o eliminación de su cuenta mediante el canal de soporte.  
• Pueden cerrar su cuenta en cualquier momento.

**8. Responsabilidades**  
• Ecom MKT Lab no garantiza disponibilidad continua del servicio.  
• Los vendedores son responsables de la veracidad de sus publicaciones.  
• Los compradores son responsables de revisar totales/costos antes de pagar.

**9. Modificaciones**  
• Ecom MKT Lab puede modificar estos términos notificando a los usuarios en la plataforma.
""")
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
