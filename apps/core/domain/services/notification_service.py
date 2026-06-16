from typing import Optional, Tuple
from django.contrib.auth.models import User
from apps.core.infrastructure.models.models import Notification, AuditLog


def create_notification(
    user: User,
    type: str,
    title: str,
    message: str,
    icon: str = 'fa-bell',
) -> Notification:
    """Create a notification for a user"""
    return Notification.objects.create(user=user, type=type, title=title, message=message, icon=icon)


def create_audit_log(
    user: User,
    action: str,
    entity: str,
    entity_id: str = '',
    details: str = '',
) -> AuditLog:
    """Create an audit log entry"""
    return AuditLog.objects.create(
        user=user,
        action=action,
        entity=entity,
        entity_id=str(entity_id),
        details=details,
    )


def notify_task_assignment(task, assigner: User, assignee: User) -> None:
    """Notify user about task assignment"""
    if assignee and assignee != assigner:
        create_notification(
            assignee,
            'task_assigned',
            'Tarea asignada',
            f'Se te asigno la tarea "{task.title}" en el proyecto {task.project.name}',
            'fa-tasks',
        )


def notify_project_assignment(project, assigner: User, lead: User) -> None:
    """Notify user about project lead assignment"""
    if lead and lead != assigner:
        create_notification(
            lead,
            'project_assigned',
            'Proyecto asignado',
            f'Fuiste asignado como jefe del proyecto "{project.name}"',
            'fa-folder',
        )


def notify_project_membership(project, assigner: User, member: User) -> None:
    """Notify user about being added to a project"""
    if member and member != assigner:
        create_notification(
            member,
            'project_member',
            'Agregado a proyecto',
            f'Fuiste agregado al proyecto "{project.name}"',
            'fa-users',
        )


def notify_sprint_start(sprint, initiator: User) -> None:
    """Notify team members about sprint start"""
    members = sprint.project.members.all()
    if sprint.project.lead and sprint.project.lead != initiator:
        create_notification(
            sprint.project.lead,
            'sprint_start',
            'Sprint iniciado',
            f'El sprint "{sprint.name}" del proyecto {sprint.project.name} ha comenzado',
            'fa-flag',
        )
    for member in members:
        if member != initiator:
            create_notification(
                member,
                'sprint_start',
                'Sprint iniciado',
                f'El sprint "{sprint.name}" del proyecto {sprint.project.name} ha comenzado',
                'fa-flag',
            )


def notify_comment(task, commenter: User) -> None:
    """Notify about new comment on task"""
    if task.assignee and task.assignee != commenter:
        create_notification(
            task.assignee,
            'comment',
            'Nuevo comentario',
            f'{commenter.get_full_name()} comento en "{task.title}"',
            'fa-comment',
        )
    elif task.project.lead and task.project.lead != commenter:
        create_notification(
            task.project.lead,
            'comment',
            'Nuevo comentario',
            f'{commenter.get_full_name()} comento en "{task.title}"',
            'fa-comment',
        )


def notify_service_assignment(service_request, assigner: User, assignee: User) -> None:
    """Notify about service request assignment"""
    if assignee and assignee != assigner:
        create_notification(
            assignee,
            'service_assigned',
            'Solicitud asignada',
            f'Se te asigno la solicitud de servicio "{service_request.get_service_display()}" de {service_request.client.name}',
            'fa-headset',
        )
