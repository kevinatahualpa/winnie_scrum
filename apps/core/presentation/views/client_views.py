import json
import secrets
import string

from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Count, Sum
from django.views.decorators.http import require_http_methods, require_POST
from django.utils import timezone

from apps.core.infrastructure.models.models import Client, Project, UserProfile
from apps.core.domain.services.permission_service import get_user_role, can_manage_admin
from apps.core.domain.services.notification_service import create_audit_log
from apps.core.presentation.forms import ClientForm


@login_required
def ver_clientes(request):
    """Render the list of clients. Admins see all; others see clients of their projects."""
    user = request.user
    role = get_user_role(user)

    if role in ('jefe-proyecto', 'miembro'):
        clients_list = Client.active.filter(Q(projects__lead=user) | Q(projects__members=user)).distinct()
    else:
        clients_list = Client.active.prefetch_related('projects').order_by('name')

    return render(request, 'core/clients.html', {'clients': clients_list})


@require_http_methods(["GET", "POST"])
@login_required
def crear_cliente(request):
    if not can_manage_admin(request.user):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Sin permiso'}, status=403)
        messages.error(request, 'No tienes permiso para crear clientes')
        return redirect('ver_clientes')

    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save()
            from apps.core.domain.services.notification_service import create_audit_log
            create_audit_log(request.user, 'CLIENT_CREATE', 'client', client.id, f'Cliente creado: {client.name}')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'object': {'id': client.id, 'name': client.name, 'contact': client.contact, 'email': client.email, 'phone': client.phone, 'industry': client.industry}})
            messages.success(request, f'Cliente "{client.name}" creado')
            return redirect('ver_clientes')
        elif request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    else:
        form = ClientForm()

    return render(request, 'core/client_form.html', {'form': form})


@require_http_methods(["GET", "POST"])
@login_required
def editar_cliente(request, pk):
    client = get_object_or_404(Client, pk=pk)

    if not can_manage_admin(request.user):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Sin permiso'}, status=403)
        messages.error(request, 'No tienes permiso para editar clientes')
        return redirect('ver_clientes')

    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            from apps.core.domain.services.notification_service import create_audit_log
            create_audit_log(request.user, 'CLIENT_EDIT', 'client', client.id, f'Cliente editado: {client.name}')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'object': {'id': client.id, 'name': client.name, 'contact': client.contact, 'email': client.email, 'phone': client.phone, 'industry': client.industry}})
            messages.success(request, f'Cliente "{client.name}" actualizado')
            return redirect('ver_clientes')
        elif request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    else:
        form = ClientForm(instance=client)

    return render(request, 'core/client_form.html', {'form': form, 'client': client})


@require_POST
@login_required
def eliminar_cliente(request, pk):
    """Soft delete a client (mark as inactive). Requires admin role.

    El cliente no se elimina fisicamente: se preserva el historial de
    proyectos y solicitudes de servicio asociados.
    """
    client = get_object_or_404(Client, pk=pk)

    if not can_manage_admin(request.user):
        messages.error(request, 'No tienes permiso para eliminar clientes')
        return redirect('ver_clientes')

    name = client.name
    client.is_active = False
    client.save(update_fields=['is_active'])

    from apps.core.domain.services.notification_service import create_audit_log
    create_audit_log(request.user, 'CLIENT_ARCHIVE', 'client', pk, f'Cliente archivado: {name}')
    messages.success(request, f'Cliente "{name}" archivado')
    return redirect('ver_clientes')


# ---------------------------------------------------------------------------
# Detalle de cliente + gestion de usuarios
# ---------------------------------------------------------------------------

