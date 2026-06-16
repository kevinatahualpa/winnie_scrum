"""Wizard de auto-registro en 3 pasos.

Inspirado en patrones de LinkedIn, Trello y Notion: el visitante nunca
ve un formulario gigante. Cada paso valida su propio bloque y persiste
en sesion hasta que el ultimo paso crea el User + UserProfile +
CandidateProfile en una sola transaccion.

Pasos:
    1. Datos basicos     -> email, password, nombre, apellido
    2. Perfil profesional-> headline, bio, años, links, especialidad
    3. Skills + CV       -> tecnologias con nivel + archivo CV

Estado guardado en request.session bajo la clave 'reg_wizard'.
"""

import secrets
import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST
from django.core.exceptions import ValidationError
from django.db import transaction
import logging

from apps.core.infrastructure.models.models import (
    CandidateProfile, CandidateTechnology, RegistrationRequest, Specialty, Technology, UserProfile,
)
from apps.core.domain.services.notification_service import create_notification, create_audit_log
from apps.core.domain.services.permission_service import is_admin

logger = logging.getLogger(__name__)


WIZARD_SESSION_KEY = 'reg_wizard'
ALLOWED_CV_EXT = {'.pdf', '.doc', '.docx'}
MAX_CV_BYTES = 5 * 1024 * 1024  # 5MB


def _get_wizard(request):
    return request.session.get(WIZARD_SESSION_KEY, {})


def _set_wizard(request, data):
    request.session[WIZARD_SESSION_KEY] = data
    request.session.modified = True


def _clear_wizard(request):
    request.session.pop(WIZARD_SESSION_KEY, None)
    request.session.modified = True


def _step_progress(step):
    return {'current': step, 'total': 3}


# ---------------------------------------------------------------------------
# Paso 1: datos basicos
# ---------------------------------------------------------------------------

@require_http_methods(["GET", "POST"])
def registro_paso1(request):
    """Paso 1 del wizard: email, contraseña, nombre, apellido.

    Valida que el email no este registrado antes de continuar.
    """
    if request.user.is_authenticated:
        return redirect('ver_dashboard')

    if request.method == 'POST':
        email = (request.POST.get('email') or '').strip().lower()
        password = request.POST.get('password') or ''
        password_confirm = request.POST.get('password_confirm') or ''
        first_name = (request.POST.get('first_name') or '').strip()
        last_name = (request.POST.get('last_name') or '').strip()
        accept = request.POST.get('accept_terms')

        errors = []
        if not email or '@' not in email:
            errors.append('Ingresa un email valido.')
        if len(password) < 8:
            errors.append('La contraseña debe tener al menos 8 caracteres.')
        if password != password_confirm:
            errors.append('Las contraseñas no coinciden.')
        if not first_name or not last_name:
            errors.append('Nombre y apellido son obligatorios.')
        if not accept:
            errors.append('Debes aceptar los terminos para continuar.')
        from django.contrib.auth.models import User
        if not errors and User.objects.filter(username=email).exists():
            errors.append('Este email ya esta registrado. Inicia sesion.')

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'core/wizard/step1_account.html', {
                'progress': _step_progress(1),
                'form_data': request.POST,
            })

        _set_wizard(request, {
            'email': email,
            'password': password,
            'first_name': first_name,
            'last_name': last_name,
        })
        return redirect('registro_paso2')

    return render(request, 'core/wizard/step1_account.html', {
        'progress': _step_progress(1),
        'form_data': {},
    })


# ---------------------------------------------------------------------------
# Paso 2: perfil profesional
# ---------------------------------------------------------------------------

@require_http_methods(["GET", "POST"])
def registro_paso2(request):
    """Paso 2: headline, bio, años de experiencia, links, especialidad.

    Mantiene los datos del paso 1 en sesion. Permite volver atras sin
    perder lo ya cargado.
    """
    if request.user.is_authenticated:
        return redirect('ver_dashboard')
    wiz = _get_wizard(request)
    if not wiz.get('email'):
        messages.info(request, 'Comienza desde el paso 1.')
        return redirect('registro_paso1')

    specialties = Specialty.objects.select_related('parent').order_by('category', 'name')

    if request.method == 'POST':
        action = request.POST.get('action', 'next')
        wiz.update({
            'headline': (request.POST.get('headline') or '').strip(),
            'bio': (request.POST.get('bio') or '').strip(),
            'years_experience': int(request.POST.get('years_experience') or 0),
            'portfolio_url': (request.POST.get('portfolio_url') or '').strip(),
            'linkedin_url': (request.POST.get('linkedin_url') or '').strip(),
            'github_url': (request.POST.get('github_url') or '').strip(),
            'primary_specialty_id': request.POST.get('primary_specialty') or None,
            'secondary_specialty_ids': request.POST.getlist('secondary_specialties'),
        })
        _set_wizard(request, wiz)

        if action == 'back':
            return redirect('registro_paso1')
        return redirect('registro_paso3')

    form_data = {
        'headline': wiz.get('headline', ''),
        'bio': wiz.get('bio', ''),
        'years_experience': wiz.get('years_experience', 0),
        'portfolio_url': wiz.get('portfolio_url', ''),
        'linkedin_url': wiz.get('linkedin_url', ''),
        'github_url': wiz.get('github_url', ''),
        'primary_specialty': wiz.get('primary_specialty_id') or '',
        'secondary_specialties': wiz.get('secondary_specialty_ids', []),
    }
    return render(request, 'core/wizard/step2_profile.html', {
        'progress': _step_progress(2),
        'form_data': form_data,
        'specialties': specialties,
    })


