from typing import Optional, Tuple, List
from datetime import timedelta, date
from django.db import transaction
from django.contrib.auth.models import User
from apps.core.infrastructure.models.models import Project, Sprint
from apps.core.infrastructure.repositories import ProjectRepository
from apps.core.domain.services.permission_service import can_manage_project, can_manage_area
from apps.core.domain.services.notification_service import (
    create_audit_log, notify_project_assignment, notify_project_membership
)

project_repo = ProjectRepository()


class ProjectService:
    """Service layer for Project business logic"""

    @staticmethod
    @transaction.atomic
    def crear_proyecto(
        user: User,
        name: str,
        area_id: int,
        description: str = '',
        status: str = 'planned',
        lead_id: Optional[int] = None,
        client_id: Optional[int] = None,
        budget: float = 0,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        color: str = '#00bcd4',
        members: Optional[List[int]] = None,
    ) -> Tuple[Optional[Project], Optional[str]]:
        """Create a new project with permission check and notifications"""
        if not can_manage_area(user):
            return None, 'No tienes permiso para crear proyectos'

        project = project_repo.create(
            name=name,
            area_id=area_id,
            description=description,
            status=status,
            lead_id=lead_id or None,
            client_id=client_id or None,
            budget=budget or 0,
            start_date=start_date or None,
            end_date=end_date or None,
            color=color,
        )

        if members:
            project.members.set(members)
            for member_id in members:
                member = User.objects.get(id=member_id)
                notify_project_membership(project, user, member)

        if project.lead:
            # El jefe de proyecto tambien es miembro del proyecto.
            project.members.add(project.lead)
            notify_project_assignment(project, user, project.lead)

        # Sprint inicial por defecto (Sprint 1) en planificacion.
        sprint_start = project.start_date or date.today()
        Sprint.objects.create(
            project=project,
            name='Sprint 1',
            start_date=sprint_start,
            end_date=sprint_start + timedelta(days=14),
            status='PLAN',
        )

        create_audit_log(user, 'PROJECT_CREATE', 'project', project.id, f'Proyecto creado: {project.name}')
        return project, None

    @staticmethod
    @transaction.atomic
    def editar_proyecto(
        user: User,
        project: Project,
        **kwargs,
    ) -> Tuple[Optional[Project], Optional[str]]:
        """Update an existing project with permission check"""
        if not can_manage_project(user, project):
            return None, 'No tienes permiso para editar este proyecto'

        old_lead_id = project.lead_id
        old_member_ids = set(project.members.values_list('id', flat=True))

        member_ids = kwargs.pop('members', None)

        project = project_repo.update(project.id, **kwargs)

        if member_ids is not None:
            project.members.set(member_ids)

        if kwargs.get('lead_id') and kwargs['lead_id'] != old_lead_id:
            lead = User.objects.get(id=kwargs['lead_id'])
            notify_project_assignment(project, user, lead)

        # El jefe de proyecto siempre debe estar entre los miembros.
        if project.lead_id:
            project.members.add(project.lead_id)

        if member_ids is not None:
            new_member_ids = set(int(m) for m in member_ids)
            for member_id in new_member_ids - old_member_ids:
                member = User.objects.get(id=member_id)
                notify_project_membership(project, user, member)

        create_audit_log(user, 'PROJECT_EDIT', 'project', project.id, f'Proyecto editado: {project.name}')
        return project, None

    @staticmethod
    @transaction.atomic
    def eliminar_proyecto(
        user: User,
        project: Project,
    ) -> Tuple[bool, Optional[str]]:
        """Delete a project with permission check"""
        if not can_manage_project(user, project):
            return False, 'No tienes permiso para eliminar este proyecto'

        name = project.name
        project_repo.delete(project.id)
        create_audit_log(user, 'PROJECT_DELETE', 'project', project.id, f'Proyecto eliminado: {name}')
        return True, None
