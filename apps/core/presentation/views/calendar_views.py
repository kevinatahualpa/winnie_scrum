from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q, F
from django.utils import timezone

from apps.core.infrastructure.models.models import Sprint, Project, Substitution
from apps.core.domain.services.permission_service import get_user_role

TYPE_SPRINT = 'sprint'
TYPE_SPRINT_END = 'sprint-end'
TYPE_PROJECT = 'project'
TYPE_PROJECT_END = 'project-end'
TYPE_SUPLENCIA = 'suplencia'

EVENT_COLORS = {
    TYPE_SPRINT: '#3b82f6',
    TYPE_SPRINT_END: '#10b981',
    TYPE_PROJECT: '#8b5cf6',
    TYPE_PROJECT_END: '#6366f1',
    TYPE_SUPLENCIA: '#f59e0b',
}

EVENT_ICONS = {
    TYPE_SPRINT: 'fa-running',
    TYPE_SPRINT_END: 'fa-flag-checkered',
    TYPE_PROJECT: 'fa-folder-open',
    TYPE_PROJECT_END: 'fa-folder',
    TYPE_SUPLENCIA: 'fa-exchange-alt',
}

EVENT_LABELS = {
    TYPE_SPRINT: 'Sprint',
    TYPE_SPRINT_END: 'Fin de Sprint',
    TYPE_PROJECT: 'Proyecto',
    TYPE_PROJECT_END: 'Fin de Proyecto',
    TYPE_SUPLENCIA: 'Suplencia',
}


@login_required
def ver_calendario(request):
    user = request.user
    profile = getattr(user, 'profile', None)
    role = get_user_role(user)
    year = int(request.GET.get('year', timezone.now().year))
    month = int(request.GET.get('month', timezone.now().month))
    if month < 1:
        month = 12
        year -= 1
    elif month > 12:
        month = 1
        year += 1

    project_ids = None
    if role == 'miembro':
        project_ids = set(
            Project.objects.filter(
                Q(lead=user) | Q(members=user)
            ).values_list('id', flat=True)
        )

    events = []

    sprints = Sprint.objects.filter(
        Q(start_date__year=year, start_date__month=month) |
        Q(end_date__year=year, end_date__month=month)
    ).select_related('project')
    if project_ids is not None:
        sprints = sprints.filter(project_id__in=project_ids)

    for sprint in sprints:
        color = sprint.project.color if sprint.project and sprint.project.color else EVENT_COLORS[TYPE_SPRINT]
        events.append({
            'title': sprint.name,
            'date': _date_str(sprint.start_date),
            'type': TYPE_SPRINT,
            'color': color,
            'icon': EVENT_ICONS[TYPE_SPRINT],
            'label': EVENT_LABELS[TYPE_SPRINT],
            'project': sprint.project.name if sprint.project else '',
            'detail': f'Sprint: {sprint.name}',
        })
        if sprint.end_date != sprint.start_date:
            events.append({
                'title': sprint.name,
                'date': _date_str(sprint.end_date),
                'type': TYPE_SPRINT_END,
                'color': EVENT_COLORS[TYPE_SPRINT_END],
                'icon': EVENT_ICONS[TYPE_SPRINT_END],
                'label': EVENT_LABELS[TYPE_SPRINT_END],
                'project': sprint.project.name if sprint.project else '',
                'detail': f'Finaliza sprint: {sprint.name}',
            })

    projects_qs = Project.objects.filter(
        Q(start_date__year=year, start_date__month=month) |
        Q(end_date__year=year, end_date__month=month)
    )
    if project_ids is not None:
        projects_qs = projects_qs.filter(id__in=project_ids)

    for project in projects_qs:
        if project.start_date:
            events.append({
                'title': project.name,
                'date': _date_str(project.start_date),
                'type': TYPE_PROJECT,
                'color': project.color or EVENT_COLORS[TYPE_PROJECT],
                'icon': EVENT_ICONS[TYPE_PROJECT],
                'label': EVENT_LABELS[TYPE_PROJECT],
                'project': project.name,
                'detail': f'Inicia proyecto: {project.name}',
            })
        if project.end_date and project.end_date != project.start_date:
            events.append({
                'title': project.name,
                'date': _date_str(project.end_date),
                'type': TYPE_PROJECT_END,
                'color': EVENT_COLORS[TYPE_PROJECT_END],
                'icon': EVENT_ICONS[TYPE_PROJECT_END],
                'label': EVENT_LABELS[TYPE_PROJECT_END],
                'project': project.name,
                'detail': f'Finaliza proyecto: {project.name}',
            })

    suplencias = Substitution.objects.filter(
        active=True
    ).filter(
        Q(start_date__year=year, start_date__month=month) |
        Q(end_date__year=year, end_date__month=month)
    ).select_related('original_user', 'substitute_user')

    for sup in suplencias:
        events.append({
            'title': f'{sup.substitute_user.get_full_name()} cubre a {sup.original_user.get_full_name()}',
            'date': _date_str(sup.start_date),
            'type': TYPE_SUPLENCIA,
            'color': EVENT_COLORS[TYPE_SUPLENCIA],
            'icon': EVENT_ICONS[TYPE_SUPLENCIA],
            'label': EVENT_LABELS[TYPE_SUPLENCIA],
            'project': '',
            'detail': f'{sup.substitute_user.get_full_name()} suple a {sup.original_user.get_full_name()}',
        })
        if sup.end_date != sup.start_date:
            events.append({
                'title': f'Fin suplencia: {sup.substitute_user.get_full_name()}',
                'date': _date_str(sup.end_date),
                'type': TYPE_SUPLENCIA,
                'color': EVENT_COLORS[TYPE_SUPLENCIA],
                'icon': EVENT_ICONS[TYPE_SUPLENCIA],
                'label': EVENT_LABELS[TYPE_SUPLENCIA],
                'project': '',
                'detail': f'Termina suplencia de {sup.original_user.get_full_name()}',
            })

    events.sort(key=lambda e: e['date'])

    month_name = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                   'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'][month]

    return render(request, 'core/calendar.html', {
        'events': events, 'year': year, 'month': month,
        'month_name': month_name,
        'event_types': [
            {'key': TYPE_SPRINT, 'color': EVENT_COLORS[TYPE_SPRINT], 'icon': EVENT_ICONS[TYPE_SPRINT], 'label': EVENT_LABELS[TYPE_SPRINT]},
            {'key': TYPE_SPRINT_END, 'color': EVENT_COLORS[TYPE_SPRINT_END], 'icon': EVENT_ICONS[TYPE_SPRINT_END], 'label': EVENT_LABELS[TYPE_SPRINT_END]},
            {'key': TYPE_PROJECT, 'color': EVENT_COLORS[TYPE_PROJECT], 'icon': EVENT_ICONS[TYPE_PROJECT], 'label': EVENT_LABELS[TYPE_PROJECT]},
            {'key': TYPE_PROJECT_END, 'color': EVENT_COLORS[TYPE_PROJECT_END], 'icon': EVENT_ICONS[TYPE_PROJECT_END], 'label': EVENT_LABELS[TYPE_PROJECT_END]},
            {'key': TYPE_SUPLENCIA, 'color': EVENT_COLORS[TYPE_SUPLENCIA], 'icon': EVENT_ICONS[TYPE_SUPLENCIA], 'label': EVENT_LABELS[TYPE_SUPLENCIA]},
        ],
    })


def _date_str(d):
    return d.strftime('%Y-%m-%d') if d else ''
