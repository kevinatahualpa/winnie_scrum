"""Recuperacion de contrasena olvidada (flujo publico con token).

Usa el generador de tokens seguro de Django (sin modelos extra). El enlace
de reseteo caduca automaticamente cuando cambia la contrasena o pasa el
tiempo configurado en PASSWORD_RESET_TIMEOUT.
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from apps.core.domain.services.email_service import send_email
from apps.core.domain.services.notification_service import create_audit_log


def recuperar_password(request):
    """Recibe el email del panel 'Olvidaste tu contrasena' y envia el enlace.

    Siempre responde con exito generico para no revelar que emails existen.
    """
    if request.method != 'POST':
        return redirect('iniciar_sesion')

    email = (request.POST.get('email') or '').strip().lower()
    generic = ('Si el email existe, te enviamos un enlace para restablecer '
               'tu contrasena. Revisa tu bandeja.')

    if email:
        user = User.objects.filter(username__iexact=email, is_active=True).first()
        if user and getattr(user, 'email', ''):
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = request.build_absolute_uri(
                reverse('resetear_password', kwargs={'uidb64': uid, 'token': token})
            )
            subject = 'Winnie · Restablecer tu contrasena'
            message = (
                f'Hola {user.get_full_name() or user.username},\n\n'
                'Recibimos una solicitud para restablecer tu contrasena en Winnie.\n\n'
                'Abre el siguiente enlace para elegir una nueva contrasena:\n\n'
                f'{reset_url}\n\n'
                'Si no solicitaste esto, ignora este mensaje; tu contrasena no cambiara.\n\n'
                'Equipo Winnie'
            )
            send_email(subject=subject, message=message, recipient_list=[user.email])

    messages.success(request, generic)
    return redirect('iniciar_sesion')


def _get_user_from_uid(uidb64):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        return User.objects.filter(pk=uid).first()
    except (TypeError, ValueError, OverflowError):
        return None


def resetear_password(request, uidb64, token):
    """Valida el token y permite establecer una nueva contrasena."""
    user = _get_user_from_uid(uidb64)
    valid = user is not None and default_token_generator.check_token(user, token)

    if not valid:
        messages.error(request, 'El enlace de restablecimiento no es valido o expiro. Solicita uno nuevo.')
        return redirect('iniciar_sesion')

    if request.method == 'POST':
        new1 = request.POST.get('new_password1', '')
        new2 = request.POST.get('new_password2', '')
        if new1 != new2:
            messages.error(request, 'Las contrasenas no coinciden')
            return render(request, 'core/reset_password.html', {'valid': True})
        try:
            validate_password(new1, user)
        except ValidationError as e:
            messages.error(request, ' '.join(e.messages))
            return render(request, 'core/reset_password.html', {'valid': True})

        user.set_password(new1)
        user.save()
        create_audit_log(user, 'PASSWORD_RESET', 'user', details='Contrasena restablecida via email')
        if getattr(user, 'email', ''):
            send_email(
                subject='Winnie · Tu contrasena fue cambiada',
                message=(
                    f'Hola {user.get_full_name() or user.username},\n\n'
                    'Tu contrasena de Winnie se cambio correctamente.\n\n'
                    'Si no fuiste tu, contacta a un administrador de inmediato.\n\n'
                    'Equipo Winnie'
                ),
                recipient_list=[user.email],
            )
        messages.success(request, 'Contrasena restablecida. Ya puedes iniciar sesion.')
        return redirect('iniciar_sesion')

    return render(request, 'core/reset_password.html', {'valid': True})