# ---------------------------------------------------------------------------
# Paso 3: tecnologias + CV
# ---------------------------------------------------------------------------

@require_http_methods(["GET", "POST"])
def registro_paso3(request):
    """Paso 3 final: tecnologias con nivel + archivo CV.

    En el POST se ejecuta la transaccion completa: crea User,
    UserProfile (pending) y CandidateProfile con tecnologias y CV.
    """
    from django.contrib.auth.models import User

    if request.user.is_authenticated:
        return redirect('ver_dashboard')
    wiz = _get_wizard(request)
    if not wiz.get('email') or not wiz.get('password'):
        return redirect('registro_paso1')

    technologies = Technology.objects.filter(is_active=True).order_by('category', 'name')

    if request.method == 'POST':
        action = request.POST.get('action', 'submit')

        tech_ids = request.POST.getlist('technology')
        levels = request.POST.getlist('level')
        years_list = request.POST.getlist('years_using')

        tech_data = []
        for i, tid in enumerate(tech_ids):
            try:
                level = int(levels[i]) if i < len(levels) else 2
                years_using = int(years_list[i]) if i < len(years_list) else 0
            except (ValueError, IndexError):
                level, years_using = 2, 0
            tech_data.append({
                'technology_id': int(tid),
                'level': max(1, min(4, level)),
                'years_using': max(0, years_using),
            })

        wiz['technologies'] = tech_data
        _set_wizard(request, wiz)

        if action == 'back':
            return redirect('registro_paso2')

        cv = request.FILES.get('cv')
        if cv:
            ext = '.' + cv.name.rsplit('.', 1)[-1].lower() if '.' in cv.name else ''
            if ext not in ALLOWED_CV_EXT:
                messages.error(request, 'El CV debe ser PDF, DOC o DOCX.')
                return _render_step3(request, technologies, wiz)
            if cv.size > MAX_CV_BYTES:
                messages.error(request, 'El CV supera 5MB.')
                return _render_step3(request, technologies, wiz)

        # Generar token y guardar en RegistrationRequest
        token = secrets.token_urlsafe(32)
        ip = _get_client_ip(request)
        expires = timezone.now() + timedelta(hours=24)

        try:
            with transaction.atomic():
                # Guardar CV temporalmente si existe
                cv_path = None
                if cv:
                    cv_path = f'cv_temp/{token}_{cv.name}'
                    # Nota: guardaré el archivo en un campo File del RegistrationRequest
                    # o lo procesaré al verificar. Simplifico: guardaré en data como referencia
                    pass

                req = RegistrationRequest.objects.create(
                    token=token,
                    email=wiz['email'],
                    data={
                        'email': wiz['email'],
                        'password': wiz['password'],
                        'first_name': wiz['first_name'],
                        'last_name': wiz['last_name'],
                        'headline': wiz.get('headline', ''),
                        'bio': wiz.get('bio', ''),
                        'years_experience': wiz.get('years_experience', 0),
                        'portfolio_url': wiz.get('portfolio_url', ''),
                        'linkedin_url': wiz.get('linkedin_url', ''),
                        'github_url': wiz.get('github_url', ''),
                        'primary_specialty_id': wiz.get('primary_specialty_id') or None,
                        'secondary_specialty_ids': wiz.get('secondary_specialty_ids', []),
                        'technologies': tech_data,
                        'cv_name': cv.name if cv else None,
                    },
                    ip_address=ip,
                    expires_at=expires,
                )

                # Guardar CV como archivo temporal
                if cv:
                    req.cv_file = cv
                    req.save()

                # Enviar email de verificación
                verify_url = request.build_absolute_uri(
                    reverse('verificar_registro', kwargs={'token': token})
                )
                subject = 'Winnie - Verifica tu solicitud de acceso'
                message = f"""Hola {wiz['first_name']},

Recibimos tu solicitud de acceso a Winnie.

Para confirmar tu email y completar el proceso, haz clic en el siguiente enlace:

{verify_url}

Este enlace expira en 24 horas.

Si no solicitaste acceso, ignora este mensaje.

Equipo Winnie
"""
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[wiz['email']],
                    fail_silently=False,
                )

        except Exception as e:
            logger.exception('Error al guardar solicitud de registro')
            messages.error(request, f'Error al crear la solicitud: {e}')
            return _render_step3(request, technologies, wiz)

        _clear_wizard(request)
        return render(request, 'core/wizard/verify_email.html', {
            'email': wiz['email'],
        })

    return _render_step3(request, technologies, wiz)


