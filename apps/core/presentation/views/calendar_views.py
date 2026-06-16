from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone

from apps.core.infrastructure.models.models import Sprint, Project
from apps.core.domain.services.permission_service import get_user_role


@login_required
def ver_calendario(request):
    """Render the calendar view showing sprint start/end dates for a given month.

    Supports navigation between months via year/month query parameters.
    Members see only sprints from their projects.
    """
    user = request.user
    profile = getattr(user, 'profile', None)
    role = get_user_role(user)
    year = int(request.GET.get('year', timezone.now().year))
    month = int(request.GET.get('month', timezone.now().month))

    sprints = Sprint.objects.filter(
        Q(start_date__year=year, start_date__month=month) |
        Q(end_date__year=year, end_date__month=month)
    ).select_related('project')

    if role == 'miembro':
        project_ids = list(Project.objects.filter(Q(lead=user) | Q(members=user)).values_list('id', flat=True))
        sprints = sprints.filter(project_id__in=project_ids)

    events = []
    for sprint in sprints:
        events.append({
            'title': sprint.name,
            'date': sprint.start_date,
            'type': 'sprint',
            'color': sprint.project.color if sprint.project else '#00bcd4',
            'project': sprint.project.name if sprint.project else '',
        })
        if sprint.end_date != sprint.start_date:
            events.append({
                'title': f'{sprint.name} (fin)',
                'date': sprint.end_date,
                'type': 'sprint',
                'color': '#2e7d32',
                'project': sprint.project.name if sprint.project else '',
            })

    month_name = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                   'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'][month]

    return render(request, 'core/calendar.html', {
        'events': events, 'year': year, 'month': month,
        'month_name': month_name,
    })
