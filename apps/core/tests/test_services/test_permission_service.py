from django.test import TestCase
from django.contrib.auth.models import User
from apps.core.infrastructure.models.models import Area, Specialty, UserProfile, Project, Client
from apps.core.domain.services.permission_service import (
    get_user_role, can_manage_admin, can_manage_area,
    can_manage_project, can_manage_task, can_assign_to_project,
    can_view_project, can_change_user_role, can_delete_user,
    can_view_audit_log, can_view_all_audit_log, can_view_settings,
    can_delete_project,
    filter_queryset_by_role,
    is_read_only, is_super_admin, is_admin,
    get_client_project_ids, ROLE_HIERARCHY,
)


class PermissionServiceTest(TestCase):
    def setUp(self):
        self.area = Area.objects.create(code='IT01', name='TI')
        self.specialty = Specialty.objects.create(name='Developer', category='development')
        self.client_obj = Client.objects.create(name='Test Client SA')

        self.super_admin = User.objects.create_user(username='super@test.com', email='super@test.com', password='pass')
        UserProfile.objects.create(user=self.super_admin, role='super-admin', status='active')

        self.admin = User.objects.create_user(username='admin@test.com', email='admin@test.com', password='pass')
        UserProfile.objects.create(user=self.admin, role='admin', status='active')

        self.jefe_area = User.objects.create_user(username='ja@test.com', email='ja@test.com', password='pass')
        UserProfile.objects.create(user=self.jefe_area, role='jefe-area', area=self.area, status='active')

        self.jefe_proyecto = User.objects.create_user(username='jp@test.com', email='jp@test.com', password='pass')
        UserProfile.objects.create(user=self.jefe_proyecto, role='jefe-proyecto', status='active')

        self.miembro = User.objects.create_user(username='member@test.com', email='member@test.com', password='pass')
        UserProfile.objects.create(user=self.miembro, role='miembro', status='active')

        self.observer = User.objects.create_user(username='obs@test.com', email='obs@test.com', password='pass')
        UserProfile.objects.create(user=self.observer, role='observer', status='active')

        self.cliente = User.objects.create_user(username='cli@test.com', email='cli@test.com', password='pass')
        UserProfile.objects.create(user=self.cliente, role='cliente', client=self.client_obj, status='active')

        self.project = Project.objects.create(name='Test Project', area=self.area, lead=self.jefe_proyecto)
        self.project.members.add(self.miembro)

    def test_role_hierarchy(self):
        self.assertEqual(ROLE_HIERARCHY['miembro'], 0)
        self.assertEqual(ROLE_HIERARCHY['jefe-proyecto'], 1)
        self.assertEqual(ROLE_HIERARCHY['jefe-area'], 2)
        self.assertEqual(ROLE_HIERARCHY['admin'], 3)
        self.assertEqual(ROLE_HIERARCHY['super-admin'], 4)

    def test_get_user_role(self):
        self.assertEqual(get_user_role(self.super_admin), 'super-admin')
        self.assertEqual(get_user_role(self.admin), 'admin')
        self.assertEqual(get_user_role(self.jefe_area), 'jefe-area')
        self.assertEqual(get_user_role(self.jefe_proyecto), 'jefe-proyecto')
        self.assertEqual(get_user_role(self.miembro), 'miembro')

    def test_get_user_role_no_profile(self):
        user_no_profile = User.objects.create_user(username='noprofile@test.com', email='noprofile@test.com', password='pass')
        self.assertEqual(get_user_role(user_no_profile), 'miembro')

    def test_can_manage_admin(self):
        self.assertTrue(can_manage_admin(self.super_admin))
        self.assertTrue(can_manage_admin(self.admin))
        self.assertFalse(can_manage_admin(self.jefe_area))
        self.assertFalse(can_manage_admin(self.jefe_proyecto))
        self.assertFalse(can_manage_admin(self.miembro))

    def test_can_manage_area(self):
        self.assertTrue(can_manage_area(self.super_admin))
        self.assertTrue(can_manage_area(self.admin))
        self.assertTrue(can_manage_area(self.jefe_area))
        self.assertFalse(can_manage_area(self.jefe_proyecto))
        self.assertFalse(can_manage_area(self.miembro))

    def test_can_manage_project(self):
        self.assertTrue(can_manage_project(self.super_admin))
        self.assertTrue(can_manage_project(self.admin))
        self.assertTrue(can_manage_project(self.jefe_area))
        self.assertTrue(can_manage_project(self.jefe_proyecto))
        self.assertFalse(can_manage_project(self.miembro))

    def test_can_manage_project_specific(self):
        self.assertTrue(can_manage_project(self.super_admin, self.project))
        self.assertTrue(can_manage_project(self.admin, self.project))
        self.assertTrue(can_manage_project(self.jefe_area, self.project))
        self.assertTrue(can_manage_project(self.jefe_proyecto, self.project))
        self.assertFalse(can_manage_project(self.miembro, self.project))

    def test_can_manage_task_no_task(self):
        self.assertTrue(can_manage_task(self.super_admin))
        self.assertTrue(can_manage_task(self.admin))
        self.assertTrue(can_manage_task(self.jefe_area))
        self.assertTrue(can_manage_task(self.jefe_proyecto))
        self.assertFalse(can_manage_task(self.miembro))

    def test_filter_queryset_by_role_project(self):
        project2 = Project.objects.create(name='Other Project')

        all_projects = Project.objects.all()

        super_admin_projects = filter_queryset_by_role(all_projects, self.super_admin, 'super-admin', 'project')
        self.assertEqual(super_admin_projects.count(), 2)

        miembro_projects = filter_queryset_by_role(all_projects, self.miembro, 'miembro', 'project')
        self.assertEqual(miembro_projects.count(), 1)
        self.assertIn(self.project, miembro_projects)

    def test_filter_queryset_by_role_task(self):
        from apps.core.infrastructure.models.models import Task
        project2 = Project.objects.create(name='Other Project')
        task1 = Task.objects.create(project=self.project, title='Task 1', assignee=self.miembro)
        task2 = Task.objects.create(project=project2, title='Task 2')

        all_tasks = Task.objects.all()

        admin_tasks = filter_queryset_by_role(all_tasks, self.admin, 'admin', 'task')
        self.assertEqual(admin_tasks.count(), 2)

        miembro_tasks = filter_queryset_by_role(all_tasks, self.miembro, 'miembro', 'task')
        self.assertEqual(miembro_tasks.count(), 1)
        self.assertEqual(miembro_tasks.first(), task1)


