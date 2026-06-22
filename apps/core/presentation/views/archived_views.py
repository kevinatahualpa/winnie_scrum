"""Vista unica de Archivados para empresa pequena (~20 personas).

Politica: cualquier admin+ ve todos los items archivados (soft deleted)
y puede restaurarlos. No hay purga automatica. Todo queda en audit log.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.timesince import timesince
from django.views.decorators.http import require_POST

from apps.core.domain.services.notification_service import create_audit_log
from apps.core.domain.services.permission_service import is_admin
from apps.core.infrastructure.models.models import (
    Area, AuditLog, Client, Document, Project, ServiceRequest, Specialty, Technology, User, UserProfile,
)


ARCHIVE_ACTIONS = {
    'project': ['PROJECT_CANCEL', 'PROJECT_ARCHIVE'],
    'area': ['AREA_ARCHIVE', 'AREA_INACTIVE'],
    'client': ['CLIENT_ARCHIVE'],
    'specialty': ['SPECIALTY_ARCHIVE'],
    'technology': ['TECHNOLOGY_ARCHIVE'],
    'service_request': ['SERVICE_CANCEL'],
    'document': ['DOCUMENT_ARCHIVE'],
    'user': ['USER_REJECT', 'USER_DEACTIVATE'],
}


def _can_restore(user):
    """Solo admin+ puede restaurar items archivados."""
    return is_admin(user)


def _archive_info(entity_type, entity_id):
    """Busca la ultima accion de archivado en audit log.

    Retorna tupla (user, timestamp) o (None, None) si no hay registro.
    """
    actions = ARCHIVE_ACTIONS.get(entity_type, [])
    if not actions:
        return None, None
    log = (
        AuditLog.objects
        .filter(entity=entity_type, entity_id=str(entity_id), action__in=actions)
        .select_related('user')
        .order_by('-created_at')
        .first()
    )
    if log:
        return log.user, log.created_at
    return None, None


@login_required
def ver_archivados(request):
    """Listado unificado de todos los items archivados del sistema.

    Muestra en una sola vista: proyectos cancelados, areas inactivas,
    clientes archivados, especialidades inactivas, solicitudes canceladas,
    documentos archivados, usuarios desactivados/rechazados.
    """
    if not _can_restore(request.user):
        messages.error(request, 'No tienes permiso para ver items archivados')
        return redirect('ver_dashboard')

    cancelled_projects = list(
        Project.objects.filter(status='cancelled')
        .select_related('area', 'lead').order_by('-created_at')
    )
    inactive_areas = list(
        Area.objects.filter(status='inactive').order_by('code')
    )
    archived_clients = list(
        Client.objects.filter(is_active=False).order_by('name')
    )
    inactive_specialties = list(
        Specialty.objects.filter(is_active=False).order_by('category', 'name')
    )
    inactive_technologies = list(
        Technology.objects.filter(is_active=False).order_by('category', 'name')
    )
    cancelled_service_requests = list(
        ServiceRequest.objects.filter(status='cancelled')
        .select_related('client', 'assigned_to').order_by('-created_at')
    )
    archived_documents = list(
        Document.objects.filter(is_active=False)
        .select_related('project', 'uploaded_by').order_by('-deleted_at')
    )
    dismissed_users = list(
        UserProfile.objects.filter(status__in=['dismissed', 'rejected'])
        .select_related('user', 'area', 'specialty').order_by('-created_at')
    )

    for p in cancelled_projects:
        user, ts = _archive_info('project', p.id)
        p.archived_by = user
        p.archived_at = ts
    for a in inactive_areas:
        user, ts = _archive_info('area', a.id)
        a.archived_by = user
        a.archived_at = ts
    for c in archived_clients:
        user, ts = _archive_info('client', c.id)
        c.archived_by = user
        c.archived_at = ts
    for s in inactive_specialties:
        user, ts = _archive_info('specialty', s.id)
        s.archived_by = user
        s.archived_at = ts
    for t in inactive_technologies:
        user, ts = _archive_info('technology', t.id)
        t.archived_by = user
        t.archived_at = ts
    for sr in cancelled_service_requests:
        user, ts = _archive_info('service_request', sr.id)
        sr.archived_by = user
        sr.archived_at = ts
    for d in archived_documents:
        user, ts = _archive_info('document', d.id)
        d.archived_by = user
        d.archived_at = ts or d.deleted_at
    for u in dismissed_users:
        user, ts = _archive_info('user', u.id)
        u.archived_by = user
        u.archived_at = ts

    context = {
        'cancelled_projects': cancelled_projects,
        'inactive_areas': inactive_areas,
        'archived_clients': archived_clients,
        'inactive_specialties': inactive_specialties,
        'inactive_technologies': inactive_technologies,
        'cancelled_service_requests': cancelled_service_requests,
        'archived_documents': archived_documents,
        'dismissed_users': dismissed_users,
    }

    total = sum(
        len(v) if hasattr(v, '__len__') else v.count()
        for v in context.values()
    )
    context['total_archived'] = total

    return render(request, 'core/archived.html', context)


def _require_double_confirm(request, tipo, obj_name):
    """Para items criticos, requiere confirmacion explicita via parametro.

    El template debe incluir un input donde el usuario escribe el nombre
    del item. Si no coincide, se rechaza el restore.
    """
    if tipo not in ('project', 'user'):
        return True
    typed = (request.POST.get('confirmacion') or '').strip()
    return typed == obj_name


@require_POST
@login_required
def restaurar(request, tipo, pk):
    """Accion generica para restaurar un item archivado.

    `tipo` indica la entidad: project, area, client, specialty,
    service_request, document, user.

    Para `project` y `user` requiere doble confirmacion: el usuario
    debe escribir el nombre exacto del item en el campo 'confirmacion'.
    """
    if not _can_restore(request.user):
        messages.error(request, 'No tienes permiso para restaurar')
        return redirect('ver_archivados')

    user = request.user

    if tipo == 'project':
        obj = Project.objects.filter(pk=pk, status='cancelled').first()
        if not obj:
            messages.error(request, 'Proyecto no encontrado o no archivado')
            return redirect('ver_archivados')
        if not _require_double_confirm(request, tipo, obj.name):
            messages.error(request, f'Confirmacion invalida. Debes escribir exactamente "{obj.name}" para restaurar este proyecto critico.')
            return redirect('ver_archivados')
        name = obj.name
        obj.status = 'planned'
        obj.save(update_fields=['status'])
        create_audit_log(user, 'PROJECT_RESTORE', 'project', pk, f'Proyecto restaurado: {name}')

    elif tipo == 'area':
        obj = Area.objects.filter(pk=pk, status='inactive').first()
        if not obj:
            messages.error(request, 'Area no encontrada o no archivada')
            return redirect('ver_archivados')
        name = obj.name
        obj.status = 'active'
        obj.save(update_fields=['status'])
        create_audit_log(user, 'AREA_RESTORE', 'area', pk, f'Area restaurada: {name}')

    elif tipo == 'client':
        obj = Client.objects.filter(pk=pk, is_active=False).first()
        if not obj:
            messages.error(request, 'Cliente no encontrado o no archivado')
            return redirect('ver_archivados')
        name = obj.name
        obj.is_active = True
        obj.save(update_fields=['is_active'])
        create_audit_log(user, 'CLIENT_RESTORE', 'client', pk, f'Cliente restaurado: {name}')

    elif tipo == 'specialty':
        obj = Specialty.objects.filter(pk=pk, is_active=False).first()
        if not obj:
            messages.error(request, 'Especialidad no encontrada o no archivada')
            return redirect('ver_archivados')
        name = obj.name
        obj.is_active = True
        obj.save(update_fields=['is_active'])
        create_audit_log(user, 'SPECIALTY_RESTORE', 'specialty', pk, f'Especialidad restaurada: {name}')

    elif tipo == 'technology':
        obj = Technology.objects.filter(pk=pk, is_active=False).first()
        if not obj:
            messages.error(request, 'Tecnologia no encontrada o no archivada')
            return redirect('ver_archivados')
        name = obj.name
        obj.is_active = True
        obj.save(update_fields=['is_active'])
        create_audit_log(user, 'TECHNOLOGY_RESTORE', 'technology', pk, f'Tecnologia restaurada: {name}')

    elif tipo == 'service_request':
        obj = ServiceRequest.objects.filter(pk=pk, status='cancelled').first()
        if not obj:
            messages.error(request, 'Solicitud no encontrada o no cancelada')
            return redirect('ver_archivados')
        obj.status = 'new'
        obj.save(update_fields=['status'])
        create_audit_log(user, 'SERVICE_RESTORE', 'service_request', pk,
                         f'Solicitud de servicio restaurada: {obj.get_service_display()}')

    elif tipo == 'document':
        obj = Document.objects.filter(pk=pk, is_active=False).first()
        if not obj:
            messages.error(request, 'Documento no encontrado o no archivado')
            return redirect('ver_archivados')
        obj.restore()
        create_audit_log(user, 'DOCUMENT_RESTORE', 'document', pk, f'Documento restaurado: {obj.name}')

    elif tipo == 'user':
        obj = UserProfile.objects.filter(pk=pk, status__in=['dismissed', 'rejected']).first()
        if not obj:
            messages.error(request, 'Usuario no encontrado o no archivado')
            return redirect('ver_archivados')
        full_name = obj.user.get_full_name() or obj.user.username
        if not _require_double_confirm(request, tipo, full_name):
            messages.error(request, f'Confirmacion invalida. Debes escribir exactamente "{full_name}" para restaurar este usuario.')
            return redirect('ver_archivados')
        obj.status = 'active'
        obj.user.is_active = True
        obj.save(update_fields=['status'])
        obj.user.save(update_fields=['is_active'])
        create_audit_log(user, 'USER_RESTORE', 'user', obj.user.id, f'Usuario restaurado: {full_name}')

    else:
        messages.error(request, f'Tipo de item desconocido: {tipo}')
        return redirect('ver_archivados')

    from django.core.cache import cache
    cache.delete('archived_items_count')
    messages.success(request, f'Item restaurado correctamente')
    return redirect('ver_archivados')
