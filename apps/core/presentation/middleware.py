import time
from django.core.cache import cache
from django.http import HttpResponse
from django.conf import settings
from django.contrib.auth import logout
from django.contrib import messages
from django.shortcuts import redirect
from django.utils import timezone
from datetime import timedelta


class RateLimitMiddleware:
    RATE_LIMIT_ENDPOINTS = {
        'iniciar_sesion', 'registrarse', 'solicitar_acceso',
        'registro_paso1', 'registro_paso2', 'registro_paso3',
    }
    MAX_REQUESTS = 5
    WINDOW_SECONDS = 3600  # 1 hora

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == 'POST' and hasattr(request, 'resolver_match') and request.resolver_match:
            url_name = request.resolver_match.url_name
            if url_name in self.RATE_LIMIT_ENDPOINTS:
                ip = self._get_client_ip(request)
                cache_key = f'ratelimit:{url_name}:{ip}'
                try:
                    attempts = cache.incr(cache_key)
                except ValueError:
                    cache.set(cache_key, 1, self.WINDOW_SECONDS)
                    attempts = 1
                if attempts > self.MAX_REQUESTS:
                    return HttpResponse(
                        '<h1>429 Too Many Requests</h1><p>Intente nuevamente en 60 segundos.</p>',
                        status=429
                    )
        return self.get_response(request)

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '127.0.0.1')


class SingleSessionMiddleware:
    """Fuerza una sola sesion activa por usuario y registra actividad.

    - Si el usuario inicia sesion en otro dispositivo, la sesion anterior
      queda invalidada (se cierra en su siguiente request).
    - Actualiza `last_seen` (con throttle) para saber quien esta en linea.
    """

    LAST_SEEN_THROTTLE = 60  # segundos entre escrituras de last_seen

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if user is not None and user.is_authenticated:
            profile = getattr(user, 'profile', None)
            if profile is not None:
                current_key = request.session.session_key
                stored_key = profile.active_session_key

                # Sesion desplazada por un login mas reciente en otro dispositivo
                if stored_key and current_key and stored_key != current_key:
                    logout(request)
                    messages.error(
                        request,
                        'Tu sesion se cerro porque se inicio sesion en otro dispositivo.'
                    )
                    return redirect('iniciar_sesion')

                # Registrar actividad (throttled para no escribir en cada request)
                now = timezone.now()
                if not profile.last_seen or profile.last_seen < now - timedelta(seconds=self.LAST_SEEN_THROTTLE):
                    UserProfile = profile.__class__
                    UserProfile.objects.filter(pk=profile.pk).update(last_seen=now)

        return self.get_response(request)

