from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.urls import reverse
from django.http import JsonResponse
from django.db import transaction

from apps.core.infrastructure.models.models import Sprint, Project, Task
from apps.core.domain.services.permission_service import get_user_role, can_manage_project, filter_queryset_by_role
from apps.core.domain.services.sprint_service import SprintService
from apps.core.domain.services.notification_service import create_audit_log
from apps.core.presentation.forms import SprintForm
from django.db.models import Count, Q


@login_required
@xframe_options_sameorigin
def ver_sprints(request):
    """Sprint list grouped by project with progress bars.

    Shows done/total tasks per sprint. Filterable by project.
    """
    user = request.user
    role = get_user_role(user)
    project_id = request.GET.get('project')

    sprints_qs = Sprint.objects.select_related('project').annotate(
        tasks_finished=Count('tasks', filter=Q(tasks__status='DONE')),
        tasks_total=Count('tasks'),
    ).order_by('project__name', '-start_date')
    sprints_qs = filter_queryset_by_role(sprints_qs, user, role, model_type='sprint')

    if project_id:
        sprints_qs = sprints_qs.filter(project_id=project_id)

    active_sprint = sprints_qs.filter(status='ACT').first()
    active_sprint_data = {}
    if active_sprint:
        active_sprint_tasks = active_sprint.tasks.all()
        active_sprint_data = {
            'total': active_sprint_tasks.count(),
            'done': active_sprint_tasks.filter(status='DONE').count(),
        }

    projects = filter_queryset_by_role(
        Project.objects.filter(status='active'), user, role, model_type='project'
    )

    return render(request, 'core/sprints.html', {
        'sprints': sprints_qs,
        'active_sprint': active_sprint,
        'active_sprint_data': active_sprint_data,
        'projects': projects,
        'sprint_form': SprintForm(),
    })


@require_POST
@login_required
def crear_sprint(request):
    """Create a new sprint in a project. Requires project management permission."""
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    role = get_user_role(request.user)

    form = SprintForm(request.POST)
    if form.is_valid():
        project = form.cleaned_data['project']
        if not can_manage_project(request.user, project):
            if is_ajax:
                return JsonResponse({'success': False, 'error': 'No tienes permiso para este proyecto'}, status=403)
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
            if is_ajax:
                return JsonResponse({'success': False, 'error': error}, status=400)
            messages.error(request, error)
        else:
            if is_ajax:
                return JsonResponse({'success': True, 'message': f'Sprint "{sprint.name}" creado'})
            messages.success(request, f'Sprint "{sprint.name}" creado')
    else:
        if is_ajax:
            errs = '; '.join(f'{f}: {e}' for f, el in form.errors.items() for e in el)
            return JsonResponse({'success': False, 'error': errs or 'Datos inválidos'}, status=400)
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f'{field}: {error}')

    return redirect('ver_sprints')


@require_POST
@login_required
def eliminar_sprint(request, pk):
    """Delete a sprint. Its tasks return to the Product Backlog (sprint=NULL).

    AJAX-aware: returns JSON when requested with X-Requested-With.
    """
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    sprint = get_object_or_404(Sprint.objects.select_related('project'), pk=pk)

    if not can_manage_project(request.user, sprint.project):
        if is_ajax:
            return JsonResponse({'success': False, 'error': 'No tienes permiso'}, status=403)
        messages.error(request, 'No tienes permiso para eliminar este sprint')
        return redirect('ver_sprints')

    name = sprint.name
    with transaction.atomic():
        Task.objects.filter(sprint=sprint).update(sprint=None, status='TODO')
        create_audit_log(request.user, 'SPRINT_DELETE', 'sprint', sprint.pk, f'Sprint eliminado: {name}')
        sprint.delete()

    if is_ajax:
        return JsonResponse({'success': True, 'message': f'Sprint "{name}" eliminado'})
    messages.success(request, f'Sprint "{name}" eliminado. Sus tareas volvieron al backlog.')
    return redirect('ver_sprints')


