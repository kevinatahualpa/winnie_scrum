from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count
from django.views.decorators.http import require_http_methods, require_POST

from apps.core.infrastructure.models.models import Area, Project
from apps.core.domain.services.permission_service import get_user_role, can_manage_admin
from apps.core.presentation.forms import AreaForm


@login_required
def ver_areas(request):
    """Render the list of organizational areas.

    Admins see all areas with project counts. Jefe-area sees only their area.
    Jefe-proyecto/miembro see areas of projects they belong to.
    """
    user = request.user
    role = get_user_role(user)
    profile = getattr(user, 'profile', None)

    if role == 'jefe-area' and profile and profile.area:
        areas = Area.objects.filter(id=profile.area.id)
    elif role in ('jefe-proyecto', 'miembro'):
        areas = Area.objects.filter(Q(projects__lead=user) | Q(projects__members=user)).distinct()
    else:
        areas = Area.objects.annotate(project_count=Count('projects')).order_by('code')

    return render(request, 'core/areas.html', {'areas': areas})


@require_http_methods(["GET", "POST"])
@login_required
def crear_area(request):
    if not can_manage_admin(request.user):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Sin permiso'}, status=403)
        messages.error(request, 'No tienes permiso para crear areas')
        return redirect('ver_areas')

    if request.method == 'POST':
        form = AreaForm(request.POST)
        if form.is_valid():
            area = form.save()
            from apps.core.domain.services.notification_service import create_audit_log
            create_audit_log(request.user, 'AREA_CREATE', 'area', area.id, f'Area creada: {area.name}')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'object': {'id': area.id, 'name': area.name, 'code': area.code, 'color': area.color, 'description': area.description, 'status': area.status, 'project_count': 0}})
            messages.success(request, f'Area "{area.name}" creada')
            return redirect('ver_areas')
        elif request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    else:
        form = AreaForm()

    return render(request, 'core/area_form.html', {'form': form})


@require_http_methods(["GET", "POST"])
@login_required
def editar_area(request, pk):
    area = get_object_or_404(Area, pk=pk)

    if not can_manage_admin(request.user):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Sin permiso'}, status=403)
        messages.error(request, 'No tienes permiso para editar areas')
        return redirect('ver_areas')

    if request.method == 'POST':
        form = AreaForm(request.POST, instance=area)
        if form.is_valid():
            form.save()
            from apps.core.domain.services.notification_service import create_audit_log
            create_audit_log(request.user, 'AREA_EDIT', 'area', area.id, f'Area editada: {area.name}')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'object': {'id': area.id, 'name': area.name, 'code': area.code, 'color': area.color, 'description': area.description, 'status': area.status, 'project_count': getattr(area, 'project_count', 0)}})
            messages.success(request, f'Area "{area.name}" actualizada')
            return redirect('ver_areas')
        elif request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    else:
        form = AreaForm(instance=area)

    return render(request, 'core/area_form.html', {'form': form, 'area': area})


@require_POST
@login_required
def eliminar_area(request, pk):
    """Soft delete an area (mark as inactive). Requires admin role.

    El area no se elimina fisicamente para preservar el historial
    de proyectos y usuarios que la referencian.
    """
    area = get_object_or_404(Area, pk=pk)

    if not can_manage_admin(request.user):
        messages.error(request, 'No tienes permiso para eliminar areas')
        return redirect('ver_areas')

    name = area.name
    area.status = 'inactive'
    area.save(update_fields=['status'])

    from apps.core.domain.services.notification_service import create_audit_log
    create_audit_log(request.user, 'AREA_ARCHIVE', 'area', pk, f'Area archivada: {name}')
    messages.success(request, f'Area "{name}" archivada')
    return redirect('ver_areas')
