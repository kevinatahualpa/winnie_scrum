from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.db.models import Q
from django.urls import reverse
from urllib.parse import urlencode

from apps.core.infrastructure.models.models import Task, Project, User, Specialty, Sprint, UserProfile
from apps.core.domain.services.permission_service import get_user_role, can_manage_task
from apps.core.domain.services.task_service import TaskService
from apps.core.presentation.forms import TaskForm


@require_http_methods(["GET", "POST"])
@login_required
def crear_tarea(request):
    """Create a new task. Requires task management permission (not miembro without assignment).

    GET: Render the task creation form with projects, users, and specialties.
    POST: Create task via TaskService, notify assignee, redirect to board.
    """
    user = request.user
    role = get_user_role(user)

    if role == 'miembro' or not can_manage_task(user):
        messages.error(request, 'No tienes permiso para crear tareas')
        return redirect('ver_tablero')

    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            project = form.cleaned_data['project']
            if not can_manage_task(user):
                messages.error(request, 'No tienes permiso para crear tareas en este proyecto')
                return redirect('ver_tablero')

            task, error = TaskService.crear_tarea(
                user=user,
                project=project,
                title=form.cleaned_data['title'],
                type=form.cleaned_data['type'],
                priority=form.cleaned_data['priority'],
                points=form.cleaned_data['points'],
                status=form.cleaned_data['status'],
                description=form.cleaned_data['description'],
                assignee_id=form.cleaned_data['assignee'].id if form.cleaned_data.get('assignee') else None,
                sprint_id=form.cleaned_data['sprint'].id if form.cleaned_data.get('sprint') else None,
                required_specialty_id=form.cleaned_data['required_specialty'].id if form.cleaned_data.get('required_specialty') else None,
                tags=form.cleaned_data['tags'],
            )

            if error:
                messages.error(request, error)
                return redirect('ver_tablero')

            messages.success(request, f'Tarea "{task.title}" creada')
            return redirect('ver_tablero')
    else:
        form = TaskForm()

    projects = Project.objects.filter(status='active')
    if role in ('jefe-area', 'jefe-proyecto', 'miembro'):
        from apps.core.domain.services.permission_service import filter_queryset_by_role
        projects = filter_queryset_by_role(projects, user, role, model_type='project')

    user_ids = list(UserProfile.objects.filter(status='active').values_list('user_id', flat=True))
    users = User.objects.filter(is_active=True, id__in=user_ids).select_related('profile', 'profile__specialty')
    specialties = Specialty.active.all()

    form.fields['project'].queryset = projects
    form.fields['assignee'].queryset = users
    form.fields['required_specialty'].queryset = specialties

    return render(request, 'core/task_form.html', {
        'form': form, 'projects': projects, 'users': users, 'specialties': specialties,
        'sprints': Sprint.objects.none(), 'points_list': ['1', '2', '3', '5', '8', '13'],
    })


@require_http_methods(["GET", "POST"])
@login_required
def editar_tarea(request, pk):
    """Edit an existing task. Requires task management permission for the specific task.

    GET: Render the task edit form with current data.
    POST: Update task via TaskService, notify new assignee if changed, redirect to board.
    """
    task = get_object_or_404(Task, pk=pk)

    if not can_manage_task(request.user, task):
        messages.error(request, 'No tienes permiso para editar esta tarea')
        return redirect('ver_tablero')

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            updated_task, error = TaskService.editar_tarea(
                user=request.user,
                task=task,
                title=form.cleaned_data['title'],
                type=form.cleaned_data['type'],
                priority=form.cleaned_data['priority'],
                points=form.cleaned_data['points'],
                status=form.cleaned_data['status'],
                description=form.cleaned_data['description'],
                assignee_id=form.cleaned_data['assignee'].id if form.cleaned_data.get('assignee') else None,
                sprint_id=form.cleaned_data['sprint'].id if form.cleaned_data.get('sprint') else None,
                required_specialty_id=form.cleaned_data['required_specialty'].id if form.cleaned_data.get('required_specialty') else None,
                tags=form.cleaned_data['tags'],
            )

            if error:
                messages.error(request, error)
                return redirect('ver_tablero')

            messages.success(request, f'Tarea "{updated_task.title}" actualizada')
            return redirect('ver_tablero')
    else:
        form = TaskForm(instance=task)

    projects = Project.objects.filter(status='active')
    user_ids = list(UserProfile.objects.filter(status='active').values_list('user_id', flat=True))
    users = User.objects.filter(is_active=True, id__in=user_ids).select_related('profile', 'profile__specialty')
    specialties = Specialty.active.all()
    sprints = Sprint.objects.filter(project=task.project)

    tags_str = ', '.join(task.tags.values_list('name', flat=True))
    form.fields['tags'].initial = tags_str

    form.fields['project'].queryset = projects
    form.fields['assignee'].queryset = users
    form.fields['required_specialty'].queryset = specialties
    form.fields['sprint'].queryset = sprints

    return render(request, 'core/task_form.html', {
        'form': form, 'projects': projects, 'users': users,
        'specialties': specialties, 'sprints': sprints,
        'points_list': ['1', '2', '3', '5', '8', '13'],
    })


