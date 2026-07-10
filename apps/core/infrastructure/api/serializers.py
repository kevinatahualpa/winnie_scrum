from rest_framework import serializers
from apps.core.infrastructure.models.models import (
    Area, Client, Specialty, Technology, UserProfile,
    Project, Sprint, Tag, Task, Comment,
)


class AreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = ['id', 'code', 'name', 'description', 'color', 'status', 'created_at']
        read_only_fields = ['id', 'created_at']


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['id', 'name', 'contact', 'email', 'phone', 'industry', 'created_at']
        read_only_fields = ['id', 'created_at']


class SpecialtySerializer(serializers.ModelSerializer):
    full_path = serializers.CharField(read_only=True)
    is_root = serializers.BooleanField(read_only=True)

    class Meta:
        model = Specialty
        fields = [
            'id', 'name', 'category', 'parent', 'description',
            'color', 'full_path', 'is_root',
        ]
        read_only_fields = ['id', 'full_path', 'is_root']


class TechnologySerializer(serializers.ModelSerializer):
    class Meta:
        model = Technology
        fields = ['id', 'name', 'category', 'color', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserProfileSerializer(serializers.ModelSerializer):
    initials = serializers.CharField(read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_full_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'id', 'user_email', 'user_full_name', 'phone', 'area', 'specialty',
            'client', 'role', 'status', 'color', 'avatar', 'initials', 'created_at',
        ]
        read_only_fields = ['id', 'initials', 'user_email', 'user_full_name', 'created_at']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'color']
        read_only_fields = ['id']


class SprintSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sprint
        fields = ['id', 'project', 'name', 'start_date', 'end_date', 'goal', 'status']
        read_only_fields = ['id']


class ProjectSerializer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField()
    area_name = serializers.CharField(source='area.name', read_only=True)
    lead_name = serializers.CharField(source='lead.get_full_name', read_only=True)
    client_name = serializers.CharField(source='client.name', read_only=True)
    members_names = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'area', 'area_name', 'description', 'status',
            'lead', 'lead_name', 'members', 'members_names',
            'client', 'client_name',
            'budget', 'start_date', 'end_date', 'color', 'progress',
            'created_at',
        ]
        read_only_fields = ['id', 'progress', 'members_names', 'created_at']

    def get_members_names(self, obj):
        return [
            {'id': u.id, 'name': u.get_full_name() or u.email}
            for u in obj.members.all()
        ]

    def get_progress(self, obj):
        total = getattr(obj, '_task_total', None)
        if total is None:
            return obj.progress
        if total == 0:
            return 0
        done = getattr(obj, '_task_done', 0)
        return round((done / total) * 100)


class TaskSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    sprint_name = serializers.CharField(source='sprint.name', read_only=True)
    assignee_name = serializers.CharField(source='assignee.get_full_name', read_only=True)
    tags_list = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id', 'project', 'project_name', 'sprint', 'sprint_name',
            'title', 'type', 'priority', 'points', 'assignee', 'assignee_name',
            'required_specialty', 'status', 'description', 'tags', 'tags_list',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'tags_list', 'created_at', 'updated_at']

    def get_tags_list(self, obj):
        return [{'id': t.id, 'name': t.name, 'color': t.color} for t in obj.tags.all()]


class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'task', 'project', 'author', 'author_name', 'text', 'file', 'created_at']
        read_only_fields = ['id', 'author', 'author_name', 'created_at']
