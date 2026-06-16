from apps.core.domain.repositories import DjangoRepository
from apps.core.infrastructure.models.models import (
    Area, Specialty, Technology, CandidateProfile, CandidateTechnology,
    UserProfile, Substitution,
    Client, Project, Sprint, Task, Tag, Comment,
    Document, ServiceRequest, TimeEntry, Notification, AuditLog
)


class AreaRepository(DjangoRepository):
    model = Area


class SpecialtyRepository(DjangoRepository):
    model = Specialty


class TechnologyRepository(DjangoRepository):
    model = Technology

    def get_active(self):
        return self.model.objects.filter(is_active=True)


class CandidateRepository(DjangoRepository):
    model = CandidateProfile

    def get_pending(self):
        return self.model.objects.filter(user__profile__status='pending')


class UserRepository(DjangoRepository):
    model = UserProfile


class SubstitutionRepository(DjangoRepository):
    model = Substitution


class ClientRepository(DjangoRepository):
    model = Client


class ProjectRepository(DjangoRepository):
    model = Project

    def get_with_details(self):
        return self.model.objects.select_related('area', 'lead', 'client').prefetch_related('members')

    def get_by_area(self, area_id):
        return self.model.objects.filter(area_id=area_id)

    def get_by_user(self, user):
        from django.db.models import Q
        return self.model.objects.filter(
            Q(lead=user) | Q(members=user)
        ).distinct()


class SprintRepository(DjangoRepository):
    model = Sprint

    def get_by_project(self, project_id):
        return self.model.objects.filter(project_id=project_id)

    def get_active(self):
        return self.model.objects.filter(status='active')

    def get_by_project_ordered(self, project_id):
        return self.model.objects.filter(project_id=project_id).order_by('-start_date')


class TaskRepository(DjangoRepository):
    model = Task

    def get_by_project(self, project_id):
        return self.model.objects.filter(project_id=project_id)

    def get_by_assignee(self, user_id):
        return self.model.objects.filter(assignee_id=user_id)

    def get_by_status(self, status):
        return self.model.objects.filter(status=status)

    def get_with_relations(self):
        return self.model.objects.select_related('assignee', 'project', 'sprint').prefetch_related('tags')

    def get_by_project_ids(self, project_ids):
        return self.model.objects.filter(project_id__in=project_ids)


class TagRepository(DjangoRepository):
    model = Tag


class CommentRepository(DjangoRepository):
    model = Comment

    def get_by_task(self, task_id):
        return self.model.objects.filter(task_id=task_id).order_by('created_at')

    def get_by_project(self, project_id):
        return self.model.objects.filter(project_id=project_id).order_by('created_at')


class DocumentRepository(DjangoRepository):
    model = Document

    def get_by_project(self, project_id):
        return self.model.objects.filter(project_id=project_id)


class ServiceRequestRepository(DjangoRepository):
    model = ServiceRequest

    def get_by_assigned_to(self, user_id):
        return self.model.objects.filter(assigned_to_id=user_id)


class TimeEntryRepository(DjangoRepository):
    model = TimeEntry

    def get_by_user(self, user_id):
        return self.model.objects.filter(user_id=user_id)

    def get_by_user_and_date(self, user_id, date):
        return self.model.objects.filter(user_id=user_id, date=date)

    def get_by_user_and_date_range(self, user_id, start_date, end_date):
        return self.model.objects.filter(user_id=user_id, date__gte=start_date, date__lte=end_date)


class NotificationRepository(DjangoRepository):
    model = Notification

    def get_by_user(self, user_id):
        return self.model.objects.filter(user_id=user_id)

    def get_unread_by_user(self, user_id):
        return self.model.objects.filter(user_id=user_id, read=False)

    def mark_all_read(self, user_id):
        return self.model.objects.filter(user_id=user_id, read=False).update(read=True)


class AuditLogRepository(DjangoRepository):
    model = AuditLog

    def get_latest(self, limit=100):
        return self.model.objects.select_related('user').order_by('-created_at')[:limit]
