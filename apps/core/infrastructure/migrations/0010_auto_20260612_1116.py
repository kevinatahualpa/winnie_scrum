"""Limpia UserProfiles existentes para que cumplan las reglas del modelo.

Reglas que se aplican (a partir de esta migracion + clean() del modelo):
  - miembro / jefe-area / jefe-proyecto: area_id obligatorio
  - cliente: client_id obligatorio
  - super-admin / admin / observer: sin area ni client obligatorios
  - cliente: debe tener area_id=NULL (los clientes no pertenecen a un area)

Estrategia:
  1. Para miembros / jefe-area / jefe-proyecto sin area, asignar D3 (default_area_id).
  2. Para clientes sin client, asignar el primer cliente que exista.
  3. Para clientes con area asignada, limpiar a NULL.
"""

from django.db import migrations


DEFAULT_AREA_ID = 3  # D3: Servicios Digitales y Desarrollo


def assign_areas_and_clients(apps, schema_editor):
    UserProfile = apps.get_model('core', 'UserProfile')
    Client = apps.get_model('core', 'Client')

    # Asignar area a miembros, jefe-area y jefe-proyecto que no la tengan
    fixed_members = UserProfile.objects.filter(
        role__in=['miembro', 'jefe-area', 'jefe-proyecto'],
        area__isnull=True,
    ).update(area_id=DEFAULT_AREA_ID)
    if fixed_members:
        print(f"  - {fixed_members} miembros/jefes sin area -> asignados a D3")

    # Asignar el primer client a clientes que no lo tengan
    first_client = Client.objects.order_by('id').first()
    if first_client:
        fixed_clients = UserProfile.objects.filter(
            role='cliente',
            client__isnull=True,
        ).update(client_id=first_client.id)
        if fixed_clients:
            print(f"  - {fixed_clients} clientes sin client -> asignados a {first_client.name}")

    # Limpiar area de clientes (los clientes no pertenecen a un area interna)
    cleared = UserProfile.objects.filter(
        role='cliente',
    ).exclude(area__isnull=True).update(area_id=None)
    if cleared:
        print(f"  - {cleared} clientes tenian area -> limpiadas a NULL")


def reverse_noop(apps, schema_editor):
    # No es trivial hacer reverse porque perderiamos los valores asignados.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_remove_candidateprofile_auto_checklist_and_more'),
    ]

    operations = [
        migrations.RunPython(assign_areas_and_clients, reverse_noop),
    ]