def _render_step3(request, technologies, wiz):
    return render(request, 'core/wizard/step3_skills.html', {
        'progress': _step_progress(3),
        'technologies': technologies,
        'selected_techs': wiz.get('technologies', []),
    })


def _get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '127.0.0.1')


# ---------------------------------------------------------------------------
# Verificación de email
# ---------------------------------------------------------------------------

def verificar_registro(request, token):
    """Confirma una solicitud de registro mediante token.

    Busca el RegistrationRequest, crea el User + UserProfile + CandidateProfile
    y notifica al admin.
    """
    from django.contrib.auth.models import User

    req = RegistrationRequest.objects.filter(token=token, status='pending').first()

    if not req:
        messages.error(request, 'El enlace de verificación no es válido o ya fue usado.')
        return redirect('iniciar_sesion')

    if timezone.now() > req.expires_at:
        req.status = 'expired'
        req.save()
        messages.error(request, 'El enlace de verificación ha expirado. Inicia el registro de nuevo.')
        return redirect('iniciar_sesion')

    data = req.data
    cv = req.cv_file

    try:
        with transaction.atomic():
            user = User.objects.create_user(
                username=data['email'],
                email=data['email'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                password=data['password'],
            )
            UserProfile.objects.create(user=user, role='miembro', status='pending')

            cp = CandidateProfile.objects.create(
                user=user,
                headline=data.get('headline', ''),
                bio=data.get('bio', ''),
                years_experience=data.get('years_experience', 0),
                portfolio_url=data.get('portfolio_url', ''),
                linkedin_url=data.get('linkedin_url', ''),
                github_url=data.get('github_url', ''),
                cv_file=cv,
                primary_specialty_id=data.get('primary_specialty_id') or None,
            )
            if data.get('secondary_specialty_ids'):
                cp.secondary_specialties.set(
                    Specialty.objects.filter(id__in=data['secondary_specialty_ids'])
                )
            for t in data.get('technologies', []):
                CandidateTechnology.objects.create(
                    candidate=cp,
                    technology_id=t['technology_id'],
                    level=t['level'],
                    years_using=t['years_using'],
                )
            create_audit_log(
                user, 'USER_REGISTER_WIZARD', 'user', user.id,
                f'Registro wizard verificado: {user.get_full_name()}',
            )
    except Exception as e:
        logger.exception('Error al verificar registro')
        messages.error(request, f'Error al procesar la verificación: {e}')
        return redirect('iniciar_sesion')

    req.status = 'verified'
    req.save()

    # Notificar a admins
    admins = User.objects.filter(
        profile__role__in=['super-admin', 'admin'],
        profile__status='active',
    )
    for admin in admins:
        create_notification(
            admin, 'new_registration', 'Nueva solicitud de acceso',
            f'{user.get_full_name()} ({user.email}) solicito acceso. '
            f'Especialidad: {cp.primary_specialty.name if cp.primary_specialty else "no indicada"}. '
            f'{len(data.get("technologies", []))} tecnologia(s) declarada(s).',
            'fa-user-clock',
        )

    # Notificar al usuario
    subject = 'Winnie - Solicitud confirmada'
    message = f"""Hola {user.first_name},

Tu solicitud de acceso fue confirmada y enviada al equipo.

Un administrador revisará tu perfil y te notificará cuando sea aprobada.

Gracias por tu interés en Winnie.

Equipo Winnie
"""
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )

    messages.success(
        request,
        '¡Tu solicitud fue confirmada! Un administrador la revisará y te notificará por email.',
    )
    return redirect('iniciar_sesion')


# ---------------------------------------------------------------------------
# Cancelar wizard
# ---------------------------------------------------------------------------

@require_POST
def registro_cancelar(request):
    _clear_wizard(request)
    messages.info(request, 'Solicitud cancelada.')
    return redirect('iniciar_sesion')