class ReadOnlyRolePermissionTest(TestCase):
    """Verifica que cliente y observer no pueden gestionar recursos."""

    def setUp(self):
        self.area = Area.objects.create(code='IT01', name='TI')
        self.client_obj = Client.objects.create(name='Empresa SA')
        self.client_project = Project.objects.create(name='Proyecto Cliente', client=self.client_obj, area=self.area)
        self.other_project = Project.objects.create(name='Otro Proyecto', area=self.area)

        self.observer = User.objects.create_user(username='obs@test.com', email='obs@test.com', password='pass')
        UserProfile.objects.create(user=self.observer, role='observer', status='active')

        self.cliente = User.objects.create_user(username='cli@test.com', email='cli@test.com', password='pass')
        UserProfile.objects.create(user=self.cliente, role='cliente', client=self.client_obj, status='active')

    def test_observer_cannot_manage_anything(self):
        self.assertFalse(can_manage_admin(self.observer))
        self.assertFalse(can_manage_area(self.observer))
        self.assertFalse(can_manage_project(self.observer))
        self.assertFalse(can_manage_task(self.observer))

    def test_cliente_cannot_manage_anything(self):
        self.assertFalse(can_manage_admin(self.cliente))
        self.assertFalse(can_manage_area(self.cliente))
        self.assertFalse(can_manage_project(self.cliente))
        self.assertFalse(can_manage_task(self.cliente))

    def test_is_read_only_for_observer(self):
        self.assertTrue(is_read_only(self.observer))

    def test_is_read_only_for_cliente(self):
        self.assertTrue(is_read_only(self.cliente))

    def test_is_read_only_false_for_admin(self):
        admin = User.objects.create_user(username='a@t.com', email='a@t.com', password='p')
        UserProfile.objects.create(user=admin, role='admin', status='active')
        self.assertFalse(is_read_only(admin))

    def test_observer_sees_all_projects(self):
        all_projects = Project.objects.all()
        filtered = filter_queryset_by_role(all_projects, self.observer, 'observer', 'project')
        self.assertEqual(filtered.count(), 2)

    def test_cliente_sees_only_their_projects(self):
        all_projects = Project.objects.all()
        filtered = filter_queryset_by_role(all_projects, self.cliente, 'cliente', 'project')
        self.assertEqual(filtered.count(), 1)
        self.assertIn(self.client_project, filtered)
        self.assertNotIn(self.other_project, filtered)

    def test_cliente_sees_only_their_tasks(self):
        from apps.core.infrastructure.models.models import Task
        Task.objects.create(project=self.client_project, title='Cliente task')
        Task.objects.create(project=self.other_project, title='Other task')

        all_tasks = Task.objects.all()
        filtered = filter_queryset_by_role(all_tasks, self.cliente, 'cliente', 'task')
        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first().title, 'Cliente task')

    def test_cliente_user_queryset_is_empty(self):
        from apps.core.infrastructure.models.models import UserProfile
        all_profiles = UserProfile.objects.all()
        filtered = filter_queryset_by_role(all_profiles, self.cliente, 'cliente', 'user')
        self.assertEqual(filtered.count(), 0)

    def test_observer_role_in_hierarchy(self):
        self.assertIn('observer', ROLE_HIERARCHY)
        self.assertIn('cliente', ROLE_HIERARCHY)
        self.assertEqual(ROLE_HIERARCHY['observer'], ROLE_HIERARCHY['cliente'])

    def test_get_client_project_ids_returns_clients_projects(self):
        ids = get_client_project_ids(self.cliente)
        self.assertEqual(ids, [self.client_project.id])

    def test_get_client_project_ids_returns_empty_for_non_client(self):
        self.assertEqual(get_client_project_ids(self.observer), [])

    def test_substitution_does_not_promote_observer_to_admin(self):
        from apps.core.infrastructure.models.models import Substitution
        from datetime import date, timedelta
        from django.utils import timezone

        admin_user = User.objects.create_user(username='a2@t.com', email='a2@t.com', password='p')
        UserProfile.objects.create(user=admin_user, role='admin', status='active')

        today = timezone.now().date()
        Substitution.objects.create(
            original_user=admin_user,
            substitute_user=self.observer,
            start_date=today - timedelta(days=1),
            end_date=today + timedelta(days=1),
        )
        self.assertEqual(get_user_role(self.observer), 'admin')


