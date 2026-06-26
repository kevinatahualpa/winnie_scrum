from django.test import TestCase
from django.contrib.auth.models import User
from apps.core.infrastructure.models.models import (
    Area, Specialty, UserProfile, Project, Sprint, Task,
    Comment, Document, ServiceRequest, TimeEntry, Notification,
    AuditLog, Client, Substitution
)
from datetime import date, timedelta
from django.utils import timezone


class AreaModelTest(TestCase):
    def setUp(self):
        self.area = Area.objects.create(
            code='IT01',
            name='Tecnologia de Informacion',
            description='Area de TI',
            color='#00bcd4',
        )

    def test_area_creation(self):
        self.assertEqual(self.area.code, 'IT01')
        self.assertEqual(self.area.name, 'Tecnologia de Informacion')
        self.assertEqual(str(self.area), 'IT01 - Tecnologia de Informacion')

    def test_area_default_values(self):
        self.assertEqual(self.area.status, 'active')
        self.assertEqual(self.area.color, '#00bcd4')
        self.assertEqual(self.area.status, 'active')

    def test_area_ordering(self):
        area2 = Area.objects.create(code='AA01', name='Administracion')
        areas = list(Area.objects.all())
        self.assertEqual(areas[0], area2)
        self.assertEqual(areas[1], self.area)


class SpecialtyModelTest(TestCase):
    def setUp(self):
        self.specialty = Specialty.objects.create(
            name='Python Developer',
            category='development',
            description='Desarrollo en Python',
            color='#306998',
        )

    def test_specialty_creation(self):
        self.assertEqual(self.specialty.name, 'Python Developer')
        self.assertEqual(self.specialty.category, 'development')
        self.assertEqual(str(self.specialty), 'Python Developer')

    def test_specialty_categories(self):
        categories = [choice[0] for choice in Specialty._meta.get_field('category').choices]
        self.assertIn('development', categories)
        self.assertIn('design', categories)
        self.assertIn('data', categories)


class UserProfileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='test@test.com',
            email='test@test.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
        )
        self.area = Area.objects.create(code='IT01', name='TI')
        self.specialty = Specialty.objects.create(name='Developer', category='development')
        self.profile = UserProfile.objects.create(
            user=self.user,
            area=self.area,
            specialty=self.specialty,
            role='jefe-proyecto',
            status='active',
        )

    def test_profile_creation(self):
        self.assertEqual(self.profile.role, 'jefe-proyecto')
        self.assertEqual(self.profile.status, 'active')
        self.assertEqual(self.profile.area, self.area)

    def test_profile_initials(self):
        self.assertEqual(self.profile.initials, 'TU')

    def test_profile_default_status(self):
        user2 = User.objects.create_user(username='pending@test.com', email='pending@test.com', password='pass')
        profile2 = UserProfile.objects.create(user=user2)
        self.assertEqual(profile2.status, 'pending')

    def test_profile_str(self):
        expected = f'Test User (Jefe de Proyecto)'
        self.assertEqual(str(self.profile), expected)


class ProjectModelTest(TestCase):
    def setUp(self):
        self.area = Area.objects.create(code='IT01', name='TI')
        self.client = Client.objects.create(name='Test Client')
        self.lead = User.objects.create_user(username='lead@test.com', email='lead@test.com', password='pass')
        self.project = Project.objects.create(
            name='Test Project',
            area=self.area,
            client=self.client,
            lead=self.lead,
            description='A test project',
            status='active',
            budget=10000.00,
        )

    def test_project_creation(self):
        self.assertEqual(self.project.name, 'Test Project')
        self.assertEqual(self.project.status, 'active')
        self.assertEqual(self.project.budget, 10000.00)
        self.assertEqual(str(self.project), 'Test Project')

    def test_project_progress_no_tasks(self):
        self.assertEqual(self.project.progress, 0)

    def test_project_progress_with_tasks(self):
        Task.objects.create(project=self.project, title='Task 1', status='done')
        Task.objects.create(project=self.project, title='Task 2', status='todo')
        Task.objects.create(project=self.project, title='Task 3', status='done')
        self.assertEqual(self.project.progress, 67)

    def test_project_default_status(self):
        project2 = Project.objects.create(name='New Project')
        self.assertEqual(project2.status, 'planned')


class SprintModelTest(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='Test Project')
        self.sprint = Sprint.objects.create(
            project=self.project,
            name='Sprint 1',
            start_date=date(2026, 5, 1),
            end_date=date(2026, 5, 14),
            goal='Complete user stories',
        )

    def test_sprint_creation(self):
        self.assertEqual(self.sprint.name, 'Sprint 1')
        self.assertEqual(self.sprint.status, 'planned')
        self.assertEqual(str(self.sprint), 'Sprint 1 (Test Project)')

    def test_sprint_default_status(self):
        self.assertEqual(self.sprint.status, 'planned')


