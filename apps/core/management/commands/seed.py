"""Seed de base de datos con datos demo realistas para Winnie.

Estructura:
    - 2 areas
    - 8 usuarios (super-admin, admin, jefe-area, 2 jefes-proyecto, 3 miembros, 1 cliente)
    - 4 clientes
    - 4 proyectos con sprints, tareas y miembros asignados
    - Comentarios de proyecto
    - El cliente solo ve su proyecto asignado

Uso:
    python manage.py flush
    python manage.py seed_technologies --reset
    python manage.py seed
"""

import datetime

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from apps.core.infrastructure.models.models import (
    Area, Specialty, UserProfile, Client, Project,
    Sprint, Task, Tag, Comment,
)


class Command(BaseCommand):
    help = 'Seed database with demo data'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database...')
        today = datetime.date.today()

        # ═══════════════════════════════════════════
        # 1. AREAS (2)
        # ═══════════════════════════════════════════
        areas_data = [
            {'code': 'DEV', 'name': 'Desarrollo y Consultoria', 'description': 'Proyectos de desarrollo de software, consultoria TI y soporte tecnico.', 'color': '#2e7d32'},
            {'code': 'INN', 'name': 'Innovacion y Producto', 'description': 'Desarrollo de nuevos productos digitales, apps moviles y transformacion digital.', 'color': '#0277bd'},
        ]

        areas = {}
        for data in areas_data:
            area, _ = Area.objects.get_or_create(code=data['code'], defaults=data)
            areas[data['code']] = area
            self.stdout.write(f'  Area: {area.code} - {area.name}')

        # ═══════════════════════════════════════════
        # 2. ESPECIALIDADES (solo las usadas)
        # ═══════════════════════════════════════════
        specialties_data = [
            {'name': 'Backend Developer', 'category': 'development', 'description': 'APIs, bases de datos, logica de servidor', 'color': '#2e7d32'},
            {'name': 'Frontend Developer', 'category': 'development', 'description': 'Interfaces web, React, UX/UI', 'color': '#0277bd'},
            {'name': 'FullStack Developer', 'category': 'development', 'description': 'Frontend y backend', 'color': '#6554c0'},
            {'name': 'QA Engineer', 'category': 'qa', 'description': 'Testing manual y automatizado', 'color': '#c62828'},
            {'name': 'Scrum Master', 'category': 'management', 'description': 'Facilitacion agil', 'color': '#f57f17'},
            {'name': 'Product Owner', 'category': 'management', 'description': 'Gestion de producto y backlog', 'color': '#039be5'},
        ]

        specialties = {}
        for data in specialties_data:
            spec, _ = Specialty.objects.get_or_create(name=data['name'], defaults=data)
            if not spec.is_active:
                spec.is_active = True; spec.save()
            specialties[data['name']] = spec
            self.stdout.write(f'  Specialty: {spec.name}')

        # Desactivar especialidades que ya no usamos
        Specialty.objects.exclude(name__in=[d['name'] for d in specialties_data]).update(is_active=False)

        # ═══════════════════════════════════════════
        # 3. CLIENTES (4)
        # ═══════════════════════════════════════════
        clients_data = [
            {'name': 'Corporacion Minera SAC', 'contact': 'Carlos Mendoza', 'email': 'cmendoza@corpminera.com', 'phone': '+51 987 654 321', 'industry': 'Mineria'},
            {'name': 'FashionPeru S.R.L.', 'contact': 'Maria Lopez', 'email': 'mlopez@fashionperu.com', 'phone': '+51 965 432 109', 'industry': 'Moda'},
            {'name': 'MediSalud SAC', 'contact': 'Dra. Gabriela Ponce', 'email': 'gponce@medisalud.pe', 'phone': '+51 943 210 987', 'industry': 'Salud'},
            {'name': 'Municipalidad Metropolitana de Lima', 'contact': 'Ing. Jorge Huaman', 'email': 'jhuaman@munlima.gob.pe', 'phone': '+51 932 109 876', 'industry': 'Gobierno'},
        ]

        clients = {}
        for data in clients_data:
            client, _ = Client.objects.get_or_create(name=data['name'], defaults=data)
            clients[data['name']] = client
            self.stdout.write(f'  Client: {client.name}')

        # ═══════════════════════════════════════════
        # 4. USUARIOS (8)
        # ═══════════════════════════════════════════
        users_data = [
            {'username': 'super@gmail.com', 'email': 'super@gmail.com', 'first_name': 'Carlos', 'last_name': 'SuperAdmin', 'password': '123456', 'role': 'super-admin', 'color': '#c62828', 'area': None, 'specialty': None, 'phone': '+51 994 520 017', 'client': None},
            {'username': 'admin@gmail.com', 'email': 'admin@gmail.com', 'first_name': 'Ana', 'last_name': 'Administradora', 'password': '123456', 'role': 'admin', 'color': '#f57f17', 'area': None, 'specialty': None, 'phone': '+51 994 520 018', 'client': None},
            {'username': 'jefe.areas@hackthony.com', 'email': 'jefe.areas@hackthony.com', 'first_name': 'Roberto', 'last_name': 'Jefe Area', 'password': 'area123', 'role': 'jefe-area', 'color': '#6554c0', 'area': 'DEV', 'specialty': 'Scrum Master', 'phone': '+51 994 520 019', 'client': None},
            {'username': 'jp.miguel@hackthony.com', 'email': 'jp.miguel@hackthony.com', 'first_name': 'Miguel', 'last_name': 'Torres', 'password': 'jp123', 'role': 'jefe-proyecto', 'color': '#00bcd4', 'area': 'DEV', 'specialty': 'FullStack Developer', 'phone': '+51 994 520 020', 'client': None},
            {'username': 'jp.laura@hackthony.com', 'email': 'jp.laura@hackthony.com', 'first_name': 'Laura', 'last_name': 'Quispe', 'password': 'jp123', 'role': 'jefe-proyecto', 'color': '#e91e63', 'area': 'INN', 'specialty': 'Product Owner', 'phone': '+51 994 520 021', 'client': None},
            {'username': 'pedro@hackthony.com', 'email': 'pedro@hackthony.com', 'first_name': 'Pedro', 'last_name': 'Backend', 'password': 'member123', 'role': 'miembro', 'color': '#2e7d32', 'area': 'DEV', 'specialty': 'Backend Developer', 'phone': '+51 994 520 022', 'client': None},
            {'username': 'sofia@hackthony.com', 'email': 'sofia@hackthony.com', 'first_name': 'Sofia', 'last_name': 'Frontend', 'password': 'member123', 'role': 'miembro', 'color': '#4caf50', 'area': 'INN', 'specialty': 'Frontend Developer', 'phone': '+51 994 520 023', 'client': None},
            {'username': 'valeria@hackthony.com', 'email': 'valeria@hackthony.com', 'first_name': 'Valeria', 'last_name': 'QA', 'password': 'member123', 'role': 'miembro', 'color': '#9c27b0', 'area': 'DEV', 'specialty': 'QA Engineer', 'phone': '+51 994 520 024', 'client': None},
            {'username': 'cliente@hackthony.com', 'email': 'cliente@hackthony.com', 'first_name': 'Gabriela', 'last_name': 'Ponce', 'password': 'cliente123', 'role': 'cliente', 'color': '#26a69a', 'area': None, 'specialty': None, 'phone': '+51 994 520 027', 'client': 'MediSalud SAC'},
        ]

        user_objects = {}
        for data in users_data:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email': data['email'],
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                }
            )
            if created:
                user.set_password(data['password'])
                user.save()

            area = areas.get(data['area']) if data.get('area') else None
            specialty = specialties.get(data['specialty']) if data.get('specialty') else None
            client_obj = clients.get(data['client']) if data.get('client') else None

            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    'phone': data['phone'],
                    'area': area,
                    'specialty': specialty,
                    'client': client_obj,
                    'role': data['role'],
                    'color': data['color'],
                    'status': 'active',
                }
            )
            user_objects[data['username']] = user
            self.stdout.write(f'  User: {user.get_full_name()} ({data["role"]})')

        # ═══════════════════════════════════════════
        # 5. PROYECTOS (4)
        # ═══════════════════════════════════════════
        projects_data = [
            {
                'name': 'Consultoria TI - CorpMinera',
                'area': 'DEV',
                'description': 'Consultoria estrategica y diseno de arquitectura de red para 3 sedes.',
                'status': 'active',
                'lead': 'jp.miguel@hackthony.com',
                'client': 'Corporacion Minera SAC',
                'budget': 85000,
                'start_date': today - datetime.timedelta(days=90),
                'end_date': today + datetime.timedelta(days=60),
                'color': '#00bcd4',
                'members': ['pedro@hackthony.com', 'valeria@hackthony.com'],
            },
            {
                'name': 'E-commerce - FashionPeru',
                'area': 'DEV',
                'description': 'Plataforma e-commerce con catalogo, carrito y pasarela de pagos integrada.',
                'status': 'active',
                'lead': 'jp.miguel@hackthony.com',
                'client': 'FashionPeru S.R.L.',
                'budget': 35000,
                'start_date': today - datetime.timedelta(days=45),
                'end_date': today + datetime.timedelta(days=30),
                'color': '#2e7d32',
                'members': ['pedro@hackthony.com'],
            },
            {
                'name': 'App Movil - MediSalud',
                'area': 'INN',
                'description': 'Aplicacion movil para gestion de citas medicas y expediente digital. Cliente accede al portal.',
                'status': 'active',
                'lead': 'jp.laura@hackthony.com',
                'client': 'MediSalud SAC',
                'budget': 62000,
                'start_date': today - datetime.timedelta(days=60),
                'end_date': today + datetime.timedelta(days=90),
                'color': '#26c6da',
                'members': ['sofia@hackthony.com', 'pedro@hackthony.com'],
            },
            {
                'name': 'Portal Web - Municipalidad Lima',
                'area': 'DEV',
                'description': 'Portal de transparencia y servicios en linea para ciudadanos.',
                'status': 'planned',
                'lead': 'jp.miguel@hackthony.com',
                'client': 'Municipalidad Metropolitana de Lima',
                'budget': 54000,
                'start_date': today + datetime.timedelta(days=15),
                'end_date': today + datetime.timedelta(days=120),
                'color': '#ab47bc',
                'members': ['valeria@hackthony.com'],
            },
        ]

        projects = {}
        for data in projects_data:
            lead = user_objects.get(data['lead'])
            client = clients.get(data['client']) if data['client'] else None
            project, _ = Project.objects.get_or_create(
                name=data['name'],
                defaults={
                    'area': areas[data['area']],
                    'description': data['description'],
                    'status': data['status'],
                    'lead': lead,
                    'client': client,
                    'budget': data['budget'],
                    'start_date': data['start_date'],
                    'end_date': data['end_date'],
                    'color': data['color'],
                }
            )
            # Asignar miembros
            for member_username in data.get('members', []):
                member = user_objects.get(member_username)
                if member:
                    project.members.add(member)
                    self.stdout.write(f'    + member {member.get_full_name()} -> {project.name}')
            projects[data['name']] = project
            self.stdout.write(f'  Project: {project.name} ({project.status})')

        # ═══════════════════════════════════════════
        # 6. SPRINTS (2-3 por proyecto activo)
        # ═══════════════════════════════════════════
        sprints_data = [
            # Consultoria TI - CorpMinera
            {'project': 'Consultoria TI - CorpMinera', 'name': 'Sprint 1 - Diagnostico', 'start_date': today - datetime.timedelta(days=80), 'end_date': today - datetime.timedelta(days=66), 'goal': 'Inventariar activos TI y diagnosticar estado actual', 'status': 'completed'},
            {'project': 'Consultoria TI - CorpMinera', 'name': 'Sprint 2 - Diseno', 'start_date': today - datetime.timedelta(days=60), 'end_date': today - datetime.timedelta(days=46), 'goal': 'Disenar arquitectura de red propuesta', 'status': 'completed'},
            {'project': 'Consultoria TI - CorpMinera', 'name': 'Sprint 3 - Entrega', 'start_date': today - datetime.timedelta(days=40), 'end_date': today + datetime.timedelta(days=2), 'goal': 'Entregar informe final y plan de implementacion', 'status': 'active'},
            # E-commerce - FashionPeru
            {'project': 'E-commerce - FashionPeru', 'name': 'Sprint 1 - MVP', 'start_date': today - datetime.timedelta(days=40), 'end_date': today - datetime.timedelta(days=26), 'goal': 'Catalogo de productos con filtros', 'status': 'completed'},
            {'project': 'E-commerce - FashionPeru', 'name': 'Sprint 2 - Pagos', 'start_date': today - datetime.timedelta(days=20), 'end_date': today + datetime.timedelta(days=8), 'goal': 'Integrar pasarela de pagos MercadoPago', 'status': 'active'},
            # App Movil - MediSalud
            {'project': 'App Movil - MediSalud', 'name': 'Sprint 1 - Discovery', 'start_date': today - datetime.timedelta(days=55), 'end_date': today - datetime.timedelta(days=41), 'goal': 'Wireframes y diseno UX de flujos principales', 'status': 'completed'},
            {'project': 'App Movil - MediSalud', 'name': 'Sprint 2 - Citas MVP', 'start_date': today - datetime.timedelta(days=35), 'end_date': today - datetime.timedelta(days=21), 'goal': 'Flujo de agendamiento de citas funcional', 'status': 'completed'},
            {'project': 'App Movil - MediSalud', 'name': 'Sprint 3 - Expediente Digital', 'start_date': today - datetime.timedelta(days=14), 'end_date': today + datetime.timedelta(days=14), 'goal': 'Expediente medico digital con historial de consultas', 'status': 'active'},
        ]

        sprints = {}
        for data in sprints_data:
            project = projects[data['project']]
            sprint, _ = Sprint.objects.get_or_create(
                name=data['name'],
                project=project,
                defaults={
                    'start_date': data['start_date'],
                    'end_date': data['end_date'],
                    'goal': data['goal'],
                    'status': data['status'],
                }
            )
            sprints[(data['project'], data['name'])] = sprint
            self.stdout.write(f'  Sprint: {sprint} ({sprint.status})')

        # ═══════════════════════════════════════════
        # 7. TAREAS (asignadas a sprints y miembros)
        # ═══════════════════════════════════════════
        tasks_data = [
            # --- Consultoria TI - CorpMinera ---
            {'project': 'Consultoria TI - CorpMinera', 'sprint': 'Sprint 1 - Diagnostico', 'title': 'Reunion kickoff con cliente', 'type': 'task', 'priority': 'high', 'points': 3, 'assignee': 'jp.miguel@hackthony.com', 'status': 'done', 'description': 'Primera reunion para definir alcance, objetivos y entregables.', 'tags': 'kickoff'},
            {'project': 'Consultoria TI - CorpMinera', 'sprint': 'Sprint 1 - Diagnostico', 'title': 'Inventario de activos TI en 3 sedes', 'type': 'story', 'priority': 'high', 'points': 8, 'assignee': 'pedro@hackthony.com', 'status': 'done', 'description': 'Levantar inventario completo de hardware, software y conectividad.', 'tags': 'inventario'},
            {'project': 'Consultoria TI - CorpMinera', 'sprint': 'Sprint 2 - Diseno', 'title': 'Disenar arquitectura de red propuesta', 'type': 'story', 'priority': 'high', 'points': 13, 'assignee': 'pedro@hackthony.com', 'status': 'done', 'description': 'Elaborar diagrama de arquitectura de red con redundancia.', 'tags': 'arquitectura'},
            {'project': 'Consultoria TI - CorpMinera', 'sprint': 'Sprint 3 - Entrega', 'title': 'Redactar informe final de consultoria', 'type': 'task', 'priority': 'high', 'points': 5, 'assignee': 'jp.miguel@hackthony.com', 'status': 'in-progress', 'description': 'Documento ejecutivo con diagnostico, propuesta y plan de accion.', 'tags': 'documentacion'},
            {'project': 'Consultoria TI - CorpMinera', 'sprint': 'Sprint 3 - Entrega', 'title': 'Validar reporte de inventario (QA)', 'type': 'task', 'priority': 'medium', 'points': 2, 'assignee': 'valeria@hackthony.com', 'status': 'todo', 'description': 'Revisar que el PDF de inventario se genere correctamente.', 'tags': 'qa'},
            # --- E-commerce - FashionPeru ---
            {'project': 'E-commerce - FashionPeru', 'sprint': 'Sprint 1 - MVP', 'title': 'Catalogo de productos con filtros', 'type': 'story', 'priority': 'high', 'points': 8, 'assignee': 'pedro@hackthony.com', 'status': 'done', 'description': 'Pagina de listado con filtros por categoria, talla, color y precio.', 'tags': 'frontend'},
            {'project': 'E-commerce - FashionPeru', 'sprint': 'Sprint 1 - MVP', 'title': 'API de productos (CRUD)', 'type': 'story', 'priority': 'high', 'points': 5, 'assignee': 'jp.miguel@hackthony.com', 'status': 'done', 'description': 'Endpoints REST para gestion de catalogo.', 'tags': 'backend'},
            {'project': 'E-commerce - FashionPeru', 'sprint': 'Sprint 2 - Pagos', 'title': 'Integrar MercadoPago Checkout Pro', 'type': 'task', 'priority': 'high', 'points': 8, 'assignee': 'pedro@hackthony.com', 'status': 'in-progress', 'description': 'Implementar flujo de pago con MercadoPago.', 'tags': 'backend,pagos'},
            {'project': 'E-commerce - FashionPeru', 'sprint': 'Sprint 2 - Pagos', 'title': 'Pantalla de confirmacion de pedido', 'type': 'task', 'priority': 'medium', 'points': 3, 'assignee': 'jp.miguel@hackthony.com', 'status': 'todo', 'description': 'Disenar e implementar pantalla post-pago.', 'tags': 'frontend'},
            # --- App Movil - MediSalud ---
            {'project': 'App Movil - MediSalud', 'sprint': 'Sprint 1 - Discovery', 'title': 'Wireframes de flujos principales', 'type': 'story', 'priority': 'high', 'points': 8, 'assignee': 'sofia@hackthony.com', 'status': 'done', 'description': 'Disenar wireframes en Figma de las 5 pantallas principales.', 'tags': 'ux,figma'},
            {'project': 'App Movil - MediSalud', 'sprint': 'Sprint 2 - Citas MVP', 'title': 'Pantalla de agendamiento de citas', 'type': 'story', 'priority': 'high', 'points': 8, 'assignee': 'sofia@hackthony.com', 'status': 'done', 'description': 'UI para seleccionar fecha, especialidad y medico.', 'tags': 'frontend'},
            {'project': 'App Movil - MediSalud', 'sprint': 'Sprint 2 - Citas MVP', 'title': 'API de disponibilidad de medicos', 'type': 'task', 'priority': 'high', 'points': 8, 'assignee': 'pedro@hackthony.com', 'status': 'done', 'description': 'Endpoint que devuelve horarios disponibles segun especialidad.', 'tags': 'backend'},
            {'project': 'App Movil - MediSalud', 'sprint': 'Sprint 3 - Expediente Digital', 'title': 'Vista de historial medico', 'type': 'story', 'priority': 'high', 'points': 5, 'assignee': 'sofia@hackthony.com', 'status': 'in-progress', 'description': 'Interfaz para ver consultas pasadas, recetas y examenes.', 'tags': 'frontend'},
            {'project': 'App Movil - MediSalud', 'sprint': 'Sprint 3 - Expediente Digital', 'title': 'API de expediente medico', 'type': 'task', 'priority': 'high', 'points': 5, 'assignee': 'pedro@hackthony.com', 'status': 'done', 'description': 'Endpoints para CRUD de historial clinico.', 'tags': 'backend'},
            {'project': 'App Movil - MediSalud', 'sprint': 'Sprint 3 - Expediente Digital', 'title': 'Pruebas funcionales de flujo de citas', 'type': 'task', 'priority': 'medium', 'points': 3, 'assignee': 'valeria@hackthony.com', 'status': 'todo', 'description': 'Ejecutar casos de prueba del flujo completo de agendamiento.', 'tags': 'qa'},
            # --- Portal Web - Municipalidad Lima (sin sprint, en backlog) ---
            {'project': 'Portal Web - Municipalidad Lima', 'sprint': None, 'title': 'Definir requerimientos con municipio', 'type': 'task', 'priority': 'high', 'points': 5, 'assignee': 'jp.miguel@hackthony.com', 'status': 'backlog', 'description': 'Reunion inicial para levantar requerimientos del portal.', 'tags': 'kickoff'},
            {'project': 'Portal Web - Municipalidad Lima', 'sprint': None, 'title': 'Disenar wireframes del portal', 'type': 'story', 'priority': 'high', 'points': 8, 'assignee': 'valeria@hackthony.com', 'status': 'backlog', 'description': 'Wireframes de las 3 secciones principales del portal.', 'tags': 'ux'},
        ]

        tags_cache = {}
        for data in tasks_data:
            project = projects[data['project']]
            assignee = user_objects.get(data['assignee'])
            sprint = sprints.get((data['project'], data['sprint'])) if data['sprint'] else None

            task, created = Task.objects.get_or_create(
                title=data['title'],
                project=project,
                defaults={
                    'type': data['type'],
                    'priority': data['priority'],
                    'points': data['points'],
                    'assignee': assignee,
                    'status': data['status'],
                    'description': data['description'],
                    'sprint': sprint,
                }
            )
            if not created and sprint and not task.sprint:
                task.sprint = sprint; task.save()

            for tag_name in data['tags'].split(','):
                tag_name = tag_name.strip()
                if tag_name not in tags_cache:
                    tags_cache[tag_name], _ = Tag.objects.get_or_create(
                        name=tag_name, defaults={'color': '#64748b'},
                    )
                task.tags.add(tags_cache[tag_name])
            self.stdout.write(f'  Task: {task.title[:50]} [{task.status}]')

        # ═══════════════════════════════════════════
        # 8. COMENTARIOS DE PROYECTO (chat grupal)
        # ═══════════════════════════════════════════
        comments_data = [
            {'project': 'Consultoria TI - CorpMinera', 'author': 'jp.miguel@hackthony.com', 'text': 'Bienvenidos al proyecto! Arrancamos con el inventario de activos en las 3 sedes.', 'days_ago': 78},
            {'project': 'Consultoria TI - CorpMinera', 'author': 'pedro@hackthony.com', 'text': 'Listo Miguel, ya tengo el 60% relevado. La sede norte tiene mucho equipo legacy.', 'days_ago': 74},
            {'project': 'Consultoria TI - CorpMinera', 'author': 'jp.miguel@hackthony.com', 'text': 'Anotado. Priorizamos reemplazo de switches en sede norte para el informe.', 'days_ago': 72},
            {'project': 'App Movil - MediSalud', 'author': 'jp.laura@hackthony.com', 'text': 'Chicos, los wireframes quedaron muy bien. El cliente aprobo el diseno.', 'days_ago': 50},
            {'project': 'App Movil - MediSalud', 'author': 'sofia@hackthony.com', 'text': 'Genial! Empiezo con el desarrollo de la pantalla de agendamiento.', 'days_ago': 35},
            {'project': 'E-commerce - FashionPeru', 'author': 'jp.miguel@hackthony.com', 'text': 'El MVP del catalogo esta listo. Ahora vamos por la integracion de pagos.', 'days_ago': 22},
        ]

        for data in comments_data:
            project = projects[data['project']]
            author = user_objects[data['author']]
            Comment.objects.create(
                project=project,
                author=author,
                text=data['text'],
                created_at=today - datetime.timedelta(days=data['days_ago']),
            )

        self.stdout.write(self.style.SUCCESS('\nDatabase seeded successfully!'))
        self.stdout.write(f'  Areas: {len(areas)}')
        self.stdout.write(f'  Users: {len(user_objects)}')
        self.stdout.write(f'  Clients: {len(clients)}')
        self.stdout.write(f'  Projects: {len(projects)}')
        self.stdout.write(f'  Sprints: {len(sprints)}')
        self.stdout.write(f'  Tasks: {len(tasks_data)}')
        self.stdout.write(f'  Comments: {len(comments_data)}')
