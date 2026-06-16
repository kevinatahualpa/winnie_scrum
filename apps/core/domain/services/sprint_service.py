from typing import Optional, Tuple
from django.db import transaction
from django.contrib.auth.models import User
from apps.core.infrastructure.models.models import Sprint, Task
from apps.core.infrastructure.repositories import SprintRepository
from apps.core.domain.services.permission_service import can_manage_project
from apps.core.domain.services.notification_service import create_audit_log, notify_sprint_start

sprint_repo = SprintRepository()


class SprintService:
    """Service layer for Sprint business logic"""

    @staticmethod
    @transaction.atomic
    def crear_sprint(
        user: User,
        project,
        name: str,
        start_date,
        end_date,
        goal: str = '',
    ) -> Tuple[Optional[Sprint], Optional[str]]:
        """Create a new sprint with permission check"""
        if not can_manage_project(user, project):
            return None, 'No tienes permiso para crear sprints en este proyecto'

        if start_date > end_date:
            return None, 'La fecha de inicio debe ser anterior o igual a la fecha de fin'

        sprint = sprint_repo.create(
            project=project,
            name=name,
            start_date=start_date,
            end_date=end_date,
            goal=goal,
            status='planned',
        )

        create_audit_log(user, 'SPRINT_CREATE', 'sprint', sprint.id, f'Sprint creado: {sprint.name}')
        return sprint, None

    @staticmethod
    @transaction.atomic
    def iniciar_sprint(
        user: User,
        sprint: Sprint,
    ) -> Tuple[Optional[Sprint], Optional[str]]:
        """Start a sprint and notify team members"""
        if not can_manage_project(user, sprint.project):
            return None, 'No tienes permiso para iniciar este sprint'

        Sprint.objects.filter(project=sprint.project, status='active').update(status='planned')
        sprint.status = 'active'
        sprint.save()

        notify_sprint_start(sprint, user)
        create_audit_log(user, 'SPRINT_START', 'sprint', sprint.id, f'Sprint iniciado: {sprint.name}')
        return sprint, None

    @staticmethod
    @transaction.atomic
    def completar_sprint(
        user: User,
        sprint: Sprint,
    ) -> Tuple[Optional[Sprint], Optional[str]]:
        """Complete a sprint and move incomplete tasks back to backlog"""
        if not can_manage_project(user, sprint.project):
            return None, 'No tienes permiso para completar este sprint'

        sprint.status = 'completed'
        sprint.save()

        Task.objects.filter(sprint=sprint, status__in=['backlog', 'todo', 'in-progress']).update(status='backlog')

        create_audit_log(user, 'SPRINT_COMPLETE', 'sprint', sprint.id, f'Sprint completado: {sprint.name}')
        return sprint, None
