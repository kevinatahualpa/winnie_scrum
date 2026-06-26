from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST

from apps.core.infrastructure.models.models import Technology
from apps.core.domain.services.permission_service import can_manage_admin
from apps.core.presentation.forms import TechnologyForm


@login_required
def ver_tecnologias(request):
    """Render the list of active technologies ordered by category and name.

    Por defecto no muestra tecnologias archivadas (is_active=False).
    Use ?archived=1 para ver archivadas (solo admins).
    """
    show_archived = request.GET.get('archived') == '1'
    if show_archived:
        qs = Technology.objects.all().order_by('category', 'name')
    else:
        qs = Technology.objects.filter(is_active=True).order_by('category', 'name')
    return render(request, 'core/technologies.html', {
        'technologies': qs,
        'show_archived': show_archived,
    })


@require_http_methods(["GET", "POST"])
@login_required
def crear_tecnologia(request):
    if not can_manage_admin(request.user):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Sin permiso'}, status=403)
        messages.error(request, 'No tienes permiso para crear tecnologias')
        return redirect('ver_tecnologias')

    if request.method == 'POST':
        form = TechnologyForm(request.POST)
        if form.is_valid():
            technology = form.save()
            from apps.core.domain.services.notification_service import create_audit_log
            create_audit_log(request.user, 'TECHNOLOGY_CREATE', 'technology', technology.id,
                             f'Tecnologia creada: {technology.name}')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'object': {'id': technology.id, 'name': technology.name, 'category': technology.category, 'category_display': technology.get_category_display(), 'color': technology.color}})
            messages.success(request, f'Tecnologia "{technology.name}" creada')
            return redirect('ver_tecnologias')
        elif request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    else:
        form = TechnologyForm()

    return render(request, 'core/technology_form.html', {'form': form})


@require_http_methods(["GET", "POST"])
@login_required
def editar_tecnologia(request, pk):
    technology = get_object_or_404(Technology, pk=pk)

    if not can_manage_admin(request.user):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Sin permiso'}, status=403)
        messages.error(request, 'No tienes permiso para editar tecnologias')
        return redirect('ver_tecnologias')

    if request.method == 'POST':
        form = TechnologyForm(request.POST, instance=technology)
        if form.is_valid():
            form.save()
            from apps.core.domain.services.notification_service import create_audit_log
            create_audit_log(request.user, 'TECHNOLOGY_EDIT', 'technology', technology.id,
                             f'Tecnologia editada: {technology.name}')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'object': {'id': technology.id, 'name': technology.name, 'category': technology.category, 'category_display': technology.get_category_display(), 'color': technology.color}})
            messages.success(request, f'Tecnologia "{technology.name}" actualizada')
            return redirect('ver_tecnologias')
        elif request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    else:
        form = TechnologyForm(instance=technology)

    return render(request, 'core/technology_form.html', {'form': form, 'technology': technology})


@require_POST
@login_required
def eliminar_tecnologia(request, pk):
    """Soft delete a technology (mark as inactive). Requires admin role.

    La tecnologia no se elimina fisicamente: candidatos que la
    referencian mantienen la asociacion visible.
    """
    technology = get_object_or_404(Technology, pk=pk)

    if not can_manage_admin(request.user):
        messages.error(request, 'No tienes permiso para eliminar tecnologias')
        return redirect('ver_tecnologias')

    name = technology.name
    technology.is_active = False
    technology.save(update_fields=['is_active'])

    from apps.core.domain.services.notification_service import create_audit_log
    create_audit_log(request.user, 'TECHNOLOGY_ARCHIVE', 'technology', pk,
                     f'Tecnologia archivada: {name}')
    messages.success(request, f'Tecnologia "{name}" archivada')
    return redirect('ver_tecnologias')
