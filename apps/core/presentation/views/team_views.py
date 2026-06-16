from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.views.decorators.http import require_http_methods, require_POST
from django.core.paginator import Paginator

from apps.core.infrastructure.models.models import UserProfile, Area, Specialty, Project, Client
from apps.core.domain.services.permission_service import (
    get_user_role, can_manage_admin, can_delete_user, filter_queryset_by_role,
)
from apps.core.domain.services.user_service import UserService
from apps.core.presentation.forms import MemberForm


def _role_choices_with_clients():
    """Build (value, label) tuples from the model so adding a new role
    automatically updates the team filter without code changes.
    Excludes 'cliente' because clients are managed in their own portal."""
    excluded = {'cliente'}
    field = UserProfile._meta.get_field('role')
    return [(v, l) for v, l in field.choices if v not in excluded]


def _member_form_context(form, areas, specialties, clients):
    return {
        'form': form, 'areas': areas, 'specialties': specialties,
        'clients': clients, 'role_choices': _role_choices_with_clients(),
    }


@login_required
def ver_equipo(request):
    """Render la lista de USUARIOS separada en dos secciones:
       1. Equipo interno (miembros, jefes, admins, observers)
       2. Clientes (solo visible para super-admin/admin)

    Soporta filtros por area, empresa (cliente), proyecto y rol.
    La seccion de Clientes solo aparece para super-admin/admin.
    """
    user = request.user
    role = get_user_role(user)
    area_id = request.GET.get('area')
    project_id = request.GET.get('project')
    filter_role = request.GET.get('role')
    client_id = request.GET.get('client')

    base_qs = UserProfile.objects.select_related(
        'user', 'area', 'specialty', 'client',
    ).filter(status='active')

    areas = Area.objects.filter(status='active')
    clients = Client.objects.all().order_by('name')
    projects = filter_queryset_by_role(Project.objects.all(), user, role, model_type='project')

    if role == 'jefe-area' and getattr(user, 'profile', None) and user.profile.area:
        projects = projects.filter(area=user.profile.area)
        area_id = str(user.profile.area.id)

    project_ids = list(projects.values_list('id', flat=True))
    all_projects = Project.objects.filter(Q(id__in=project_ids)).select_related('area')

    projects_by_user = {}
    for project in all_projects:
        member_ids = list(project.members.values_list('id', flat=True))
        if project.lead_id:
            member_ids.append(project.lead_id)
        for mid in member_ids:
            if mid not in projects_by_user:
                projects_by_user[mid] = []
            projects_by_user[mid].append(project)

    def enrich(qs):
        data = []
        for m in qs:
            user_projects = projects_by_user.get(m.user_id, [])
            m.projects_list = []
            for p in user_projects:
                is_lead = p.lead_id == m.user_id
                m.projects_list.append({'project': p, 'is_lead': is_lead})
            m.project_count = len(user_projects)
            m.has_projects = m.project_count > 0
            data.append(m)
        return data

    # ---- SECCION 1: equipo interno (todos los roles menos cliente) ----
    internal_qs = base_qs.exclude(role='cliente')
    internal_qs = filter_queryset_by_role(internal_qs, user, role, model_type='user')
    if area_id:
        internal_qs = internal_qs.filter(area_id=area_id)
    if project_id:
        internal_qs = internal_qs.filter(
            Q(user__projects__id=project_id) | Q(user__led_projects__id=project_id)
        ).distinct()
    if filter_role:
        internal_qs = internal_qs.filter(role=filter_role)
    internal_users = enrich(internal_qs)

    filters = {
        'area': area_id, 'project': project_id,
        'role': filter_role,
    }

    return render(request, 'core/team.html', {
        'internal_users': internal_users,
        'role': role, 'areas': areas,
        'clients': clients, 'projects': projects,
        'role_choices': _role_choices_with_clients(), 'filters': filters,
    })


