"""Regression test para bug: audit view falla con user=None."""
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from apps.core.infrastructure.models.models import (
    Area, UserProfile, AuditLog,
)


class AuditLogNullUserTest(TestCase):
    """Verifica que el template audit.html maneja correctamente logs sin user.

    Bug original: `{{ log.user.get_full_name|default:log.user.username }}`
    fallaba con VariableDoesNotExist cuando log.user es None.
    """

    def setUp(self):
        self.super_admin = User.objects.create_user(
            username='super@test.com', email='super@test.com', password='pass'
        )
        UserProfile.objects.create(user=self.super_admin, role='super-admin', status='active')

    def test_audit_view_renders_when_user_is_null(self):
        """AuditLog con user=None debe renderizar 'Sistema' sin error."""
        AuditLog.objects.create(
            user=None,
            action='SYSTEM_CLEANUP',
            entity='system',
            entity_id='0',
            details='Limpieza automatica sin usuario',
        )

        self.client.login(username="super@test.com", password='pass')
        response = self.client.get(reverse('ver_auditoria'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sistema')

    def test_audit_view_renders_normal_user(self):
        """AuditLog con user real debe mostrar el nombre."""
        AuditLog.objects.create(
            user=self.super_admin,
            action='TEST_ACTION',
            entity='test',
            entity_id='1',
            details='Test normal',
        )

        self.client.login(username="super@test.com", password='pass')
        response = self.client.get(reverse('ver_auditoria'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'super@test.com')

    def test_audit_view_handles_mixed_users(self):
        """Mezcla de logs con user y sin user renderiza todos correctamente."""
        AuditLog.objects.create(
            user=self.super_admin,
            action='USER_ACTION',
            entity='test',
            entity_id='1',
            details='Con usuario',
        )
        AuditLog.objects.create(
            user=None,
            action='SYSTEM_ACTION',
            entity='test',
            entity_id='2',
            details='Sin usuario',
        )

        self.client.login(username="super@test.com", password='pass')
        response = self.client.get(reverse('ver_auditoria'))

        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertIn('super@test.com', body)
        self.assertIn('Sistema', body)
