from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from apps.core.infrastructure.models.models import Project, Task, Sprint, Document, ServiceRequest
from apps.core.domain.services.permission_service import get_user_role, is_read_only
from apps.core.presentation.forms import ServiceRequestForm


@login_required
def ver_portal_cliente(request):
    """Portal de cliente: lista de proyectos del cliente asociado al usuario.

    Read-only por defecto. El cliente puede crear ServiceRequest (soporte).
    """
    user = request.user
    role = get_user_role(user)

    if role != 'cliente':
        return redirect('ver_dashboard')

    profile = getattr(user, 'profile', None)
    if not profile or not profile.client_id:
        return render(request, 'core/client_portal.html', {
            'client': None, 'projects': [], 'services': [],
        })

    client = profile.client
    projects = Project.objects.filter(client=client).select_related('area', 'lead').order_by('-created_at')
    services = ServiceRequest.objects.filter(client=client).order_by('-created_at')[:10]

    return render(request, 'core/client_portal.html', {
        'client': client,
        'projects': projects,
        'services': services,
    })


@login_required
def ver_detalle_proyecto_cliente(request, pk):
    """Detalle de proyecto para cliente: solo lectura, sin acciones de edicion."""
    user = request.user
    role = get_user_role(user)

    if role != 'cliente':
        messages.error(request, 'Acceso restringido al portal de cliente')
        return redirect('ver_dashboard')

    project = get_object_or_404(Project, pk=pk, client__isnull=False)

    if not project.client or project.client_id != user.profile.client_id:
        messages.error(request, 'No tienes permiso para ver este proyecto')
        return redirect('ver_portal_cliente')

    tasks = project.tasks.select_related('assignee', 'sprint').order_by('-created_at')
    sprints = project.sprints.order_by('-start_date')
    documents = project.documents.select_related('uploaded_by').order_by('-created_at')

    return render(request, 'core/client_project_detail.html', {
        'project': project, 'tasks': tasks, 'sprints': sprints, 'documents': documents,
    })


@login_required
def crear_solicitud_cliente(request):
    """Cliente crea una nueva solicitud de servicio desde el portal."""
    user = request.user
    role = get_user_role(user)

    if role != 'cliente':
        messages.error(request, 'Acceso restringido')
        return redirect('ver_dashboard')

    profile = getattr(user, 'profile', None)
    if not profile or not profile.client_id:
        messages.error(request, 'Tu usuario no esta vinculado a un cliente')
        return redirect('ver_portal_cliente')

    if request.method == 'POST':
        form = ServiceRequestForm(request.POST)
        if form.is_valid():
            sr = form.save(commit=False)
            sr.client_id = profile.client_id
            sr.status = 'new'
            sr.save()
            messages.success(request, 'Solicitud enviada. Te contactaremos pronto.')
            return redirect('ver_portal_cliente')
    else:
        form = ServiceRequestForm()

    return render(request, 'core/client_service_form.html', {'form': form})