class CanAssignToProjectTest(TestCase):
    """Tests for can_assign_to_project — who can add/remove project members."""

    def setUp(self):
        self.area1 = Area.objects.create(code='IT', name='TI')
        self.area2 = Area.objects.create(code='MKT', name='Marketing')

        self.project_in_area1 = Project.objects.create(name='P1', area=self.area1)
        self.project_in_area2 = Project.objects.create(name='P2', area=self.area2)

        self.admin = User.objects.create_user(username='admin@t.com', email='admin@t.com', password='p')
        UserProfile.objects.create(user=self.admin, role='admin', status='active')

        self.jefe_area1 = User.objects.create_user(username='ja1@t.com', email='ja1@t.com', password='p')
        UserProfile.objects.create(user=self.jefe_area1, role='jefe-area', area=self.area1, status='active')

        self.jefe_area2 = User.objects.create_user(username='ja2@t.com', email='ja2@t.com', password='p')
        UserProfile.objects.create(user=self.jefe_area2, role='jefe-area', area=self.area2, status='active')

        self.jefe_proyecto = User.objects.create_user(username='jp@t.com', email='jp@t.com', password='p')
        UserProfile.objects.create(user=self.jefe_proyecto, role='jefe-proyecto', status='active')
        self.project_in_area1.lead = self.jefe_proyecto
        self.project_in_area1.save()

        self.miembro = User.objects.create_user(username='m@t.com', email='m@t.com', password='p')
        UserProfile.objects.create(user=self.miembro, role='miembro', status='active')

        self.cliente = User.objects.create_user(username='c@t.com', email='c@t.com', password='p')
        UserProfile.objects.create(user=self.cliente, role='cliente', status='active')

        self.observer = User.objects.create_user(username='o@t.com', email='o@t.com', password='p')
        UserProfile.objects.create(user=self.observer, role='observer', status='active')

    def test_admin_can_assign_to_any_project(self):
        self.assertTrue(can_assign_to_project(self.admin, self.project_in_area1))
        self.assertTrue(can_assign_to_project(self.admin, self.project_in_area2))

    def test_jefe_area_can_assign_to_own_area_project(self):
        self.assertTrue(can_assign_to_project(self.jefe_area1, self.project_in_area1))

    def test_jefe_area_cannot_assign_to_other_area_project(self):
        self.assertFalse(can_assign_to_project(self.jefe_area1, self.project_in_area2))

    def test_jefe_proyecto_can_assign_to_their_project(self):
        self.assertTrue(can_assign_to_project(self.jefe_proyecto, self.project_in_area1))

    def test_jefe_proyecto_cannot_assign_to_other_project(self):
        self.assertFalse(can_assign_to_project(self.jefe_proyecto, self.project_in_area2))

    def test_miembro_cannot_assign_to_any_project(self):
        self.assertFalse(can_assign_to_project(self.miembro, self.project_in_area1))
        self.assertFalse(can_assign_to_project(self.miembro, self.project_in_area2))

    def test_cliente_cannot_assign_to_any_project(self):
        self.assertFalse(can_assign_to_project(self.cliente, self.project_in_area1))

    def test_observer_cannot_assign_to_any_project(self):
        self.assertFalse(can_assign_to_project(self.observer, self.project_in_area1))

    def test_none_project_returns_false(self):
        self.assertFalse(can_assign_to_project(self.admin, None))


