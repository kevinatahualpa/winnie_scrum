from django.test import TestCase
from django.contrib.auth.models import User
from apps.core.infrastructure.models.models import Area, Client, Project
from apps.core.domain.services.project_service import ProjectService


class ProjectServiceTest(TestCase):
    def setUp(self):
        self.area = Area.objects.create(code='IT01', name='TI')
        self.client = Client.objects.create(name='Test Client')

        self.admin = User.objects.create_user(username='admin@test.com', email='admin@test.com', password='pass')
        from apps.core.infrastructure.models.models import UserProfile
        UserProfile.objects.create(user=self.admin, role='admin', status='active')

        self.miembro = User.objects.create_user(username='member@test.com', email='member@test.com', password='pass')
        UserProfile.objects.create(user=self.miembro, role='miembro', status='active')

    def test_create_project_success(self):
        project, error = ProjectService.crear_proyecto(
            user=self.admin,
            name='New Project',
            area_id=self.area.id,
            description='A new project',
            status='active',
        )
        self.assertIsNotNone(project)
        self.assertIsNone(error)
        self.assertEqual(project.name, 'New Project')
        self.assertEqual(project.area, self.area)

    def test_create_project_no_permission(self):
        project, error = ProjectService.crear_proyecto(
            user=self.miembro,
            name='Unauthorized Project',
            area_id=self.area.id,
        )
        self.assertIsNone(project)
        self.assertIsNotNone(error)
        self.assertIn('No tienes permiso', error)

    def test_update_project_success(self):
        project = Project.objects.create(name='Old Name', area=self.area)
        updated, error = ProjectService.editar_proyecto(
            user=self.admin,
            project=project,
            name='New Name',
            description='Updated description',
        )
        self.assertIsNotNone(updated)
        self.assertIsNone(error)
        self.assertEqual(updated.name, 'New Name')

    def test_update_project_no_permission(self):
        project = Project.objects.create(name='Test', area=self.area)
        updated, error = ProjectService.editar_proyecto(
            user=self.miembro,
            project=project,
            name='Hacked',
        )
        self.assertIsNone(updated)
        self.assertIsNotNone(error)

    def test_delete_project_success(self):
        project = Project.objects.create(name='To Delete', area=self.area)
        success, error = ProjectService.eliminar_proyecto(self.admin, project)
        self.assertTrue(success)
        self.assertIsNone(error)
        self.assertFalse(Project.objects.filter(id=project.id).exists())

    def test_delete_project_no_permission(self):
        project = Project.objects.create(name='Protected', area=self.area)
        success, error = ProjectService.eliminar_proyecto(self.miembro, project)
        self.assertFalse(success)
        self.assertIsNotNone(error)
