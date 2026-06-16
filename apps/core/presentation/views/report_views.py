from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q

from apps.core.infrastructure.models.models import Project, Task
from apps.core.domain.services.permission_service import get_user_role, filter_queryset_by_role


@login_required
def ver_reportes(request):
    """Render analytics reports with task breakdowns by status, type, and priority.

    Filters data by user role. Members see only their assigned tasks.
    """
    user = request.user
    role = get_user_role(user)

    projects = filter_queryset_by_role(Project.objects.all(), user, role, model_type='project')
    project_ids = list(projects.values_list('id', flat=True))
    tasks = Task.objects.filter(project_id__in=project_ids)

    if role == 'miembro':
        tasks = tasks.filter(assignee=user)

    by_status = tasks.values('status').annotate(count=Count('id')).order_by('-count')
    by_type = tasks.values('type').annotate(count=Count('id')).order_by('-count')
    by_priority = tasks.values('priority').annotate(count=Count('id')).order_by('-count')

    return render(request, 'core/reports.html', {
        'by_status': by_status, 'by_type': by_type, 'by_priority': by_priority,
        'total_projects': projects.count(), 'total_tasks': tasks.count(),
    })
