from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods, require_POST

from apps.core.infrastructure.models.models import Specialty
from apps.core.domain.services.permission_service import can_manage_admin
from apps.core.presentation.forms import SpecialtyForm


@login_required
def ver_especialidades(request):
    """Render the list of active specialties ordered by category and name.

    Por defecto no muestra especialidades archivadas (is_active=False).
    Use ?archived=1 para ver archivadas (solo admins).
    """
    show_archived = request.GET.get('archived') == '1'
    qs = Specialty.active.order_by('category', 'name')
    if not show_archived:
        qs = qs.filter(is_active=True)
    return render(request, 'core/specialties.html', {
        'specialties': qs,
        'show_archived': show_archived,
    })


@require_http_methods(["GET", "POST"])
@login_required
def crear_especialidad(request):
    """Create a new specialty. Requires admin role."""
    if not can_manage_admin(request.user):
        messages.error(request, 'No tienes permiso para crear especialidades')
        return redirect('ver_especialidades')

    if request.method == 'POST':
        form = SpecialtyForm(request.POST)
        if form.is_valid():
            specialty = form.save()
            from apps.core.domain.services.notification_service import create_audit_log
            create_audit_log(request.user, 'SPECIALTY_CREATE', 'specialty', specialty.id, f'Especialidad creada: {specialty.name}')
            messages.success(request, f'Especialidad "{specialty.name}" creada')
            return redirect('ver_especialidades')
    else:
        form = SpecialtyForm()

    return render(request, 'core/specialty_form.html', {'form': form})


@require_http_methods(["GET", "POST"])
@login_required
def editar_especialidad(request, pk):
    """Update an existing specialty. Requires admin role."""
    specialty = get_object_or_404(Specialty, pk=pk)

    if not can_manage_admin(request.user):
        messages.error(request, 'No tienes permiso para editar especialidades')
        return redirect('ver_especialidades')

    if request.method == 'POST':
        form = SpecialtyForm(request.POST, instance=specialty)
        if form.is_valid():
            form.save()
            from apps.core.domain.services.notification_service import create_audit_log
            create_audit_log(request.user, 'SPECIALTY_EDIT', 'specialty', specialty.id, f'Especialidad editada: {specialty.name}')
            messages.success(request, f'Especialidad "{specialty.name}" actualizada')
            return redirect('ver_especialidades')
    else:
        form = SpecialtyForm(instance=specialty)

    return render(request, 'core/specialty_form.html', {'form': form, 'specialty': specialty})


@require_POST
@login_required
def eliminar_especialidad(request, pk):
    """Soft delete a specialty (mark as inactive). Requires admin role.

    La especialidad no se elimina fisicamente: usuarios que la
    referencian en su perfil mantienen la asociacion visible.
    """
    specialty = get_object_or_404(Specialty, pk=pk)

    if not can_manage_admin(request.user):
        messages.error(request, 'No tienes permiso para eliminar especialidades')
        return redirect('ver_especialidades')

    name = specialty.name
    specialty.is_active = False
    specialty.save(update_fields=['is_active'])

    from apps.core.domain.services.notification_service import create_audit_log
    create_audit_log(request.user, 'SPECIALTY_ARCHIVE', 'specialty', pk, f'Especialidad archivada: {name}')
    messages.success(request, f'Especialidad "{name}" archivada')
    return redirect('ver_especialidades')
