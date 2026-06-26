"""Poblar el catalogo de tecnologias que la empresa requiere.

Catalogo simplificado para consultora de desarrollo de software enfocada en MIPEs.

Uso:
    python manage.py seed_technologies --reset
"""
from django.core.management.base import BaseCommand
from apps.core.infrastructure.models.models import Technology


TECHNOLOGIES = [
    ('Django', 'framework', '#092e20'),
    ('React', 'framework', '#61dafb'),
    ('PostgreSQL', 'database', '#336791'),
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