class TaskModelTest(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='Test Project')
        self.user = User.objects.create_user(username='dev@test.com', email='dev@test.com', password='pass')
        self.task = Task.objects.create(
            project=self.project,
            title='Test Task',
            type='story',
            priority='high',
            points=5,
            status='todo',
            assignee=self.user,
        )

    def test_task_creation(self):
        self.assertEqual(self.task.title, 'Test Task')
        self.assertEqual(self.task.type, 'story')
        self.assertEqual(self.task.priority, 'high')
        self.assertEqual(self.task.points, 5)
        self.assertEqual(str(self.task), 'Test Task')

    def test_task_default_values(self):
        task2 = Task.objects.create(project=self.project, title='Default Task')
        self.assertEqual(task2.type, 'task')
        self.assertEqual(task2.priority, 'medium')
        self.assertEqual(task2.points, 1)
        self.assertEqual(task2.status, 'backlog')

    def test_task_type_choices(self):
        types = [choice[0] for choice in Task.TYPE_CHOICES]
        self.assertIn('story', types)
        self.assertIn('task', types)
        self.assertIn('bug', types)
        self.assertIn('epic', types)

    def test_task_status_choices(self):
        statuses = [choice[0] for choice in Task.STATUS_CHOICES]
        self.assertIn('backlog', statuses)
        self.assertIn('todo', statuses)
        self.assertIn('in-progress', statuses)
        self.assertIn('done', statuses)


class CommentModelTest(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='Test Project')
        self.user = User.objects.create_user(username='commenter@test.com', email='commenter@test.com', password='pass')
        self.task = Task.objects.create(project=self.project, title='Test Task')
        self.comment = Comment.objects.create(
            task=self.task,
            author=self.user,
            text='This is a comment',
        )

    def test_comment_creation(self):
        self.assertEqual(self.comment.text, 'This is a comment')
        self.assertEqual(self.comment.author, self.user)
        self.assertIn('Comment by', str(self.comment))


class NotificationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='notif@test.com', email='notif@test.com', password='pass')
        self.notification = Notification.objects.create(
            user=self.user,
            type='task_assigned',
            title='Tarea asignada',
            message='Se te asigno una tarea',
            icon='fa-tasks',
        )

    def test_notification_creation(self):
        self.assertEqual(self.notification.type, 'task_assigned')
        self.assertFalse(self.notification.read)
        self.assertIn('Tarea asignada', str(self.notification))

    def test_notification_default_read(self):
        self.assertFalse(self.notification.read)


class AuditLogModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='auditor@test.com', email='auditor@test.com', password='pass')
        self.log = AuditLog.objects.create(
            user=self.user,
            action='LOGIN',
            entity='user',
            details='Inicio de sesion',
        )

    def test_audit_log_creation(self):
        self.assertEqual(self.log.action, 'LOGIN')
        self.assertEqual(self.log.entity, 'user')
        self.assertIn('LOGIN', str(self.log))


class SubstitutionModelTest(TestCase):
    def setUp(self):
        self.original = User.objects.create_user(username='original@test.com', email='original@test.com', password='pass')
        self.substitute = User.objects.create_user(username='sub@test.com', email='sub@test.com', password='pass')
        today = timezone.now().date()
        self.substitution = Substitution.objects.create(
            original_user=self.original,
            substitute_user=self.substitute,
            start_date=today - timedelta(days=1),
            end_date=today + timedelta(days=7),
            scope='all',
        )

    def test_substitution_creation(self):
        self.assertEqual(self.substitution.scope, 'all')
        self.assertTrue(self.substitution.active)
        self.assertIn('suple a', str(self.substitution))

    def test_is_current_active(self):
        self.assertTrue(self.substitution.is_current)

    def test_is_current_expired(self):
        past_sub = Substitution.objects.create(
            original_user=self.original,
            substitute_user=self.substitute,
            start_date=timezone.now().date() - timedelta(days=10),
            end_date=timezone.now().date() - timedelta(days=5),
        )
        self.assertFalse(past_sub.is_current)

    def test_is_current_future(self):
        future_sub = Substitution.objects.create(
            original_user=self.original,
            substitute_user=self.substitute,
            start_date=timezone.now().date() + timedelta(days=5),
            end_date=timezone.now().date() + timedelta(days=10),
        )
        self.assertFalse(future_sub.is_current)

    def test_is_current_inactive(self):
        self.substitution.active = False
        self.substitution.save()
        self.assertFalse(self.substitution.is_current)


class TimeEntryModelTest(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='Test Project')
        self.user = User.objects.create_user(username='timer@test.com', email='timer@test.com', password='pass')
        self.task = Task.objects.create(project=self.project, title='Test Task')
        self.entry = TimeEntry.objects.create(
            task=self.task,
            user=self.user,
            date=timezone.now().date(),
            hours=4.5,
            description='Worked on feature',
        )

    def test_time_entry_creation(self):
        self.assertEqual(self.entry.hours, 4.5)
        self.assertEqual(self.entry.description, 'Worked on feature')
        self.assertIn('4.5h', str(self.entry))


class ServiceRequestModelTest(TestCase):
    def setUp(self):
        self.client = Client.objects.create(name='Test Client')
        self.sr = ServiceRequest.objects.create(
            client=self.client,
            service='consultoria',
            description='Need consulting help',
        )

    def test_service_request_creation(self):
        self.assertEqual(self.sr.service, 'consultoria')
        self.assertEqual(self.sr.status, 'new')
        self.assertIn('Consultoria', str(self.sr))

    def test_service_request_default_status(self):
        self.assertEqual(self.sr.status, 'new')
