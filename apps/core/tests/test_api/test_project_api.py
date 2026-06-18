from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.infrastructure.models.models import Area, Client, Project, UserProfile


def _token_for(user):
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)


class _BaseApiTest(TestCase):
    def setUp(self):
        self.area = Area.objects.create(code='IT01', name='TI')
        self.client_model = Client.objects.create(name='Acme')

        self.admin = User.objects.create_user(
            username='admin@test.com', email='admin@test.com', password='pass123'
        )
        UserProfile.objects.create(user=self.admin, role='admin', status='active', area=self.area)

        self.miembro = User.objects.create_user(
            username='member@test.com', email='member@test.com', password='pass123'
        )
        UserProfile.objects.create(user=self.miembro, role='miembro', status='active', area=self.area)

        self.client_admin = APIClient()
        self.client_admin.credentials(HTTP_AUTHORIZATION=f'Bearer {_token_for(self.admin)}')

        self.client_member = APIClient()
        self.client_member.credentials(HTTP_AUTHORIZATION=f'Bearer {_token_for(self.miembro)}')

        self.client_anon = APIClient()


class ProjectListCreateApiTest(_BaseApiTest):
    URL = '/api/v1/projects/'

    def test_anon_cannot_list(self):
        r = self.client_anon.get(self.URL)
        self.assertIn(r.status_code, (401, 403))

    def test_admin_can_list_empty(self):
        r = self.client_admin.get(self.URL)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['results'], [])

    def test_admin_can_create_project(self):
        r = self.client_admin.post(self.URL, {
            'name': 'Proyecto API',
            'area': self.area.id,
            'description': 'Creado via API',
            'status': 'planned',
            'budget': '1500.00',
            'color': '#ff0000',
        }, format='json')
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data['name'], 'Proyecto API')
        self.assertEqual(r.data['area'], self.area.id)
        self.assertTrue(Project.objects.filter(name='Proyecto API').exists())

    def test_member_cannot_create_project(self):
        r = self.client_member.post(self.URL, {
            'name': 'Proyecto no permitido',
            'area': self.area.id,
        }, format='json')
        self.assertEqual(r.status_code, 403)
        self.assertIn('detail', r.data)


class ProjectRetrieveUpdateDestroyApiTest(_BaseApiTest):
    def setUp(self):
        super().setUp()
        self.project = Project.objects.create(
            name='Original', area=self.area, status='planned', lead=self.admin,
        )

    def test_admin_can_retrieve(self):
        r = self.client_admin.get(f'/api/v1/projects/{self.project.id}/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['name'], 'Original')
        self.assertIn('progress', r.data)

    def test_admin_can_update(self):
        r = self.client_admin.patch(f'/api/v1/projects/{self.project.id}/', {
            'name': 'Renombrado',
            'status': 'active',
        }, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, 'Renombrado')
        self.assertEqual(self.project.status, 'active')

    def test_member_cannot_update_other_project(self):
        r = self.client_member.patch(f'/api/v1/projects/{self.project.id}/', {
            'name': 'Hackeado',
        }, format='json')
        self.assertEqual(r.status_code, 403)

    def test_admin_cannot_delete_only_super_admin(self):
        r = self.client_admin.delete(f'/api/v1/projects/{self.project.id}/')
        self.assertEqual(r.status_code, 403)
        self.assertTrue(Project.objects.filter(id=self.project.id).exists())


class ProjectNestedTasksApiTest(_BaseApiTest):
    def setUp(self):
        super().setUp()
        self.project = Project.objects.create(name='Con tareas', area=self.area, lead=self.admin)
        self.project.members.add(self.miembro)

    def test_admin_sees_nested_tasks_empty(self):
        r = self.client_admin.get(f'/api/v1/projects/{self.project.id}/tasks/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['results'], [])


class AuthTokenApiTest(_BaseApiTest):
    def test_obtain_token_with_valid_credentials(self):
        r = self.client_anon.post('/api/v1/auth/token/', {
            'username': 'admin@test.com',
            'password': 'pass123',
        }, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertIn('access', r.data)
        self.assertIn('refresh', r.data)

    def test_obtain_token_with_invalid_credentials(self):
        r = self.client_anon.post('/api/v1/auth/token/', {
            'username': 'admin@test.com',
            'password': 'wrong',
        }, format='json')
        self.assertEqual(r.status_code, 401)
