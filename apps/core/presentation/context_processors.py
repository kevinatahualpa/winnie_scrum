from django.core.cache import cache
from django.db.models import Q
from apps.core.infrastructure.models.models import (
    Notification, UserProfile, Message, Area, Client, Specialty,
    Project, ServiceRequest, Document,
)


def unread_notifications(request):
    """Context processor that injects notification and message data into all templates.

    Provides unread counts, notification preview (5 most recent), pending
    registration count for admins, unread message count, and archived
    items count for admin sidebar badge.
    Uses caching to reduce database queries.
    """
    context = {
        'unread_count': 0, 'notifications_preview': [],
        'pending_count': 0, 'unread_messages': 0,
        'archived_count': 0,
    }

    if request.user.is_authenticated:
        cache_key_unread = f'unread_count_{request.user.id}'
        cache_key_preview = f'notifications_preview_{request.user.id}'
        cache_key_msgs = f'unread_messages_{request.user.id}'

        unread_count = cache.get(cache_key_unread)
        if unread_count is None:
            unread_count = Notification.objects.filter(user=request.user, read=False).count()
            cache.set(cache_key_unread, unread_count, timeout=60)
        context['unread_count'] = unread_count

        notifications_preview = cache.get(cache_key_preview)
        if notifications_preview is None:
            notifications_preview = list(Notification.objects.filter(user=request.user).order_by('-created_at')[:5])
            cache.set(cache_key_preview, notifications_preview, timeout=120)
        context['notifications_preview'] = notifications_preview

        unread_messages = cache.get(cache_key_msgs)
        if unread_messages is None:
            unread_messages = Message.objects.filter(receiver=request.user, read=False).count()
            cache.set(cache_key_msgs, unread_messages, timeout=60)
        context['unread_messages'] = unread_messages

        profile = getattr(request.user, 'profile', None)
        role = profile.role if profile else 'miembro'
        if role in ('super-admin', 'admin'):
            cache_key_pending = 'pending_registrations_count'
            pending_count = cache.get(cache_key_pending)
            if pending_count is None:
                pending_count = UserProfile.objects.filter(status='pending').count()
                cache.set(cache_key_pending, pending_count, timeout=120)
            context['pending_count'] = pending_count

            cache_key_archived = 'archived_items_count'
            archived_count = cache.get(cache_key_archived)
            if archived_count is None:
                archived_count = (
                    Project.objects.filter(status='cancelled').count()
                    + Area.objects.filter(status='inactive').count()
                    + Client.objects.filter(is_active=False).count()
                    + Specialty.objects.filter(is_active=False).count()
                    + ServiceRequest.objects.filter(status='cancelled').count()
                    + Document.objects.filter(is_active=False).count()
                    + UserProfile.objects.filter(status__in=['dismissed', 'rejected']).count()
                )
                cache.set(cache_key_archived, archived_count, timeout=60)
            context['archived_count'] = archived_count

    return context


def sidebar_projects(request):
    """Inject the projects visible to the current user into the sidebar.

    Admins see all active projects; other roles see only the projects they
    have access to (via role-based filtering). Limited and cached to keep the
    sidebar light.
    """
    context = {'sidebar_projects': [], 'can_create_project': False}

    if not request.user.is_authenticated:
        return context

    from apps.core.domain.services.permission_service import (
        get_user_role, filter_queryset_by_role, can_manage_project, is_admin,
    )

    user = request.user
    role = get_user_role(user)

    if role == 'cliente':
        return context

    cache_key = f'sidebar_projects_{user.id}'
    projects = cache.get(cache_key)
    if projects is None:
        qs = Project.objects.exclude(status='cancelled').only('id', 'name')
        if not is_admin(user):
            qs = filter_queryset_by_role(qs, user, role, model_type='project')
        projects = list(qs.order_by('name')[:15])
        cache.set(cache_key, projects, timeout=60)

    context['sidebar_projects'] = projects
    context['can_create_project'] = can_manage_project(user)
    return context


def quick_task_data(request):
    """Provide data for the global quick-create task modal (topbar search).

    Exposes the projects and assignees the user can pick, plus whether the
    user is allowed to create tasks at all. Cached briefly.
    """
    context = {'quick_task_projects': [], 'quick_task_assignees': [], 'can_create_task': False}

    if not request.user.is_authenticated:
        return context

    from apps.core.domain.services.permission_service import (
        get_user_role, filter_queryset_by_role, can_manage_task, is_admin,
    )

    user = request.user
    role = get_user_role(user)

    if role == 'cliente' or not can_manage_task(user):
        return context

    context['can_create_task'] = True

    cache_key_p = f'quick_task_projects_{user.id}'
    projects = cache.get(cache_key_p)
    if projects is None:
        qs = Project.objects.filter(status='active').only('id', 'name')
        if not is_admin(user):
            qs = filter_queryset_by_role(qs, user, role, model_type='project')
        projects = list(qs.order_by('name'))
        cache.set(cache_key_p, projects, timeout=120)
    context['quick_task_projects'] = projects

    cache_key_a = 'quick_task_assignees'
    assignees = cache.get(cache_key_a)
    if assignees is None:
        user_ids = list(UserProfile.objects.filter(status='active').values_list('user_id', flat=True))
        from apps.core.infrastructure.models.models import User as UserModel
        assignees = list(
            UserModel.objects.filter(is_active=True, id__in=user_ids)
            .select_related('profile').order_by('first_name')
        )
        cache.set(cache_key_a, assignees, timeout=120)
    context['quick_task_assignees'] = assignees

    return context

