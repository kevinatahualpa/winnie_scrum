from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator

from apps.core.infrastructure.models.models import Document, Project
from apps.core.domain.services.permission_service import get_user_role, can_manage_project, filter_queryset_by_role


@login_required
def ver_documentos(request):
    """Render the documents list with filtering by project and sorting options.

    Supports sorting by name, size, and creation date. Shows total storage used.
    Uses pagination (30 per page) and role-based document filtering.
    """
    user = request.user
    role = get_user_role(user)
    project_id = request.GET.get('project')
    sort = request.GET.get('sort', '-created_at')

    docs = Document.objects.select_related('project', 'uploaded_by')
    if project_id:
        docs = docs.filter(project_id=project_id)
    docs = filter_queryset_by_role(docs, user, role, model_type='document')

    valid_sorts = ['name', '-name', 'size', '-size', 'created_at', '-created_at']
    if sort in valid_sorts:
        docs = docs.order_by(sort)
    else:
        docs = docs.order_by('-created_at')

    paginator = Paginator(docs, 30)
    page = request.GET.get('page', 1)
    documents = paginator.get_page(page)

    projects = filter_queryset_by_role(Project.objects.all(), user, role, model_type='project')
    total_size = Document.objects.filter(project_id__in=projects.values_list('id', flat=True)).aggregate(total=Sum('size'))['total'] or 0

    return render(request, 'core/documents.html', {
        'documents': documents, 'projects': projects,
        'selected_project': project_id, 'sort': sort,
        'total_size': total_size,
    })


@require_POST
@login_required
def subir_documento(request):
    """Upload a new document to a project.

    Validates file extension (allowed types) and size (max 10MB).
    Auto-detects document type based on file extension.
    Requires project membership or management permission.
    """
    project = get_object_or_404(Project, pk=request.POST.get('project'))
    role = get_user_role(request.user)

    if role == 'miembro':
        if not (project.lead == request.user or project.members.filter(id=request.user.id).exists()):
            messages.error(request, 'No tienes permiso para subir documentos a este proyecto')
            return redirect('ver_documentos')
    elif not can_manage_project(request.user, project):
        messages.error(request, 'No tienes permiso para subir documentos a este proyecto')
        return redirect('ver_documentos')

    file = request.FILES.get('file')
    if not file:
        messages.error(request, 'No se selecciono ningun archivo')
        return redirect('ver_documentos')

    ALLOWED_EXTENSIONS = {
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.txt', '.csv', '.zip', '.rar', '.7z',
        '.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.bmp',
        '.mp4', '.avi', '.mov', '.mp3', '.wav',
        '.py', '.js', '.html', '.css', '.json', '.xml', '.sql', '.md',
    }
    MAX_FILE_SIZE = 10 * 1024 * 1024

    ext = ''
    if '.' in file.name:
        ext = '.' + file.name.rsplit('.', 1)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        messages.error(request, f'Tipo de archivo no permitido (. {ext}).')
        return redirect('ver_documentos')

    if file.size > MAX_FILE_SIZE:
        messages.error(request, f'Archivo demasiado grande ({file.size / 1024 / 1024:.1f}MB). Maximo: 10MB')
        return redirect('ver_documentos')

    TYPE_MAP = {
        '.pdf': 'pdf', '.doc': 'word', '.docx': 'word',
        '.xls': 'excel', '.xlsx': 'excel', '.csv': 'excel',
        '.png': 'image', '.jpg': 'image', '.jpeg': 'image', '.gif': 'image', '.svg': 'image', '.webp': 'image', '.bmp': 'image',
    }
    doc_type = TYPE_MAP.get(ext, 'other')

    doc = Document.objects.create(
        project=project, name=file.name, file=file,
        uploaded_by=request.user, size=file.size, type=doc_type,
    )

    messages.success(request, f'Documento "{doc.name}" subido correctamente ({file.size / 1024:.0f}KB)')
    return redirect('ver_documentos')


