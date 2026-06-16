from django.shortcuts import render


def handler404(request, exception):
    """Render a custom 404 error page."""
    return render(request, 'core/errors/404.html', status=404)


def handler500(request):
    """Render a custom 500 error page."""
    return render(request, 'core/errors/500.html', status=500)


def handler403(request, exception):
    """Render a custom 403 error page."""
    return render(request, 'core/errors/403.html', status=403)


def handler400(request, exception):
    """Render a custom 400 error page."""
    return render(request, 'core/errors/400.html', status=400)
