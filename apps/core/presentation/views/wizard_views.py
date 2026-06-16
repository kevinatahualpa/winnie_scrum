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

from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST
from django.core.exceptions import ValidationError
from django.db import transaction
import logging

from apps.core.infrastructure.models.models import (
    CandidateProfile, CandidateTechnology, Specialty, Technology, UserProfile,
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

        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=wiz['email'],
                    email=wiz['email'],
                    first_name=wiz['first_name'],
                    last_name=wiz['last_name'],
                    password=wiz['password'],
                )
                UserProfile.objects.create(user=user, role='miembro', status='pending')

                cp = CandidateProfile.objects.create(
                    user=user,
                    headline=wiz.get('headline', ''),
                    bio=wiz.get('bio', ''),
                    years_experience=wiz.get('years_experience', 0),
                    portfolio_url=wiz.get('portfolio_url', ''),
                    linkedin_url=wiz.get('linkedin_url', ''),
                    github_url=wiz.get('github_url', ''),
                    cv_file=cv,
                    primary_specialty_id=wiz.get('primary_specialty_id') or None,
                )
                if wiz.get('secondary_specialty_ids'):
                    cp.secondary_specialties.set(
                        Specialty.objects.filter(id__in=wiz['secondary_specialty_ids'])
                    )
                for t in tech_data:
                    CandidateTechnology.objects.create(
                        candidate=cp,
                        technology_id=t['technology_id'],
                        level=t['level'],
                        years_using=t['years_using'],
                    )
                create_audit_log(
                    user, 'USER_REGISTER_WIZARD', 'user', user.id,
                    f'Registro wizard: {user.get_full_name()} ({len(tech_data)} techs)',
                )
        except Exception as e:
            messages.error(request, f'Error al crear la solicitud: {e}')
            return _render_step3(request, technologies, wiz)

        admins = User.objects.filter(
            profile__role__in=['super-admin', 'admin'],
            profile__status='active',
        )
        for admin in admins:
            create_notification(
                admin, 'new_registration', 'Nueva solicitud de acceso',
                f'{user.get_full_name()} ({user.email}) solicito acceso. '
                f'Especialidad: {cp.primary_specialty.name if cp.primary_specialty else "no indicada"}. '
                f'{len(tech_data)} tecnologia(s) declarada(s).',
                'fa-user-clock',
            )

        _clear_wizard(request)
        messages.success(
            request,
            'Tu solicitud fue enviada. Un administrador la revisara y te '
            'notificara por email cuando sea aprobada.',
        )
        return redirect('iniciar_sesion')

    return _render_step3(request, technologies, wiz)


def _render_step3(request, technologies, wiz):
    return render(request, 'core/wizard/step3_skills.html', {
        'progress': _step_progress(3),
        'technologies': technologies,
        'selected_techs': wiz.get('technologies', []),
    })


# ---------------------------------------------------------------------------
# Cancelar wizard
# ---------------------------------------------------------------------------

@require_POST
def registro_cancelar(request):
    _clear_wizard(request)
    messages.info(request, 'Solicitud cancelada.')
    return redirect('iniciar_sesion')
