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

    All heavy aggregations use annotate/aggregate to avoid N+1 queries.
    """
    user = request.user
    role = get_user_role(user)
    profile = getattr(user, 'profile', None)

    if role == 'cliente':
        return redirect('ver_portal_cliente')

    context = {
        'role': role,
        'user': user,
    }

    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())

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
            todo=Count('id', filter=Q(status='TODO')),
            in_progress=Count('id', filter=Q(status='PROG')),
            done=Count('id', filter=Q(status='DONE')),
            bugs=Count('id', filter=Q(type='bug', status__in=['TODO', 'PROG'])),
        )

        pending_count = UserProfile.objects.filter(status='pending').count()

        recent_tasks = tasks.select_related('assignee', 'project').order_by('-created_at')[:8]
        recent_projects = projects.select_related('area', 'lead', 'client').order_by('-created_at')[:5]

        total_hours_week = TimeEntry.objects.filter(
            date__gte=monday, date__lte=today
        ).aggregate(total=Sum('hours'))['total'] or 0

        project_stats = projects.aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(status='active')),
        )
        total_areas = Area.objects.filter(status='active').count()
        total_users = User.objects.filter(is_active=True).count()
        active_sprints = sprints.filter(status='ACT').count()

        context.update({
            'total_projects': project_stats['total'],
            'active_projects': project_stats['active'],
            'total_tasks': task_stats['total'],
            'todo_tasks': task_stats['todo'],
            'in_progress_tasks': task_stats['in_progress'],
            'done_tasks': task_stats['done'],
            'active_sprints': active_sprints,
            'bugs': task_stats['bugs'],
            'total_areas': total_areas,
            'total_users': total_users,
            'pending_count': pending_count,
            'total_hours_week': total_hours_week,
            'recent_tasks': recent_tasks,
            'recent_projects': recent_projects,
            'has_projects': project_stats['total'] > 0,
            'areas': Area.objects.filter(status='active'),
            'selected_area': area_id,
        })

    elif role == 'jefe-area':
        user_area = profile.area if profile else None
        area_projects = Project.objects.filter(area=user_area) if user_area else Project.objects.none()
        area_project_ids = list(area_projects.values_list('id', flat=True))

        selected_project_id = request.GET.get('project')
        if selected_project_id and int(selected_project_id) in area_project_ids:
            filter_project_ids = [int(selected_project_id)]
        else:
            filter_project_ids = area_project_ids

        area_tasks = Task.objects.filter(project_id__in=filter_project_ids) if filter_project_ids else Task.objects.none()
        task_stats = area_tasks.aggregate(
            total=Count('id'),
            todo=Count('id', filter=Q(status='TODO')),
            in_progress=Count('id', filter=Q(status='PROG')),
            done=Count('id', filter=Q(status='DONE')),
            bugs=Count('id', filter=Q(type='bug', status__in=['TODO', 'PROG'])),
        )

        area_members = UserProfile.objects.filter(
            area=user_area, status='active'
        ).select_related('user').order_by('user__first_name') if user_area else []

        area_projects_enriched = (
            area_projects
            .annotate(_member_count=Count('members', distinct=True))
            .select_related('area', 'lead', 'client')
            .order_by('-created_at')
        )
        for p in area_projects_enriched:
            p.member_count = p._member_count + (1 if p.lead else 0)

        area_sprints_qs = Sprint.objects.filter(
            project_id__in=filter_project_ids, status='active'
        ).select_related('project').order_by('end_date')[:5]
        active_sprints = Sprint.objects.filter(
            project_id__in=filter_project_ids, status='active'
        ).count()
        project_stats = area_projects.aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(status='active')),
        )

        context.update({
            'user_area': user_area,
            'total_projects': project_stats['total'],
            'active_projects': project_stats['active'],
            'total_tasks': task_stats['total'],
            'todo_tasks': task_stats['todo'],
            'in_progress_tasks': task_stats['in_progress'],
            'done_tasks': task_stats['done'],
            'bugs': task_stats['bugs'],
            'active_sprints': active_sprints,
            'area_members': area_members,
            'area_member_count': len(area_members),
            'area_projects': area_projects_enriched,
            'recent_tasks': area_tasks.select_related('assignee', 'project').order_by('-created_at')[:8],
            'area_sprints': area_sprints_qs,
            'has_projects': project_stats['total'] > 0,
            'selected_project': selected_project_id,
        })

    elif role == 'jefe-proyecto':
        lead_projects = Project.objects.filter(lead=user)
        member_projects = Project.objects.filter(members=user)
        all_projects = (lead_projects | member_projects).distinct()
        project_ids = list(all_projects.values_list('id', flat=True))

        project_tasks = Task.objects.filter(project_id__in=project_ids) if project_ids else Task.objects.none()
        task_stats = project_tasks.aggregate(
            total=Count('id'),
            todo=Count('id', filter=Q(status='TODO')),
            in_progress=Count('id', filter=Q(status='PROG')),
            done=Count('id', filter=Q(status='DONE')),
            bugs=Count('id', filter=Q(type='bug', status__in=['TODO', 'PROG'])),
        )

        # Team members: extract IDs in a single query (no nested loops)
        team_member_ids = set(
            User.objects.filter(
                Q(projects__in=project_ids) | Q(led_projects__in=project_ids)
            ).values_list('id', flat=True).distinct()
        )
        team_member_ids.discard(user.id)

        team_members = (
            UserProfile.objects
            .filter(user_id__in=team_member_ids, status='active')
            .annotate(
                task_total=Count(
                    'user__assigned_tasks',
                    filter=Q(user__assigned_tasks__project_id__in=project_ids),
                ),
                task_in_progress=Count(
                    'user__assigned_tasks',
                    filter=Q(
                        user__assigned_tasks__project_id__in=project_ids,
                        user__assigned_tasks__status='PROG',
                    ),
                ),
                task_done=Count(
                    'user__assigned_tasks',
                    filter=Q(
                        user__assigned_tasks__project_id__in=project_ids,
                        user__assigned_tasks__status='DONE',
                    ),
                ),
            )
            .select_related('user', 'specialty')
            .order_by('user__first_name')
        )

        project_sprints_qs = Sprint.objects.filter(
            project_id__in=project_ids, status='active'
        ).select_related('project').order_by('end_date')[:5]
        active_sprints = Sprint.objects.filter(
            project_id__in=project_ids, status='active'
        ).count()

        projects_enriched = (
            all_projects
            .annotate(
                task_count=Count('tasks', distinct=True),
                completed_task_count=Count(
                    'tasks', filter=Q(tasks__status='DONE'), distinct=True
                ),
            )
            .select_related('area', 'lead', 'client')
            .order_by('-created_at')
        )
        project_stats = all_projects.aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(status='active')),
        )

        context.update({
            'total_projects': project_stats['total'],
            'active_projects': project_stats['active'],
            'total_tasks': task_stats['total'],
            'todo_tasks': task_stats['todo'],
            'in_progress_tasks': task_stats['in_progress'],
            'done_tasks': task_stats['done'],
            'bugs': task_stats['bugs'],
            'active_sprints': active_sprints,
            'team_members': team_members,
            'team_member_count': team_members.count(),
            'projects': projects_enriched[:5],
            'recent_tasks': project_tasks.select_related('assignee', 'project').order_by('-created_at')[:8],
            'project_sprints': project_sprints_qs,
            'has_projects': project_stats['total'] > 0,
        })

    else:
        my_projects = Project.objects.filter(
            Q(members=user) | Q(lead=user)
        ).distinct()
        my_project_ids = list(my_projects.values_list('id', flat=True))

        my_tasks = Task.objects.filter(assignee=user)
        my_task_stats = my_tasks.aggregate(
            total=Count('id'),
            todo=Count('id', filter=Q(status='TODO')),
            in_progress=Count('id', filter=Q(status='PROG')),
            done=Count('id', filter=Q(status='DONE')),
            bugs=Count('id', filter=Q(type='bug', status__in=['TODO', 'PROG'])),
        )

        time_this_week = TimeEntry.objects.filter(
            user=user, date__gte=monday, date__lte=today
        ).aggregate(total=Sum('hours'))['total'] or 0

        unread_notifications = Notification.objects.filter(
            user=user, read=False
        ).select_related().order_by('-created_at')[:5]

        recent_my_tasks = my_tasks.select_related('project', 'sprint').order_by('-updated_at')[:8]

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