def _generate_random_password(length: int = 12) -> str:
    """Genera un password aleatorio seguro (letras + digitos)."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


@login_required
def client_detail(request, pk):
    """Muestra el detalle de un cliente: datos, usuarios y proyectos."""
    if not can_manage_admin(request.user):
        messages.error(request, 'No tienes permiso para ver este cliente')
        return redirect('ver_clientes')

    client = get_object_or_404(Client, pk=pk)
    users = UserProfile.objects.filter(
        client=client, role='cliente',
    ).select_related('user').order_by('user__first_name', 'user__last_name')

    projects = Project.objects.filter(client=client).select_related(
        'area', 'lead', 'lead__profile',
    ).order_by('-created_at')

    return render(request, 'core/client_detail.html', {
        'client': client,
        'client_users': users,
        'projects': projects,
    })


@require_http_methods(["GET", "POST"])
@login_required
def client_create_user(request, pk):
    """Crea un usuario con role='cliente' asociado a este cliente.

    El admin puede elegir el password o dejar que se genere uno aleatorio.
    El password generado se muestra UNA vez en pantalla (no se puede
    recuperar despues porque Django lo hashea).
    """
    if not can_manage_admin(request.user):
        messages.error(request, 'No tienes permiso para crear usuarios cliente')
        return redirect('ver_clientes')

    client = get_object_or_404(Client, pk=pk)
    generated_password = None

    if request.method == 'POST':
        first_name = (request.POST.get('first_name') or '').strip()
        last_name = (request.POST.get('last_name') or '').strip()
        email = (request.POST.get('email') or '').strip().lower()
        password = request.POST.get('password') or ''

        errors = []
        if not first_name:
            errors.append('El nombre es obligatorio.')
        if not last_name:
            errors.append('El apellido es obligatorio.')
        if not email or '@' not in email:
            errors.append('Email invalido.')
        elif User.objects.filter(username=email).exists():
            errors.append(f'Ya existe un usuario con el email "{email}".')

        if not password:
            password = _generate_random_password()
            generated_password = password

        if len(password) < 6:
            errors.append('La contrasena debe tener al menos 6 caracteres.')

        if not client:
            errors.append('El cliente es obligatorio para crear un usuario cliente.')

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'core/client_create_user.html', {
                'client': client,
                'form_data': request.POST,
            })

        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=password,
                )
                UserProfile.objects.create(
                    user=user,
                    role='cliente',
                    status='active',
                    client=client,
                )
                create_audit_log(
                    request.user, 'CLIENT_USER_CREATE', 'user', user.id,
                    f'Usuario cliente creado: {user.get_full_name()} ({email}) para {client.name}',
                )
        except Exception as e:
            messages.error(request, f'Error al crear el usuario: {e}')
            return render(request, 'core/client_create_user.html', {
                'client': client,
                'form_data': request.POST,
            })

        if generated_password:
            messages.success(
                request,
                f'Usuario {user.get_full_name()} creado. La contrasena es: '
                f'{generated_password} (mostrada solo una vez, copiala ahora).',
            )
        else:
            messages.success(
                request,
                f'Usuario {user.get_full_name()} creado correctamente.',
            )
        return redirect('client_detail', pk=client.pk)

    return render(request, 'core/client_create_user.html', {
        'client': client,
        'form_data': {},
    })


@require_POST
@login_required
def client_reset_password(request, pk, user_id):
    """Resetea el password de un usuario cliente. Solo admin."""
    if not can_manage_admin(request.user):
        messages.error(request, 'No tienes permiso para resetear contrasenas')
        return redirect('ver_clientes')

    client = get_object_or_404(Client, pk=pk)
    profile = get_object_or_404(
        UserProfile, pk=user_id, client=client, role='cliente',
    )

    new_password = _generate_random_password()
    profile.user.set_password(new_password)
    profile.user.save(update_fields=['password'])

    create_audit_log(
        request.user, 'CLIENT_USER_RESET_PW', 'user', profile.user.id,
        f'Password reseteado para {profile.user.get_full_name()} ({client.name})',
    )

    messages.success(
        request,
        f'Nueva contrasena para {profile.user.get_full_name()}: '
        f'{new_password} (mostrada solo una vez, copiala ahora).',
    )
    return redirect('client_detail', pk=client.pk)
