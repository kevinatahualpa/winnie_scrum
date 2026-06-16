from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def ver_perfil(request):
    """Render the current user's profile page showing their details and role."""
    user = request.user
    profile = getattr(user, 'profile', None)
    return render(request, 'core/profile.html', {'profile': profile})
