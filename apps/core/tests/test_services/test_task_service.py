from django.test import TestCase
from django.contrib.auth.models import User
from apps.core.infrastructure.models.models import Area, Project, Task, UserProfile
from apps.core.domain.services.task_service import TaskService


class TaskServiceTest(TestCase):
    def setUp(self):
        self.area = Area.objects.create(code='IT01', name='TI')
        self.project = Project.objects.create(name='Test Project', area=self.area)

        self.admin = User.objects.create_user(username='admin@test.com', email='admin@test.com', password='pass')
        UserProfile.objects.create(user=self.admin, role='admin', status='active')

        self.jefe_proyecto = User.objects.create_user(username='jp@test.com', email='jp@test.com', password='pass')
        UserProfile.objects.create(user=self.jefe_proyecto, role='jefe-proyecto', status='active')
        self.project.lead = self.jefe_proyecto
        self.project.save()

        self.miembro = User.objects.create_user(username='member@test.com', email='member@test.com', password='pass')
        UserProfile.objects.create(user=self.miembro, role='miembro', status='active')
        self.project.members.add(self.miembro)

    def test_create_task_success(self):
        task, error = TaskService.crear_tarea(
            user=self.admin,
            project=self.project,
            title='New Task',
            type='story',
            priority='high',
            points=5,
        )
        self.assertIsNotNone(task)
        self.assertIsNone(error)
        self.assertEqual(task.title, 'New Task')
        self.assertEqual(task.type, 'story')

    def test_create_task_miembro_denied_by_service(self):
        """Members cannot create tasks; they can only edit their assigned ones."""
        task, error = TaskService.crear_tarea(
            user=self.miembro,
            project=self.project,
            title='Member Task',
        )
        self.assertIsNone(task)
        self.assertIsNotNone(error)

    def test_update_task_success(self):
        task = Task.objects.create(project=self.project, title='Old Title')
        updated, error = TaskService.editar_tarea(
            user=self.admin,
            task=task,
            title='New Title',
            priority='high',
        )
        self.assertIsNotNone(updated)
        self.assertIsNone(error)
        self.assertEqual(updated.title, 'New Title')

    def test_update_task_no_permission(self):
        task = Task.objects.create(project=self.project, title='Protected')
        updated, error = TaskService.editar_tarea(
            user=self.miembro,
            task=task,
            title='Hacked',
        )
        self.assertIsNone(updated)
        self.assertIsNotNone(error)

    def test_delete_task_success(self):
        task = Task.objects.create(project=self.project, title='To Delete')
        success, error = TaskService.eliminar_tarea(self.admin, task)
        self.assertTrue(success)
        self.assertIsNone(error)
        self.assertFalse(Task.objects.filter(id=task.id).exists())

    def test_delete_task_no_permission(self):
        task = Task.objects.create(project=self.project, title='Protected')
        success, error = TaskService.eliminar_tarea(self.miembro, task)
        self.assertFalse(success)
        self.assertIsNotNone(error)

    def test_update_status_success(self):
        task = Task.objects.create(project=self.project, title='Status Test')
        success, error = TaskService.actualizar_estado(self.admin, task, 'PROG')
        self.assertTrue(success)
        self.assertIsNone(error)
        task.refresh_from_db()
        self.assertEqual(task.status, 'PROG')

    def test_update_status_invalid(self):
        task = Task.objects.create(project=self.project, title='Status Test')
        success, error = TaskService.actualizar_estado(self.admin, task, 'invalid-status')
        self.assertFalse(success)
        self.assertIsNotNone(error)
