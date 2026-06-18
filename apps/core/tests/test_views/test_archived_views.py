from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from apps.core.infrastructure.models.models import (
    Area, Client, Specialty, Project, UserProfile, Document,
)
from apps.core.tests.test_views.test_more_views import DocumentsViewsTest


class ArchivedViewsTest(TestCase):
    """Tests para la vista unificada de Archivados.

    Cubre el ciclo: archivar (soft delete) -> ver en archivados -> restaurar.
    Solo admin+ puede ver y restaurar.
    """

    def setUp(self):
        self.area = Area.objects.create(code='IT', name='TI', status='active')
        self.super_admin = User.objects.create_user(
            username='super@test.com', email='super@test.com', password='pass'
        )
        UserProfile.objects.create(user=self.super_admin, role='super-admin', status='active')

        self.admin = User.objects.create_user(
            username='admin@test.com', email='admin@test.com', password='pass'
        )
        UserProfile.objects.create(user=self.admin, role='admin', status='active')

        self.member = User.objects.create_user(
            username='member@test.com', email='member@test.com', password='pass'
        )
        UserProfile.objects.create(user=self.member, role='miembro', status='active')

    def test_ver_archivados_requires_admin(self):
        self.client.login(username='member@test.com', password='pass')
        response = self.client.get(reverse('ver_archivados'))
        self.assertRedirects(response, reverse('ver_dashboard'))

    def test_admin_can_see_archived_page(self):
        self.client.login(username='admin@test.com', password='pass')
        response = self.client.get(reverse('ver_archivados'))
        self.assertEqual(response.status_code, 200)

    def test_super_admin_can_see_archived_page(self):
        self.client.login(username='super@test.com', password='pass')
        response = self.client.get(reverse('ver_archivados'))
        self.assertEqual(response.status_code, 200)

    def test_full_cycle_area_archive_and_restore(self):
        self.client.login(username='admin@test.com', password='pass')

        self.client.post(reverse('eliminar_area', args=[self.area.id]))

        self.area.refresh_from_db()
        self.assertEqual(self.area.status, 'inactive')

        response = self.client.get(reverse('ver_archivados'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.area, response.context['inactive_areas'])

        self.client.post(reverse('restaurar', args=['area', self.area.id]))

        self.area.refresh_from_db()
        self.assertEqual(self.area.status, 'active')

    def test_restore_invalid_type_returns_error(self):
        self.client.login(username='admin@test.com', password='pass')
        response = self.client.post(reverse('restaurar', args=['invalid_type', 1]))
        self.assertRedirects(response, reverse('ver_archivados'))

    def test_restore_non_existent_item_returns_error(self):
        self.client.login(username='admin@test.com', password='pass')
        response = self.client.post(reverse('restaurar', args=['area', 99999]))
        self.assertRedirects(response, reverse('ver_archivados'))

    def test_full_cycle_client_archive_and_restore(self):
        client_obj = Client.objects.create(name='Test Client SA')
        self.client.login(username='admin@test.com', password='pass')

        self.client.post(reverse('eliminar_cliente', args=[client_obj.id]))
        client_obj.refresh_from_db()
        self.assertFalse(client_obj.is_active)

        response = self.client.get(reverse('ver_archivados'))
        self.assertIn(client_obj, response.context['archived_clients'])

        self.client.post(reverse('restaurar', args=['client', client_obj.id]))
        client_obj.refresh_from_db()
        self.assertTrue(client_obj.is_active)

    def test_full_cycle_specialty_archive_and_restore(self):
        specialty = Specialty.objects.create(name='Backend', category='development')
        self.client.login(username='admin@test.com', password='pass')

        self.client.post(reverse('eliminar_especialidad', args=[specialty.id]))
        specialty.refresh_from_db()
        self.assertFalse(specialty.is_active)

        response = self.client.get(reverse('ver_archivados'))
        self.assertIn(specialty, response.context['inactive_specialties'])

        self.client.post(reverse('restaurar', args=['specialty', specialty.id]))
        specialty.refresh_from_db()
        self.assertTrue(specialty.is_active)

    def test_restore_requires_post(self):
        self.client.login(username='admin@test.com', password='pass')
        response = self.client.get(reverse('restaurar', args=['area', self.area.id]))
        self.assertEqual(response.status_code, 405)

    def test_total_archived_counter(self):
        self.client.login(username='admin@test.com', password='pass')

        self.area.status = 'inactive'
        self.area.save()

        response = self.client.get(reverse('ver_archivados'))
        self.assertEqual(response.context['total_archived'], 1)