@require_POST
@login_required
def eliminar_tarea(request, pk):
    """Delete a task. Requires task management permission for the specific task."""
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    task = get_object_or_404(Task, pk=pk)
    title = task.title
    success, error = TaskService.eliminar_tarea(request.user, task)

    if is_ajax:
        if success:
            return JsonResponse({'success': True, 'message': f'Tarea "{title}" eliminada'})
        return JsonResponse({'success': False, 'error': error}, status=400)

    if not success:
        messages.error(request, error)
    else:
        messages.success(request, f'Tarea "{title}" eliminada')

    return redirect('ver_tablero')


@require_POST
@login_required
def crear_tarea_rapida(request):
    """Quick task creation via AJAX modal. Returns JSON."""
    import json
    user = request.user
    role = get_user_role(user)

    if role == 'miembro' or not can_manage_task(user):
        return JsonResponse({'success': False, 'error': 'No tienes permiso para crear tareas'}, status=403)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, AttributeError):
        data = request.POST

    project_id = data.get('project')
    title = data.get('title', '').strip()

    if not title or not project_id:
        return JsonResponse({'success': False, 'error': 'Título y proyecto son requeridos'}, status=400)

    project = get_object_or_404(Project, pk=project_id)

    # Optional inline-required fields (Jira-style inline create)
    require_meta = data.get('require_meta') in ('1', 1, True, 'true')
    assignee_val = data.get('assignee') or None
    due_val = data.get('due_date') or None
    if require_meta:
        if not assignee_val:
            return JsonResponse({'success': False, 'error': 'Debes asignar un responsable'}, status=400)
        if not due_val:
            return JsonResponse({'success': False, 'error': 'Debes seleccionar una fecha de vencimiento'}, status=400)

    due_date = None
    if due_val:
        from datetime import date
        try:
            due_date = date.fromisoformat(due_val)
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'Fecha inválida'}, status=400)

    task, error = TaskService.crear_tarea(
        user=user,
        project=project,
        title=title,
        type=data.get('type', 'task'),
        priority=data.get('priority', 'medium'),
        points=int(data.get('points', 1)),
        status=data.get('status', 'TODO'),
        description=data.get('description', ''),
        assignee_id=assignee_val,
        sprint_id=data.get('sprint') or None,
        required_specialty_id=None,
        tags='',
        due_date=due_date,
    )

    if error:
        return JsonResponse({'success': False, 'error': error}, status=400)

    return JsonResponse({
        'success': True,
        'task': {
            'id': task.pk,
            'title': task.title,
            'type': task.type,
            'get_type_display': task.get_type_display(),
            'priority': task.priority,
            'get_priority_display': task.get_priority_display(),
            'points': task.points,
            'status': task.status,
            'assignee': task.assignee.get_full_name() if task.assignee else None,
            'assignee_id': task.assignee_id,
            'project_id': task.project_id,
            'project_name': task.project.name,
        }
    })


