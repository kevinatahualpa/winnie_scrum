from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.views.decorators.http import require_http_methods, require_POST
from django.core.paginator import Paginator

from apps.core.infrastructure.models.models import Project, Area, Client, User, Comment, Message, UserProfile
from apps.core.domain.services.permission_service import (
    get_user_role, can_manage_area, can_manage_project, can_assign_to_project,
    can_delete_project,
    filter_queryset_by_role,
)
from apps.core.domain.services.project_service import ProjectService
from apps.core.domain.services.notification_service import create_audit_log, create_notification
from apps.core.presentation.forms import ProjectForm


@login_required
def ver_proyectos(request):
    """Render the paginated list of projects filtered by user role and area.

    Admins see all projects. Other roles see only projects they have access to.
    Uses select_related and prefetch_related to avoid N+1 queries.
    """
    user = request.user
    role = get_user_role(user)
    area_id = request.GET.get('area')

    queryset = Project.objects.select_related('area', 'lead', 'client').prefetch_related('members')

    if role in ('jefe-area', 'jefe-proyecto', 'miembro'):
        queryset = filter_queryset_by_role(queryset, user, role, model_type='project')

    if area_id:
        queryset = queryset.filter(area_id=area_id)

    paginator = Paginator(queryset, 20)
    page = request.GET.get('page', 1)
    projects = paginator.get_page(page)

    areas = Area.objects.filter(status='active')

    return render(request, 'core/projects.html', {
        'projects': projects,
        'areas': areas,
        'selected_area': area_id,
    })


@login_required
def ver_detalle_proyecto(request, pk):
    """Render project detail page with tasks, sprints, chat and DMs.

    Members can only view projects they are assigned to.
    Supports ?dm=<user_id> to open a direct message with a project member.
    """
    user = request.user
    role = get_user_role(user)
    project = get_object_or_404(Project, pk=pk)

    if role == 'miembro':
        if not (project.lead == user or project.members.filter(id=user.id).exists()):
            messages.error(request, 'No tienes permiso para ver este proyecto')
            return redirect('ver_proyectos')

    tasks = project.tasks.select_related('assignee', 'sprint').order_by('-created_at')
    if role == 'miembro':
        tasks = tasks.filter(assignee=user)
    sprints = project.sprints.order_by('-start_date')
    comments = project.comments.select_related('author').order_by('created_at')
    documents = project.documents.select_related('uploaded_by').order_by('-created_at')

    project_members = list(User.objects.filter(
        Q(led_projects=project) | Q(projects=project)
    ).exclude(id=user.id).distinct().select_related('profile'))

    dm_user = None
    dm_messages = None
    dm_user_id = request.GET.get('dm')
    if dm_user_id and dm_user_id.isdigit():
        dm_user = User.objects.filter(pk=dm_user_id).first()
        if dm_user and (dm_user in project_members or dm_user == project.lead or project.members.filter(id=dm_user.id).exists()):
            dm_user = User.objects.select_related('profile').get(pk=dm_user_id)
            dm_messages = Message.objects.filter(
                Q(sender=user, receiver=dm_user) | Q(sender=dm_user, receiver=user)
            ).order_by('created_at')
            Message.objects.filter(sender=dm_user, receiver=user, read=False).update(read=True)

    return render(request, 'core/project_detail.html', {
        'project': project, 'tasks': tasks, 'sprints': sprints,
        'comments': comments, 'documents': documents,
        'project_members': project_members, 'dm_user': dm_user, 'dm_messages': dm_messages,
        'can_assign_members': can_assign_to_project(request.user, project),
    })


