from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q

from apps.core.infrastructure.models.models import Task, Project, User
from apps.core.domain.services.permission_service import get_user_role


@login_required
def buscar(request):
    """Global search endpoint returning matching tasks, projects, and users.

    Returns JSON response with up to 10 tasks, 5 projects, and 5 users.
    Members see only their own tasks and projects.
    """
    user = request.user
    role = get_user_role(user)
    query = request.GET.get('q', '').strip()

    if not query:
        return JsonResponse({'tasks': [], 'projects': [], 'users': []})

    tasks = Task.objects.filter(title__icontains=query)
    projects = Project.objects.filter(name__icontains=query)

    if role == 'miembro':
        tasks = tasks.filter(assignee=user)
        project_ids = list(Project.objects.filter(Q(lead=user) | Q(members=user)).values_list('id', flat=True))
        tasks = tasks.filter(project_id__in=project_ids)
        projects = projects.filter(id__in=project_ids)

    tasks = tasks[:10].values('id', 'title', 'project__name')
    projects = projects[:5].values('id', 'name')
    users = User.objects.filter(
        Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(email__icontains=query)
    )[:5].values('id', 'first_name', 'last_name', 'email')

    return JsonResponse({
        'tasks': list(tasks),
        'projects': list(projects),
        'users': list(users),
    })
