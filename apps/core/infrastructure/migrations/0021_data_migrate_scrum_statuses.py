# Generated migration — data-only: converts old status codes to new Scrum codes.

from django.db import migrations


SPRINT_STATUS_MAP = {
    'planned': 'PLAN',
    'active': 'ACT',
    'completed': 'CMP',
}

TASK_STATUS_MAP = {
    'backlog': 'TODO',
    'todo': 'TODO',
    'in-progress': 'PROG',
    'done': 'DONE',
}


def convert_sprint_statuses(apps, schema_editor):
    Sprint = apps.get_model('core', 'Sprint')
    for old, new in SPRINT_STATUS_MAP.items():
        Sprint.objects.filter(status=old).update(status=new)


def reverse_sprint_statuses(apps, schema_editor):
    Sprint = apps.get_model('core', 'Sprint')
    reverse_map = {v: k for k, v in SPRINT_STATUS_MAP.items()}
    for new, old in reverse_map.items():
        Sprint.objects.filter(status=new).update(status=old)


def convert_task_statuses(apps, schema_editor):
    Task = apps.get_model('core', 'Task')
    for old, new in TASK_STATUS_MAP.items():
        Task.objects.filter(status=old).update(status=new)


def reverse_task_statuses(apps, schema_editor):
    Task = apps.get_model('core', 'Task')
    reverse_map = {v: k for k, v in TASK_STATUS_MAP.items()}
    for new, old in reverse_map.items():
        Task.objects.filter(status=new).update(status=old)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_scrum_refactor_status_position'),
    ]

    operations = [
        migrations.RunPython(convert_sprint_statuses, reverse_sprint_statuses),
        migrations.RunPython(convert_task_statuses, reverse_task_statuses),
    ]
