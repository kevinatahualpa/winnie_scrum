from rest_framework import permissions
from apps.core.domain.services.permission_service import (
    can_manage_area,
    can_manage_project,
    can_manage_task,
    can_delete_project,
    is_read_only,
)


class IsAuthenticated(permissions.IsAuthenticated):
    pass


class CanManageArea(permissions.BasePermission):
    """Permiso para crear/editar recursos a nivel area (proyectos)."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return can_manage_area(request.user)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return can_manage_project(request.user, obj)


class CanManageProject(permissions.BasePermission):
    """Permiso para gestionar tareas dentro de un proyecto."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return can_manage_task(request.user)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return can_manage_task(request.user, obj)


class CanDeleteProject(permissions.BasePermission):
    """Permiso para eliminar proyectos: solo super-admin."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method not in ('DELETE',):
            return True
        return True

    def has_object_permission(self, request, view, obj):
        if request.method != 'DELETE':
            return True
        return can_delete_project(request.user, obj)


class ReadOnlyIfNotManager(permissions.BasePermission):
    """Lectura para todos los autenticados; escritura solo managers."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return not is_read_only(request.user)
