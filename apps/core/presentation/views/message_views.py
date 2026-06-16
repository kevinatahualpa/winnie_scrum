from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q, Max
from django.views.decorators.http import require_POST, require_GET

from apps.core.infrastructure.models.models import Message, UserProfile, Project, Comment
from apps.core.domain.services.notification_service import create_notification
from apps.core.domain.services.permission_service import filter_queryset_by_role, get_user_role


def _get_threads(user):
    """Build unified conversation list: DMs + project chats, sorted by last activity."""
    role = get_user_role(user)
    threads = []

    available_projects = filter_queryset_by_role(
        Project.objects.all(), user, role, model_type='project'
    )

    project_ids = set(available_projects.values_list('id', flat=True))

    dm_last = Message.objects.filter(
        Q(sender=user) | Q(receiver=user)
    ).values('sender', 'receiver').annotate(
        last_msg=Max('created_at')
    )

    seen_users = set()
    for conv in dm_last:
        other_id = conv['receiver'] if conv['sender'] == user.id else conv['sender']
        if other_id in seen_users:
            continue
        seen_users.add(other_id)
        last = Message.objects.filter(
            Q(sender=user, receiver_id=other_id) | Q(sender_id=other_id, receiver=user)
        ).latest('created_at')
        unread = Message.objects.filter(sender_id=other_id, receiver=user, read=False).count()
        partner = User.objects.select_related('profile').get(id=other_id)
        threads.append({
            'type': 'dm',
            'partner': partner,
            'unread': unread,
            'last_time': last.created_at,
            'last_text': last.subject,
            'last_preview': last.body[:60],
            'is_mine': last.sender == user,
            'url_name': 'ver_conversacion',
            'url_id': partner.id,
        })

    project_comments = Comment.objects.filter(
        project_id__in=project_ids
    ).values('project_id').annotate(
        last_cm=Max('created_at')
    )

    for pc in project_comments:
        p = available_projects.filter(id=pc['project_id']).first()
        if not p:
            continue
        last = Comment.objects.filter(project=p).latest('created_at')
        threads.append({
            'type': 'project',
            'project': p,
            'unread': 0,
            'last_time': last.created_at,
            'last_text': p.name,
            'last_preview': last.text[:60],
            'is_mine': last.author == user,
            'url_name': 'ver_detalle_proyecto',
            'url_id': p.id,
        })

    threads.sort(key=lambda t: t['last_time'], reverse=True)
    return threads


@login_required
def ver_mensajes(request):
    """WhatsApp-style inbox: left panel with conversations (DMs + projects)."""
    return render(request, 'core/messages_inbox.html', {
        'threads': _get_threads(request.user),
    })


@login_required
def ver_conversacion(request, user_id):
    """WhatsApp-style inbox with an active DM conversation on the right panel."""
    current = request.user
    partner = get_object_or_404(User.objects.select_related('profile'), pk=user_id)

    msgs = Message.objects.filter(
        Q(sender=current, receiver=partner) | Q(sender=partner, receiver=current)
    ).order_by('created_at')

    Message.objects.filter(sender=partner, receiver=current, read=False).update(read=True)

    users = User.objects.filter(is_active=True, profile__status='active').exclude(id=current.id).select_related('profile').order_by('first_name')

    projects = filter_queryset_by_role(
        Project.objects.filter(status='active'), current, model_type='project'
    ).order_by('name')

    return render(request, 'core/messages_inbox.html', {
        'threads': _get_threads(current),
        'partner': partner,
        'messages_list': msgs,
        'users': users,
        'projects': projects,
    })


@require_GET
@login_required
def buscar_usuarios(request):
    """AJAX endpoint: return users filtered by project (optional) and search term."""
    from django.http import JsonResponse
    term = request.GET.get('q', '').strip()
    project_id = request.GET.get('project', '').strip()

    qs = User.objects.filter(is_active=True, profile__status='active').exclude(id=request.user.id)

    if project_id:
        qs = qs.filter(Q(projects__id=project_id) | Q(led_projects__id=project_id)).distinct()

    if term:
        qs = qs.filter(
            Q(first_name__icontains=term) | Q(last_name__icontains=term) | Q(email__icontains=term)
        )

    qs = qs.select_related('profile')[:15]

    data = [{
        'id': u.id,
        'name': u.get_full_name() or u.username,
        'email': u.email,
        'initials': u.profile.initials if hasattr(u, 'profile') else u.username[:2].upper(),
        'color': getattr(u.profile, 'color', '#00bcd4'),
        'role': getattr(u.profile, 'get_role_display', lambda: '')() if hasattr(u, 'profile') else '',
    } for u in qs]

    return JsonResponse({'users': data})


@require_POST
@login_required
def enviar_mensaje(request):
    """Send a private message to another user. Supports ?next= for redirect."""
    receiver_id = request.POST.get('receiver_id')
    subject = request.POST.get('subject', '').strip()
    body = request.POST.get('body', '').strip()
    next_url = request.POST.get('next', '').strip()

    if not receiver_id or not subject or not body:
        messages.error(request, 'Todos los campos son obligatorios')
        return redirect('ver_mensajes')

    receiver = get_object_or_404(User, pk=receiver_id)

    Message.objects.create(
        sender=request.user,
        receiver=receiver,
        subject=subject,
        body=body,
    )

    create_notification(
        receiver, 'new_message', 'Nuevo mensaje',
        f'{request.user.get_full_name()} te ha enviado un mensaje',
        'fa-envelope'
    )

    messages.success(request, f'Mensaje enviado a {receiver.get_full_name() or receiver.username}')
    if next_url:
        return redirect(next_url)
    return redirect('ver_conversacion', user_id=receiver.id)