@require_POST
@login_required
def actualizar_campo_tarea(request, pk):
    """Update a single task field via AJAX (inline editing)."""
    task = get_object_or_404(Task, pk=pk)
    if not can_manage_task(request.user, task):
        return JsonResponse({'success': False, 'error': 'Sin permiso'}, status=403)

    import json
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, AttributeError):
        data = request.POST

    field = data.get('field')
    value = data.get('value', '').strip()

    valid_fields = {'title', 'priority', 'assignee', 'points'}

    if field not in valid_fields:
        return JsonResponse({'success': False, 'error': 'Campo inválido'}, status=400)

    kwargs = {}
    if field == 'assignee':
        kwargs['assignee_id'] = value or None
    elif field == 'points':
        kwargs['points'] = int(value) if value else 1
    else:
        kwargs[field] = value

    updated, error = TaskService.editar_tarea(
        user=request.user, task=task, **kwargs
    )

    if error:
        return JsonResponse({'success': False, 'error': error}, status=400)

    return JsonResponse({'success': True, 'field': field, 'value': value})


@require_POST
@login_required
def actualizar_estado_tarea(request, pk):
    """Update task status via AJAX (used by board drag-and-drop).

    Returns JSON response with success/error status.
    Used by the Kanban board for drag-and-drop status changes.
    """
    task = get_object_or_404(Task, pk=pk)
    if not can_manage_task(request.user, task):
        return JsonResponse({'success': False, 'error': 'No permission'}, status=403)

    new_status = request.POST.get('status')
    if not new_status:
        import json as _json
        try:
            new_status = _json.loads(request.body).get('status')
        except (ValueError, AttributeError):
            new_status = None
    success, error = TaskService.actualizar_estado(request.user, task, new_status)

    if success:
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': error}, status=400)


@require_POST
@login_required
def comentar_tarea(request, task_pk):
    """Add a comment to a task and notify the assignee/project lead.

    Members can only comment on tasks they are assigned to.
    Preserves board filter params on redirect.
    """
    from apps.core.infrastructure.models.models import Comment
    from apps.core.domain.services.notification_service import notify_comment, create_audit_log

    task = get_object_or_404(Task, pk=task_pk)
    role = get_user_role(request.user)

    if role == 'miembro' and task.assignee != request.user:
        messages.error(request, 'No tienes permiso para comentar en esta tarea')
        return redirect('ver_tablero')

    text = request.POST.get('text', '').strip()
    if text:
        Comment.objects.create(task=task, author=request.user, text=text)
        create_audit_log(request.user, 'COMMENT', 'comment', task.id, f'Comentario en: {task.title}')
        notify_comment(task, request.user)

    params = {}
    for key in ('area', 'project', 'assignee'):
        val = request.GET.get(key) or request.POST.get(key, '')
        if val:
            params[key] = val

    url = reverse('ver_tablero')
    if params:
        url += '?' + urlencode(params)
    return redirect(url)


@login_required
def task_json(request, pk):
    """Return task data as JSON for the drawer edit form."""
    task = get_object_or_404(
        Task.objects.select_related('project', 'sprint', 'assignee'),
        pk=pk
    )
    if not can_manage_task(request.user, task):
        return JsonResponse({'error': 'No tienes permiso'}, status=403)

    return JsonResponse({
        'id': task.pk,
        'title': task.title,
        'project': task.project_id,
        'project_name': task.project.name,
        'sprint': task.sprint_id,
        'sprint_name': task.sprint.name if task.sprint else '',
        'assignee': task.assignee_id,
        'type': task.type,
        'priority': task.priority,
        'points': task.points,
        'status': task.status,
        'description': task.description,
    })


@login_required
def sprints_por_proyecto(request, project_id):
    """Return sprints for a project as JSON for dynamic select."""
    user = request.user
    from apps.core.domain.services.permission_service import filter_queryset_by_role
    get_user_role_local = get_user_role
    role = get_user_role_local(user)

    project = get_object_or_404(Project, pk=project_id)
    sprints = Sprint.objects.filter(project=project).order_by('-start_date')
    sprints = filter_queryset_by_role(sprints, user, role, model_type='sprint')

    data = [{'value': '', 'label': 'Sin sprint (backlog)'}]
    for s in sprints:
        data.append({
            'value': s.pk,
            'label': f'{s.name} ({s.get_status_display()})',
        })
    return JsonResponse({'sprints': data})
