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
    specialties = Specialty.objects.all()

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
    specialties = Specialty.objects.all()
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
    task = get_object_or_404(Task, pk=pk)
    success, error = TaskService.eliminar_tarea(request.user, task)

    if not success:
        messages.error(request, error)
    else:
        messages.success(request, f'Tarea "{task.title}" eliminada')

    return redirect('ver_tablero')


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
