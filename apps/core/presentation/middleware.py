import time
from django.core.cache import cache
from django.http import HttpResponse


class RateLimitMiddleware:
    RATE_LIMIT_ENDPOINTS = {'login', 'register'}
    MAX_REQUESTS = 10
    WINDOW_SECONDS = 60

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == 'POST' and hasattr(request, 'resolver_match') and request.resolver_match:
            url_name = request.resolver_match.url_name
            if url_name in self.RATE_LIMIT_ENDPOINTS:
                ip = self._get_client_ip(request)
                cache_key = f'ratelimit:{url_name}:{ip}'
                attempts = cache.get(cache_key, 0)
                if attempts >= self.MAX_REQUESTS:
                    return HttpResponse(
                        '<h1>429 Too Many Requests</h1><p>Intente nuevamente en 60 segundos.</p>',
                        status=429
                    )
                cache.set(cache_key, attempts + 1, self.WINDOW_SECONDS)
        return self.get_response(request)

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '127.0.0.1')
