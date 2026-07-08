import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.core.paginator import Paginator

from apps.core.infrastructure.models.models import Task, Project, User, UserProfile
from apps.core.domain.services.permission_service import get_user_role, filter_queryset_by_role


@login_required
def ver_backlog(request):
    """Render the Product Backlog — global inventory of unassigned tasks.

    Shows only tasks with sprint=NULL (not yet part of any sprint).
    Ordered by persisted position field, then priority, then creation date.
    Role-based filtering scopes visibility per user.
    """
    user = request.user
    profile = getattr(user, 'profile', None)
    role = get_user_role(user)

    tasks = Task.objects.select_related(
        'assignee', 'project', 'sprint', 'required_specialty'
    ).prefetch_related('tags')

    if role in ('super-admin', 'admin'):
        pass
    elif role == 'jefe-area' and profile and profile.area:
        project_ids = list(Project.objects.filter(area=profile.area).values_list('id', flat=True))
        tasks = tasks.filter(project_id__in=project_ids)
    elif role in ('jefe-proyecto', 'miembro'):
        project_ids = list(Project.objects.filter(
            Q(lead=user) | Q(members=user)
        ).values_list('id', flat=True))
        tasks = tasks.filter(project_id__in=project_ids)
        if role == 'miembro':
            tasks = tasks.filter(assignee=user)

    tasks = tasks.filter(sprint__isnull=True, status='TODO').order_by(
        'position', '-priority', '-created_at'
    )

    paginator = Paginator(tasks, 30)
    page = request.GET.get('page', 1)
    tasks = paginator.get_page(page)

    projects = filter_queryset_by_role(
        Project.objects.all(), user, role, model_type='project'
    ).distinct()
    user_ids = list(UserProfile.objects.filter(status='active').values_list('user_id', flat=True))
    assignees = User.objects.filter(is_active=True, id__in=user_ids).select_related('profile')

    return render(request, 'core/backlog.html', {
        'tasks': tasks, 'projects': projects, 'assignees': assignees,
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
