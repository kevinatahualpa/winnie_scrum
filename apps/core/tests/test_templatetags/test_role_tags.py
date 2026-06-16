from django.test import TestCase
from django.contrib.auth.models import User
from apps.core.infrastructure.models.models import UserProfile
from apps.core.templatetags.role_tags import has_role, role_is


class RoleTagsTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='admin@test.com', email='admin@test.com', password='pass')
        UserProfile.objects.create(user=self.admin, role='admin', status='active')

        self.miembro = User.objects.create_user(username='member@test.com', email='member@test.com', password='pass')
        UserProfile.objects.create(user=self.miembro, role='miembro', status='active')

        self.no_profile = User.objects.create_user(username='noprofile@test.com', email='noprofile@test.com', password='pass')

    def test_has_role_single(self):
        self.assertTrue(has_role(self.admin, 'admin'))
        self.assertFalse(has_role(self.admin, 'super-admin'))

    def test_has_role_multiple(self):
        self.assertTrue(has_role(self.admin, 'super-admin,admin'))
        self.assertTrue(has_role(self.miembro, 'jefe-proyecto,miembro'))
        self.assertFalse(has_role(self.miembro, 'super-admin,admin'))

    def test_has_role_no_profile(self):
        self.assertTrue(has_role(self.no_profile, 'miembro'))
        self.assertFalse(has_role(self.no_profile, 'admin'))

    def test_role_is_correct(self):
        self.assertTrue(role_is(self.admin, 'admin'))
        self.assertFalse(role_is(self.admin, 'miembro'))

    def test_role_is_no_profile(self):
        self.assertTrue(role_is(self.no_profile, 'miembro'))
        self.assertFalse(role_is(self.no_profile, 'admin'))

    def test_has_role_whitespace_handling(self):
        self.assertTrue(has_role(self.admin, ' super-admin , admin '))
