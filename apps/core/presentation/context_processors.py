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
