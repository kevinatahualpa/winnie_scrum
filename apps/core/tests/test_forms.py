from django.test import TestCase
from django.contrib.auth.models import User
from apps.core.infrastructure.models.models import (
    Area, Specialty, Client, Project, Sprint, Task,
    UserProfile, ServiceRequest, Substitution
)
from apps.core.presentation.forms import (
    AreaForm, SpecialtyForm, ClientForm, ProjectForm,
    SprintForm, TaskForm, MemberForm, ServiceRequestForm,
    SubstitutionForm
)
from datetime import date, timedelta
from django.utils import timezone


class AreaFormTest(TestCase):
    def test_area_form_valid(self):
        form = AreaForm(data={
            'code': 'DEV01', 'name': 'Desarrollo', 'description': 'Dev area',
            'color': '#00bcd4', 'icon': 'fa-code', 'status': 'active',
        })
        self.assertTrue(form.is_valid())

    def test_area_form_required_fields(self):
        form = AreaForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('code', form.errors)
        self.assertIn('name', form.errors)

    def test_area_form_code_max_length(self):
        form = AreaForm(data={'code': 'X' * 21, 'name': 'Test'})
        self.assertFalse(form.is_valid())

    def test_area_form_save(self):
        form = AreaForm(data={
            'code': 'QA01', 'name': 'QA', 'description': 'Quality',
            'color': '#ff0000', 'icon': 'fa-bug', 'status': 'active',
        })
        self.assertTrue(form.is_valid())
        area = form.save()
        self.assertEqual(area.code, 'QA01')
        self.assertEqual(area.name, 'QA')


class SpecialtyFormTest(TestCase):
    def test_specialty_form_valid(self):
        form = SpecialtyForm(data={
            'name': 'Python Dev', 'category': 'development',
            'description': 'Python developer', 'color': '#306998',
        })
        self.assertTrue(form.is_valid())

    def test_specialty_form_invalid_category(self):
        form = SpecialtyForm(data={
            'name': 'Bad', 'category': 'invalid', 'color': '#000',
        })
        self.assertFalse(form.is_valid())

    def test_specialty_form_required_fields(self):
        form = SpecialtyForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)


class ClientFormTest(TestCase):
    def test_client_form_valid(self):
        form = ClientForm(data={
            'name': 'Test Client', 'contact': 'John', 'email': 'john@test.com',
            'phone': '123456789', 'industry': 'Tech',
        })
        self.assertTrue(form.is_valid())

    def test_client_form_invalid_email(self):
        form = ClientForm(data={'name': 'Test', 'email': 'not-an-email'})
        self.assertFalse(form.is_valid())

    def test_client_form_minimal(self):
        form = ClientForm(data={'name': 'Minimal Client'})
        self.assertTrue(form.is_valid())


