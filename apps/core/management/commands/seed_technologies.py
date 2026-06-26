"""Poblar el catalogo de tecnologias que la empresa requiere.

Idempotente: si la tecnologia ya existe, no la duplica.

Uso:
    python manage.py seed_technologies
"""
from django.core.management.base import BaseCommand
from apps.core.infrastructure.models.models import Technology


TECHNOLOGIES = [
    # Lenguajes
    ('Python', 'language', '#3776ab'),
    ('JavaScript', 'language', '#f7df1e'),
    ('TypeScript', 'language', '#3178c6'),
    ('PHP', 'language', '#777bb4'),

    # Frameworks
    ('Django', 'framework', '#092e20'),
    ('Node.js', 'framework', '#3c873a'),
    ('Laravel', 'framework', '#ff2d20'),
    ('React', 'framework', '#61dafb'),

    # Bases de datos
    ('PostgreSQL', 'database', '#336791'),
    ('MySQL', 'database', '#00758f'),
    ('MongoDB', 'database', '#47a248'),

    # Herramientas
    ('Docker', 'tool', '#2496ed'),
    ('Git', 'tool', '#f05032'),
    ('Jira', 'tool', '#0052cc'),

    # Plataformas
    ('AWS', 'platform', '#ff9900'),
    ('Google Cloud', 'platform', '#4285f4'),
]


class Command(BaseCommand):
    help = 'Poblar el catalogo de tecnologias requeridas por la empresa'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset', action='store_true',
            help='Desactivar tecnologias que no estan en el catalogo por defecto',
        )

    def handle(self, *args, **options):
        created = 0
        updated = 0
        for name, category, color in TECHNOLOGIES:
            obj, was_created = Technology.objects.get_or_create(
                name=name,
                defaults={'category': category, 'color': color},
            )
            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f'  + {name}'))
            else:
                changed = False
                if obj.category != category:
                    obj.category = category; changed = True
                if obj.color != color:
                    obj.color = color; changed = True
                if not obj.is_active:
                    obj.is_active = True; changed = True
                if changed:
                    obj.save()
                    updated += 1
                    self.stdout.write(f'  ~ {name} (actualizado)')

        if options['reset']:
            keep = {n for n, *_ in TECHNOLOGIES}
            off = Technology.objects.exclude(name__in=keep)
            count = off.count()
            off.update(is_active=False)
            self.stdout.write(self.style.WARNING(f'  - {count} tecnologia(s) desactivadas'))

        self.stdout.write(self.style.SUCCESS(
            f'\nListo: {created} creadas, {updated} actualizadas. '
            f'Total activas: {Technology.objects.filter(is_active=True).count()}'
        ))
