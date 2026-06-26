from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from apps.core.infrastructure.models.models import Area, Specialty, UserProfile
from apps.core.domain.services.notification_service import create_audit_log, create_notification
from apps.core.domain.services.permission_service import get_user_role
from apps.core.domain.services.user_service import UserService


def iniciar_sesion(request):
    """Handle user authentication via email/password.

    Checks account status (pending/dismissed) before allowing login.
    Creates audit log entry on successful authentication.
    Redirects 'cliente' role to the client portal instead of the main dashboard.
    """
    if request.user.is_authenticated:
        return redirect('ver_dashboard')
    if request.method == 'POST':
        email = (request.POST.get('email') or '').strip().lower()
        password = request.POST.get('password', '')
        if not email or not password:
            messages.error(request, 'Email y contrasena son obligatorios')
            return render(request, 'core/login.html')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            profile = getattr(user, 'profile', None)
            if profile and profile.status == 'pending':
                messages.error(request, 'Tu solicitud sera revisada por un administrador')
                return render(request, 'core/login.html')
            if profile and profile.status == 'dismissed':
                messages.error(request, 'Cuenta desactivada')
                return render(request, 'core/login.html')
            login(request, user)
            create_audit_log(user, 'LOGIN', 'user', details='Inicio de sesion exitoso')
            if profile and profile.role == 'cliente':
                return redirect('ver_portal_cliente')
            return redirect('ver_dashboard')
        messages.error(request, 'Credenciales incorrectas')
    return render(request, 'core/login.html')


@login_required
def cerrar_sesion(request):
    """Log out the current user and create an audit log entry."""
    create_audit_log(request.user, 'LOGOUT', 'user')
    logout(request)
    return redirect('iniciar_sesion')


def registrarse(request):
    """Solicitud publica de acceso al sistema.

    Esta vista NO registra usuarios como activos. Crea un User con
    UserProfile.status='pending'. Un administrador debe aprobar la
    solicitud y asignar rol, area y proyectos antes de que el usuario
    pueda iniciar sesion.

    Los 3 flujos de registro en el sistema son:
    1. /solicitar-acceso/  -> Cualquier persona solicita acceso (queda pending).
    2. /ver_usuarios/create/ -> Un admin registra a un miembro del equipo (queda active).
    3. /ver_usuarios/create/ -> Un admin registra a un cliente con rol=cliente (queda active).

    """
    if request.user.is_authenticated:
        return redirect('ver_dashboard')
    if request.method == 'POST':
        email = (request.POST.get('email') or '').strip().lower()
        password = request.POST.get('password', '')
        first_name = (request.POST.get('first_name') or '').strip()
        last_name = (request.POST.get('last_name') or '').strip()
        if not email or not password or len(password) < 8:
            messages.error(request, 'Email y contrasena (min 8 caracteres) son obligatorios')
            return render(request, 'core/login.html', {'show_register': True})
        if User.objects.filter(username=email).exists():
            messages.error(request, 'Email ya registrado')
            return render(request, 'core/login.html', {'show_register': True})
        user, error = UserService.self_register(
            email=email, first_name=first_name, last_name=last_name, password=password
        )
        if error:
            messages.error(request, error)
            return render(request, 'core/login.html', {'show_register': True})

        admins = User.objects.filter(profile__role__in=['super-admin', 'admin'], profile__status='active')
        for admin in admins:
            create_notification(
                admin, 'new_registration', 'Nueva solicitud de acceso',
                f'{user.get_full_name()} ({user.email}) solicito acceso y espera aprobacion',
                'fa-user-clock'
            )

        messages.success(
            request,
            'Tu solicitud fue enviada. Un administrador la revisara y te '
            'notificara por email cuando sea aprobada. No podras iniciar '
            'sesion hasta entonces.'
        )
        return redirect('iniciar_sesion')
    return render(request, 'core/login.html', {'show_register': True})
