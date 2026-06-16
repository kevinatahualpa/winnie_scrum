from django.http import JsonResponse
from django.db import connection
from django.views.decorators.http import require_GET


@require_GET
def verificar_salud(request):
    """Health check endpoint for container orchestration"""
    health = {
        'status': 'healthy',
        'version': '1.0.0',
    }

    try:
        connection.ensure_connection()
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        health['database'] = 'connected'
    except Exception as e:
        health['status'] = 'unhealthy'
        health['database'] = f'disconnected: {str(e)}'

    status_code = 200 if health['status'] == 'healthy' else 503
    return JsonResponse(health, status=status_code)


@require_GET
def verificar_disponibilidad(request):
    """Readiness check - verifies app can serve traffic"""
    try:
        connection.ensure_connection()
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        return JsonResponse({'status': 'ready'}, status=200)
    except Exception:
        return JsonResponse({'status': 'not_ready'}, status=503)
