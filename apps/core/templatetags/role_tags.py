from django import template
from apps.core.domain.services.permission_service import get_user_role

register = template.Library()


@register.filter(name='has_role')
def has_role(user, roles_str):
    """
    Check if user has one of the specified roles (considering substitutions).
    Usage: {% if user|has_role:"super-admin,admin" %}
    """
    user_role = get_user_role(user)
    allowed_roles = [r.strip() for r in roles_str.split(',')]
    return user_role in allowed_roles


@register.filter(name='role_is')
def role_is(user, role):
    """
    Check if user has exactly the specified role (considering substitutions).
    Usage: {% if user|role_is:"admin" %}
    """
    user_role = get_user_role(user)
    return user_role == role


@register.filter(name='get_item')
def get_item(dictionary, key):
    """Devuelve el .value booleano de un check (compatibilidad)."""
    if not dictionary:
        return False
    val = dictionary.get(key, False)
    if isinstance(val, dict):
        return val.get('value', False)
    return bool(val)
