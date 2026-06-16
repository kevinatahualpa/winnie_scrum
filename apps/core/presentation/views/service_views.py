from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods, require_POST

from apps.core.infrastructure.models.models import ServiceRequest, Client, User
from apps.core.domain.services.permission_service import get_user_role, can_manage_area
from apps.core.presentation.forms import ServiceRequestForm


@login_required
def ver_servicios(request):
    """Render the service requests list. Admins see all; others see only assigned requests."""
    user = request.user
    role = get_user_role(user)

    requests = ServiceRequest.objects.select_related('assigned_to').order_by('-created_at')
    if role in ('jefe-proyecto', 'miembro'):
        requests = requests.filter(assigned_to=user)

    return render(request, 'core/services.html', {'service_requests': requests})


@require_http_methods(["GET", "POST"])
@login_required
def crear_servicio(request):
    """Create a new service request. Requires area management permission."""
    if not can_manage_area(request.user):
        messages.error(request, 'No tienes permiso para crear solicitudes')
        return redirect('ver_servicios')

    if request.method == 'POST':
        form = ServiceRequestForm(request.POST)
        if form.is_valid():
            sr = form.save()
            from apps.core.domain.services.notification_service import create_audit_log
            create_audit_log(request.user, 'SERVICE_REQUEST', 'service_request', sr.id,
                            f'Solicitud de servicio: {sr.client.name if sr.client else "N/A"}')
            messages.success(request, 'Solicitud de servicio creada')
            return redirect('ver_servicios')
    else:
        form = ServiceRequestForm()

    return render(request, 'core/service_form.html', {'form': form})


@require_http_methods(["GET", "POST"])
@login_required
def editar_servicio(request, pk):
    """Update a service request (status, assignment). Requires area management permission.

    Notifies the newly assigned user when assignment changes.
    """
    sr = get_object_or_404(ServiceRequest, pk=pk)

    if not can_manage_area(request.user):
        messages.error(request, 'No tienes permiso para editar solicitudes')
        return redirect('ver_servicios')

    if request.method == 'POST':
        old_assigned_id = sr.assigned_to_id
        form = ServiceRequestForm(request.POST, instance=sr)
        if form.is_valid():
            form.save()
            from apps.core.domain.services.notification_service import create_audit_log, notify_service_assignment
            create_audit_log(request.user, 'SERVICE_STATUS', 'service_request', sr.id,
                            f'Estado actualizado: {sr.get_status_display()}')

            if sr.assigned_to_id and sr.assigned_to_id != old_assigned_id:
                assigned = User.objects.get(id=sr.assigned_to_id)
                notify_service_assignment(sr, request.user, assigned)

            messages.success(request, 'Solicitud actualizada')
            return redirect('ver_servicios')
    else:
        form = ServiceRequestForm(instance=sr)

    return render(request, 'core/service_form.html', {'form': form, 'service_request': sr})


@require_POST
@login_required
def eliminar_servicio(request, pk):
    """Delete a service request. Requires area management permission."""
    sr = get_object_or_404(ServiceRequest, pk=pk)

    if not can_manage_area(request.user):
        messages.error(request, 'No tienes permiso para eliminar solicitudes')
        return redirect('ver_servicios')

    sr.delete()
    messages.success(request, 'Solicitud eliminada')
    return redirect('ver_servicios')
