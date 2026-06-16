from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Case, When, Value, IntegerField
from django.core.paginator import Paginator

from apps.core.infrastructure.models.models import Task, Project
from apps.core.domain.services.permission_service import get_user_role


@login_required
def ver_backlog(request):
    """Render the product backlog view showing unstarted tasks.

    Displays tasks with status 'ver_backlog' or 'todo', ordered by priority
    (high > medium > low) then by creation date (newest first).
    Uses pagination (30 per page) and role-based filtering.
    """
    user = request.user
    profile = getattr(user, 'profile', None)
    role = get_user_role(user)

    tasks = Task.objects.select_related('assignee', 'project', 'sprint', 'required_specialty').prefetch_related('tags')

    if role in ('super-admin', 'admin'):
        pass
    elif role == 'jefe-area' and profile and profile.area:
        project_ids = list(Project.objects.filter(area=profile.area).values_list('id', flat=True))
        tasks = tasks.filter(project_id__in=project_ids)
    elif role in ('jefe-proyecto', 'miembro'):
        project_ids = list(Project.objects.filter(Q(lead=user) | Q(members=user)).values_list('id', flat=True))
        tasks = tasks.filter(project_id__in=project_ids)
        if role == 'miembro':
            tasks = tasks.filter(assignee=user)

    tasks = tasks.filter(status__in=['backlog', 'todo']).annotate(
        priority_order=Case(
            When(priority='high', then=Value(0)),
            When(priority='medium', then=Value(1)),
            When(priority='low', then=Value(2)),
            output_field=IntegerField(),
        )
    ).order_by('priority_order', '-created_at')

    paginator = Paginator(tasks, 30)
    page = request.GET.get('page', 1)
    tasks = paginator.get_page(page)

    return render(request, 'core/backlog.html', {'tasks': tasks})
