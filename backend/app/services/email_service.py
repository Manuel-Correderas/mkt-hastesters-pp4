# backend/app/services/email_service.py
import os
import smtplib
from email.message import EmailMessage

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))   # 587 TLS, 465 SSL
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER)

def send_recovery_email(to_email: str, nombre: str, temp_password: str):
    """
    Envía mail de recuperación con contraseña temporal.
    Si falla el SMTP, NO rompe el endpoint (solo loguea).
    """
    try:
        msg = EmailMessage()
        msg["Subject"] = "Recuperación de contraseña - Ecom MKT Lab"
        msg["From"] = SMTP_FROM
        msg["To"] = to_email

        msg.set_content(
            f"Hola {nombre or ''}!\n\n"
            f"Tu contraseña temporal es: {temp_password}\n"
            f"Vence en 15 minutos.\n\n"
            f"Después de ingresar, cambiála desde tu perfil.\n"
        )

        # ----- conexión SMTP segura -----
        if SMTP_PORT == 465:
            # SSL directo
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=20) as server:
                server.login(SMTP_USER, SMTP_PASS)
                server.send_message(msg)
        else:
            # TLS (587 típico)
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(SMTP_USER, SMTP_PASS)
                server.send_message(msg)

    except Exception as e:
        # Importantísimo: que NO explote el ASGI
        print(f"[EMAIL] Error enviando recuperación a {to_email}: {e}")
