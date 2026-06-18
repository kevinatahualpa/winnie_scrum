from typing import Optional
from django.db.models import QuerySet, Q
from django.contrib.auth.models import User
from apps.core.infrastructure.models.models import (
    Project, Task, Sprint, Document, UserProfile,
    get_substituting_for
)

ROLE_HIERARCHY: dict[str, int] = {
    'observer': -1,
    'cliente': -1,
    'miembro': 0,
    'jefe-proyecto': 1,
    'jefe-area': 2,
    'admin': 3,
    'super-admin': 4,
}

READ_ONLY_ROLES = ('observer', 'cliente')

INTERNAL_ROLES = ('miembro', 'jefe-proyecto', 'jefe-area', 'admin', 'super-admin')
MANAGEMENT_ROLES = ('jefe-area', 'admin', 'super-admin')


def get_user_role(user: User) -> str:
    """Get effective role considering substitutions.

    Returns the highest role the user can act as right now, including
    any temporary substitution.
    """
    profile = getattr(user, 'profile', None)
    role: str = profile.role if profile else 'miembro'

    subs = get_substituting_for(user)
    for original in subs:
        orig_profile = getattr(original, 'profile', None)
        if orig_profile:
            orig_role = orig_profile.role
            if ROLE_HIERARCHY.get(orig_role, 0) > ROLE_HIERARCHY.get(role, 0):
                role = orig_role
    return role


def is_read_only(user: User) -> bool:
    """True if the user can only view, never edit (observer/cliente)."""
    return get_user_role(user) in READ_ONLY_ROLES


def is_super_admin(user: User) -> bool:
    """True only for super-admin (the highest privilege level)."""
    return get_user_role(user) == 'super-admin'


def is_admin(user: User) -> bool:
    """True for admin and super-admin (admin or higher)."""
    return get_user_role(user) in ('super-admin', 'admin')


def can_manage_admin(user: User) -> bool:
    """Can manage system-wide resources (areas, specialties, services, clients)."""
    return is_admin(user)


def can_manage_area(user: User) -> bool:
    """Can manage area-level resources (projects, members in the area)."""
    return get_user_role(user) in MANAGEMENT_ROLES


def can_manage_project(user: User, project: Optional[Project] = None) -> bool:
    """Can create/edit/delete a project.

    - super-admin / admin: any project
    - jefe-area: only projects in their own area
    - jefe-proyecto: only projects they lead
    - miembro: never (can only view and work on tasks)
    - cliente / observer: never
    """
    role = get_user_role(user)
    if is_admin(user):
        return True
    if role == 'jefe-area':
        profile = getattr(user, 'profile', None)
        if profile and profile.area:
            if project is None:
                return True
            return project.area_id == profile.area_id
    if role == 'jefe-proyecto':
        if project is None:
            return True
        return project.lead_id == user.id
    return False


def can_manage_task(user: User, task: Optional[Task] = None) -> bool:
    """Can create/edit/delete tasks.

    - super-admin / admin: any task
    - jefe-area: tasks in projects of their own area
    - jefe-proyecto: tasks in projects they lead
    - miembro: only their assigned tasks (when task is given)
    - cliente / observer: never
    """
    role = get_user_role(user)
    if is_admin(user):
        return True
    if role == 'jefe-area':
        profile = getattr(user, 'profile', None)
        if profile and profile.area:
            if task is None:
                return True
            return task.project.area_id == profile.area_id
    if role == 'jefe-proyecto':
        if task is None:
            return True
        return task.project.lead_id == user.id
    if role == 'miembro':
        if task is None:
            return False
        return task.assignee_id == user.id
    return False


def can_view_project(user: User, project: Project) -> bool:
    """Can the user see this project at all?

    Visibility is broader than management. A user can see projects they
    don't manage (read-only). This is what the dashboard and lists use.
    """
    if project is None:
        return False
    role = get_user_role(user)
    if is_admin(user) or role == 'observer':
        return True
    if role == 'jefe-area':
        profile = getattr(user, 'profile', None)
        return bool(profile and profile.area_id and profile.area_id == project.area_id)
    if role == 'jefe-proyecto':
        return project.lead_id == user.id or project.members.filter(id=user.id).exists()
    if role == 'miembro':
        return project.lead_id == user.id or project.members.filter(id=user.id).exists()
    if role == 'cliente':
        profile = getattr(user, 'profile', None)
        return bool(profile and profile.client_id and project.client_id == profile.client_id)
    return False


def can_assign_to_project(user: User, project: Project) -> bool:
    """Can the user add/remove members from this project?

    - super-admin / admin: any project
    - jefe-area: only projects in their own area
    - jefe-proyecto: only projects they lead
    - miembro / cliente / observer: never
    """
    if project is None:
        return False
    role = get_user_role(user)
    if is_admin(user):
        return True
    if role == 'jefe-area':
        profile = getattr(user, 'profile', None)
        return bool(profile and profile.area_id and profile.area_id == project.area_id)
    if role == 'jefe-proyecto':
        return project.lead_id == user.id
    return False