@require_http_methods(["GET", "POST"])
@login_required
def registrar_usuario(request):
    """Create a new team member. Requires admin role.

    Project assignment is NOT done here. The admin creates the profile;
    project assignment happens later from the project's own members view
    (gestionar_miembros_proyecto) by admin, jefe-area or jefe-proyecto.
    """
    if not can_manage_admin(request.user):
        messages.error(request, 'No tienes permiso para crear usuarios')
        return redirect('ver_equipo')

    areas = Area.objects.filter(status='active')
    specialties = Specialty.objects.all()
    clients = Client.objects.all().order_by('name')

    if request.method == 'POST':
        form = MemberForm(
            request.POST,
            clients_qs=clients,
            areas_qs=areas,
            specialties_qs=specialties,
        )
        if form.is_valid():
            client_obj = form.cleaned_data.get('client')
            profile, error = UserService.registrar_usuario(
                user_creator=request.user,
                email=form.cleaned_data['email'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                password=form.cleaned_data['password'] or 'password123',
                phone=form.cleaned_data['phone'],
                area_id=form.cleaned_data['area'].id if form.cleaned_data.get('area') else None,
                specialty_id=form.cleaned_data['specialty'].id if form.cleaned_data.get('specialty') else None,
                client_id=client_obj.id if client_obj else None,
                role=form.cleaned_data['role'],
                status=form.cleaned_data['status'],
                color=form.cleaned_data['color'],
            )

            if error:
                messages.error(request, error)
                return render(request, 'core/team_member_form.html',
                              _member_form_context(form, areas, specialties, clients))

            messages.success(
                request,
                f'Usuario "{profile.user.get_full_name()}" creado. '
                f'Para asignarlo a proyectos, ve al detalle del proyecto y usa "Gestionar Miembros".'
            )
            return redirect('ver_equipo')
        else:
            for field, errs in form.errors.items():
                for e in errs:
                    messages.error(request, f'{field}: {e}')
    else:
        form = MemberForm(
            clients_qs=clients,
            areas_qs=areas,
            specialties_qs=specialties,
        )

    return render(request, 'core/team_member_form.html',
                  _member_form_context(form, areas, specialties, clients))


@require_http_methods(["GET", "POST"])
@login_required
def editar_usuario(request, pk):
    """Update an existing team member's profile. Requires admin role.

    Project assignment is NOT done here; it lives in
    gestionar_miembros_proyecto on the project detail page.
    """
    profile = get_object_or_404(UserProfile, pk=pk)

    areas = Area.objects.filter(status='active')
    specialties = Specialty.objects.all()
    clients = Client.objects.all().order_by('name')

    if request.method == 'POST':
        form = MemberForm(
            request.POST,
            instance=profile,
            clients_qs=clients,
            areas_qs=areas,
            specialties_qs=specialties,
        )
        if form.is_valid():
            client_obj = form.cleaned_data.get('client')
            updated_profile, error = UserService.editar_usuario(
                user_editor=request.user,
                profile=profile,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'] or None,
                phone=form.cleaned_data['phone'],
                area_id=form.cleaned_data['area'].id if form.cleaned_data.get('area') else None,
                specialty_id=form.cleaned_data['specialty'].id if form.cleaned_data.get('specialty') else None,
                client_id=client_obj.id if client_obj else None,
                role=form.cleaned_data['role'],
                status=form.cleaned_data['status'],
                color=form.cleaned_data['color'],
            )

            if error:
                messages.error(request, error)
                ctx = _member_form_context(form, areas, specialties, clients)
                ctx['profile'] = profile
                return render(request, 'core/team_member_form.html', ctx)

            messages.success(request, f'Usuario "{updated_profile.user.get_full_name()}" actualizado')
            return redirect('ver_equipo')
        else:
            for field, errs in form.errors.items():
                for e in errs:
                    messages.error(request, f'{field}: {e}')
    else:
        form = MemberForm(
            instance=profile,
            initial={
                'first_name': profile.user.first_name,
                'last_name': profile.user.last_name,
                'email': profile.user.email,
            },
            clients_qs=clients,
            areas_qs=areas,
            specialties_qs=specialties,
        )

    ctx = _member_form_context(form, areas, specialties, clients)
    ctx['profile'] = profile
    return render(request, 'core/team_member_form.html', ctx)


@require_POST
@login_required
def desactivar_usuario(request, pk):
    """Soft delete a team member (deactivate instead of deleting).

    Admins and super-admins can deactivate. Cannot deactivate yourself.
    Preserves all history.
    """
    profile = get_object_or_404(UserProfile, pk=pk)

    if not can_delete_user(request.user, profile.user):
        messages.error(request, 'No tienes permiso para desactivar este usuario')
        return redirect('ver_equipo')

    success, error = UserService.desactivar_usuario(request.user, profile)

    if not success:
        messages.error(request, error)
    else:
        messages.success(request, f'Usuario "{profile.user.get_full_name()}" desactivado')

    return redirect('ver_equipo')


@require_POST
@login_required
def reactivar_usuario(request, pk):
    """Reactivate a previously deactivated user."""
    profile = get_object_or_404(UserProfile, pk=pk)

    if not can_manage_admin(request.user):
        messages.error(request, 'No tienes permiso para reactivar usuarios')
        return redirect('ver_equipo_desactivados')

    success, error = UserService.reactivar_usuario(request.user, profile)

    if not success:
        messages.error(request, error)
    else:
        messages.success(request, f'Usuario "{profile.user.get_full_name()}" reactivado')

    return redirect('ver_equipo_desactivados')


@login_required
def ver_equipo_desactivados(request):
    """Show deactivated/dismissed users with option to reactivate."""
    user = request.user
    role = get_user_role(user)

    if not can_manage_admin(user):
        messages.error(request, 'No tienes permiso para ver usuarios desactivados')
        return redirect('ver_equipo')

    desactivados_qs = UserProfile.objects.select_related(
        'user', 'area', 'specialty', 'client',
    ).filter(status='dismissed')

    desactivados = []
    for m in desactivados_qs:
        desactivados.append(m)

    return render(request, 'core/team.html', {
        'dismissed_users': desactivados,
        'role': role,
        'show_dismissed': True,
    })