@require_http_methods(["GET", "POST"])
@login_required
def crear_proyecto(request):
    """Create a new project. Requires area management role (admin or jefe-area).

    GET: Render the project creation form.
    POST: Create project via ProjectService, notify lead and members, redirect to list.
    """
    if not can_manage_area(request.user):
        messages.error(request, 'No tienes permiso para crear proyectos')
        return redirect('ver_proyectos')

    areas = Area.objects.filter(status='active')
    users = User.objects.filter(is_active=True)
    clients = Client.active.all()

    if request.method == 'POST':
        form = ProjectForm(request.POST)
        form.fields['area'].queryset = areas
        form.fields['lead'].queryset = users
        form.fields['client'].queryset = clients
        form.fields['members'].queryset = users

        if form.is_valid():
            members = form.cleaned_data.get('members', [])
            member_ids = [m.id for m in members] if members else None
            project, error = ProjectService.crear_proyecto(
                user=request.user,
                name=form.cleaned_data['name'],
                area_id=form.cleaned_data['area'].id if form.cleaned_data.get('area') else None,
                description=form.cleaned_data['description'],
                status=form.cleaned_data['status'],
                lead_id=form.cleaned_data['lead'].id if form.cleaned_data.get('lead') else None,
                client_id=form.cleaned_data['client'].id if form.cleaned_data.get('client') else None,
                budget=form.cleaned_data['budget'],
                start_date=form.cleaned_data['start_date'],
                end_date=form.cleaned_data['end_date'],
                color=form.cleaned_data['color'],
                members=member_ids,
            )

            if error:
                messages.error(request, error)
                return redirect('ver_proyectos')

            messages.success(request, f'Proyecto "{project.name}" creado')
            return redirect('ver_proyectos')
        else:
            for field, errs in form.errors.items():
                for e in errs:
                    messages.error(request, f'{field}: {e}')
    else:
        form = ProjectForm()
        form.fields['area'].queryset = areas
        form.fields['lead'].queryset = users
        form.fields['client'].queryset = clients
        form.fields['members'].queryset = users

    return render(request, 'core/project_form.html', {'form': form, 'areas': areas, 'users': users, 'clients': clients})


@require_http_methods(["GET", "POST"])
@login_required
def editar_proyecto(request, pk):
    """Update an existing project. Requires project management permission.

    GET: Render the project edit form with current data.
    POST: Update project via ProjectService, notify new lead/members, redirect to list.
    """
    project = get_object_or_404(Project, pk=pk)
    areas = Area.objects.filter(status='active')
    users = User.objects.filter(is_active=True)
    clients = Client.active.all()

    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        form.fields['area'].queryset = areas
        form.fields['lead'].queryset = users
        form.fields['client'].queryset = clients
        form.fields['members'].queryset = users

        if form.is_valid():
            members = form.cleaned_data.get('members', [])
            member_ids = [m.id for m in members] if members else None
            updated_project, error = ProjectService.editar_proyecto(
                user=request.user,
                project=project,
                name=form.cleaned_data['name'],
                area_id=form.cleaned_data['area'].id if form.cleaned_data.get('area') else None,
                description=form.cleaned_data['description'],
                status=form.cleaned_data['status'],
                lead_id=form.cleaned_data['lead'].id if form.cleaned_data.get('lead') else None,
                client_id=form.cleaned_data['client'].id if form.cleaned_data.get('client') else None,
                budget=form.cleaned_data['budget'],
                start_date=form.cleaned_data['start_date'],
                end_date=form.cleaned_data['end_date'],
                color=form.cleaned_data['color'],
                members=member_ids,
            )

            if error:
                messages.error(request, error)
                return redirect('ver_proyectos')

            messages.success(request, f'Proyecto "{updated_project.name}" actualizado')
            return redirect('ver_proyectos')
        else:
            for field, errs in form.errors.items():
                for e in errs:
                    messages.error(request, f'{field}: {e}')
    else:
        form = ProjectForm(instance=project)
        form.fields['area'].queryset = areas
        form.fields['lead'].queryset = users
        form.fields['client'].queryset = clients
        form.fields['members'].queryset = users

    return render(request, 'core/project_form.html', {'form': form, 'project': project, 'areas': areas, 'users': users, 'clients': clients})


@require_POST
@login_required
def eliminar_proyecto(request, pk):
    """Soft delete a project (mark as cancelled). Only super-admin can delete projects.

    El proyecto no se elimina fisicamente: se marca como 'cancelled' para
    preservar el historial de tareas, sprints, documentos y comentarios.
    Admin puede editar y pausar proyectos pero no eliminarlos.
    """
    project = get_object_or_404(Project, pk=pk)

    if not can_delete_project(request.user, project):
        messages.error(request, 'Solo el super-admin puede eliminar proyectos')
        return redirect('ver_proyectos')

    project_name = project.name
    project.status = 'cancelled'
    project.save(update_fields=['status'])

    from apps.core.domain.services.notification_service import create_audit_log
    create_audit_log(request.user, 'PROJECT_CANCEL', 'project', pk, f'Proyecto cancelado: {project_name}')
    messages.success(request, f'Proyecto "{project_name}" cancelado y archivado')
    return redirect('ver_proyectos')


