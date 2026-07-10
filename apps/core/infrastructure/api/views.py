from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.core.infrastructure.models.models import (
    Area, Client, Specialty, Technology, UserProfile,
    Project, Sprint, Tag, Task, Comment,
)
from apps.core.domain.services.permission_service import (
    filter_queryset_by_role,
    get_user_role,
    can_delete_project,
)
from apps.core.domain.services.project_service import ProjectService
from apps.core.domain.services.task_service import TaskService
from apps.core.domain.services.sprint_service import SprintService

from .serializers import (
    AreaSerializer, ClientSerializer, SpecialtySerializer, TechnologySerializer,
    UserProfileSerializer, TagSerializer, SprintSerializer,
    ProjectSerializer, TaskSerializer, CommentSerializer,
)
from .permissions import (
    CanManageArea, CanManageProject, CanDeleteProject, ReadOnlyIfNotManager,
)


class AreaViewSet(viewsets.ModelViewSet):
    queryset = Area.active.all()
    serializer_class = AreaSerializer
    permission_classes = [IsAuthenticated, ReadOnlyIfNotManager]
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'code', 'created_at']


class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.active.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated, ReadOnlyIfNotManager]
    search_fields = ['name', 'contact', 'email', 'industry']
    ordering_fields = ['name', 'created_at']

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=['is_active'])


class SpecialtyViewSet(viewsets.ModelViewSet):
    queryset = Specialty.active.all()
    serializer_class = SpecialtySerializer
    permission_classes = [IsAuthenticated, ReadOnlyIfNotManager]
    search_fields = ['name', 'description']
    ordering_fields = ['category', 'name']
    filterset_fields = ['category', 'parent']

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=['is_active'])


class TechnologyViewSet(viewsets.ModelViewSet):
    queryset = Technology.objects.all()
    serializer_class = TechnologySerializer
    permission_classes = [IsAuthenticated, ReadOnlyIfNotManager]
    search_fields = ['name']
    ordering_fields = ['category', 'name']
    filterset_fields = ['category', 'is_active']


class UserProfileViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UserProfile.objects.select_related('user', 'area', 'specialty', 'client')
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['role', 'status', 'area', 'specialty']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']

    def get_queryset(self):
        qs = super().get_queryset()
        return filter_queryset_by_role(qs, self.request.user, model_type='user')


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, CanManageArea, CanDeleteProject]
    search_fields = ['name', 'description', 'client__name']
    ordering_fields = ['name', 'status', 'created_at', 'start_date', 'end_date']
    filterset_fields = ['status', 'area', 'lead', 'client']

    def get_queryset(self):
        qs = Project.objects.select_related('area', 'lead', 'client').prefetch_related('members').annotate(
            _task_total=Count('tasks', distinct=True),
            _task_done=Count('tasks', filter=Q(tasks__status='DONE'), distinct=True),
        )
        return filter_queryset_by_role(qs, self.request.user, model_type='project')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        members = serializer.validated_data.get('members', [])
        member_ids = [m.id for m in members] if members else None
        project, error = ProjectService.crear_proyecto(
            user=request.user,
            name=serializer.validated_data['name'],
            area_id=serializer.validated_data.get('area').id if serializer.validated_data.get('area') else None,
            description=serializer.validated_data.get('description', ''),
            status=serializer.validated_data.get('status', 'planned'),
            lead_id=serializer.validated_data.get('lead').id if serializer.validated_data.get('lead') else None,
            client_id=serializer.validated_data.get('client').id if serializer.validated_data.get('client') else None,
            budget=float(serializer.validated_data.get('budget', 0) or 0),
            start_date=str(serializer.validated_data.get('start_date')) if serializer.validated_data.get('start_date') else None,
            end_date=str(serializer.validated_data.get('end_date')) if serializer.validated_data.get('end_date') else None,
            color=serializer.validated_data.get('color', '#00bcd4'),
            members=member_ids,
        )
        if error:
            return Response({'detail': error}, status=status.HTTP_403_FORBIDDEN)
        return Response(ProjectSerializer(project, context=self.get_serializer_context()).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data
        members = validated.pop('members', None)
        member_ids = [m.id for m in members] if members is not None else None
        kwargs_data = {}
        for k, v in validated.items():
            if k in ('area', 'lead', 'client'):
                kwargs_data[f'{k}_id'] = v.id if v else None
            else:
                kwargs_data[k] = v
        if member_ids is not None:
            kwargs_data['members'] = member_ids
        project, error = ProjectService.editar_proyecto(
            user=request.user, project=instance, **kwargs_data
        )
        if error:
            return Response({'detail': error}, status=status.HTTP_403_FORBIDDEN)
        return Response(ProjectSerializer(project, context=self.get_serializer_context()).data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not can_delete_project(request.user, instance):
            return Response({'detail': 'Solo el super-admin puede eliminar proyectos'},
                            status=status.HTTP_403_FORBIDDEN)
        instance_name = instance.name
        instance.status = 'cancelled'
        instance.save(update_fields=['status'])
        from apps.core.domain.services.notification_service import create_audit_log
        create_audit_log(request.user, 'PROJECT_CANCEL', 'project', instance.id,
                         f'Proyecto cancelado via API: {instance_name}')
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def tasks(self, request, pk=None):
        project = self.get_object()
        tasks = Task.objects.filter(project=project).select_related('assignee', 'sprint', 'project').prefetch_related('tags')
        tasks = filter_queryset_by_role(tasks, request.user, model_type='task')
        page = self.paginate_queryset(tasks)
        serializer = TaskSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['get'])
    def sprints(self, request, pk=None):
        project = self.get_object()
        sprints = Sprint.objects.filter(project=project)
        serializer = SprintSerializer(sprints, many=True, context={'request': request})
        return Response(serializer.data)


class SprintViewSet(viewsets.ModelViewSet):
    serializer_class = SprintSerializer
    permission_classes = [IsAuthenticated, ReadOnlyIfNotManager]
    filterset_fields = ['project', 'status']
    ordering_fields = ['start_date', 'end_date', 'status']

    def get_queryset(self):
        qs = Sprint.objects.select_related('project')
        return filter_queryset_by_role(qs, self.request.user, model_type='sprint')


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, CanManageProject]
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'priority', 'status', 'points']
    filterset_fields = ['status', 'priority', 'type', 'project', 'sprint', 'assignee']

    def get_queryset(self):
        qs = Task.objects.select_related('assignee', 'project', 'sprint').prefetch_related('tags')
        return filter_queryset_by_role(qs, self.request.user, model_type='task')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        v = serializer.validated_data
        tags_csv = request.data.get('tags_csv') or None
        task, error = TaskService.crear_tarea(
            user=request.user,
            project=v['project'],
            title=v['title'],
            type=v.get('type', 'task'),
            priority=v.get('priority', 'medium'),
            points=v.get('points', 1),
            status=v.get('status', 'backlog'),
            description=v.get('description', ''),
            assignee_id=v.get('assignee').id if v.get('assignee') else None,
            sprint_id=v.get('sprint').id if v.get('sprint') else None,
            required_specialty_id=v.get('required_specialty').id if v.get('required_specialty') else None,
            tags=tags_csv,
        )
        if error:
            return Response({'detail': error}, status=status.HTTP_403_FORBIDDEN)
        return Response(TaskSerializer(task, context=self.get_serializer_context()).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        v = serializer.validated_data
        tags_csv = request.data.get('tags_csv')
        kwargs_data = {}
        for k, val in v.items():
            if k in ('project', 'sprint', 'assignee', 'required_specialty'):
                kwargs_data[f'{k}_id'] = val.id if val else None
            elif k == 'tags':
                continue
            else:
                kwargs_data[k] = val
        if tags_csv is not None:
            kwargs_data['tags'] = tags_csv
        task, error = TaskService.editar_tarea(
            user=request.user, task=instance, **kwargs_data
        )
        if error:
            return Response({'detail': error}, status=status.HTTP_403_FORBIDDEN)
        return Response(TaskSerializer(task, context=self.get_serializer_context()).data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        success, error = TaskService.eliminar_tarea(request.user, instance)
        if error:
            return Response({'detail': error}, status=status.HTTP_403_FORBIDDEN)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def cambiar_estado(self, request, pk=None):
        task = self.get_object()
        new_status = request.data.get('status')
        if not new_status:
            return Response({'detail': 'Falta el campo status'}, status=status.HTTP_400_BAD_REQUEST)
        success, error = TaskService.actualizar_estado(request.user, task, new_status)
        if error:
            return Response({'detail': error}, status=status.HTTP_400_BAD_REQUEST)
        return Response(TaskSerializer(task, context=self.get_serializer_context()).data)


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['name']
    ordering_fields = ['name']


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['task', 'project']
    ordering_fields = ['created_at']

    def get_queryset(self):
        qs = Comment.objects.select_related('author', 'task', 'project')
        return filter_queryset_by_role(qs, self.request.user, model_type='comment')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
