"""Vistas para revision de candidatos en formato drawer.

Cuando el admin hace click en el ojo de la lista de pendientes, se abre
un drawer (off-canvas) con dos paneles:

  - Izquierda: checklist de validacion (7 puntos) + nota libre
  - Derecha:  PDF del CV embebido, agrandable a fullscreen

Los checks se guardan via AJAX (sin recargar), y al final el admin
puede aprobar o rechazar desde el mismo drawer.
"""

import mimetypes
import os

from django.contrib.auth.decorators import login_required
from django.http import (
    FileResponse, HttpResponseBadRequest, JsonResponse,
)
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST, require_http_methods

from apps.core.domain.services.notification_service import (
    create_audit_log, create_notification,
)
from apps.core.domain.services.permission_service import (
    get_user_role, is_super_admin,
)
from apps.core.domain.services.ai_service import analyze_candidate
from apps.core.infrastructure.models.models import (
    Area, CandidateProfile, Specialty, UserProfile,
)


CHECKLIST_ITEMS = [
    ('cv_coherente', 'CV coherente con skills', 'fa-file-contract',
     'El CV describe las tecnologias y nivel que el candidato declaro.'),
    ('experiencia', 'Años de experiencia plausibles', 'fa-briefcase',
     'Los años de experiencia declarados son consistentes con el CV.'),
    ('tecnologias', 'Nivel tecnico creible', 'fa-code',
     'Las tecnologias marcadas como Avanzado/Experto son plausibles.'),
    ('documentacion', 'Documentacion valida', 'fa-certificate',
     'Hay certificados, titulos u otra documentacion que respalde el perfil.'),
]

# Score minimo para aprobar (de un total de 4 checks)
MIN_SCORE_TO_APPROVE = 3


def _normalize_check_entry(entry):
    """Convierte un check al formato uniforme {value, confidence, evidence}.

    Acepta:
      - bool (formato antiguo sin IA): True/False -> confidence 100
      - dict: lo devuelve tal cual
      - None/missing: {False, 0, ''}
    """
    if entry is None or entry is False:
        return {'value': False, 'confidence': 0, 'evidence': ''}
    if entry is True:
        return {'value': True, 'confidence': 100, 'evidence': 'Marcado manualmente'}
    if isinstance(entry, dict):
        return {
            'value': bool(entry.get('value', False)),
            'confidence': int(entry.get('confidence', 0)),
            'evidence': str(entry.get('evidence', '')),
        }
    return {'value': False, 'confidence': 0, 'evidence': ''}


def _normalize_checklist(checklist):
    """Normaliza todos los checks al formato dict."""
    return {key: _normalize_check_entry(checklist.get(key)) for key, *_ in CHECKLIST_ITEMS}


def _require_admin(request):
    role = get_user_role(request.user)
    if role not in ('super-admin', 'admin'):
        return False
    return True


@login_required
def candidato_detalle(request, pk):
    """Drawer/page con CV embebido y checklist de validacion."""
    if not _require_admin(request):
        return JsonResponse({'error': 'forbidden'}, status=403)

    profile = get_object_or_404(UserProfile, pk=pk, status='pending')
    candidate = (
        CandidateProfile.objects
        .select_related('user', 'primary_specialty', 'reviewed_by')
        .prefetch_related(
            'secondary_specialties',
            'candidatetechnology_set__technology',
        )
        .filter(user=profile.user)
        .first()
    )

    existing = candidate.review_checklist if candidate else {}
    all_areas = Area.objects.filter(status='active')

    # CSRF: usamos get_token que devuelve el masked token correcto.
    # Si no hay cookie, crea una nueva. La cookie csrftoken del browser
    # ya tiene el secret correcto, asi que el masked token generado
    # sera valido para el siguiente POST en la misma sesion.
    from django.middleware.csrf import get_token
    csrf_token = get_token(request)

    response = render(request, 'core/candidate_drawer.html', {
        'user_profile': profile,
        'candidate': candidate,
        'checklist_items': CHECKLIST_ITEMS,
        'existing_checklist': _normalize_checklist(existing),
        'all_areas': all_areas,
        'csrf_secret': csrf_token,
    })
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate'
    # Permitir que el drawer se embeba en sí mismo (el iframe del PDF)
    response['X-Frame-Options'] = 'SAMEORIGIN'
    return response


@login_required
@require_POST
def candidato_save_checklist(request, pk):
    """Guarda el checklist via AJAX y devuelve el score actualizado."""
    if not _require_admin(request):
        return JsonResponse({'error': 'forbidden'}, status=403)

    profile = get_object_or_404(UserProfile, pk=pk, status='pending')
    candidate = CandidateProfile.objects.filter(user=profile.user).first()
    if not candidate:
        return JsonResponse({'error': 'no_candidate'}, status=404)

    valid_keys = {k for k, *_ in CHECKLIST_ITEMS}
    cleaned = {}
    score = 0
    for key in valid_keys:
        # Acepta 'true'/'false' (str) o True/False (bool)
        raw = request.POST.get(key, 'false')
        value = raw in ('true', 'True', '1', True, 'on')
        cleaned[key] = {
            'value': value,
            'confidence': 100,
            'evidence': 'Marcado manualmente por el revisor' if value else '',
        }
        if value:
            score += 1

    note = (request.POST.get('note') or '').strip()[:1000]

    candidate.review_checklist = cleaned
    candidate.checklist_score = score
    candidate.checklist_completed_at = timezone.now()
    candidate.reviewed_by = request.user
    if note and not candidate.review_notes:
        candidate.review_notes = note
    candidate.save(update_fields=[
        'review_checklist', 'checklist_score',
        'checklist_completed_at', 'reviewed_by', 'review_notes',
    ])

    create_audit_log(
        request.user, 'CANDIDATE_CHECKLIST', 'user', profile.user.id,
        f'Checklist de {profile.user.get_full_name()}: {score}/7 checks',
    )

    return JsonResponse({
        'ok': True,
        'score': score,
        'total': len(CHECKLIST_ITEMS),
        'completed_at': candidate.checklist_completed_at.strftime('%d/%m/%Y %H:%M'),
    })


