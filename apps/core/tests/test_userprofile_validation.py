"""Tests de las reglas de integridad de UserProfile segun rol.

Las reglas son:
  - miembro / jefe-area / jefe-proyecto: area_id obligatorio
  - cliente: client_id obligatorio, area_id NO debe estar
  - super-admin / admin / observer: area_id y client_id opcionales
"""
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.core.infrastructure.models.models import Area, Client, UserProfile


class UserProfileRoleValidationTest(TestCase):
    def setUp(self):
        self.area_d1 = Area.objects.create(code='D1', name='Consultoria')
        self.area_d3 = Area.objects.create(code='D3', name='Servicios Digitales')
        self.client_acme = Client.objects.create(name='Acme SAC')

    def _make_user(self, email='test@x.com'):
        return User.objects.create_user(
            username=email, email=email, first_name='T', last_name='X',
        )

    # ---- Miembro ----
    def test_miembro_sin_area_falla(self):
        u = self._make_user()
        p = UserProfile(user=u, role='miembro', status='active')
        with self.assertRaises(ValidationError) as cm:
            p.clean()
        self.assertIn('area', cm.exception.message_dict)

    def test_miembro_con_area_pasa(self):
        u = self._make_user()
        p = UserProfile(user=u, role='miembro', status='active', area=self.area_d1)
        p.clean()  # no debe raise

    def test_miembro_con_client_falla(self):
        u = self._make_user()
        p = UserProfile(user=u, role='miembro', status='active',
                       area=self.area_d1, client=self.client_acme)
        with self.assertRaises(ValidationError) as cm:
            p.clean()
        self.assertIn('client', cm.exception.message_dict)

    # ---- Jefe de area ----
    def test_jefe_area_sin_area_falla(self):
        u = self._make_user('ja@x.com')
        p = UserProfile(user=u, role='jefe-area', status='active')
        with self.assertRaises(ValidationError) as cm:
            p.clean()
        self.assertIn('area', cm.exception.message_dict)

    def test_jefe_area_con_area_pasa(self):
        u = self._make_user('ja@x.com')
        p = UserProfile(user=u, role='jefe-area', status='active', area=self.area_d1)
        p.clean()

    def test_jefe_area_con_client_falla(self):
        u = self._make_user('ja@x.com')
        p = UserProfile(user=u, role='jefe-area', status='active',
                       area=self.area_d1, client=self.client_acme)
        with self.assertRaises(ValidationError):
            p.clean()

    # ---- Jefe de proyecto ----
    def test_jefe_proyecto_sin_area_falla(self):
        u = self._make_user('jp@x.com')
        p = UserProfile(user=u, role='jefe-proyecto', status='active')
        with self.assertRaises(ValidationError) as cm:
            p.clean()
        self.assertIn('area', cm.exception.message_dict)

    def test_jefe_proyecto_con_area_pasa(self):
        u = self._make_user('jp@x.com')
        p = UserProfile(user=u, role='jefe-proyecto', status='active', area=self.area_d3)
        p.clean()

    # ---- Cliente ----
    def test_cliente_sin_client_falla(self):
        u = self._make_user('cli@x.com')
        p = UserProfile(user=u, role='cliente', status='active')
        with self.assertRaises(ValidationError) as cm:
            p.clean()
        self.assertIn('client', cm.exception.message_dict)

    def test_cliente_con_client_pasa(self):
        u = self._make_user('cli@x.com')
        p = UserProfile(user=u, role='cliente', status='active', client=self.client_acme)
        p.clean()

    def test_cliente_con_area_falla(self):
        u = self._make_user('cli@x.com')
        p = UserProfile(user=u, role='cliente', status='active',
                       client=self.client_acme, area=self.area_d1)
        with self.assertRaises(ValidationError) as cm:
            p.clean()
        self.assertIn('area', cm.exception.message_dict)

    # ---- Admin / super-admin / observer: sin area ni client esta OK ----
    def test_admin_sin_area_pasa(self):
        u = self._make_user('a@x.com')
        p = UserProfile(user=u, role='admin', status='active')
        p.clean()

    def test_super_admin_sin_area_pasa(self):
        u = self._make_user('sa@x.com')
        p = UserProfile(user=u, role='super-admin', status='active')
        p.clean()

    def test_observer_sin_area_pasa(self):
        u = self._make_user('o@x.com')
        p = UserProfile(user=u, role='observer', status='active')
        p.clean()

    def test_admin_con_client_falla(self):
        u = self._make_user('a@x.com')
        p = UserProfile(user=u, role='admin', status='active', client=self.client_acme)
        with self.assertRaises(ValidationError) as cm:
            p.clean()
        self.assertIn('client', cm.exception.message_dict)