class ProjectFormTest(TestCase):
    def setUp(self):
        self.area = Area.objects.create(code='IT01', name='TI')

    def test_project_form_valid(self):
        form = ProjectForm(data={
            'name': 'Test Project', 'area': self.area.id,
            'status': 'active',
        })
        self.assertTrue(form.is_valid())

    def test_project_form_optional_fields(self):
        form = ProjectForm(data={'name': 'Minimal Project', 'status': 'planned'})
        self.assertTrue(form.is_valid())

    def test_project_form_save(self):
        form = ProjectForm(data={'name': 'Saved Project', 'status': 'planned'})
        self.assertTrue(form.is_valid())
        project = form.save()
        self.assertEqual(project.name, 'Saved Project')

    def test_project_form_color(self):
        form = ProjectForm(data={
            'name': 'Color Test', 'status': 'planned',
            'area': self.area.id, 'color': '#abc123',
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['color'], '#abc123')


class SprintFormTest(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='Test Project')

    def test_sprint_form_valid(self):
        form = SprintForm(data={
            'project': self.project.id, 'name': 'Sprint 1',
            'start_date': date.today(), 'end_date': date.today() + timedelta(days=14),
        })
        self.assertTrue(form.is_valid())

    def test_sprint_form_required_fields(self):
        form = SprintForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_sprint_form_save(self):
        form = SprintForm(data={
            'project': self.project.id, 'name': 'Sprint Saved',
            'start_date': date.today(), 'end_date': date.today() + timedelta(days=14),
        })
        self.assertTrue(form.is_valid())
        sprint = form.save()
        self.assertEqual(sprint.name, 'Sprint Saved')


class TaskFormTest(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='Test Project')
        self.user = User.objects.create_user(username='dev@test.com', email='dev@test.com', password='pass')

    def test_task_form_valid(self):
        form = TaskForm(data={
            'project': self.project.id, 'title': 'Test Task',
            'type': 'task', 'priority': 'medium', 'points': 3,
            'assignee': self.user.id, 'status': 'todo',
        })
        self.assertTrue(form.is_valid())

    def test_task_form_invalid_priority(self):
        form = TaskForm(data={
            'project': self.project.id, 'title': 'Bad Priority',
            'priority': 'urgent',
        })
        self.assertFalse(form.is_valid())

    def test_task_form_save(self):
        form = TaskForm(data={
            'project': self.project.id, 'title': 'Saved Task',
            'type': 'story', 'priority': 'high', 'points': 5,
            'assignee': self.user.id, 'status': 'backlog',
        })
        self.assertTrue(form.is_valid())
        task = form.save()
        self.assertEqual(task.title, 'Saved Task')

    def test_task_form_tags_field(self):
        form = TaskForm(data={
            'project': self.project.id, 'title': 'Task with tags',
            'type': 'task', 'priority': 'low', 'points': 1,
            'assignee': self.user.id, 'status': 'backlog',
        })
        self.assertTrue(form.is_valid())


class MemberFormTest(TestCase):
    def setUp(self):
        self.area = Area.objects.create(code='IT01', name='TI')
        self.specialty = Specialty.objects.create(name='Dev', category='development')

    def test_member_form_valid(self):
        form = MemberForm(data={
            'first_name': 'John', 'last_name': 'Doe',
            'email': 'john@test.com', 'password': 'test12345',
            'password_confirm': 'test12345',
            'role': 'miembro', 'status': 'active', 'color': '#00bcd4',
            'area': self.area.id, 'specialty': self.specialty.id,
        })
        self.assertTrue(form.is_valid())

    def test_member_form_required_names(self):
        form = MemberForm(data={'email': 'test@test.com', 'role': 'miembro', 'color': '#00bcd4'})
        self.assertFalse(form.is_valid())
        self.assertIn('first_name', form.errors)
        self.assertIn('last_name', form.errors)

    def test_member_form_invalid_email(self):
        form = MemberForm(data={
            'first_name': 'John', 'last_name': 'Doe',
            'email': 'not-email', 'role': 'miembro', 'color': '#00bcd4',
        })
        self.assertFalse(form.is_valid())


class ServiceRequestFormTest(TestCase):
    def setUp(self):
        self.client = Client.objects.create(name='Test Client')

    def test_service_form_valid(self):
        form = ServiceRequestForm(data={
            'client': self.client.id, 'service': 'consultoria',
            'description': 'Need help', 'status': 'new',
        })
        self.assertTrue(form.is_valid())

    def test_service_form_save(self):
        form = ServiceRequestForm(data={
            'client': self.client.id, 'service': 'soporte',
            'description': 'Support needed', 'status': 'new',
        })
        self.assertTrue(form.is_valid())
        sr = form.save()
        self.assertEqual(sr.description, 'Support needed')

    def test_service_form_invalid_service_choice(self):
        form = ServiceRequestForm(data={
            'client': self.client.id, 'service': 'invalid_service',
        })
        self.assertFalse(form.is_valid())


class SubstitutionFormTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1@test.com', email='user1@test.com', password='pass')
        self.user2 = User.objects.create_user(username='user2@test.com', email='user2@test.com', password='pass')

    def test_substitution_form_valid(self):
        form = SubstitutionForm(data={
            'original_user': self.user1.id, 'substitute_user': self.user2.id,
            'start_date': timezone.now().date(),
            'end_date': timezone.now().date() + timedelta(days=7),
            'scope': 'all',
        })
        self.assertTrue(form.is_valid())

    def test_substitution_form_save(self):
        form = SubstitutionForm(data={
            'original_user': self.user1.id, 'substitute_user': self.user2.id,
            'start_date': timezone.now().date(),
            'end_date': timezone.now().date() + timedelta(days=7),
            'scope': 'all', 'reason': 'Vacation coverage',
        })
        self.assertTrue(form.is_valid())
        sub = form.save()
        self.assertEqual(sub.scope, 'all')
