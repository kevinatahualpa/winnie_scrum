from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from apps.core.infrastructure.models.models import Area, UserProfile


class AuthViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.area = Area.objects.create(code='IT01', name='TI')
        self.user = User.objects.create_user(
            username='test@test.com',
            email='test@test.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            area=self.area,
            role='admin',
            status='active',
        )

    def test_login_page_loads(self):
        response = self.client.get(reverse('iniciar_sesion'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/login.html')

    def test_login_success(self):
        response = self.client.post(reverse('iniciar_sesion'), {
            'email': 'test@test.com',
            'password': 'testpass123',
        })
        self.assertRedirects(response, reverse('ver_dashboard'))

    def test_login_wrong_password(self):
        response = self.client.post(reverse('iniciar_sesion'), {
            'email': 'test@test.com',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Credenciales incorrectas')

    def test_login_pending_user(self):
        pending_user = User.objects.create_user(
            username='pending@test.com',
            email='pending@test.com',
            password='pendingpass',
        )
        UserProfile.objects.create(user=pending_user, role='miembro', status='pending')
        response = self.client.post(reverse('iniciar_sesion'), {
            'email': 'pending@test.com',
            'password': 'pendingpass',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tu solicitud sera revisada')

    def test_login_dismissed_user(self):
        dismissed_user = User.objects.create_user(
            username='dismissed@test.com',
            email='dismissed@test.com',
            password='dismissedpass',
        )
        UserProfile.objects.create(user=dismissed_user, role='miembro', status='dismissed')
        response = self.client.post(reverse('iniciar_sesion'), {
            'email': 'dismissed@test.com',
            'password': 'dismissedpass',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cuenta desactivada')

    def test_login_redirects_if_authenticated(self):
        self.client.login(username='test@test.com', password='testpass123')
        response = self.client.get(reverse('iniciar_sesion'))
        self.assertRedirects(response, reverse('ver_dashboard'))

    def test_logout(self):
        self.client.login(username='test@test.com', password='testpass123')
        response = self.client.get(reverse('cerrar_sesion'))
        self.assertRedirects(response, reverse('iniciar_sesion'))

    def test_solicitar_acceso_redirects_to_wizard(self):
        response = self.client.get(reverse('solicitar_acceso'))
        self.assertRedirects(response, reverse('registro_paso1'))

    def test_registrarse_redirects_to_wizard(self):
        response = self.client.get(reverse('registrarse'))
        self.assertRedirects(response, reverse('registro_paso1'))

    def test_wizard_step1_loads(self):
        response = self.client.get(reverse('registro_paso1'))
        self.assertEqual(response.status_code, 200)
