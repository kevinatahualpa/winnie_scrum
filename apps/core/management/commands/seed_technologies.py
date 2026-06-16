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
    ('Java', 'language', 'fa-brands fa-java', '#ed8b00'),
    ('C#', 'language', 'fa-code', '#68217a'),
    ('Go', 'language', 'fa-code', '#00add8'),
    ('PHP', 'language', 'fa-brands fa-php', '#777bb4'),
    ('Ruby', 'language', 'fa-gem', '#cc342d'),

    # Frameworks backend
    ('Django', 'framework', 'fa-code', '#092e20'),
    ('Django REST Framework', 'framework', 'fa-code', '#ff1709'),
    ('FastAPI', 'framework', 'fa-bolt', '#009688'),
    ('Flask', 'framework', 'fa-flask', '#000000'),
    ('Spring Boot', 'framework', 'fa-leaf', '#6db33f'),
    ('Laravel', 'framework', 'fa-code', '#ff2d20'),
    ('Node.js', 'framework', 'fa-brands fa-node-js', '#3c873a'),
    ('Express.js', 'framework', 'fa-code', '#000000'),
    ('.NET', 'framework', 'fa-code', '#512bd4'),

    # Frameworks frontend
    ('React', 'framework', 'fa-brands fa-react', '#61dafb'),
    ('Vue.js', 'framework', 'fa-brands fa-vuejs', '#42b883'),
    ('Angular', 'framework', 'fa-brands fa-angular', '#dd0031'),
    ('Next.js', 'framework', 'fa-code', '#000000'),
    ('Svelte', 'framework', 'fa-code', '#ff3e00'),
    ('Bootstrap', 'framework', 'fa-brands fa-bootstrap', '#7952b3'),
    ('Tailwind CSS', 'framework', 'fa-wind', '#06b6d4'),

    # Bases de datos
    ('PostgreSQL', 'database', 'fa-database', '#336791'),
    ('MySQL', 'database', 'fa-database', '#00758f'),
    ('MongoDB', 'database', 'fa-database', '#47a248'),
    ('Redis', 'database', 'fa-database', '#dc382d'),
    ('SQLite', 'database', 'fa-database', '#003b57'),
    ('Oracle', 'database', 'fa-database', '#f80000'),
    ('SQL Server', 'database', 'fa-database', '#cc2927'),

    # DevOps / Cloud
    ('Docker', 'tool', 'fa-brands fa-docker', '#2496ed'),
    ('Kubernetes', 'tool', 'fa-dharmachakra', '#326ce5'),
    ('AWS', 'platform', 'fa-brands fa-aws', '#ff9900'),
    ('Azure', 'platform', 'fa-brands fa-microsoft', '#0078d4'),
    ('Google Cloud', 'platform', 'fa-cloud', '#4285f4'),
    ('Git', 'tool', 'fa-brands fa-git-alt', '#f05032'),
    ('GitHub Actions', 'tool', 'fa-brands fa-github', '#2088ff'),
    ('GitLab CI', 'tool', 'fa-brands fa-gitlab', '#fc6d26'),
    ('Terraform', 'tool', 'fa-code', '#7b42bc'),
    ('Jenkins', 'tool', 'fa-code', '#d24939'),

    # Mobile
    ('React Native', 'framework', 'fa-mobile-alt', '#61dafb'),
    ('Flutter', 'framework', 'fa-mobile-alt', '#02569b'),
    ('Swift', 'language', 'fa-apple', '#fa7343'),
    ('Kotlin', 'language', 'fa-code', '#7f52ff'),

    # QA / Testing
    ('Selenium', 'tool', 'fa-vial', '#43b02a'),
    ('Cypress', 'tool', 'fa-vial', '#17202c'),
    ('Jest', 'tool', 'fa-vial', '#99425b'),
    ('Pytest', 'tool', 'fa-vial', '#0a9edc'),

    # Otros
    ('Figma', 'tool', 'fa-brands fa-figma', '#f24e1e'),
    ('Adobe XD', 'tool', 'fa-pen-nib', '#ff26be'),
    ('Jira', 'tool', 'fa-tasks', '#0052cc'),
    ('Confluence', 'tool', 'fa-file-alt', '#172b4d'),
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
