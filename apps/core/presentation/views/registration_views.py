from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods, require_POST
from django.utils import timezone

from apps.core.infrastructure.models.models import (
    UserProfile, Area, User, Specialty, CandidateProfile,
)
from apps.core.domain.services.permission_service import get_user_role, is_super_admin
from apps.core.domain.services.notification_service import create_notification, create_audit_log


@login_required
def ver_pendientes(request):
    """Listado de candidatos pendientes con preview de skills y CV."""
    role = get_user_role(request.user)
    if role not in ('super-admin', 'admin'):
        messages.error(request, 'No tienes permiso para ver esta pagina')
        return redirect('ver_dashboard')

    pending_users = (
        UserProfile.objects
        .filter(status='pending')
        .select_related('user', 'user__candidate_profile', 'user__candidate_profile__primary_specialty')
        .prefetch_related(
            'user__candidate_profile__candidatetechnology_set__technology',
            'user__candidate_profile__secondary_specialties',
        )
        .order_by('-created_at')
    )
    areas = Area.objects.filter(status='active')
    specialties = Specialty.objects.select_related('parent').order_by('category', 'name')

    return render(request, 'core/pending_registrations.html', {
        'pending_users': pending_users,
        'areas': areas,
        'specialties': specialties,
    })


@require_http_methods(["GET", "POST"])
@login_required
def aprobar_registro(request, pk):
    """Aprueba un candidato. Admite asignar rol final, area, especialidad y notas."""
    role = get_user_role(request.user)
    if role not in ('super-admin', 'admin'):
        messages.error(request, 'No tienes permiso')
        return redirect('ver_pendientes')

    user_profile = get_object_or_404(UserProfile, pk=pk, status='pending')

    if request.method == 'POST':
        area_id = request.POST.get('area') or None
        specialty_id = request.POST.get('specialty') or None
        requested_role = request.POST.get('role', 'miembro')
        review_notes = (request.POST.get('review_notes') or '').strip()

        if requested_role not in dict(UserProfile._meta.get_field('role').choices):
            requested_role = 'miembro'
        if requested_role in ('super-admin', 'admin') and not is_super_admin(request.user):
            messages.error(request, 'Solo el super-admin puede asignar ese rol')
            return redirect('aprobar_registro', pk=pk)

        user_profile.status = 'active'
        user_profile.role = requested_role
        user_profile.area_id = area_id
        user_profile.specialty_id = specialty_id
        user_profile.save()

        cp = CandidateProfile.objects.filter(user=user_profile.user).first()
        if cp:
            cp.reviewed_at = timezone.now()
            cp.reviewed_by = request.user
            if review_notes:
                cp.review_notes = review_notes
            cp.save(update_fields=['reviewed_at', 'reviewed_by', 'review_notes'])

        create_notification(
            user_profile.user, 'registration_approved', 'Cuenta aprobada',
            f'Tu registro fue aprobado por {request.user.get_full_name()} '
            f'con el rol "{user_profile.get_role_display()}". Ya puedes iniciar sesion en Winnie.',
            'fa-check-circle',
        )
        create_audit_log(
            request.user, 'USER_APPROVE', 'user', user_profile.user.id,
            f'Usuario aprobado: {user_profile.user.get_full_name()}, '
            f'rol: {requested_role}, area: {user_profile.area}, '
            f'especialidad: {user_profile.specialty}',
        )

        messages.success(
            request,
            f'Usuario "{user_profile.user.get_full_name()}" aprobado como {user_profile.get_role_display()}',
        )
        return redirect('ver_pendientes')

    areas = Area.objects.filter(status='active')
    specialties = Specialty.objects.select_related('parent').order_by('category', 'name')
    cp = CandidateProfile.objects.filter(user=user_profile.user).first()
    return render(request, 'core/approve_registration.html', {
        'user_profile': user_profile,
        'areas': areas,
        'specialties': specialties,
        'candidate': cp,
    })


@require_POST
@login_required
def rechazar_registro(request, pk):
    """Rechaza y elimina un candidato pendiente."""
    role = get_user_role(request.user)
    if role not in ('super-admin', 'admin'):
        messages.error(request, 'No tienes permiso')
        return redirect('ver_pendientes')

    user_profile = get_object_or_404(UserProfile, pk=pk, status='pending')
    user_obj = user_profile.user
    user_name = user_obj.get_full_name()
    review_notes = (request.POST.get('review_notes') or '').strip()

    create_notification(
        user_obj, 'registration_rejected', 'Registro rechazado',
        f'Tu registro fue rechazado por {request.user.get_full_name()}. '
        + (f'Motivo: {review_notes} ' if review_notes else '')
        + 'Si crees que es un error, contacta a un administrador.',
        'fa-times-circle',
    )
    create_audit_log(
        request.user, 'USER_REJECT', 'user', user_obj.id,
        f'Usuario rechazado: {user_name}',
    )

    user_obj.delete()
    messages.success(request, f'Usuario "{user_name}" rechazado y eliminado')
    return redirect('ver_pendientes')
