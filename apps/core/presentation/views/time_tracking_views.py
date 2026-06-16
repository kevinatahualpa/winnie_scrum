from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta

from apps.core.infrastructure.models.models import TimeEntry, Task
from apps.core.domain.services.permission_service import get_user_role


@login_required
def ver_tiempo(request):
    """Render the time tracking page showing the user's time entries.

    Displays today's and this week's total hours. Shows the 50 most recent entries.
    """
    user = request.user
    entries = TimeEntry.objects.filter(user=user).select_related('task').order_by('-date')
    today = timezone.now().date()
    today_entries = entries.filter(date=today)
    total_hours_today = today_entries.aggregate(total=Sum('hours'))['total'] or 0

    week_ago = today - timedelta(days=7)
    week_entries = entries.filter(date__gte=week_ago)
    total_hours_week = week_entries.aggregate(total=Sum('hours'))['total'] or 0

    return render(request, 'core/time_tracking.html', {
        'entries': entries[:50], 'today_entries': today_entries,
        'total_hours_today': total_hours_today, 'total_hours_week': total_hours_week,
    })


@require_POST
@login_required
def registrar_tiempo(request):
    """Create a new time entry for a task.

    Members can only log time on tasks they are assigned to.
    """
    task = get_object_or_404(Task, pk=request.POST.get('task'))
    role = get_user_role(request.user)

    if role == 'miembro' and task.assignee != request.user:
        messages.error(request, 'No tienes permiso para registrar tiempo en esta tarea')
        return redirect('ver_tiempo')

    TimeEntry.objects.create(
        task=task, user=request.user,
        date=request.POST.get('date', timezone.now().date()),
        hours=float(request.POST.get('hours', 0)),
        description=request.POST.get('description', ''),
    )

    messages.success(request, 'Tiempo registrado')
    return redirect('ver_tiempo')