@login_required
def cv_embed(request, pk):
    """Sirve el CV del candidato con headers que permiten iframe same-origin.

    Sirve el archivo desde MEDIA_ROOT pero sobreescribe X-Frame-Options
    y CSP frame-ancestors para que el PDF pueda embeberse dentro del
    drawer de revision (mismo origen).
    """
    if not _require_admin(request):
        return JsonResponse({'error': 'forbidden'}, status=403)

    profile = get_object_or_404(UserProfile, pk=pk, status='pending')
    candidate = CandidateProfile.objects.filter(user=profile.user).first()
    if not candidate or not candidate.cv_file:
        resp = HttpResponseBadRequest('Sin CV')
        resp['X-Frame-Options'] = 'SAMEORIGIN'
        return resp

    try:
        cv = candidate.cv_file
        content_type, _ = mimetypes.guess_type(cv.name)
        if not content_type:
            content_type = 'application/octet-stream'

        response = FileResponse(cv.open('rb'), content_type=content_type)
        response['Content-Disposition'] = (
            f'inline; filename="{os.path.basename(cv.name)}"'
        )
        response['X-Frame-Options'] = 'SAMEORIGIN'
        response['Content-Security-Policy'] = "frame-ancestors 'self'"
        response['Cache-Control'] = 'private, max-age=300'
        return response
    except Exception:
        resp = HttpResponseBadRequest('Error al leer el archivo')
        resp['X-Frame-Options'] = 'SAMEORIGIN'
        return resp


@login_required
@require_POST
def candidato_decidir(request, pk):
    """Aprueba o rechaza desde el drawer, en una sola decision."""
    if not _require_admin(request):
        return JsonResponse({'error': 'forbidden'}, status=403)

    profile = get_object_or_404(UserProfile, pk=pk, status='pending')
    decision = request.POST.get('decision', '')
    if decision not in ('approve', 'reject'):
        return HttpResponseBadRequest('decision invalida')

    candidate = CandidateProfile.objects.filter(user=profile.user).first()
    if not candidate:
        return JsonResponse({'error': 'no_candidate'}, status=404)

    score = candidate.checklist_score
    total = len(CHECKLIST_ITEMS)
    if decision == 'approve' and score < MIN_SCORE_TO_APPROVE:
        return JsonResponse({
            'ok': False,
            'error': f'Score {score}/{total} insuficiente. Minimo {MIN_SCORE_TO_APPROVE} checks para aprobar.',
        }, status=400)

    if decision == 'approve':
        area_id = request.POST.get('area') or None
        specialty_id = request.POST.get('specialty') or None
        requested_role = request.POST.get('role', 'miembro')

        if requested_role not in dict(UserProfile._meta.get_field('role').choices):
            requested_role = 'miembro'
        if requested_role in ('super-admin', 'admin') and not is_super_admin(request.user):
            return JsonResponse({'error': 'forbidden_role'}, status=403)

        profile.status = 'active'
        profile.role = requested_role
        profile.area_id = area_id
        profile.specialty_id = specialty_id
        profile.save()

        candidate.reviewed_at = timezone.now()
        candidate.save(update_fields=['reviewed_at'])

        create_notification(
            profile.user, 'registration_approved', 'Cuenta aprobada',
            f'Tu registro fue aprobado por {request.user.get_full_name()} '
            f'como {profile.get_role_display()}. Score del revisor: {score}/{total}.',
            'fa-check-circle',
        )
        create_audit_log(
            request.user, 'USER_APPROVE', 'user', profile.user.id,
            f'Usuario aprobado: {profile.user.get_full_name()}, rol: {requested_role}, '
            f'score checklist: {score}/{total}',
        )
    return JsonResponse({'ok': True, 'redirect': '/ver_pendientes/'})


@login_required
def candidato_ai_review(request, pk):
    """Endpoint AJAX: analiza un candidato con IA y devuelve JSON."""
    if not _require_admin(request):
        return JsonResponse({'error': 'forbidden'}, status=403)

    profile = get_object_or_404(UserProfile, pk=pk, status='pending')
    candidate = (
        CandidateProfile.objects
        .select_related('user', 'primary_specialty')
        .prefetch_related('candidatetechnology_set__technology')
        .filter(user=profile.user)
        .first()
    )
    if not candidate:
        return JsonResponse({'error': 'Sin perfil de candidato'}, status=404)

    result = analyze_candidate(candidate)
    return JsonResponse(result)

    notes = (request.POST.get('notes') or '').strip()
    user_obj = profile.user
    user_name = user_obj.get_full_name()
    create_notification(
        user_obj, 'registration_rejected', 'Registro rechazado',
        f'Tu registro fue rechazado por {request.user.get_full_name()}. '
        + (f'Motivo: {notes} ' if notes else '')
        + f'Score del revisor: {score}/{total}.',
        'fa-times-circle',
    )
    create_audit_log(
        request.user, 'USER_REJECT', 'user', user_obj.id,
        f'Usuario rechazado: {user_name} (score {score}/{total})',
    )

    profile.status = 'rejected'
    user_obj.is_active = False
    profile.save(update_fields=['status'])
    user_obj.save(update_fields=['is_active'])

    return JsonResponse({'ok': True, 'redirect': '/ver_pendientes/'})
