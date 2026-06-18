from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from apps.core.infrastructure.models.models import Area, Project, UserProfile


class ProjectViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.area = Area.objects.create(code='IT01', name='TI')

        self.admin = User.objects.create_user(username='admin@test.com', email='admin@test.com', password='pass')
        UserProfile.objects.create(user=self.admin, role='admin', status='active')

        self.miembro = User.objects.create_user(username='member@test.com', email='member@test.com', password='pass')
        UserProfile.objects.create(user=self.miembro, role='miembro', status='active')

        self.project = Project.objects.create(name='Test Project', area=self.area, lead=self.admin)

    def test_projects_list_admin(self):
        self.client.login(username='admin@test.com', password='pass')
        response = self.client.get(reverse('ver_proyectos'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Project')

    def test_projects_list_miembro_not_assigned(self):
        self.client.login(username='member@test.com', password='pass')
        response = self.client.get(reverse('ver_proyectos'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Test Project')

    def test_projects_list_miembro_assigned(self):
        self.project.members.add(self.miembro)
        self.client.login(username='member@test.com', password='pass')
        response = self.client.get(reverse('ver_proyectos'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Project')

    def test_project_detail_admin(self):
        self.client.login(username='admin@test.com', password='pass')
        response = self.client.get(reverse('ver_detalle_proyecto', args=[self.project.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Project')

    def test_project_detail_miembro_assigned(self):
        self.project.members.add(self.miembro)
        self.client.login(username='member@test.com', password='pass')
        response = self.client.get(reverse('ver_detalle_proyecto', args=[self.project.pk]))
        self.assertEqual(response.status_code, 200)

    def test_project_detail_miembro_not_assigned(self):
        self.client.login(username='member@test.com', password='pass')
        response = self.client.get(reverse('ver_detalle_proyecto', args=[self.project.pk]))
        self.assertRedirects(response, reverse('ver_proyectos'))

    def test_project_create_admin(self):
        self.client.login(username='admin@test.com', password='pass')
        response = self.client.post(reverse('crear_proyecto'), {
            'name': 'New Project',
            'area': self.area.id,
            'status': 'active',
        })
        self.assertRedirects(response, reverse('ver_proyectos'))
        self.assertTrue(Project.objects.filter(name='New Project').exists())

    def test_project_create_miembro_denied(self):
        self.client.login(username='member@test.com', password='pass')
        response = self.client.post(reverse('crear_proyecto'), {
            'name': 'Unauthorized',
            'area': self.area.id,
        })
        self.assertRedirects(response, reverse('ver_proyectos'))
        self.assertFalse(Project.objects.filter(name='Unauthorized').exists())

    def test_project_delete_admin(self):
        """Admin cannot delete projects (only super-admin can)."""
        self.client.login(username='admin@test.com', password='pass')
        response = self.client.post(reverse('eliminar_proyecto', args=[self.project.pk]))
        self.assertRedirects(response, reverse('ver_proyectos'))
        self.assertTrue(Project.objects.filter(id=self.project.pk).exists())

    def test_project_delete_super_admin_succeeds(self):
        super_admin = User.objects.create_user(username='superadmin@test.com', email='superadmin@test.com', password='pass')
        UserProfile.objects.create(user=super_admin, role='super-admin', status='active')
        self.client.login(username='superadmin@test.com', password='pass')
        response = self.client.post(reverse('eliminar_proyecto', args=[self.project.pk]))
        self.assertRedirects(response, reverse('ver_proyectos'))
        # Soft delete: el proyecto sigue existiendo pero con status='cancelled'
        project = Project.objects.get(id=self.project.pk)
        self.assertEqual(project.status, 'cancelled')

    def test_project_delete_miembro_denied(self):
        self.client.login(username='member@test.com', password='pass')
        response = self.client.post(reverse('eliminar_proyecto', args=[self.project.pk]))
        self.assertRedirects(response, reverse('ver_proyectos'))
        self.assertTrue(Project.objects.filter(id=self.project.pk).exists())
        self.assertTrue(Project.objects.filter(id=self.project.pk).exists())

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('ver_dashboard'))
        self.assertRedirects(response, f'{reverse("iniciar_sesion")}?next=/')

    def test_projects_requires_login(self):
        response = self.client.get(reverse('ver_proyectos'))
        self.assertRedirects(response, f'{reverse("iniciar_sesion")}?next=/ver_proyectos/')


class ProjectMembersViewTest(TestCase):
    """Tests for /ver_proyectos/<pk>/miembros/ view."""

    def setUp(self):
        from django.test import Client
        from apps.core.infrastructure.models.models import Specialty
        self.client = Client()
        self.area1 = Area.objects.create(code='IT', name='TI')
        self.area2 = Area.objects.create(code='MKT', name='Marketing')
        self.specialty = Specialty.objects.create(name='Dev', category='development')

        self.admin = User.objects.create_user(username='admin@t.com', email='admin@t.com', password='pass')
        UserProfile.objects.create(user=self.admin, role='admin', status='active')

        self.jefe_area1 = User.objects.create_user(username='ja1@t.com', email='ja1@t.com', password='pass')
        UserProfile.objects.create(user=self.jefe_area1, role='jefe-area', area=self.area1, status='active')

        self.jefe_area2 = User.objects.create_user(username='ja2@t.com', email='ja2@t.com', password='pass')
        UserProfile.objects.create(user=self.jefe_area2, role='jefe-area', area=self.area2, status='active')

        self.jefe_proyecto = User.objects.create_user(username='jp@t.com', email='jp@t.com', password='pass')
        UserProfile.objects.create(user=self.jefe_proyecto, role='jefe-proyecto', status='active')

        self.miembro = User.objects.create_user(username='m@t.com', email='m@t.com', password='pass')
        UserProfile.objects.create(user=self.miembro, role='miembro', area=self.area1, status='active')

        self.project = Project.objects.create(
            name='Test Project', area=self.area1, lead=self.jefe_proyecto
        )

    def test_admin_can_access_gestionar_miembros(self):
        self.client.login(username='admin@t.com', password='pass')
        response = self.client.get(reverse('gestionar_miembros_proyecto', args=[self.project.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/project_members.html')

    def test_jefe_area_can_access_own_area_project(self):
        self.client.login(username='ja1@t.com', password='pass')
        response = self.client.get(reverse('gestionar_miembros_proyecto', args=[self.project.id]))
        self.assertEqual(response.status_code, 200)

    def test_jefe_area_cannot_access_other_area_project(self):
        self.client.login(username='ja2@t.com', password='pass')
        response = self.client.get(reverse('gestionar_miembros_proyecto', args=[self.project.id]))
        self.assertEqual(response.status_code, 302)

    def test_jefe_proyecto_can_access_own_project(self):
        self.client.login(username='jp@t.com', password='pass')
        response = self.client.get(reverse('gestionar_miembros_proyecto', args=[self.project.id]))
        self.assertEqual(response.status_code, 200)

    def test_miembro_cannot_access(self):
        self.client.login(username='m@t.com', password='pass')
        response = self.client.get(reverse('gestionar_miembros_proyecto', args=[self.project.id]))
        self.assertEqual(response.status_code, 302)

    def test_admin_can_add_member(self):
        self.client.login(username='admin@t.com', password='pass')
        response = self.client.post(
            reverse('gestionar_miembros_proyecto', args=[self.project.id]),
            {'action': 'add', 'user_id': self.miembro.id},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.miembro, self.project.members.all())

    def test_jefe_proyecto_can_add_member_to_own_project(self):
        self.client.login(username='jp@t.com', password='pass')
        response = self.client.post(
            reverse('gestionar_miembros_proyecto', args=[self.project.id]),
            {'action': 'add', 'user_id': self.miembro.id},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.miembro, self.project.members.all())

    def test_admin_can_remove_member(self):
        self.project.members.add(self.miembro)
        self.client.login(username='admin@t.com', password='pass')
        response = self.client.post(
            reverse('gestionar_miembros_proyecto', args=[self.project.id]),
            {'action': 'remove', 'user_id': self.miembro.id},
        )
        self.assertEqual(response.status_code, 302)
        self.assertNotIn(self.miembro, self.project.members.all())

    def test_cannot_remove_project_lead(self):
        self.client.login(username='admin@t.com', password='pass')
        response = self.client.post(
            reverse('gestionar_miembros_proyecto', args=[self.project.id]),
            {'action': 'remove', 'user_id': self.jefe_proyecto.id},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.project.lead_id, self.jefe_proyecto.id)

    def test_add_member_creates_audit_log(self):
        from apps.core.infrastructure.models.models import AuditLog
        self.client.login(username='admin@t.com', password='pass')
        self.client.post(
            reverse('gestionar_miembros_proyecto', args=[self.project.id]),
            {'action': 'add', 'user_id': self.miembro.id},
        )
        log = AuditLog.objects.filter(action='PROJECT_MEMBER_ADD', entity_id=str(self.project.id)).first()
        self.assertIsNotNone(log)
        self.assertIn(self.miembro.get_full_name() or self.miembro.username, log.details)

    def test_add_existing_member_is_idempotent(self):
        self.project.members.add(self.miembro)
        self.client.login(username='admin@t.com', password='pass')
        response = self.client.post(
            reverse('gestionar_miembros_proyecto', args=[self.project.id]),
            {'action': 'add', 'user_id': self.miembro.id},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.project.members.count(), 1)
