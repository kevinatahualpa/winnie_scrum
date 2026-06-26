from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count

from apps.core.infrastructure.models.models import Task, Project, Area, User
from apps.core.domain.services.permission_service import get_user_role, filter_queryset_by_role


@login_required
def ver_tablero(request):
    """Render the Scrum board (Kanban view) with drag-and-drop task columns.

    Displays tasks grouped by status (backlog, todo, in-progress, done)
    with filtering by area, project, and assignee based on user role.
    Each task card shows an observation count with quick-access comment button.
    """
    user = request.user
    profile = getattr(user, 'profile', None)
    role = get_user_role(user)
    area_id = request.GET.get('area')
    project_id = request.GET.get('project')
    assignee_id = request.GET.get('assignee')

    tasks = Task.objects.select_related('assignee', 'project', 'sprint').prefetch_related('tags')

    if area_id:
        tasks = tasks.filter(project__area_id=area_id)
    if project_id:
        tasks = tasks.filter(project_id=project_id)
    if assignee_id:
        tasks = tasks.filter(assignee_id=assignee_id)
    tasks = filter_queryset_by_role(tasks, user, role, model_type='task')

    tasks = tasks.annotate(comment_count=Count('comments'))

    columns = {
        'backlog': tasks.filter(status='backlog'),
        'todo': tasks.filter(status='todo'),
        'in-progress': tasks.filter(status='in-progress'),
        'done': tasks.filter(status='done'),
    }
    board_columns = [
        ('backlog', 'Backlog', columns['backlog']),
        ('todo', 'Por Hacer', columns['todo']),
        ('in-progress', 'En Progreso', columns['in-progress']),
        ('done', 'Completado', columns['done']),
    ]

    areas = Area.objects.filter(status='active')
    projects = filter_queryset_by_role(Project.objects.all(), user, role, model_type='project').distinct()
    if area_id:
        projects = projects.filter(area_id=area_id)

    if role == 'jefe-area' and profile and profile.area:
        area_id = str(profile.area.id)

    project_ids = list(projects.values_list('id', flat=True))

    if project_id:
        assignees = User.objects.filter(
            Q(projects__id=project_id) | Q(led_projects__id=project_id)
        ).distinct().select_related('profile').prefetch_related('projects', 'led_projects')
    elif area_id:
        assignees = User.objects.filter(
            Q(projects__area_id=area_id) | Q(led_projects__area_id=area_id)
        ).distinct().select_related('profile').prefetch_related('projects', 'led_projects')
    else:
        assignees = User.objects.filter(
            Q(projects__id__in=project_ids) | Q(led_projects__id__in=project_ids)
        ).distinct().select_related('profile').prefetch_related('projects', 'led_projects')

    # Build data-projects for client-side cascade
    assignee_opts = []
    for u in assignees:
        pids = set()
        for p in u.projects.all():
            pids.add(str(p.id))
        for p in u.led_projects.all():
            pids.add(str(p.id))
        assignee_opts.append((u, ','.join(sorted(pids))))

    filters = {'area': area_id, 'project': project_id, 'assignee': assignee_id}

    return render(request, 'core/board.html', {
        'board_columns': board_columns, 'projects': projects, 'areas': areas,
        'assignee_opts': assignee_opts, 'filters': filters, 'role': role,
    })
