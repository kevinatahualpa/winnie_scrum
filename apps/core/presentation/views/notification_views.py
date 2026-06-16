from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from apps.core.infrastructure.models.models import Notification


@login_required
def ver_notificaciones(request):
    """Render the user's notification page showing the 50 most recent notifications."""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:50]
    return render(request, 'core/notifications.html', {'notifications': notifications})


@require_POST
@login_required
def marcar_notificacion_leida(request, pk):
    """Mark a single notification as read. User must own the notification."""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.read = True
    notification.save()
    return redirect('ver_notificaciones')


@require_POST
@login_required
def marcar_todas_leidas(request):
    """Mark all of the user's unread notifications as read in a single query."""
    Notification.objects.filter(user=request.user, read=False).update(read=True)
    return redirect('ver_notificaciones')
