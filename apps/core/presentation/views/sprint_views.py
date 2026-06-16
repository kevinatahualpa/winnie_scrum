from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator

from apps.core.infrastructure.models.models import Sprint, Project
from apps.core.domain.services.permission_service import get_user_role, can_manage_project, filter_queryset_by_role
from apps.core.domain.services.sprint_service import SprintService
from apps.core.presentation.forms import SprintForm


@login_required
def ver_sprints(request):
    """Render the paginated list of sprints with active sprint statistics.

    Shows sprint progress (total tasks vs done) for the active sprint.
    Filters sprints by user role (admin sees all, others see scoped sprints).
    """
    user = request.user
    role = get_user_role(user)

    sprints_qs = Sprint.objects.select_related('project').order_by('-start_date')
    sprints_qs = filter_queryset_by_role(sprints_qs, user, role, model_type='sprint')

    active_sprint = sprints_qs.filter(status='active').first()
    active_sprint_data = {}
    if active_sprint:
        active_sprint_tasks = active_sprint.tasks.all()
        active_sprint_data = {
            'total': active_sprint_tasks.count(),
            'done': active_sprint_tasks.filter(status='done').count(),
        }

    projects = filter_queryset_by_role(
        Project.objects.filter(status='active'), user, role, model_type='project'
    )

    paginator = Paginator(sprints_qs, 20)
    page = request.GET.get('page', 1)
    sprints_list = paginator.get_page(page)

    return render(request, 'core/sprints.html', {
        'sprints': sprints_list, 'active_sprint': active_sprint,
        'active_sprint_data': active_sprint_data, 'projects': projects,
        'sprint_form': SprintForm(),
    })


@require_POST
@login_required
def crear_sprint(request):
    """Create a new sprint in a project. Requires project management permission."""
    role = get_user_role(request.user)
    if role == 'miembro' or not can_manage_project(request.user):
        messages.error(request, 'No tienes permiso para crear sprints')
        return redirect('ver_sprints')

    form = SprintForm(request.POST)
    if form.is_valid():
        project = form.cleaned_data['project']
        if not can_manage_project(request.user, project):
            messages.error(request, 'No tienes permiso para este proyecto')
            return redirect('ver_sprints')

        sprint, error = SprintService.crear_sprint(
            user=request.user,
            project=project,
            name=form.cleaned_data['name'],
            start_date=form.cleaned_data['start_date'],
            end_date=form.cleaned_data['end_date'],
            goal=form.cleaned_data['goal'],
        )

        if error:
            messages.error(request, error)
        else:
            messages.success(request, f'Sprint "{sprint.name}" creado')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f'{field}: {error}')

    return redirect('ver_sprints')


@require_POST
@login_required
def iniciar_sprint(request, pk):
    """Start a planned sprint. Deactivates any currently active sprint in the same project.

    Notifies all project team members about the sprint start.
    """
    sprint = get_object_or_404(Sprint, pk=pk)
    sprint, error = SprintService.iniciar_sprint(request.user, sprint)

    if error:
        messages.error(request, error)
    else:
        messages.success(request, f'Sprint "{sprint.name}" iniciado')

    return redirect('ver_sprints')


@require_POST
@login_required
def completar_sprint(request, pk):
    """Complete a sprint and move incomplete tasks back to backlog."""
    sprint = get_object_or_404(Sprint, pk=pk)
    sprint, error = SprintService.completar_sprint(request.user, sprint)

    if error:
        messages.error(request, error)
    else:
        messages.success(request, f'Sprint "{sprint.name}" completado')

    return redirect('ver_sprints')
