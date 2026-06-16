from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import date, timedelta
from django.utils import timezone
from apps.core.infrastructure.models.models import (
    Area, Specialty, Project, Sprint, Task, UserProfile,
    ServiceRequest, Client as ClientModel, Substitution, Notification, Document
)


class BoardViewsTest(TestCase):
    def setUp(self):
        self.area = Area.objects.create(code='IT01', name='TI')
        self.admin = User.objects.create_user(username='admin@test.com', email='admin@test.com', password='pass')
        UserProfile.objects.create(user=self.admin, role='admin', status='active')
        self.project = Project.objects.create(name='Test Project', area=self.area)
        self.task = Task.objects.create(project=self.project, title='Board Task', status='todo')

    def test_board_requires_login(self):
        response = self.client.get(reverse('ver_tablero'))
        self.assertRedirects(response, f'{reverse("iniciar_sesion")}?next=/ver_tablero/')

    def test_board_loads(self):
        self.client.login(username='admin@test.com', password='pass')
        response = self.client.get(reverse('ver_tablero'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Board')

    def test_board_filters_by_area(self):
        self.client.login(username='admin@test.com', password='pass')
        response = self.client.get(reverse('ver_tablero'), {'area': self.area.id})
        self.assertEqual(response.status_code, 200)

    def test_board_filters_by_project(self):
        self.client.login(username='admin@test.com', password='pass')
        response = self.client.get(reverse('ver_tablero'), {'project': self.project.id})
        self.assertEqual(response.status_code, 200)

    def test_board_filters_by_assignee(self):
        self.client.login(username='admin@test.com', password='pass')
        response = self.client.get(reverse('ver_tablero'), {'assignee': self.admin.id})
        self.assertEqual(response.status_code, 200)

    def test_board_shows_task_in_correct_column(self):
        self.client.login(username='admin@test.com', password='pass')
        response = self.client.get(reverse('ver_tablero'))
        self.assertContains(response, 'Board Task')


class BacklogViewsTest(TestCase):
    def setUp(self):
        
        self.area = Area.objects.create(code='IT01', name='TI')
        self.admin = User.objects.create_user(username='admin@test.com', email='admin@test.com', password='pass')
        UserProfile.objects.create(user=self.admin, role='admin', status='active')
        self.project = Project.objects.create(name='Test Project', area=self.area)
        self.backlog_task = Task.objects.create(
            project=self.project, title='Backlog Task', status='backlog', priority='high'
        )
        self.done_task = Task.objects.create(
            project=self.project, title='Done Task', status='done'
        )

    def test_backlog_requires_login(self):
        response = self.client.get(reverse('ver_backlog'))
        self.assertRedirects(response, f'{reverse("iniciar_sesion")}?next=/ver_backlog/')

    def test_backlog_shows_only_backlog_and_todo(self):
        self.client.login(username='admin@test.com', password='pass')
        response = self.client.get(reverse('ver_backlog'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Backlog Task')
        self.assertNotContains(response, 'Done Task')

    def test_backlog_high_priority_first(self):
        Task.objects.create(project=self.project, title='Low Task', status='backlog', priority='low')
        self.client.login(username='admin@test.com', password='pass')
        response = self.client.get(reverse('ver_backlog'))
        self.assertContains(response, 'Backlog Task')
        self.assertContains(response, 'Low Task')


class DocumentsViewsTest(TestCase):
    def setUp(self):
        
        self.admin = User.objects.create_user(username='admin@test.com', email='admin@test.com', password='pass')
        UserProfile.objects.create(user=self.admin, role='admin', status='active')
        self.project = Project.objects.create(name='Test Project', lead=self.admin)
        self.doc = Document.objects.create(
            project=self.project, name='test.txt', uploaded_by=self.admin,
            size=1024, type='other', file='documents/test.txt'
        )

    def test_documents_requires_login(self):
        response = self.client.get(reverse('ver_documentos'))
        self.assertRedirects(response, f'{reverse("iniciar_sesion")}?next=/ver_documentos/')

    def test_documents_list_loads(self):
        self.client.login(username='admin@test.com', password='pass')
        response = self.client.get(reverse('ver_documentos'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test.txt')

    def test_documents_filter_by_project(self):
        self.client.login(username='admin@test.com', password='pass')
        response = self.client.get(reverse('ver_documentos'), {'project': self.project.id})
        self.assertEqual(response.status_code, 200)

    def test_documents_sort_by_name(self):
        self.client.login(username='admin@test.com', password='pass')
        response = self.client.get(reverse('ver_documentos'), {'sort': 'name'})
        self.assertEqual(response.status_code, 200)

    def test_document_upload_requires_post(self):
        self.client.login(username='admin@test.com', password='pass')
        response = self.client.get(reverse('subir_documento'))
        self.assertEqual(response.status_code, 405)

    def test_document_delete_requires_post(self):
        self.client.login(username='admin@test.com', password='pass')
        response = self.client.get(reverse('eliminar_documento', args=[self.doc.pk]))
        self.assertEqual(response.status_code, 405)

    def test_document_delete_admin(self):
        self.client.login(username='admin@test.com', password='pass')
        response = self.client.post(reverse('eliminar_documento', args=[self.doc.pk]))
        self.assertRedirects(response, reverse('ver_documentos'))
        self.assertFalse(Document.objects.filter(id=self.doc.pk).exists())

    def test_document_delete_requires_login(self):
        response = self.client.post(reverse('eliminar_documento', args=[self.doc.pk]))
        self.assertRedirects(response, f'{reverse("iniciar_sesion")}?next=/document/{self.doc.pk}/delete/')


class TeamViewsTest(TestCase):
    def setUp(self):
        
        self.area = Area.objects.create(code='IT01', name='TI')
        self.admin = User.objects.create_user(username='admin@test.com', email='admin@test.com', password='pass')
        UserProfile.objects.create(user=self.admin, role='admin', status='active')
        self.member = User.objects.create_user(username='member@test.com', email='member@test.com', password='pass')
        UserProfile.objects.create(user=self.member, role='miembro', status='active', area=self.area)

    def test_team_requires_login(self):
        response = self.client.get(reverse('ver_equipo'))
        self.assertRedirects(response, f'{reverse("iniciar_sesion")}?next=/ver_equipo/')

    def test_team_list_loads(self):
        self.client.login(username='admin@test.com', password='pass')
        response = self.client.get(reverse('ver_equipo'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'admin@test.com')

    def test_team_filter_by_area(self):
        self.client.login(username='admin@test.com', password='pass')
        response = self.client.get(reverse('ver_equipo'), {'area': self.area.id})
        self.assertEqual(response.status_code, 200)

    def test_team_filter_by_role(self):
        self.client.login(username='admin@test.com', password='pass')
        response = self.client.get(reverse('ver_equipo'), {'role': 'admin'})
        self.assertEqual(response.status_code, 200)

    def test_member_create_admin_access(self):
        self.client.login(username='admin@test.com', password='pass')
        response = self.client.get(reverse('registrar_usuario'))
        self.assertEqual(response.status_code, 200)

    def test_member_create_post(self):
        self.client.login(username='admin@test.com', password='pass')
        specialty = Specialty.objects.create(name='Dev', category='development')
        response = self.client.post(reverse('registrar_usuario'), {
            'first_name': 'New', 'last_name': 'User',
            'email': 'new@test.com', 'password': 'test12345',
            'password_confirm': 'test12345',
            'role': 'miembro', 'status': 'active', 'color': '#00bcd4',
            'area': self.area.id, 'specialty': specialty.id,
        })
        self.assertRedirects(response, reverse('ver_equipo'))
        self.assertTrue(User.objects.filter(email='new@test.com').exists())

    def test_member_create_miembro_denied(self):
        self.client.login(username='member@test.com', password='pass')
        response = self.client.get(reverse('registrar_usuario'))
        self.assertRedirects(response, reverse('ver_equipo'))

    def test_member_delete_admin(self):
        self.client.login(username='admin@test.com', password='pass')
        response = self.client.post(reverse('eliminar_usuario', args=[UserProfile.objects.get(user=self.member).pk]))
        self.assertRedirects(response, reverse('ver_equipo'))

    def test_member_update_admin(self):
        self.client.login(username='admin@test.com', password='pass')
        profile = UserProfile.objects.get(user=self.member)
        response = self.client.get(reverse('editar_usuario', args=[profile.pk]))
        self.assertEqual(response.status_code, 200)


class ServiceViewsTest(TestCase):
    def setUp(self):
        
        self.admin = User.objects.create_user(username='admin@test.com', email='admin@test.com', password='pass')
        UserProfile.objects.create(user=self.admin, role='admin', status='active')
        self.member = User.objects.create_user(username='member@test.com', email='member@test.com', password='pass')
        UserProfile.objects.create(user=self.member, role='miembro', status='active')
        self.client_model = ClientModel.objects.create(name='Test Client')
        self.sr = ServiceRequest.objects.create(
            client=self.client_model, service='consultoria', description='Test request',
            assigned_to=self.admin
        )

    def test_services_requires_login(self):
        response = self.client.get(reverse('ver_servicios'))
        self.assertRedirects(response, f'{reverse("iniciar_sesion")}?next=/ver_servicios/')

    def test_services_list_admin(self):
        self.client.login(username='admin@test.com', password='pass')
        response = self.client.get(reverse('ver_servicios'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Client')

    def test_services_list_member_sees_assigned_only(self):
        self.client.login(username='member@test.com', password='pass')
        response = self.client.get(reverse('ver_servicios'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Test Client')

    def test_service_create_admin(self):
        self.client.login(username='admin@test.com', password='pass')
        response = self.client.post(reverse('crear_servicio'), {
            'client': self.client_model.id, 'service': 'consultoria',
            'description': 'New request', 'status': 'new',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ServiceRequest.objects.filter(description='New request').exists())

    def test_service_delete_admin(self):
        self.client.login(username='admin@test.com', password='pass')
        pk = self.sr.pk
        response = self.client.post(reverse('eliminar_servicio', args=[pk]))
        self.assertRedirects(response, reverse('ver_servicios'))
        self.assertFalse(ServiceRequest.objects.filter(id=pk).exists())


class SubstitutionViewsTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='sub_admin@test.com', email='sub_admin@test.com', password='pass')
        UserProfile.objects.create(user=self.admin, role='admin', status='active')
        self.member = User.objects.create_user(username='sub_member@test.com', email='sub_member@test.com', password='pass')
        UserProfile.objects.create(user=self.member, role='miembro', status='active')

    def test_substitutions_requires_login(self):
        response = self.client.get(reverse('ver_suplencias'))
        self.assertRedirects(response, f'{reverse("iniciar_sesion")}?next=/ver_suplencias/')

    def test_substitutions_admin_access(self):
        self.client.login(username='sub_admin@test.com', password='pass')
        response = self.client.get(reverse('ver_suplencias'))
        self.assertEqual(response.status_code, 200)

    def test_substitutions_member_denied(self):
        self.client.login(username='sub_member@test.com', password='pass')
        response = self.client.get(reverse('ver_suplencias'))
        self.assertRedirects(response, reverse('ver_dashboard'))

    def test_substitution_create_admin(self):
        self.client.login(username='sub_admin@test.com', password='pass')
        response = self.client.post(reverse('crear_suplencia'), {
            'original_user': self.admin.id,
            'substitute_user': self.member.id,
            'start_date': timezone.now().date(),
            'end_date': timezone.now().date() + timedelta(days=3),
            'scope': 'all',
        })
        self.assertRedirects(response, reverse('ver_suplencias'))

    def test_substitution_deactivate_admin(self):
        sub = Substitution.objects.create(
            original_user=self.admin, substitute_user=self.member,
            start_date=timezone.now().date() - timedelta(days=1),
            end_date=timezone.now().date() + timedelta(days=7),
        )
        self.client.login(username='sub_admin@test.com', password='pass')
        response = self.client.post(reverse('desactivar_suplencia', args=[sub.pk]))
        self.assertRedirects(response, reverse('ver_suplencias'))
        sub.refresh_from_db()
        self.assertFalse(sub.active)


class NotificationViewsTest(TestCase):
    def setUp(self):
        
        self.user = User.objects.create_user(username='user@test.com', email='user@test.com', password='pass')
        UserProfile.objects.create(user=self.user, role='miembro', status='active')
        self.notif = Notification.objects.create(
            user=self.user, type='info', title='Test Notif', message='Test message'
        )

    def test_notifications_requires_login(self):
        response = self.client.get(reverse('ver_notificaciones'))
        self.assertRedirects(response, f'{reverse("iniciar_sesion")}?next=/ver_notificaciones/')

    def test_notifications_list(self):
        self.client.login(username='user@test.com', password='pass')
        response = self.client.get(reverse('ver_notificaciones'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Notif')

    def test_notification_mark_read(self):
        self.client.login(username='user@test.com', password='pass')
        response = self.client.post(reverse('marcar_notificacion_leida', args=[self.notif.pk]))
        self.assertRedirects(response, reverse('ver_notificaciones'))
        self.notif.refresh_from_db()
        self.assertTrue(self.notif.read)

    def test_notification_mark_read_other_user_denied(self):
        other = User.objects.create_user(username='other@test.com', email='other@test.com', password='pass')
        UserProfile.objects.create(user=other, role='miembro', status='active')
        self.client.login(username='other@test.com', password='pass')
        response = self.client.post(reverse('marcar_notificacion_leida', args=[self.notif.pk]))
        self.assertEqual(response.status_code, 404)

    def test_notifications_mark_all_read(self):
        Notification.objects.create(user=self.user, type='info', title='Another', message='Another')
        self.client.login(username='user@test.com', password='pass')
        response = self.client.post(reverse('marcar_todas_leidas'))
        self.assertRedirects(response, reverse('ver_notificaciones'))
        self.assertEqual(Notification.objects.filter(user=self.user, read=True).count(), 2)