class RoleHierarchyTest(TestCase):
    """Tests for the difference between super-admin and admin, and the
    hierarchy of permissions."""

    def setUp(self):
        self.super_admin = User.objects.create_user(username='super@t.com', email='super@t.com', password='p')
        UserProfile.objects.create(user=self.super_admin, role='super-admin', status='active')

        self.admin = User.objects.create_user(username='admin@t.com', email='admin@t.com', password='p')
        UserProfile.objects.create(user=self.admin, role='admin', status='active')

        self.other_super_admin = User.objects.create_user(username='super2@t.com', email='super2@t.com', password='p')
        UserProfile.objects.create(user=self.other_super_admin, role='super-admin', status='active')

        self.member_user = User.objects.create_user(username='m@t.com', email='m@t.com', password='p')
        UserProfile.objects.create(user=self.member_user, role='miembro', status='active')

    def test_is_super_admin_only_for_super_admin(self):
        self.assertTrue(is_super_admin(self.super_admin))
        self.assertFalse(is_super_admin(self.admin))
        self.assertFalse(is_super_admin(self.member_user))

    def test_is_admin_for_both_admin_and_super_admin(self):
        self.assertTrue(is_admin(self.super_admin))
        self.assertTrue(is_admin(self.admin))
        self.assertFalse(is_admin(self.member_user))

    def test_can_change_user_role_only_super_admin(self):
        self.assertTrue(can_change_user_role(self.super_admin, self.member_user))
        self.assertFalse(can_change_user_role(self.admin, self.member_user))
        self.assertFalse(can_change_user_role(self.super_admin, self.super_admin))
        self.assertFalse(can_change_user_role(self.super_admin, self.other_super_admin))

    def test_can_delete_user_only_super_admin(self):
        self.assertTrue(can_delete_user(self.super_admin, self.member_user))
        self.assertTrue(can_delete_user(self.super_admin, self.admin))
        self.assertFalse(can_delete_user(self.admin, self.member_user))
        self.assertFalse(can_delete_user(self.super_admin, self.super_admin))
        self.assertFalse(can_delete_user(self.super_admin, self.other_super_admin))

    def test_can_view_audit_log_for_both_admins(self):
        self.assertTrue(can_view_audit_log(self.super_admin))
        self.assertTrue(can_view_audit_log(self.admin))
        self.assertFalse(can_view_audit_log(self.member_user))

    def test_can_view_all_audit_log_only_super_admin(self):
        self.assertTrue(can_view_all_audit_log(self.super_admin))
        self.assertFalse(can_view_all_audit_log(self.admin))

    def test_can_view_settings_only_super_admin(self):
        self.assertTrue(can_view_settings(self.super_admin))
        self.assertFalse(can_view_settings(self.admin))
        self.assertFalse(can_view_settings(self.member_user))

    def test_can_delete_project_only_super_admin(self):
        area = Area.objects.create(code='IT', name='TI')
        project = Project.objects.create(name='P1', area=area)
        self.assertTrue(can_delete_project(self.super_admin, project))
        self.assertFalse(can_delete_project(self.admin, project))
        self.assertFalse(can_delete_project(self.member_user, project))

    def test_miembro_cannot_create_task(self):
        """Members can only edit their assigned tasks, never create new ones."""
        self.assertFalse(can_manage_task(self.member_user))


