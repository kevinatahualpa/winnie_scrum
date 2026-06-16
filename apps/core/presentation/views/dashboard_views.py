from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum

from apps.core.infrastructure.models.models import (
    Area, Project, Sprint, Task, User, Notification, TimeEntry, UserProfile
)
from apps.core.domain.services.permission_service import get_user_role, filter_queryset_by_role


@login_required
def ver_dashboard(request):
    """Render dashboard specific to each role.

    - Admin: Global company view (all projects, users, areas, bugs)
    - Jefe Area: Area-level view (projects in area, area members, tasks)
    - Jefe Proyecto: Project-level view (their projects, team tasks, sprints)
    - Miembro: Personal view (my tasks, my projects, my time, notifications)
    - Cliente: Redirected to client portal
    """
    user = request.user
    role = get_user_role(user)
    profile = getattr(user, 'profile', None)

    if role == 'cliente':
        return redirect('ver_portal_cliente')

    # Base context
    context = {
        'role': role,
        'user': user,
    }

    # ============================================================
    # ADMIN / SUPER-ADMIN
    # ============================================================
    if role in ('super-admin', 'admin'):
        area_id = request.GET.get('area')
        projects = Project.objects.all()
        tasks = Task.objects.all()
        sprints = Sprint.objects.all()

        if area_id:
            projects = projects.filter(area_id=area_id)
            tasks = tasks.filter(project__area_id=area_id)
            sprints = sprints.filter(project__area_id=area_id)

        task_stats = tasks.aggregate(
            total=Count('id'),
            todo=Count('id', filter=Q(status__in=['backlog', 'todo'])),
            in_progress=Count('id', filter=Q(status='in-progress')),
            done=Count('id', filter=Q(status='done')),
            bugs=Count('id', filter=Q(type='bug', status__in=['backlog', 'todo', 'in-progress'])),
        )

        # Pending registrations
        pending_count = UserProfile.objects.filter(status='pending').count()

        # Recent activity
        recent_tasks = tasks.select_related('assignee', 'project').order_by('-created_at')[:8]
        recent_projects = projects.select_related('area', 'lead', 'client').order_by('-created_at')[:5]

        # Time this week (all users)
        today = datetime.now().date()
        monday = today - timedelta(days=today.weekday())
        total_hours_week = TimeEntry.objects.filter(
            date__gte=monday, date__lte=today
        ).aggregate(total=Sum('hours'))['total'] or 0

        areas = Area.objects.filter(status='active')

        context.update({
            'total_projects': projects.count(),
            'active_projects': projects.filter(status='active').count(),
            'total_tasks': task_stats['total'],
            'todo_tasks': task_stats['todo'],
            'in_progress_tasks': task_stats['in_progress'],
            'done_tasks': task_stats['done'],
            'active_sprints': sprints.filter(status='active').count(),
            'bugs': task_stats['bugs'],
            'total_areas': Area.objects.count(),
            'total_users': User.objects.filter(is_active=True).count(),
            'pending_count': pending_count,
            'total_hours_week': total_hours_week,
            'recent_tasks': recent_tasks,
            'recent_projects': recent_projects,
            'has_projects': projects.exists(),
            'areas': areas,
            'selected_area': area_id,
        })

    # ============================================================
    # JEFE DE AREA
    # ============================================================
    elif role == 'jefe-area':
        user_area = profile.area if profile else None
        area_projects = Project.objects.filter(area=user_area) if user_area else Project.objects.none()
        area_project_ids = list(area_projects.values_list('id', flat=True))

        # Filtro por proyecto específico
        selected_project_id = request.GET.get('project')
        if selected_project_id and int(selected_project_id) in area_project_ids:
            filter_project_ids = [int(selected_project_id)]
        else:
            filter_project_ids = area_project_ids

        # Tasks in area projects (filtered by project if selected)
        area_tasks = Task.objects.filter(project_id__in=filter_project_ids) if filter_project_ids else Task.objects.none()
        task_stats = area_tasks.aggregate(
            total=Count('id'),
            todo=Count('id', filter=Q(status__in=['backlog', 'todo'])),
            in_progress=Count('id', filter=Q(status='in-progress')),
            done=Count('id', filter=Q(status='done')),
            bugs=Count('id', filter=Q(type='bug', status__in=['backlog', 'todo', 'in-progress'])),
        )

        # Members in area
        area_members = UserProfile.objects.filter(area=user_area, status='active').select_related('user').order_by('user__first_name') if user_area else []
        area_member_ids = [m.user_id for m in area_members]

        # Projects with member count
        area_projects_enriched = area_projects.select_related('area', 'lead', 'client').order_by('-created_at')
        for p in area_projects_enriched:
            p.member_count = p.members.count() + (1 if p.lead else 0)

        # Sprints in area
        area_sprints = Sprint.objects.filter(
            project_id__in=filter_project_ids, status='active'
        ).select_related('project').order_by('end_date')[:5]

        context.update({
            'user_area': user_area,
            'total_projects': area_projects.count(),
            'active_projects': area_projects.filter(status='active').count(),
            'total_tasks': task_stats['total'],
            'todo_tasks': task_stats['todo'],
            'in_progress_tasks': task_stats['in_progress'],
            'done_tasks': task_stats['done'],
            'bugs': task_stats['bugs'],
            'active_sprints': area_sprints.count(),
            'area_members': area_members,
            'area_member_count': len(area_members),
            'area_projects': area_projects_enriched,
            'recent_tasks': area_tasks.select_related('assignee', 'project').order_by('-created_at')[:8],
            'area_sprints': area_sprints,
            'has_projects': area_projects.exists(),
            'selected_project': selected_project_id,
        })

    # ============================================================
    # JEFE DE PROYECTO
    # ============================================================
    elif role == 'jefe-proyecto':
        # Projects where user is lead
        lead_projects = Project.objects.filter(lead=user)
        member_projects = Project.objects.filter(members=user)
        all_projects = (lead_projects | member_projects).distinct()
        project_ids = list(all_projects.values_list('id', flat=True))

        # Tasks in these projects
        project_tasks = Task.objects.filter(project_id__in=project_ids) if project_ids else Task.objects.none()
        task_stats = project_tasks.aggregate(
            total=Count('id'),
            todo=Count('id', filter=Q(status__in=['backlog', 'todo'])),
            in_progress=Count('id', filter=Q(status='in-progress')),
            done=Count('id', filter=Q(status='done')),
            bugs=Count('id', filter=Q(type='bug', status__in=['backlog', 'todo', 'in-progress'])),
        )

        # Team members across projects
        team_member_ids = set()
        for p in all_projects:
            for m in p.members.all():
                team_member_ids.add(m.id)
            if p.lead_id:
                team_member_ids.add(p.lead_id)
        team_members = UserProfile.objects.filter(
            user_id__in=team_member_ids, status='active'
        ).select_related('user', 'specialty').order_by('user__first_name')

        # Calculate task stats for each team member
        for member in team_members:
            member.task_total = Task.objects.filter(assignee=member.user).count()
            member.task_in_progress = Task.objects.filter(assignee=member.user, status='in-progress').count()
            member.task_done = Task.objects.filter(assignee=member.user, status='done').count()

        # Sprints in these projects
        project_sprints = Sprint.objects.filter(
            project_id__in=project_ids, status='active'
        ).select_related('project').order_by('end_date')[:5]

        # Projects with task count
        projects_enriched = all_projects.select_related('area', 'lead', 'client').order_by('-created_at')
        for p in projects_enriched:
            p.task_count = p.tasks.count()
            p.completed_task_count = p.tasks.filter(status='done').count()

        context.update({
            'total_projects': all_projects.count(),
            'active_projects': all_projects.filter(status='active').count(),
            'total_tasks': task_stats['total'],
            'todo_tasks': task_stats['todo'],
            'in_progress_tasks': task_stats['in_progress'],
            'done_tasks': task_stats['done'],
            'bugs': task_stats['bugs'],
            'active_sprints': project_sprints.count(),
            'team_members': team_members,
            'team_member_count': len(team_members),
            'projects': projects_enriched[:5],
            'recent_tasks': project_tasks.select_related('assignee', 'project').order_by('-created_at')[:8],
            'project_sprints': project_sprints,
            'has_projects': all_projects.exists(),
        })

    # ============================================================
    # MIEMBRO
    # ============================================================
    else:
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

    return render(request, 'core/dashboard.html', context)
