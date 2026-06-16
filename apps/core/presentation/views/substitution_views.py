from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods, require_POST

from apps.core.infrastructure.models.models import Substitution, User
from apps.core.domain.services.permission_service import get_user_role
from apps.core.presentation.forms import SubstitutionForm


@login_required
def ver_suplencias(request):
    """Render the substitutions management page. Restricted to admin/jefe-area roles.

    Shows active and past substitutions (last 10) with user details.
    """
    role = get_user_role(request.user)
    if role not in ('super-admin', 'admin', 'jefe-area'):
        messages.error(request, 'No tienes permiso para gestionar suplencias')
        return redirect('ver_dashboard')

    all_subs = Substitution.objects.select_related('original_user', 'substitute_user').order_by('-start_date')
    active_subs = [s for s in all_subs if s.is_current]
    past_subs = [s for s in all_subs if not s.is_current]

    return render(request, 'core/substitutions.html', {
        'active_subs': active_subs, 'past_subs': past_subs[:10],
    })


@require_http_methods(["GET", "POST"])
@login_required
def crear_suplencia(request):
    """Create a new substitution (one user covering for another). Admin/jefe-area only.

    GET: Render the substitution creation form with active users.
    POST: Create substitution record and audit log entry.
    """
    role = get_user_role(request.user)
    if role not in ('super-admin', 'admin', 'jefe-area'):
        messages.error(request, 'No tienes permiso para crear suplencias')
        return redirect('ver_dashboard')

    if request.method == 'POST':
        form = SubstitutionForm(request.POST)
        if form.is_valid():
            sub = form.save()
            from apps.core.domain.services.notification_service import create_audit_log
            create_audit_log(request.user, 'SUBSTITUTION_CREATE', 'substitution',
                            sub.id, f'{sub.substitute_user} suple a {sub.original_user}')
            messages.success(request, f'Suplencia creada: {sub.substitute_user.get_full_name()} suple a {sub.original_user.get_full_name()}')
            return redirect('ver_suplencias')
    else:
        form = SubstitutionForm()

    return render(request, 'core/substitution_form.html', {'form': form})


@require_POST
@login_required
def desactivar_suplencia(request, pk):
    """Deactivate an active substitution. Admin/jefe-area only."""
    role = get_user_role(request.user)
    if role not in ('super-admin', 'admin', 'jefe-area'):
        messages.error(request, 'No tienes permiso')
        return redirect('ver_suplencias')

    sub = get_object_or_404(Substitution, pk=pk)
    sub.active = False
    sub.save()

    from apps.core.domain.services.notification_service import create_audit_log
    create_audit_log(request.user, 'SUBSTITUTION_DEACTIVATE', 'substitution', pk, 'Suplencia desactivada')

    messages.success(request, 'Suplencia desactivada')
    return redirect('ver_suplencias')
