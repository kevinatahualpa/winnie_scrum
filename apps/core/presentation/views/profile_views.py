from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages


@login_required
def ver_perfil(request):
    """Render the current user's profile page showing their details and role.
    
    Handles POST to update avatar photo."""
    user = request.user
    profile = getattr(user, 'profile', None)
    
    if request.method == 'POST' and profile:
        avatar = request.FILES.get('avatar')
        if avatar:
            profile.avatar = avatar
            profile.save()
            messages.success(request, 'Foto de perfil actualizada')
            return redirect('ver_perfil')
    
    return render(request, 'core/profile.html', {'profile': profile})
