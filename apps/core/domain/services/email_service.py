"""Servicio de envio de email reutilizable.

Usa la API HTTP de Resend (puerto 443) en produccion porque algunos hosts
(ej. Railway) bloquean SMTP. En desarrollo, si no hay RESEND_API_KEY,
cae al backend de consola de Django (imprime el correo).

Es best-effort: nunca lanza excepcion al caller para no romper el request.
"""

import logging
import os

import requests
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_email(subject, message, recipient_list, from_email=None):
    """Envia un email de texto plano. Retorna True si se intento con exito."""
    if not recipient_list:
        return False

    from_email = from_email or getattr(settings, 'DEFAULT_FROM_EMAIL', 'Winnie <noreply@resend.dev>')
    api_key = os.getenv('RESEND_API_KEY')

    if api_key:
        try:
            resp = requests.post(
                'https://api.resend.com/emails',
                json={
                    'from': from_email,
                    'to': recipient_list,
                    'subject': subject,
                    'text': message,
                },
                headers={'Authorization': f'Bearer {api_key}'},
                timeout=10,
            )
            if resp.status_code not in (200, 201):
                logger.warning(f'Resend API error {resp.status_code}: {resp.text}')
                return False
            return True
        except requests.RequestException as e:
            logger.warning(f'Error al enviar email via Resend API: {e}')
            return False

    # Sin API key: usa el backend configurado (consola en dev)
    try:
        send_mail(subject, message, from_email, recipient_list, fail_silently=True)
        return True
    except Exception as e:
        logger.warning(f'Error al enviar email via backend Django: {e}')
        return False
