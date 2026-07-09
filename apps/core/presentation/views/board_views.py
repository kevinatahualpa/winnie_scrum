from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.views.decorators.clickjacking import xframe_options_sameorigin

from apps.core.infrastructure.models.models import Task, Project, Area, User, Sprint, UserProfile
from apps.core.domain.services.permission_service import get_user_role, filter_queryset_by_role


@login_required
@xframe_options_sameorigin
def ver_tablero(request):
    """Kanban board filtered by area → project → sprint → assignee.

    When no project or sprint is selected, shows all active sprints across
    the user's visible projects. Selecting a sprint renders its Kanban.
    """
    user = request.user
    profile = getattr(user, 'profile', None)
    role = get_user_role(user)
    area_id = request.GET.get('area')
    project_id = request.GET.get('project')
    sprint_id = request.GET.get('sprint')
    assignee_id = request.GET.get('assignee')

    # ── Areas ────────────────────────────────────────────────
    if role in ('super-admin', 'admin'):
        areas = Area.objects.filter(status='active')
    elif role == 'jefe-area' and profile and profile.area:
        areas = Area.objects.filter(pk=profile.area_id, status='active')
    else:
        areas = Area.objects.none()

    # ── Projects scoped by role + area filter ────────────────
    projects = filter_queryset_by_role(
        Project.objects.filter(status='active'), user, role, model_type='project'
    ).select_related('area').distinct()
    if area_id:
        projects = projects.filter(area_id=area_id)
    if project_id:
        projects = projects.filter(pk=project_id)

    # ── Active sprints across filtered projects ─────────────
    active_sprints = Sprint.objects.filter(
        project__in=projects, status='ACT'
    ).select_related('project', 'project__area').order_by('project__name')

    # ── Selected sprint ──────────────────────────────────────
    active_sprint = None
    if sprint_id:
        active_sprint = Sprint.objects.filter(
            pk=sprint_id, status='ACT'
        ).select_related('project', 'project__area').first()
    elif project_id:
        # Un proyecto tiene un unico sprint activo: mostrarlo directo.
        active_sprint = active_sprints.first()

    board_columns = []
    if active_sprint:
        tasks = Task.objects.filter(sprint=active_sprint).select_related(
            'assignee', 'project', 'sprint'
        ).prefetch_related('tags')

        if assignee_id:
            tasks = tasks.filter(assignee_id=assignee_id)
        tasks = filter_queryset_by_role(tasks, user, role, model_type='task')
        tasks = tasks.annotate(comment_count=Count('comments'))

        board_columns = [
            ('TODO', 'Por Hacer', tasks.filter(status='TODO')),
            ('PROG', 'En Progreso', tasks.filter(status='PROG')),
            ('TEST', 'En Testing', tasks.filter(status='TEST')),
            ('DONE', 'Completado', tasks.filter(status='DONE')),
        ]

    # ── Assignees ────────────────────────────────────────────
    user_ids = list(UserProfile.objects.filter(status='active').values_list('user_id', flat=True))
    assignees = User.objects.filter(is_active=True, id__in=user_ids).select_related('profile').order_by('first_name')

    # ── Auto-scope jefe-area ─────────────────────────────────
    if role == 'jefe-area' and profile and profile.area and not area_id:
        area_id = str(profile.area.id)

    filters = {
        'area': area_id, 'project': project_id,
        'sprint': sprint_id, 'assignee': assignee_id,
    }

    return render(request, 'core/board.html', {
        'board_columns': board_columns,
        'active_sprint': active_sprint,
        'active_sprints': active_sprints,
        'projects': projects,
        'areas': areas,
        'assignees': assignees,
        'filters': filters,
        'role': role,
    })


def ver_tablero_fragment(request):
    """HTMX fragment — returns only the board columns HTML."""
    user = request.user
    role = get_user_role(user)
    sprint_id = request.GET.get('sprint')
    assignee_id = request.GET.get('assignee')

    active_sprint = None
    if sprint_id:
        active_sprint = Sprint.objects.filter(
            pk=sprint_id, status='ACT'
        ).select_related('project').first()

    board_columns = []
    if active_sprint:
        tasks = Task.objects.filter(sprint=active_sprint).select_related(
            'assignee', 'project', 'sprint'
        ).prefetch_related('tags')

        if assignee_id:
            tasks = tasks.filter(assignee_id=assignee_id)
        tasks = filter_queryset_by_role(tasks, user, role, model_type='task')
        tasks = tasks.annotate(comment_count=Count('comments'))

        board_columns = [
            ('TODO', 'Por Hacer', tasks.filter(status='TODO')),
            ('PROG', 'En Progreso', tasks.filter(status='PROG')),
            ('TEST', 'En Testing', tasks.filter(status='TEST')),
            ('DONE', 'Completado', tasks.filter(status='DONE')),
        ]

    return render(request, 'core/board_columns.html', {
        'board_columns': board_columns,
        'active_sprint': active_sprint,
    })
