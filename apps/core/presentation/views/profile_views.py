from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from apps.core.domain.services.email_service import send_email
from apps.core.presentation.upload_validators import (
    validate_upload, IMAGE_EXTENSIONS, MB,
)


@login_required
def ver_perfil(request):
    """Perfil / cuenta del usuario actual.

    Maneja tres acciones via el campo POST 'action':
      - 'avatar':   subir foto de perfil
      - 'profile':  editar nombre, apellido y telefono
      - 'password': cambiar contrasena
    """
    user = request.user
    profile = getattr(user, 'profile', None)

    if request.method == 'POST':
        action = request.POST.get('action', 'avatar')

        if action == 'avatar' and profile:
            avatar = request.FILES.get('avatar')
            if avatar:
                error = validate_upload(avatar, max_bytes=2 * MB, allowed_extensions=IMAGE_EXTENSIONS)
                if error:
                    messages.error(request, error)
                    return redirect('ver_perfil')
                profile.avatar = avatar
                profile.save()
                messages.success(request, 'Foto de perfil actualizada')
            return redirect('ver_perfil')

        if action == 'profile':
            user.first_name = request.POST.get('first_name', '').strip()
            user.last_name = request.POST.get('last_name', '').strip()
            user.save(update_fields=['first_name', 'last_name'])
            if profile:
                profile.phone = request.POST.get('phone', '').strip()
                profile.save(update_fields=['phone'])
            messages.success(request, 'Datos actualizados')
            return redirect('ver_perfil')

        if action == 'password':
            current = request.POST.get('current_password', '')
            new1 = request.POST.get('new_password1', '')
            new2 = request.POST.get('new_password2', '')

            if not user.check_password(current):
                messages.error(request, 'La contrasena actual es incorrecta')
            elif new1 != new2:
                messages.error(request, 'Las contrasenas nuevas no coinciden')
            else:
                try:
                    validate_password(new1, user)
                except ValidationError as e:
                    messages.error(request, ' '.join(e.messages))
                else:
                    user.set_password(new1)
                    user.save()
                    update_session_auth_hash(request, user)
                    if user.email:
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
                    messages.success(request, 'Contrasena actualizada')
            return redirect('ver_perfil')

    return render(request, 'core/profile.html', {'profile': profile})