@require_POST
@login_required
def comentar_proyecto(request, pk):
    """Add a comment (text and/or file) to a project and notify members."""
    project = get_object_or_404(Project, pk=pk)
    role = get_user_role(request.user)

    if role == 'miembro':
        if not (project.lead == request.user or project.members.filter(id=request.user.id).exists()):
            messages.error(request, 'No tienes permiso para comentar en este proyecto')
            return redirect('ver_detalle_proyecto', pk=pk)

    text = request.POST.get('text', '').strip()
    uploaded_file = request.FILES.get('file')

    if not text and not uploaded_file:
        return redirect('ver_detalle_proyecto', pk=pk)

    comment = Comment.objects.create(
        project=project,
        author=request.user,
        text=text,
        file=uploaded_file if uploaded_file else None,
    )

    create_audit_log(request.user, 'COMMENT', 'project', project.id, f'Mensaje en proyecto: {project.name}')

    if project.lead and project.lead != request.user:
        create_notification(
            project.lead, 'project_comment', 'Nuevo mensaje en proyecto',
            f'{request.user.get_full_name()} envió un mensaje en {project.name}',
            'fa-comment'
        )

    return redirect('ver_detalle_proyecto', pk=pk)


@require_http_methods(["GET", "POST"])
@login_required
def gestionar_miembros_proyecto(request, pk):
    """Manage the members of a project.

    Visible to users with can_assign_to_project permission:
    - super-admin / admin: any project
    - jefe-area: projects in their own area
    - jefe-proyecto: projects they lead

    GET: render current members + available users to add.
    POST: handle add/remove actions.
    """
    project = get_object_or_404(Project, pk=pk)

    if not can_assign_to_project(request.user, project):
        messages.error(request, 'No tienes permiso para gestionar los miembros de este proyecto')
        return redirect('ver_detalle_proyecto', pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')

        if not user_id:
            messages.error(request, 'Falta el usuario')
            return redirect('gestionar_miembros_proyecto', pk=pk)

        try:
            target_user = User.objects.select_related('profile').get(pk=user_id)
        except User.DoesNotExist:
            messages.error(request, 'Usuario no encontrado')
            return redirect('gestionar_miembros_proyecto', pk=pk)

        if action == 'add':
            if project.members.filter(pk=target_user.pk).exists():
                messages.info(request, f'{target_user.get_full_name() or target_user.username} ya es miembro del proyecto')
            else:
                project.members.add(target_user)
                create_audit_log(
                    request.user, 'PROJECT_MEMBER_ADD', 'project', project.id,
                    f'Agregado: {target_user.get_full_name() or target_user.username} al proyecto {project.name}'
                )
                if target_user != request.user:
                    create_notification(
                        target_user, 'project_member',
                        'Agregado a proyecto',
                        f'Fuiste agregado al proyecto "{project.name}"',
                        'fa-users',
                    )
                messages.success(request, f'{target_user.get_full_name() or target_user.username} agregado al proyecto')

        elif action == 'remove':
            if project.lead_id == target_user.pk:
                messages.error(request, 'No puedes quitar al lider del proyecto. Cambia el lider primero.')
            elif not project.members.filter(pk=target_user.pk).exists():
                messages.info(request, f'{target_user.get_full_name() or target_user.username} no es miembro del proyecto')
            else:
                project.members.remove(target_user)
                create_audit_log(
                    request.user, 'PROJECT_MEMBER_REMOVE', 'project', project.id,
                    f'Eliminado: {target_user.get_full_name() or target_user.username} del proyecto {project.name}'
                )
                messages.success(request, f'{target_user.get_full_name() or target_user.username} quitado del proyecto')
        else:
            messages.error(request, 'Accion no valida')

        return redirect('gestionar_miembros_proyecto', pk=pk)

    members = project.members.select_related('profile', 'profile__area', 'profile__specialty').order_by('first_name')

    role = get_user_role(request.user)
    available_qs = UserProfile.objects.filter(status='active').exclude(role__in=['cliente', 'observer']).exclude(user__projects=project).select_related('user', 'area', 'specialty')
    if role == 'jefe-area':
        available_qs = available_qs.filter(area_id=project.area_id)
    available_users = [
        {
            'id': p.user_id,
            'name': p.user.get_full_name() or p.user.username,
            'email': p.user.email,
            'role': p.get_role_display(),
            'area': p.area.name if p.area else '-',
            'initials': p.initials,
            'color': p.color,
        }
        for p in available_qs.order_by('user__first_name')
    ]

    return render(request, 'core/project_members.html', {
        'project': project,
        'members': members,
        'available_users': available_users,
        'can_manage': True,
    })