def can_change_user_role(user: User, target_user: User) -> bool:
    """Can change the role of another user.

    Only super-admin can change roles. Admin can only edit other fields
    of a user but not their role (avoiding privilege escalation).

    A user cannot change their own role (preventing self-lockout / self-
    escalation). A super-admin cannot demote another super-admin to
    prevent privilege lockout when multiple super-admins exist.
    """
    if not is_super_admin(user):
        return False
    if target_user.id == user.id:
        return False
    target_profile = getattr(target_user, 'profile', None)
    if target_profile and target_profile.role == 'super-admin':
        return False
    return True


def can_delete_user(user: User, target_user: User) -> bool:
    """Can delete another user.

    Only super-admin can delete users. Cannot delete yourself.
    Cannot delete another super-admin.
    """
    if not is_super_admin(user):
        return False
    if target_user.id == user.id:
        return False
    target_profile = getattr(target_user, 'profile', None)
    if target_profile and target_profile.role == 'super-admin':
        return False
    return True


def can_deactivate_user(user: User, target_user: User) -> bool:
    """Can deactivate another user (soft delete).

    Both super-admin and admin can deactivate users (separated from
    `can_delete_user`, which is destructive). Cannot deactivate yourself
    (preventing self-lockout). Cannot deactivate another super-admin.
    """
    if not is_admin(user):
        return False
    if target_user.id == user.id:
        return False
    target_profile = getattr(target_user, 'profile', None)
    if target_profile and target_profile.role == 'super-admin':
        return False
    return True


def can_view_audit_log(user: User) -> bool:
    """Can the user view the audit log at all."""
    return is_admin(user)


def can_view_all_audit_log(user: User) -> bool:
    """Can the user see audit log entries from other users.

    - super-admin: all entries
    - admin: only their own actions
    """
    return is_super_admin(user)


def can_view_settings(user: User) -> bool:
    """Can the user access system settings.

    Only super-admin (system-level configuration).
    """
    return is_super_admin(user)


def can_delete_project(user: User, project: Project) -> bool:
    """Can permanently delete a project.

    Only super-admin (project deletion is destructive and cascades to
    tasks, sprints, documents, etc.). Admin can edit but not delete.
    """
    if not is_super_admin(user):
        return False
    return True


def get_client_project_ids(user: User) -> list[int]:
    """Return project IDs the user can view as a client."""
    profile = getattr(user, 'profile', None)
    if not profile or not profile.client_id:
        return []
    return list(
        Project.objects.filter(client_id=profile.client_id)
        .values_list('id', flat=True)
    )


def filter_queryset_by_role(
    queryset: QuerySet,
    user: User,
    role: Optional[str] = None,
    model_type: str = 'project',
) -> QuerySet:
    """Filter queryset based on user role and model type.

    Visibility: what the user is allowed to see. Same as `can_view_*`
    in spirit, but applied to a queryset for list views.

    Note: super-admin and admin both see everything. If you need to
    distinguish them (e.g. for audit log), use `can_view_all_audit_log`
    in the view itself.
    """
    if not role:
        role = get_user_role(user)

    if is_admin(user):
        return queryset

    if role == 'observer':
        return queryset

    if role == 'cliente':
        project_ids = get_client_project_ids(user)
        if not project_ids:
            return queryset.none()
        if model_type == 'project':
            return queryset.filter(id__in=project_ids)
        if model_type in ('task', 'sprint', 'document', 'comment'):
            return queryset.filter(project_id__in=project_ids)
        if model_type == 'user':
            return queryset.none()
        return queryset.none()

    if role == 'jefe-area':
        profile = getattr(user, 'profile', None)
        if profile and profile.area:
            if model_type == 'project':
                return queryset.filter(area=profile.area)
            elif model_type in ('task', 'sprint', 'document', 'comment'):
                project_ids = list(Project.objects.filter(area=profile.area).values_list('id', flat=True))
                return queryset.filter(project_id__in=project_ids)
            elif model_type == 'user':
                return queryset.filter(area=profile.area)

    if role == 'jefe-proyecto':
        if model_type == 'project':
            return queryset.filter(Q(lead=user) | Q(members=user)).distinct()
        elif model_type in ('task', 'sprint', 'document', 'comment'):
            project_ids = list(Project.objects.filter(Q(lead=user) | Q(members=user)).distinct().values_list('id', flat=True))
            return queryset.filter(project_id__in=project_ids)
        elif model_type == 'user':
            project_ids = list(Project.objects.filter(Q(lead=user) | Q(members=user)).distinct().values_list('id', flat=True))
            return queryset.filter(Q(user__projects__id__in=project_ids) | Q(user__led_projects__id__in=project_ids)).distinct()

    if role == 'miembro':
        if model_type == 'project':
            return queryset.filter(Q(lead=user) | Q(members=user)).distinct()
        elif model_type == 'task':
            return queryset.filter(assignee=user)
        elif model_type in ('sprint', 'document', 'comment'):
            project_ids = list(Project.objects.filter(Q(lead=user) | Q(members=user)).distinct().values_list('id', flat=True))
            return queryset.filter(project_id__in=project_ids)
        elif model_type == 'user':
            project_ids = list(Project.objects.filter(Q(lead=user) | Q(members=user)).distinct().values_list('id', flat=True))
            return queryset.filter(Q(user__projects__id__in=project_ids) | Q(user__led_projects__id__in=project_ids)).distinct()

    return queryset.none()
