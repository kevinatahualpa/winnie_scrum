from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from apps.core.infrastructure.models.models import User, Project, Task, Sprint, Area, Specialty, Technology, Client, AuditLog
from apps.core.domain.services.permission_service import can_view_settings


@login_required
def ver_configuracion(request):
    """Render the system settings page. Restricted to super-admin role only.

    Displays aggregate counts of all system entities for administrative overview.
    """
    if not can_view_settings(request.user):
        messages.error(request, 'No tienes permiso para ver esta pagina')
        return redirect('ver_dashboard')

    context = {
        'total_users': User.objects.count(),
        'total_projects': Project.objects.count(),
        'total_tasks': Task.objects.count(),
        'total_sprints': Sprint.objects.count(),
        'total_areas': Area.objects.count(),
        'total_specialties': Specialty.active.count(),
        'total_technologies': Technology.objects.filter(is_active=True).count(),
        'total_clients': Client.active.count(),
        'total_audit_logs': AuditLog.objects.count(),
    }
    return render(request, 'core/settings.html', context)