@login_required
def editar_sprint(request, pk):
    """Edit a sprint. Rules by role and sprint status.

    GET: return sprint data as JSON for the drawer.
    POST: update fields based on role + sprint status.
      - PLAN: anyone permitted can edit name, dates, goal.
      - ACT:  only goal editable (unless super-admin, who edits everything).
      - CMP:  immutable (unless super-admin).
    """
    sprint = get_object_or_404(Sprint.objects.select_related('project'), pk=pk)
    user = request.user
    role = get_user_role(user)

    if not can_manage_project(user, sprint.project):
        return JsonResponse({'success': False, 'error': 'No tienes permiso para editar este sprint'}, status=403)

    # GET: return JSON for drawer pre-fill
    if request.method == 'GET':
        return JsonResponse({
            'id': sprint.pk,
            'name': sprint.name,
            'project': sprint.project_id,
            'project_name': sprint.project.name,
            'start_date': str(sprint.start_date),
            'end_date': str(sprint.end_date),
            'goal': sprint.goal,
            'status': sprint.status,
        })

    # POST: update
    is_super = role == 'super-admin'
    name = request.POST.get('name', '').strip()
    goal = request.POST.get('goal', '').strip()
    start_date = request.POST.get('start_date', '')
    end_date = request.POST.get('end_date', '')

    if sprint.status == 'CMP' and not is_super:
        return JsonResponse({'success': False, 'error': 'No se puede editar un sprint completado'}, status=400)

    if sprint.status == 'ACT' and not is_super:
        # Only goal can be edited on active sprints (not super-admin)
        if name or start_date or end_date:
            return JsonResponse({'success': False, 'error': 'En un sprint activo solo se puede editar el objetivo'}, status=400)
        if goal:
            sprint.goal = goal
            sprint.save(update_fields=['goal'])
            return JsonResponse({'success': True, 'message': 'Objetivo actualizado'})

    # PLAN status (or super-admin on any status): full edit
    if name:
        sprint.name = name
    if goal or goal == '':
        sprint.goal = goal
    if start_date and end_date:
        from datetime import date
        try:
            s = date.fromisoformat(start_date)
            e = date.fromisoformat(end_date)
            if s > e:
                return JsonResponse({'success': False, 'error': 'Fecha inicio debe ser <= fecha fin'}, status=400)
            sprint.start_date = s
            sprint.end_date = e
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'Fechas invalidas'}, status=400)
    elif start_date:
        from datetime import date
        try:
            sprint.start_date = date.fromisoformat(start_date)
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'Fecha inicio invalida'}, status=400)
    elif end_date:
        from datetime import date
        try:
            sprint.end_date = date.fromisoformat(end_date)
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'Fecha fin invalida'}, status=400)

    sprint.save()
    return JsonResponse({'success': True, 'message': f'Sprint "{sprint.name}" actualizado'})


@login_required
def seleccionar_tareas_sprint(request, pk):
    """GET: show Product Backlog tasks. POST: assign to sprint and activate.

    For AJAX requests (X-Requested-With: XMLHttpRequest), returns a partial
    HTML fragment for the drawer. Otherwise renders the full page.
    """
    sprint = get_object_or_404(Sprint.objects.select_related('project'), pk=pk)
    role = get_user_role(request.user)

    if not can_manage_project(request.user, sprint.project):
        messages.error(request, 'No tienes permiso para gestionar este sprint')
        return redirect('ver_sprints')

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'GET':
        backlog_tasks = Task.objects.filter(
            project=sprint.project,
            sprint__isnull=True,
            status='TODO',
        ).order_by('position', '-priority', '-created_at')

        template = 'core/sprint_task_drawer.html' if is_ajax else 'core/sprint_task_selection.html'
        return render(request, template, {
            'sprint': sprint,
            'backlog_tasks': backlog_tasks,
        })

    # POST: bulk assign selected tasks + activate sprint
    task_ids = request.POST.getlist('task_ids')
    if task_ids:
        Task.objects.filter(
            pk__in=task_ids, project=sprint.project, sprint__isnull=True
        ).update(sprint=sprint, status='TODO')

    sprint, error = SprintService.iniciar_sprint(request.user, sprint)
    if error:
        messages.error(request, error)
        if is_ajax:
            return JsonResponse({'success': False, 'error': error}, status=400)
    else:
        msg = f'Sprint "{sprint.name}" iniciado'
        if task_ids:
            msg += f' con {len(task_ids)} tareas'
        messages.success(request, msg)
        if is_ajax:
            return JsonResponse({'success': True, 'redirect': reverse('ver_sprints')})

    return redirect('ver_sprints')


@require_POST
@login_required
def iniciar_sprint(request, pk):
    """Direct sprint activation (backward-compatible POST endpoint).

    For the full flow with task selection, use seleccionar_tareas_sprint (GET+POST).
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
    """Complete a sprint. Incomplete tasks (TODO/PROG/TEST) go back to the
    Product Backlog (status='TODO', sprint=NULL). Done tasks keep historical
    sprint_id for reporting."""
    sprint = get_object_or_404(Sprint, pk=pk)
    sprint, error = SprintService.completar_sprint(request.user, sprint)

    if error:
        messages.error(request, error)
    else:
        messages.success(
            request,
            f'Sprint "{sprint.name}" completado. Las tareas pendientes '
            f'volvieron al Product Backlog.'
        )

    return redirect('ver_sprints')
