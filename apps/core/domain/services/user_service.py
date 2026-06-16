from typing import Optional, Tuple
from django.db import transaction
from django.contrib.auth.models import User
from apps.core.infrastructure.models.models import UserProfile
from apps.core.infrastructure.repositories import UserRepository
from apps.core.domain.services.permission_service import (
    can_manage_admin, can_change_user_role,
)
from apps.core.domain.services.notification_service import create_audit_log

user_repo = UserRepository()


class UserService:
    """Service layer for User/Member business logic"""

    @staticmethod
    @transaction.atomic
    def self_register(
        email: str,
        first_name: str = '',
        last_name: str = '',
        password: str = 'password123',
    ) -> Tuple[Optional[User], Optional[str]]:
        """Public self-registration - creates user with pending status."""
        if User.objects.filter(username=email).exists():
            return None, 'Email ya registrado'

        user = User.objects.create_user(
            username=email,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
        )

        UserProfile.objects.create(user=user, role='miembro', status='pending')

        create_audit_log(user, 'USER_CREATE', 'user', user.id, f'Registro: {user.get_full_name()}')
        return user, None

    @staticmethod
    @transaction.atomic
    def registrar_usuario(
        user_creator: User,
        email: str,
        first_name: str = '',
        last_name: str = '',
        password: str = 'password123',
        phone: str = '',
        area_id: Optional[int] = None,
        specialty_id: Optional[int] = None,
        client_id: Optional[int] = None,
        role: str = 'miembro',
        status: str = 'active',
        color: str = '#00bcd4',
    ) -> Tuple[Optional[UserProfile], Optional[str]]:
        """Create a new user with profile and permission check.

        For role='cliente', client_id is required. Project assignment
        happens later via the project's members view, not here.
        """
        if not can_manage_admin(user_creator):
            return None, 'No tienes permiso para crear usuarios'

        if role == 'cliente' and not client_id:
            return None, 'El rol cliente requiere una empresa asociada'

        if User.objects.filter(username=email).exists():
            return None, 'Email ya registrado'

        user = User.objects.create_user(
            username=email,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
        )

        profile = user_repo.create(
            user=user,
            phone=phone,
            area_id=area_id or None,
            specialty_id=specialty_id or None,
            client_id=client_id or None,
            role=role,
            status=status,
            color=color,
        )

        create_audit_log(user_creator, 'USER_CREATE', 'user', user.id, f'Usuario creado: {user.get_full_name()}')
        return profile, None

    @staticmethod
    @transaction.atomic
    def editar_usuario(
        user_editor: User,
        profile: UserProfile,
        **kwargs,
    ) -> Tuple[Optional[UserProfile], Optional[str]]:
        """Update an existing user and profile with permission check.

        Supports updating client_id, area_id, specialty_id, role, status, color,
        plus user fields (first_name, last_name, email, password).
        Project assignment is managed via the project's members view.

        Role change is restricted: only super-admin can change roles.
        Admin can edit other fields but not escalate privileges.
        """
        if not can_manage_admin(user_editor):
            return None, 'No tienes permiso para editar usuarios'

        user = profile.user

        if 'first_name' in kwargs:
            user.first_name = kwargs['first_name']
        if 'last_name' in kwargs:
            user.last_name = kwargs['last_name']
        if 'email' in kwargs:
            user.email = kwargs['email']
            user.username = user.email
        if 'password' in kwargs and kwargs['password']:
            user.set_password(kwargs['password'])

        user.save()

        new_role = kwargs.get('role', profile.role)
        old_role = profile.role

        if 'role' in kwargs and new_role != old_role:
            if not can_change_user_role(user_editor, user):
                return None, 'Solo el super-admin puede cambiar el rol de un usuario'

        if new_role == 'cliente' and not kwargs.get('client_id') and not profile.client_id:
            return None, 'El rol cliente requiere una empresa asociada'

        if new_role in ('observer', 'super-admin', 'admin'):
            kwargs['area_id'] = None
            kwargs['specialty_id'] = None

        profile_fields = {k: v for k, v in kwargs.items() if k in ['phone', 'area_id', 'specialty_id', 'client_id', 'role', 'status', 'color']}
        profile = user_repo.update(profile.id, **profile_fields)

        create_audit_log(user_editor, 'USER_EDIT', 'user', user.id, f'Usuario editado: {user.get_full_name()}')
        return profile, None

    @staticmethod
    @transaction.atomic
    def desactivar_usuario(
        user_deleter: User,
        profile: UserProfile,
    ) -> Tuple[bool, Optional[str]]:
        """Soft delete: deactivate user instead of deleting from database.

        Preserves all history (tasks, comments, time entries, messages).
        """
        if not can_manage_admin(user_deleter):
            return False, 'No tienes permiso para desactivar usuarios'

        if profile.status == 'dismissed':
            return False, 'Este usuario ya esta desactivado'

        name = profile.user.get_full_name()
        profile.status = 'dismissed'
        profile.save(update_fields=['status'])
        create_audit_log(user_deleter, 'USER_DEACTIVATE', 'user', profile.id, f'Usuario desactivado: {name}')
        return True, None

    @staticmethod
    @transaction.atomic
    def reactivar_usuario(
        user_activator: User,
        profile: UserProfile,
    ) -> Tuple[bool, Optional[str]]:
        """Reactivate a previously deactivated user."""
        if not can_manage_admin(user_activator):
            return False, 'No tienes permiso para reactivar usuarios'

        if profile.status != 'dismissed':
            return False, 'Este usuario ya esta activo'

        name = profile.user.get_full_name()
        profile.status = 'active'
        profile.save(update_fields=['status'])
        create_audit_log(user_activator, 'USER_REACTIVATE', 'user', profile.id, f'Usuario reactivado: {name}')
        return True, None