class CanViewProjectTest(TestCase):
    """Visibility of projects — broader than management."""

    def setUp(self):
        self.area = Area.objects.create(code='IT', name='TI')
        self.project = Project.objects.create(name='P1', area=self.area)
        self.other_area = Area.objects.create(code='MKT', name='MKT')
        self.other_project = Project.objects.create(name='P2', area=self.other_area)

        self.admin = User.objects.create_user(username='a@t.com', email='a@t.com', password='p')
        UserProfile.objects.create(user=self.admin, role='admin', status='active')

        self.observer = User.objects.create_user(username='o@t.com', email='o@t.com', password='p')
        UserProfile.objects.create(user=self.observer, role='observer', status='active')

        self.jefe_area = User.objects.create_user(username='ja@t.com', email='ja@t.com', password='p')
        UserProfile.objects.create(user=self.jefe_area, role='jefe-area', area=self.area, status='active')

        self.jefe_other = User.objects.create_user(username='jo@t.com', email='jo@t.com', password='p')
        UserProfile.objects.create(user=self.jefe_other, role='jefe-area', area=self.other_area, status='active')

        self.lead = User.objects.create_user(username='lead@t.com', email='lead@t.com', password='p')
        UserProfile.objects.create(user=self.lead, role='jefe-proyecto', status='active')
        self.project.lead = self.lead
        self.project.save()
        self.project.members.add(self.lead)

        self.member = User.objects.create_user(username='m@t.com', email='m@t.com', password='p')
        UserProfile.objects.create(user=self.member, role='miembro', status='active')

    def test_admin_sees_all_projects(self):
        self.assertTrue(can_view_project(self.admin, self.project))
        self.assertTrue(can_view_project(self.admin, self.other_project))

    def test_observer_sees_all_projects(self):
        self.assertTrue(can_view_project(self.observer, self.project))
        self.assertTrue(can_view_project(self.observer, self.other_project))

    def test_jefe_area_sees_own_area(self):
        self.assertTrue(can_view_project(self.jefe_area, self.project))
        self.assertFalse(can_view_project(self.jefe_area, self.other_project))

    def test_jefe_proyecto_sees_own_project(self):
        self.assertTrue(can_view_project(self.lead, self.project))
        self.assertFalse(can_view_project(self.lead, self.other_project))

    def test_member_sees_only_member_projects(self):
        self.assertFalse(can_view_project(self.member, self.project))
        self.project.members.add(self.member)
        self.assertTrue(can_view_project(self.member, self.project))
