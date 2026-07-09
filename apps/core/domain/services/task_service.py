from typing import Optional, Tuple
from django.db import transaction
from django.contrib.auth.models import User
from apps.core.infrastructure.models.models import Task, Tag
from apps.core.infrastructure.repositories import TaskRepository
from apps.core.domain.services.permission_service import can_manage_task
from apps.core.domain.services.notification_service import create_audit_log, notify_task_assignment

task_repo = TaskRepository()


class TaskService:
    """Service layer for Task business logic"""

    @staticmethod
    @transaction.atomic
    def crear_tarea(
        user: User,
        project,
        title: str,
        type: str = 'task',
        priority: str = 'medium',
        points: int = 1,
        status: str = 'TODO',
        description: str = '',
        assignee_id: Optional[int] = None,
        sprint_id: Optional[int] = None,
        required_specialty_id: Optional[int] = None,
        tags: Optional[str] = None,
        due_date=None,
    ) -> Tuple[Optional[Task], Optional[str]]:
        """Create a new task with permission check and notifications"""
        if not can_manage_task(user):
            return None, 'No tienes permiso para crear tareas'

        task = task_repo.create(
            project=project,
            title=title,
            type=type,
            priority=priority,
            points=points,
            status=status,
            description=description,
            assignee_id=assignee_id or None,
            sprint_id=sprint_id or None,
            required_specialty_id=required_specialty_id or None,
            due_date=due_date or None,
        )

        if assignee_id:
            assignee = User.objects.get(id=assignee_id)
            notify_task_assignment(task, user, assignee)

        if tags:
            tag_names = [t.strip() for t in tags.split(',') if t.strip()]
            for tag_name in tag_names:
                tag, _ = Tag.objects.get_or_create(name=tag_name)
                task.tags.add(tag)

        create_audit_log(user, 'TASK_CREATE', 'task', task.id, f'Tarea creada: {task.title}')
        return task, None

    @staticmethod
    @transaction.atomic
    def editar_tarea(
        user: User,
        task: Task,
        **kwargs,
    ) -> Tuple[Optional[Task], Optional[str]]:
        """Update an existing task with permission check"""
        if not can_manage_task(user, task):
            return None, 'No tienes permiso para editar esta tarea'

        old_assignee_id = task.assignee_id

        task = task_repo.update(task.id, **kwargs)

        if kwargs.get('assignee_id') and kwargs['assignee_id'] != old_assignee_id:
            assignee = User.objects.get(id=kwargs['assignee_id'])
            notify_task_assignment(task, user, assignee)

        if 'tags' in kwargs:
            tag_names = [t.strip() for t in kwargs['tags'].split(',') if t.strip()]
            task.tags.clear()
            for tag_name in tag_names:
                tag, _ = Tag.objects.get_or_create(name=tag_name)
                task.tags.add(tag)

        create_audit_log(user, 'TASK_EDIT', 'task', task.id, f'Tarea editada: {task.title}')
        return task, None

    @staticmethod
    @transaction.atomic
    def eliminar_tarea(
        user: User,
        task: Task,
    ) -> Tuple[bool, Optional[str]]:
        """Delete a task with permission check"""
        if not can_manage_task(user, task):
            return False, 'No tienes permiso para eliminar esta tarea'

        title = task.title
        task_repo.delete(task.id)
        create_audit_log(user, 'TASK_DELETE', 'task', task.id, f'Tarea eliminada: {title}')
        return True, None

    @staticmethod
    @transaction.atomic
    def actualizar_estado(
        user: User,
        task: Task,
        new_status: str,
    ) -> Tuple[bool, Optional[str]]:
        """Update task status with forward-only flow validation."""
        if not can_manage_task(user, task):
            return False, 'No tienes permiso'

        valid_statuses = dict(Task.STATUS_CHOICES).keys()
        if new_status not in valid_statuses:
            return False, 'Estado invalido'

        ALLOWED_TRANSITIONS = {
            'TODO': ['PROG'],
            'PROG': ['TEST', 'DONE'],
            'TEST': ['DONE', 'PROG'],
            'DONE': [],
        }

        if new_status not in ALLOWED_TRANSITIONS.get(task.status, []):
            names = dict(Task.STATUS_CHOICES)
            return False, f'No se puede mover de "{names.get(task.status, task.status)}" a "{names.get(new_status, new_status)}". Flujo: Por Hacer → En Progreso → En Testing → Completado'

        old_status = task.status
        task.status = new_status
        task.save()

        create_audit_log(
            user, 'TASK_STATUS_CHANGE', 'task', task.id,
            f'Tarea "{task.title}": {old_status} -> {new_status}'
        )

        if new_status == 'DONE' and task.assignee and task.assignee != user:
            from apps.core.domain.services.notification_service import create_notification
            create_notification(
                task.assignee,
                'task_completed',
                'Tarea completada',
                f'La tarea "{task.title}" fue marcada como completada',
                'fa-check-circle',
            )
        elif new_status == 'PROG' and task.assignee and task.assignee != user:
            from apps.core.domain.services.notification_service import create_notification
            create_notification(
                task.assignee,
                'task_in_progress',
                'Tarea en progreso',
                f'La tarea "{task.title}" paso a En Progreso',
                'fa-spinner',
            )

        return True, None
