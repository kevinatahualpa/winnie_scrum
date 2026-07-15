import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.db.models import Q
from django.core.paginator import Paginator

from apps.core.infrastructure.models.models import Task, Project, Area, User, UserProfile, Sprint
from apps.core.domain.services.permission_service import (
    get_user_role, filter_queryset_by_role, can_manage_task, can_manage_project,
)


def _status_counts(task_list):
    """Return dict of status counters for a list of tasks (Jira-style)."""
    counts = {'todo': 0, 'prog': 0, 'done': 0}
    for t in task_list:
        if t.status == 'DONE':
            counts['done'] += 1
        elif t.status in ('PROG', 'TEST'):
            counts['prog'] += 1
        else:
            counts['todo'] += 1
    return counts


@login_required
@xframe_options_sameorigin
def ver_backlog(request):
    """Jira-style Backlog: accordion blocks of Sprints + Product Backlog.

    When scoped to a project (?project=<id>) it shows the project's sprints
    (non-completed) as drop targets plus the backlog, each block collapsible
    with status counters and inline task actions.
    """
    user = request.user
    profile = getattr(user, 'profile', None)
    role = get_user_role(user)
    project_id = request.GET.get('project')
    area_id = request.GET.get('area')

    # Areas available for the filter (cascade: area -> project)
    if role in ('super-admin', 'admin'):
        areas = Area.objects.filter(status='active')
    elif role == 'jefe-area' and profile and profile.area:
        areas = Area.objects.filter(pk=profile.area_id, status='active')
    else:
        areas = Area.objects.none()

    # Base queryset scoped by role
    base = Task.objects.select_related('assignee', 'assignee__profile', 'project', 'sprint')
    if role in ('super-admin', 'admin'):
        pass
    elif role == 'jefe-area' and profile and profile.area:
        pids = list(Project.objects.filter(area=profile.area).values_list('id', flat=True))
        base = base.filter(project_id__in=pids)
    elif role in ('jefe-proyecto', 'miembro'):
        pids = list(Project.objects.filter(Q(lead=user) | Q(members=user)).values_list('id', flat=True))
        base = base.filter(project_id__in=pids)
        if role == 'miembro':
            led = list(Project.objects.filter(lead=user).values_list('id', flat=True))
            base = base.filter(Q(assignee=user) | Q(project_id__in=led))

    if area_id:
        base = base.filter(project__area_id=area_id)
    if project_id:
        base = base.filter(project_id=project_id)

    projects = filter_queryset_by_role(
        Project.objects.exclude(status__in=['completed', 'cancelled']), user, role, model_type='project'
    ).select_related('area').distinct()
    if area_id:
        projects = projects.filter(area_id=area_id)

    user_ids = list(UserProfile.objects.filter(status='active').values_list('user_id', flat=True))
    assignees = list(User.objects.filter(is_active=True, id__in=user_ids).select_related('profile'))

    proj_obj = projects.filter(pk=project_id).first() if project_id else None
    can_manage = bool(proj_obj) and can_manage_project(user, proj_obj)

    # Build sprint blocks (non-completed) when scoped to a project
    sprint_blocks = []
    if project_id and proj_obj:
        from django.db.models import Case, When, IntegerField
        sprints = (
            Sprint.objects.filter(project_id=project_id).exclude(status='CMP')
            .annotate(_ord=Case(When(status='ACT', then=0), default=1, output_field=IntegerField()))
            .order_by('_ord', 'start_date')
        )
        for sp in sprints:
            sp_tasks = list(base.filter(sprint=sp).order_by('position', '-priority', '-created_at'))
            sprint_blocks.append({
                'sprint': sp,
                'tasks': sp_tasks,
                'counts': _status_counts(sp_tasks),
                'total': len(sp_tasks),
            })

    backlog_tasks = list(base.filter(sprint__isnull=True).order_by('position', '-priority', '-created_at'))
    backlog_block = {
        'tasks': backlog_tasks,
        'counts': _status_counts(backlog_tasks),
        'total': len(backlog_tasks),
    }

    # General view (no project selected): group backlog tasks by project
    project_blocks = []
    if not project_id:
        by_project = {}
        for t in backlog_tasks:
            by_project.setdefault(t.project_id, []).append(t)
        for proj in projects:
            p_tasks = by_project.get(proj.id, [])
            project_blocks.append({
                'project': proj,
                'tasks': p_tasks,
                'counts': _status_counts(p_tasks),
                'total': len(p_tasks),
                'can_manage': can_manage_project(user, proj),
            })

    return render(request, 'core/backlog.html', {
        'projects': projects,
        'areas': areas,
        'assignees': assignees,
        'sprint_blocks': sprint_blocks,
        'backlog_block': backlog_block,
        'project_blocks': project_blocks,
        'current_project_id': project_id,
        'current_project': proj_obj,
        'current_area_id': area_id,
        'can_manage': can_manage,
        'can_manage_any': can_manage_task(user),
        'today': __import__('datetime').date.today(),
    })


@require_POST
@login_required
def reordenar_backlog(request):
    """Persist custom backlog ordering to the Task.position field.

    Accepts JSON: {"order": ["task_id_1", "task_id_2", ...]}
    Updates each task's position field so ordering survives sessions.
    """
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'success': False, 'error': 'JSON invalido'}, status=400)

    order = data.get('order', [])
    if not order:
        return JsonResponse({'success': False, 'error': 'Orden vacio'}, status=400)

    for idx, task_id in enumerate(order):
        Task.objects.filter(pk=task_id).update(position=idx)

    return JsonResponse({'success': True})


@require_POST
@login_required
def asignar_tarea_sprint(request):
    """Assign a backlog task to a sprint (or back to backlog) via drag-and-drop.

    Accepts JSON: {"task_id": <id>, "sprint_id": <id|null>}
    - sprint_id null/empty -> move task back to Product Backlog (sprint=NULL).
    - Task and sprint must belong to the same project.
    - Requires task management permission and access to the project.
    """
    from apps.core.domain.services.permission_service import can_manage_task, can_manage_project
    from apps.core.infrastructure.models.models import Sprint

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'success': False, 'error': 'JSON invalido'}, status=400)

    task_id = data.get('task_id')
    sprint_id = data.get('sprint_id')

    task = Task.objects.filter(pk=task_id).select_related('project').first()
    if not task:
        return JsonResponse({'success': False, 'error': 'Tarea no encontrada'}, status=404)

    if not can_manage_task(request.user) or not can_manage_project(request.user, task.project):
        return JsonResponse({'success': False, 'error': 'No tienes permiso'}, status=403)

    if sprint_id:
        sprint = Sprint.objects.filter(pk=sprint_id).select_related('project').first()
        if not sprint:
            return JsonResponse({'success': False, 'error': 'Sprint no encontrado'}, status=404)
        if sprint.project_id != task.project_id:
            return JsonResponse({'success': False, 'error': 'La tarea y el sprint deben ser del mismo proyecto'}, status=400)
        if sprint.status == 'CMP':
            return JsonResponse({'success': False, 'error': 'No se puede asignar a un sprint completado'}, status=400)
        task.sprint = sprint
        if task.status not in ('TODO', 'PROG', 'TEST', 'DONE'):
            task.status = 'TODO'
        task.save(update_fields=['sprint', 'status'])
        return JsonResponse({'success': True, 'message': f'Tarea movida a "{sprint.name}"'})

    # Move back to backlog
    task.sprint = None
    task.status = 'TODO'
    task.save(update_fields=['sprint', 'status'])
    return JsonResponse({'success': True, 'message': 'Tarea devuelta al backlog'})
