"""Poblar el catalogo de tecnologias que la empresa requiere.

Idempotente: si la tecnologia ya existe, no la duplica.

Uso:
    python manage.py seed_technologies
"""
from django.core.management.base import BaseCommand
from apps.core.infrastructure.models.models import Technology


TECHNOLOGIES = [
    # Lenguajes
    ('Python', 'language', 'fa-brands fa-python', '#3776ab'),
    ('JavaScript', 'language', 'fa-brands fa-js', '#f7df1e'),
    ('TypeScript', 'language', 'fa-code', '#3178c6'),
    ('PHP', 'language', 'fa-brands fa-php', '#777bb4'),

    # Frameworks
    ('Django', 'framework', 'fa-code', '#092e20'),
    ('Node.js', 'framework', 'fa-brands fa-node-js', '#3c873a'),
    ('Laravel', 'framework', 'fa-code', '#ff2d20'),
    ('React', 'framework', 'fa-brands fa-react', '#61dafb'),

    # Bases de datos
    ('PostgreSQL', 'database', 'fa-database', '#336791'),
    ('MySQL', 'database', 'fa-database', '#00758f'),
    ('MongoDB', 'database', 'fa-database', '#47a248'),

    # Herramientas
    ('Docker', 'tool', 'fa-brands fa-docker', '#2496ed'),
    ('Git', 'tool', 'fa-brands fa-git-alt', '#f05032'),
    ('Jira', 'tool', 'fa-tasks', '#0052cc'),

    # Plataformas
    ('AWS', 'platform', 'fa-brands fa-aws', '#ff9900'),
    ('Google Cloud', 'platform', 'fa-cloud', '#4285f4'),
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
        for name, category, icon, color in TECHNOLOGIES:
            obj, was_created = Technology.objects.get_or_create(
                name=name,
                defaults={'category': category, 'icon': icon, 'color': color},
            )
            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f'  + {name}'))
            else:
                changed = False
                if obj.category != category:
                    obj.category = category; changed = True
                if obj.icon != icon:
                    obj.icon = icon; changed = True
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
