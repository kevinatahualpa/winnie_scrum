import time
from django.core.cache import cache
from django.http import HttpResponse


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
