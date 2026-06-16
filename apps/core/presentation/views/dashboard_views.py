from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum

from apps.core.infrastructure.models.models import (
    Area, Project, Sprint, Task, User, Notification, TimeEntry
)
from apps.core.domain.services.permission_service import get_user_role, filter_queryset_by_role


@login_required
def ver_dashboard(request):
    """Render the main dashboard with two views: 'Mi Trabajo' and 'Equipo'.

    - Mi Trabajo (default): tasks, projects, time where user is involved.
    - Equipo: global stats, team view. Only for admin/jefe.

    Cliente role is redirected to the client portal.
    """
    user = request.user
    role = get_user_role(user)

    if role == 'cliente':
        return redirect('ver_portal_cliente')

    # View selector: 'mi_trabajo' (default) or 'equipo'
    view = request.GET.get('view', 'mi_trabajo')
    # Restrict 'equipo' view to admin/jefe roles
    can_team_view = role in ('super-admin', 'admin', 'jefe-area', 'jefe-proyecto')
    if view == 'equipo' and not can_team_view:
        view = 'mi_trabajo'

    context = {
        'role': role,
        'view': view,
        'can_team_view': can_team_view,
    }

    # ============================================================
    # MI TRABAJO (default for everyone)
    # ============================================================
    if view == 'mi_trabajo':
        # Projects where user is member or lead
        my_projects = Project.objects.filter(
            Q(members=user) | Q(lead=user)
        ).distinct()
        my_project_ids = list(my_projects.values_list('id', flat=True))

        # Tasks assigned to me
        my_tasks = Task.objects.filter(assignee=user)
        my_task_stats = my_tasks.aggregate(
            total=Count('id'),
            todo=Count('id', filter=Q(status__in=['backlog', 'todo'])),
            in_progress=Count('id', filter=Q(status='in-progress')),
            done=Count('id', filter=Q(status='done')),
            bugs=Count('id', filter=Q(type='bug', status__in=['backlog', 'todo', 'in-progress'])),
        )

        # Time this week (Monday to today)
        today = datetime.now().date()
        monday = today - timedelta(days=today.weekday())
        time_this_week = TimeEntry.objects.filter(
            user=user, date__gte=monday, date__lte=today
        ).aggregate(total=Sum('hours'))['total'] or 0

        # Unread notifications
        unread_notifications = Notification.objects.filter(
            user=user, read=False
        ).select_related().order_by('-created_at')[:5]

        # Recent tasks assigned to me
        recent_my_tasks = my_tasks.select_related('project', 'sprint').order_by('-updated_at')[:8]

        # Sprints from my projects
        my_sprints = Sprint.objects.filter(
            project_id__in=my_project_ids, status='active'
        ).select_related('project').order_by('end_date')[:5]

        context.update({
            'my_projects': my_projects.select_related('area', 'lead').order_by('-created_at')[:6],
            'my_project_count': my_projects.count(),
            'my_task_stats': my_task_stats,
            'my_tasks': my_tasks,
            'recent_my_tasks': recent_my_tasks,
            'my_sprints': my_sprints,
            'time_this_week': time_this_week,
            'unread_notifications': unread_notifications,
            'has_projects': my_projects.exists(),
        })

    # ============================================================
    # EQUIPO (global stats for admin/jefe)
    # ============================================================
    else:
        projects = filter_queryset_by_role(Project.objects.all(), user, role, model_type='project')
        tasks = filter_queryset_by_role(Task.objects.all(), user, role, model_type='task')
        sprints = filter_queryset_by_role(Sprint.objects.all(), user, role, model_type='sprint')

        projects = projects.distinct()
        project_ids = list(projects.values_list('id', flat=True))
        tasks_in_projects = tasks.filter(project_id__in=project_ids) if project_ids else Task.objects.none()
        sprints_in_projects = sprints.filter(project_id__in=project_ids) if project_ids else Sprint.objects.none()

        task_stats = tasks_in_projects.aggregate(
            total=Count('id'),
            todo=Count('id', filter=Q(status__in=['backlog', 'todo'])),
            in_progress=Count('id', filter=Q(status='in-progress')),
            done=Count('id', filter=Q(status='done')),
            bugs=Count('id', filter=Q(type='bug', status__in=['backlog', 'todo', 'in-progress'])),
        )

        context.update({
            'total_projects': projects.count(),
            'active_projects': projects.filter(status='active').count(),
            'total_tasks': task_stats['total'],
            'todo_tasks': task_stats['todo'],
            'in_progress_tasks': task_stats['in_progress'],
            'done_tasks': task_stats['done'],
            'active_sprints': sprints_in_projects.filter(status='active').count(),
            'bugs': task_stats['bugs'],
            'recent_tasks': tasks_in_projects.select_related('assignee', 'project').order_by('-created_at')[:8],
            'recent_projects': projects.select_related('area', 'lead', 'client').order_by('-created_at')[:5],
            'has_projects': projects.exists(),
        })

        if role in ('super-admin', 'admin'):
            context['total_areas'] = Area.objects.count()
            context['total_users'] = User.objects.filter(is_active=True).count()

    return render(request, 'core/dashboard.html', context)
