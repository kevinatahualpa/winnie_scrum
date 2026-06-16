from django.test import TestCase
from django.contrib.auth.models import User
from apps.core.infrastructure.models.models import (
    Area, Specialty, Client, Project, UserProfile,
)
from apps.core.domain.services.user_service import UserService


class UserServiceRoleManagementTest(TestCase):
    """Tests for user create/edit role, area, cliente and password behavior.

    Project assignment is no longer done in UserService. It lives in
    Project.members (M2M) and is managed from the project's own view
    (gestionar_miembros_proyecto). See tests for that view instead.
    """

    def setUp(self):
        self.area = Area.objects.create(code='IT01', name='TI')
        self.area2 = Area.objects.create(code='MKT', name='Marketing')
        self.client = Client.objects.create(name='Cliente SA')
        self.project1 = Project.objects.create(name='Project One', area=self.area)
        self.project2 = Project.objects.create(name='Project Two', area=self.area)
        self.project3 = Project.objects.create(name='Project Three', area=self.area2)

        self.super_admin = User.objects.create_user(username='super@test.com', email='super@test.com', password='pass')
        UserProfile.objects.create(user=self.super_admin, role='super-admin', status='active')

        self.admin = User.objects.create_user(username='admin@test.com', email='admin@test.com', password='pass')
        UserProfile.objects.create(user=self.admin, role='admin', status='active')

    def test_registrar_cliente_with_client_company(self):
        profile, error = UserService.registrar_usuario(
            user_creator=self.admin,
            email='cliente@empresa.com',
            first_name='Juan',
            last_name='Cliente',
            password='cli1234',
            role='cliente',
            client_id=self.client.id,
        )
        self.assertIsNotNone(profile)
        self.assertIsNone(error)
        self.assertEqual(profile.role, 'cliente')
        self.assertEqual(profile.client, self.client)

    def test_registrar_cliente_requires_client_company(self):
        profile, error = UserService.registrar_usuario(
            user_creator=self.admin,
            email='sincliente@empresa.com',
            first_name='Sin',
            last_name='Cliente',
            password='cli1234',
            role='cliente',
        )
        self.assertIsNone(profile)
        self.assertIsNotNone(error)
        self.assertIn('cliente', error.lower())

    def test_registrar_observer_without_area_or_projects(self):
        profile, error = UserService.registrar_usuario(
            user_creator=self.admin,
            email='auditor@empresa.com',
            first_name='Maria',
            last_name='Auditora',
            password='aud1234',
            role='observer',
        )
        self.assertIsNotNone(profile)
        self.assertIsNone(error)
        self.assertEqual(profile.role, 'observer')
        self.assertIsNone(profile.area)

    def test_registrar_member_with_area(self):
        profile, error = UserService.registrar_usuario(
            user_creator=self.admin,
            email='m1@test.com',
            first_name='M',
            last_name='One',
            password='m123456',
            role='miembro',
            area_id=self.area.id,
        )
        self.assertIsNotNone(profile)
        self.assertEqual(profile.area, self.area)
        self.assertEqual(profile.user.projects.count(), 0)

    def test_editar_usuario_change_to_cliente_sets_client(self):
        profile, _ = UserService.registrar_usuario(
            user_creator=self.admin,
            email='m2@test.com',
            first_name='M',
            last_name='X',
            password='m123456',
            role='miembro',
            area_id=self.area.id,
        )
        updated, error = UserService.editar_usuario(
            user_editor=self.super_admin,
            profile=profile,
            role='cliente',
            client_id=self.client.id,
        )
        self.assertIsNotNone(updated)
        self.assertIsNone(error)
        self.assertEqual(updated.role, 'cliente')
        self.assertEqual(updated.client, self.client)

    def test_editar_usuario_admin_cannot_change_role(self):
        """Admin can edit user fields but cannot change role."""
        profile, _ = UserService.registrar_usuario(
            user_creator=self.admin,
            email='m2b@test.com',
            first_name='M',
            last_name='X',
            password='m123456',
            role='miembro',
            area_id=self.area.id,
        )
        updated, error = UserService.editar_usuario(
            user_editor=self.admin,
            profile=profile,
            role='cliente',
            client_id=self.client.id,
        )
        self.assertIsNone(updated)
        self.assertIsNotNone(error)
        self.assertIn('super-admin', error.lower())

    def test_editar_usuario_change_to_cliente_requires_client(self):
        profile, _ = UserService.registrar_usuario(
            user_creator=self.admin,
            email='m3@test.com',
            first_name='M',
            last_name='X',
            password='m123456',
            role='miembro',
        )
        updated, error = UserService.editar_usuario(
            user_editor=self.super_admin,
            profile=profile,
            role='cliente',
        )
        self.assertIsNone(updated)
        self.assertIsNotNone(error)

    def test_editar_usuario_change_from_cliente_clears_client(self):
        profile, _ = UserService.registrar_usuario(
            user_creator=self.admin,
            email='c@test.com',
            first_name='C',
            last_name='L',
            password='c123456',
            role='cliente',
            client_id=self.client.id,
        )
        updated, error = UserService.editar_usuario(
            user_editor=self.super_admin,
            profile=profile,
            role='miembro',
            client_id=None,
            area_id=self.area.id,
        )
        self.assertIsNotNone(updated)
        self.assertIsNone(error)
        self.assertEqual(updated.role, 'miembro')
        self.assertIsNone(updated.client)

    def test_editar_usuario_clears_area_for_observer(self):
        profile, _ = UserService.registrar_usuario(
            user_creator=self.admin,
            email='o@test.com',
            first_name='O',
            last_name='B',
            password='o123456',
            role='miembro',
            area_id=self.area.id,
        )
        updated, error = UserService.editar_usuario(
            user_editor=self.super_admin,
            profile=profile,
            role='observer',
        )
        self.assertIsNotNone(updated)
        self.assertIsNone(error)
        self.assertIsNone(updated.area)

    def test_editar_usuario_user_cannot_change_own_role(self):
        """A super-admin cannot change their own role (preventing lockout)."""
        from apps.core.domain.services.permission_service import can_change_user_role
        self.assertFalse(can_change_user_role(self.super_admin, self.super_admin))

    def test_registrar_usuario_does_not_touch_projects(self):
        """UserService.registrar_usuario does not assign projects anymore.

        Project assignment is the responsibility of gestionar_miembros_proyecto.
        """
        profile, _ = UserService.registrar_usuario(
            user_creator=self.admin,
            email='m4@test.com',
            first_name='M',
            last_name='X',
            password='m123456',
            role='miembro',
            area_id=self.area.id,
        )
        self.assertEqual(profile.user.projects.count(), 0)
