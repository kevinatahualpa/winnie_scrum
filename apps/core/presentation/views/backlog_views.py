import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q, Case, When, Value, IntegerField
from django.core.paginator import Paginator

from apps.core.infrastructure.models.models import Task, Project, User, UserProfile
from apps.core.domain.services.permission_service import get_user_role, filter_queryset_by_role


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

    custom_order = request.session.get('backlog_order_' + str(user.id))
    if custom_order:
        task_list = list(tasks)
        task_dict = {str(t.pk): t for t in task_list}
        ordered = []
        for pk in custom_order:
            if pk in task_dict:
                ordered.append(task_dict.pop(pk))
        ordered.extend(task_dict.values())
        tasks = ordered
    else:
        tasks = list(tasks)

    paginator = Paginator(tasks, 30)
    page = request.GET.get('page', 1)
    tasks = paginator.get_page(page)

    projects = filter_queryset_by_role(Project.objects.all(), user, role, model_type='project').distinct()
    user_ids = list(UserProfile.objects.filter(status='active').values_list('user_id', flat=True))
    assignees = User.objects.filter(is_active=True, id__in=user_ids).select_related('profile')

    return render(request, 'core/backlog.html', {
        'tasks': tasks, 'projects': projects, 'assignees': assignees,
    })


@require_POST
@login_required
def reordenar_backlog(request):
    """Save custom backlog order to session."""
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400)

    order = data.get('order', [])
    if not order:
        return JsonResponse({'success': False, 'error': 'Orden vacío'}, status=400)

    request.session['backlog_order_' + str(request.user.id)] = order
    return JsonResponse({'success': True})
