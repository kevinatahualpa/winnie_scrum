from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q

from apps.core.infrastructure.models.models import Area, Project, Sprint, Task, User
from apps.core.domain.services.permission_service import get_user_role, filter_queryset_by_role


@login_required
def ver_dashboard(request):
    """Render the main dashboard with role-filtered statistics.

    Shows project/task counts, sprint status, and recent activity.
    Filters data based on user role (admin sees all, jefe-area sees area,
    jefe-proyecto/miembro see only their projects/tasks).
    Cliente role is redirected to the client portal.
    """
    user = request.user
    role = get_user_role(user)

    if role == 'cliente':
        return redirect('ver_portal_cliente')

    projects = filter_queryset_by_role(Project.objects.all(), user, role, model_type='project')
    tasks = filter_queryset_by_role(Task.objects.all(), user, role, model_type='task')
    sprints = filter_queryset_by_role(Sprint.objects.all(), user, role, model_type='sprint')

    if role == 'miembro':
        projects = projects.distinct()
    else:
        projects = projects.distinct()

    project_ids = list(projects.values_list('id', flat=True))
    tasks_in_projects = tasks.filter(project_id__in=project_ids) if project_ids else Task.objects.none()
    sprints_in_projects = sprints.filter(project_id__in=project_ids) if project_ids else Sprint.objects.none()

    task_stats = tasks_in_projects.aggregate(
        total=Count('id'),
        todo=Count('id', filter=Q(status__in=['backlog', 'todo'])),
        in_progress=Count('id', filter=Q(status='in-progress')),
        done=Count('id', filter=Q(status='done')),
        bugs=Count('id', filter=Q(type='bug', status__in=['backlog', 'todo', 'in-progress'])),
    )

    context = {
        'total_projects': projects.count(),
        'active_projects': projects.filter(status='active').count(),
        'total_tasks': task_stats['total'],
        'todo_tasks': task_stats['todo'],
        'in_progress_tasks': task_stats['in_progress'],
        'done_tasks': task_stats['done'],
        'active_sprints': sprints_in_projects.filter(status='active').count(),
        'bugs': task_stats['bugs'],
        'recent_tasks': tasks_in_projects.select_related('assignee', 'project').order_by('-created_at')[:8],
        'recent_projects': projects.select_related('area', 'lead', 'client').order_by('-created_at')[:5],
        'has_projects': projects.exists(),
    }

    if role in ('super-admin', 'admin'):
        context['total_areas'] = Area.objects.count()
        context['total_users'] = User.objects.filter(is_active=True).count()

    return render(request, 'core/dashboard.html', context)
