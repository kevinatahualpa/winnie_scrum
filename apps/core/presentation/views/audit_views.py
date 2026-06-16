from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from apps.core.infrastructure.models.models import AuditLog
from apps.core.domain.services.permission_service import (
    can_view_audit_log, can_view_all_audit_log,
)


@login_required
def ver_auditoria(request):
    """Render the audit log view.

    - super-admin: sees all 100 most recent entries (global view).
    - admin: sees only their own actions (last 100).
    - others: redirected.
    """
    if not can_view_audit_log(request.user):
        messages.error(request, 'No tienes permiso para ver el audit log')
        return redirect('ver_dashboard')

    qs = AuditLog.objects.select_related('user').order_by('-created_at')
    if not can_view_all_audit_log(request.user):
        qs = qs.filter(user=request.user)
    logs = qs[:100]

    return render(request, 'core/audit.html', {
        'logs': logs,
        'scope': 'global' if can_view_all_audit_log(request.user) else 'own',
    })