@require_POST
@login_required
def eliminar_documento(request, pk):
    """Delete a document and its associated file. Requires project management permission."""
    doc = get_object_or_404(Document, pk=pk)
    role = get_user_role(request.user)

    if role == 'miembro':
        if not (doc.project.lead == request.user or doc.project.members.filter(id=request.user.id).exists()):
            messages.error(request, 'No tienes permiso para eliminar este documento')
            return redirect('ver_documentos')
    elif not can_manage_project(request.user, doc.project):
        messages.error(request, 'No tienes permiso para eliminar este documento')
        return redirect('ver_documentos')

    name = doc.name
    if doc.file:
        doc.file.delete(save=False)
    doc.delete()

    from apps.core.domain.services.notification_service import create_audit_log
    create_audit_log(request.user, 'DOCUMENT_DELETE', 'document', pk, f'Documento eliminado: {name}')
    messages.success(request, f'Documento "{name}" eliminado')
    return redirect('ver_documentos')


@require_POST
@login_required
def subir_documento_proyecto(request, pk):
    """Upload a document from the project detail page, redirect back to project."""
    project = get_object_or_404(Project, pk=pk)
    role = get_user_role(request.user)

    if role == 'miembro':
        if not (project.lead == request.user or project.members.filter(id=request.user.id).exists()):
            messages.error(request, 'No tienes permiso para subir documentos')
            return redirect('ver_detalle_proyecto', pk=pk)
    elif not can_manage_project(request.user, project):
        messages.error(request, 'No tienes permiso para subir documentos')
        return redirect('ver_detalle_proyecto', pk=pk)

    file = request.FILES.get('file')
    if not file:
        messages.error(request, 'No se selecciono ningun archivo')
        return redirect('ver_detalle_proyecto', pk=pk)

    ALLOWED_EXTENSIONS = {
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.txt', '.csv', '.zip', '.rar', '.7z',
        '.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.bmp',
        '.mp4', '.avi', '.mov', '.mp3', '.wav',
        '.py', '.js', '.html', '.css', '.json', '.xml', '.sql', '.md',
    }
    MAX_FILE_SIZE = 10 * 1024 * 1024

    ext = ''
    if '.' in file.name:
        ext = '.' + file.name.rsplit('.', 1)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        messages.error(request, f'Tipo de archivo no permitido (.{ext}).')
        return redirect('ver_detalle_proyecto', pk=pk)

    if file.size > MAX_FILE_SIZE:
        messages.error(request, f'Archivo demasiado grande ({file.size / 1024 / 1024:.1f}MB). Maximo: 10MB')
        return redirect('ver_detalle_proyecto', pk=pk)

    TYPE_MAP = {
        '.pdf': 'pdf', '.doc': 'word', '.docx': 'word',
        '.xls': 'excel', '.xlsx': 'excel', '.csv': 'excel',
        '.png': 'image', '.jpg': 'image', '.jpeg': 'image', '.gif': 'image', '.svg': 'image', '.webp': 'image', '.bmp': 'image',
    }
    doc_type = TYPE_MAP.get(ext, 'other')

    doc = Document.objects.create(
        project=project, name=file.name, file=file,
        uploaded_by=request.user, size=file.size, type=doc_type,
    )

    from apps.core.domain.services.notification_service import create_audit_log
    create_audit_log(request.user, 'DOCUMENT_UPLOAD', 'document', doc.id, f'Documento subido: {doc.name} en proyecto {project.name}')
    messages.success(request, f'Documento "{doc.name}" subido ({file.size / 1024:.0f}KB)')
    return redirect('ver_detalle_proyecto', pk=pk)


@require_POST
@login_required
def eliminar_documento_proyecto(request, pk, doc_pk):
    """Delete a document from the project detail page, redirect back to project."""
    doc = get_object_or_404(Document, pk=doc_pk)
    role = get_user_role(request.user)

    if role == 'miembro':
        if not (doc.project.lead == request.user or doc.project.members.filter(id=request.user.id).exists()):
            messages.error(request, 'No tienes permiso para eliminar este documento')
            return redirect('ver_detalle_proyecto', pk=pk)
    elif not can_manage_project(request.user, doc.project):
        messages.error(request, 'No tienes permiso para eliminar este documento')
        return redirect('ver_detalle_proyecto', pk=pk)

    name = doc.name
    if doc.file:
        doc.file.delete(save=False)
    doc.delete()

    from apps.core.domain.services.notification_service import create_audit_log
    create_audit_log(request.user, 'DOCUMENT_DELETE', 'document', doc_pk, f'Documento eliminado: {name}')
    messages.success(request, f'Documento "{name}" eliminado')
    return redirect('ver_detalle_proyecto', pk=pk)
