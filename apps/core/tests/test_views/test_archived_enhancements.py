from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from apps.core.infrastructure.models.models import (
    Area, Client, Specialty, Project, UserProfile, AuditLog,
)
from apps.core.domain.services.notification_service import create_audit_log


class ArchivedBadgeAndContextTest(TestCase):
    """Tests para badge contador, contexto 'Archivado por X' y doble confirmacion."""

    def setUp(self):
        self.area = Area.objects.create(code='IT', name='TI', status='active')
        self.admin = User.objects.create_user(
            username='admin@test.com', email='admin@test.com', password='pass'
        )
        UserProfile.objects.create(user=self.admin, role='admin', status='active')
        self.member = User.objects.create_user(
            username='member@test.com', email='member@test.com', password='pass'
        )
        UserProfile.objects.create(user=self.member, role='miembro', status='active')

    def test_context_processor_includes_archived_count(self):
        from apps.core.presentation.context_processors import unread_notifications
        self.client.login(username='admin@test.com', password='pass')
        request = self.client.get(reverse('ver_dashboard')).wsgi_request
        ctx = unread_notifications(request)
        self.assertIn('archived_count', ctx)
        self.assertEqual(ctx['archived_count'], 0)

        self.area.status = 'inactive'
        self.area.save()
        from django.core.cache import cache
        cache.delete('archived_items_count')

        request = self.client.get(reverse('ver_dashboard')).wsgi_request
        ctx = unread_notifications(request)
        self.assertEqual(ctx['archived_count'], 1)

    def test_archived_info_appears_in_view(self):
        self.client.login(username='admin@test.com', password='pass')
        self.client.post(reverse('eliminar_area', args=[self.area.id]))

        response = self.client.get(reverse('ver_archivados'))
        self.assertEqual(response.status_code, 200)
        area_in_list = response.context['inactive_areas'][0]
        self.assertEqual(area_in_list.archived_by, self.admin)
        self.assertIsNotNone(area_in_list.archived_at)

    def test_double_confirm_required_for_project(self):
        project = Project.objects.create(name='Mi Proyecto Critico', area=self.area)
        project.status = 'cancelled'
        project.save()

        self.client.login(username='admin@test.com', password='pass')

        response = self.client.post(
            reverse('restaurar', args=['project', project.id]),
            {'confirmacion': 'nombre incorrecto'},
        )
        self.assertRedirects(response, reverse('ver_archivados'))

        project.refresh_from_db()
        self.assertEqual(project.status, 'cancelled')

    def test_double_confirm_with_correct_name_restores_project(self):
        project = Project.objects.create(name='Mi Proyecto Critico', area=self.area)
        project.status = 'cancelled'
        project.save()

        self.client.login(username='admin@test.com', password='pass')

        response = self.client.post(
            reverse('restaurar', args=['project', project.id]),
            {'confirmacion': 'Mi Proyecto Critico'},
        )
        self.assertRedirects(response, reverse('ver_archivados'))

        project.refresh_from_db()
        self.assertEqual(project.status, 'planned')

    def test_double_confirm_required_for_user(self):
        target_user = User.objects.create_user(
            username='rechazado@test.com', email='rechazado@test.com', password='pass'
        )
        profile = UserProfile.objects.create(
            user=target_user, role='miembro', status='rejected'
        )

        self.client.login(username='admin@test.com', password='pass')

        response = self.client.post(
            reverse('restaurar', args=['user', profile.id]),
            {'confirmacion': 'wrong name'},
        )
        self.assertRedirects(response, reverse('ver_archivados'))

        profile.refresh_from_db()
        self.assertEqual(profile.status, 'rejected')

    def test_double_confirm_with_correct_name_restores_user(self):
        target_user = User.objects.create_user(
            username='juan@test.com', email='juan@test.com', password='pass',
            first_name='Juan', last_name='Perez',
        )
        profile = UserProfile.objects.create(
            user=target_user, role='miembro', status='dismissed'
        )

        self.client.login(username='admin@test.com', password='pass')

        response = self.client.post(
            reverse('restaurar', args=['user', profile.id]),
            {'confirmacion': 'Juan Perez'},
        )
        self.assertRedirects(response, reverse('ver_archivados'))

        profile.refresh_from_db()
        self.assertEqual(profile.status, 'active')
        target_user.refresh_from_db()
        self.assertTrue(target_user.is_active)

    def test_non_critical_items_dont_need_double_confirm(self):
        self.client.login(username='admin@test.com', password='pass')

        self.client.post(reverse('eliminar_area', args=[self.area.id]))

        response = self.client.post(
            reverse('restaurar', args=['area', self.area.id]),
        )
        self.assertRedirects(response, reverse('ver_archivados'))

        self.area.refresh_from_db()
        self.assertEqual(self.area.status, 'active')

    def test_archived_count_cleared_after_restore(self):
        client_obj = Client.objects.create(name='Test Client')
        self.client.login(username='admin@test.com', password='pass')

        self.client.post(reverse('eliminar_cliente', args=[client_obj.id]))

        response = self.client.get(reverse('ver_dashboard'))
        self.assertEqual(response.context['archived_count'], 1)

        self.client.post(reverse('restaurar', args=['client', client_obj.id]))

        response = self.client.get(reverse('ver_dashboard'))
        self.assertEqual(response.context['archived_count'], 0)

    def test_restore_creates_audit_log_entry(self):
        self.client.login(username='admin@test.com', password='pass')

        self.client.post(reverse('eliminar_area', args=[self.area.id]))
        audit_before = AuditLog.objects.filter(action='AREA_RESTORE').count()

        self.client.post(reverse('restaurar', args=['area', self.area.id]))

        audit_after = AuditLog.objects.filter(action='AREA_RESTORE').count()
        self.assertEqual(audit_after, audit_before + 1)

        last_log = AuditLog.objects.filter(action='AREA_RESTORE').first()
        self.assertIn('restaurada', last_log.details.lower())

    def test_sidebar_archived_count_only_for_admin(self):
        from django.core.cache import cache
        cache.delete('archived_items_count')
        self.area.status = 'inactive'
        self.area.save()
        cache.delete('archived_items_count')

        self.client.login(username='admin@test.com', password='pass')
        response = self.client.get(reverse('ver_dashboard'))
        self.assertEqual(response.context['archived_count'], 1)

        self.client.logout()
        self.client.login(username='member@test.com', password='pass')
        response = self.client.get(reverse('ver_dashboard'))
        self.assertEqual(response.context['archived_count'], 0)
