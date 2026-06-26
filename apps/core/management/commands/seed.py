from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.core.infrastructure.models.models import (
    Area, Specialty, UserProfile, Client, Project,
    Sprint, Task, Tag, Comment, Document, ServiceRequest,
    TimeEntry, Notification, AuditLog
)


class Command(BaseCommand):
    help = 'Seed database with initial data'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database...')

        areas_data = [
            {'code': 'D1', 'name': 'Consultoria y Capacitacion', 'description': 'Servicios de consultoria TI, mesas de ayuda, capacitacion y learning center.', 'color': '#00bcd4', 'icon': 'fa-laptop-code'},
            {'code': 'D2', 'name': 'Eventos y Conferencias', 'description': 'Organizacion de eventos tecnologicos, marketing digital y community management.', 'color': '#6554c0', 'icon': 'fa-calendar-star'},
            {'code': 'D3', 'name': 'Servicios Digitales y Desarrollo', 'description': 'Desarrollo web, e-commerce, cloud computing y desarrollo de software.', 'color': '#2e7d32', 'icon': 'fa-code'},
            {'code': 'D4', 'name': 'Comercializacion Informatica', 'description': 'Venta de equipos, licencias, componentes y telecomunicaciones.', 'color': '#f57f17', 'icon': 'fa-shopping-cart'},
        ]

        areas = {}
        for data in areas_data:
            area, _ = Area.objects.get_or_create(code=data['code'], defaults=data)
            areas[data['code']] = area
            self.stdout.write(f'  Area: {area}')

        specialties_data = [
            {'name': 'Backend Developer', 'category': 'development', 'description': 'Desarrollo de APIs, bases de datos y logica de servidor', 'color': '#2e7d32'},
            {'name': 'Frontend Developer', 'category': 'development', 'description': 'Desarrollo de interfaces web, React, Vue, Angular', 'color': '#0277bd'},
            {'name': 'FullStack Developer', 'category': 'development', 'description': 'Desarrollo completo frontend y backend', 'color': '#6554c0'},
            {'name': 'DevOps Engineer', 'category': 'devops', 'description': 'CI/CD, infraestructura cloud, Docker, Kubernetes', 'color': '#f57f17'},
            {'name': 'UI/UX Designer', 'category': 'design', 'description': 'Diseno de interfaces y experiencia de usuario', 'color': '#e91e63'},
            {'name': 'QA Engineer', 'category': 'qa', 'description': 'Testing manual y automatizado, calidad de software', 'color': '#c62828'},
            {'name': 'Mobile Developer', 'category': 'development', 'description': 'Desarrollo de apps mobiles iOS y Android', 'color': '#00bcd4'},
            {'name': 'Data Analyst', 'category': 'data', 'description': 'Analisis de datos, Power BI, dashboards', 'color': '#ff9800'},
            {'name': 'Scrum Master', 'category': 'management', 'description': 'Facilitacion de metodologias agiles', 'color': '#6554c0'},
            {'name': 'Product Owner', 'category': 'management', 'description': 'Gestion de producto y backlog', 'color': '#039be5'},
            {'name': 'Marketing Digital', 'category': 'marketing', 'description': 'SEO, SEM, campanas digitales, analytics', 'color': '#f57f17'},
            {'name': 'Community Manager', 'category': 'marketing', 'description': 'Gestion de redes sociales y comunidad', 'color': '#e91e63'},
            {'name': 'Soporte Tecnico', 'category': 'support', 'description': 'Soporte nivel 1, 2 y 3, mesa de ayuda', 'color': '#2e7d32'},
            {'name': 'Arquitecto de Software', 'category': 'development', 'description': 'Diseno de arquitectura de sistemas', 'color': '#6554c0'},
            {'name': 'Database Administrator', 'category': 'data', 'description': 'Administracion de bases de datos', 'color': '#0277bd'},
        ]

        specialties = {}
        for data in specialties_data:
            spec, _ = Specialty.objects.get_or_create(name=data['name'], defaults=data)
            specialties[data['name']] = spec

        clients_data = [
            {'name': 'Corporacion Minera SAC', 'contact': 'Carlos Mendoza', 'email': 'cmendoza@corpminera.com', 'phone': '+51 987 654 321', 'industry': 'Mineria'},
            {'name': 'RetailPlus S.A.C.', 'contact': 'Ana Torres', 'email': 'atorres@retailplus.com', 'phone': '+51 976 543 210', 'industry': 'Retail'},
            {'name': 'FashionPeru S.R.L.', 'contact': 'Maria Lopez', 'email': 'mlopez@fashionperu.com', 'phone': '+51 965 432 109', 'industry': 'Moda'},
            {'name': 'Inmobiliaria Los Andes SAC', 'contact': 'Roberto Diaz', 'email': 'rdiaz@losandes.com', 'phone': '+51 954 321 098', 'industry': 'Inmobiliaria'},
            {'name': 'MediSalud SAC', 'contact': 'Dra. Gabriela Ponce', 'email': 'gponce@medisalud.pe', 'phone': '+51 943 210 987', 'industry': 'Salud'},
            {'name': 'Municipalidad Metropolitana de Lima', 'contact': 'Ing. Jorge Huaman', 'email': 'jhuaman@munlima.gob.pe', 'phone': '+51 932 109 876', 'industry': 'Gobierno'},
            {'name': 'Distribuidora Union S.A.', 'contact': 'Rodrigo Vargas', 'email': 'rvargas@distunion.com', 'phone': '+51 921 098 765', 'industry': 'Distribucion'},
            {'name': 'Turismo Andes S.R.L.', 'contact': 'Camila Quispe', 'email': 'cquispe@turismoandes.pe', 'phone': '+51 910 987 654', 'industry': 'Turismo'},
        ]

        clients = {}
        for data in clients_data:
            client, _ = Client.objects.get_or_create(name=data['name'], defaults=data)
            clients[data['name']] = client

        users_data = [
            {'username': 'super@gmail.com', 'email': 'super@gmail.com', 'first_name': 'Carlos', 'last_name': 'SuperAdmin', 'password': '123456', 'role': 'super-admin', 'color': '#c62828', 'area': 'D1', 'specialty': 'Arquitecto de Software', 'phone': '+51 994 520 017'},
            {'username': 'admin@gmail.com', 'email': 'admin@gmail.com', 'first_name': 'Ana', 'last_name': 'Administradora', 'password': '123456', 'role': 'admin', 'color': '#f57f17', 'area': 'D1', 'specialty': 'Product Owner', 'phone': '+51 994 520 018'},
            {'username': 'jefe.areas@hackthony.com', 'email': 'jefe.areas@hackthony.com', 'first_name': 'Roberto', 'last_name': 'Jefe Area', 'password': 'area123', 'role': 'jefe-area', 'color': '#6554c0', 'area': 'D1', 'specialty': 'Scrum Master', 'phone': '+51 994 520 019'},
            {'username': 'jp.consultoria@hackthony.com', 'email': 'jp.consultoria@hackthony.com', 'first_name': 'Laura', 'last_name': 'JP Consultoria', 'password': 'jp123', 'role': 'jefe-proyecto', 'color': '#00bcd4', 'area': 'D1', 'specialty': 'FullStack Developer', 'phone': '+51 994 520 020'},
            {'username': 'jp.eventos@hackthony.com', 'email': 'jp.eventos@hackthony.com', 'first_name': 'Maria', 'last_name': 'JP Eventos', 'password': 'jp123', 'role': 'jefe-proyecto', 'color': '#0277bd', 'area': 'D2', 'specialty': 'Marketing Digital', 'phone': '+51 994 520 021'},
            {'username': 'miembro1@hackthony.com', 'email': 'miembro1@hackthony.com', 'first_name': 'Pedro', 'last_name': 'Backend', 'password': 'member123', 'role': 'miembro', 'color': '#2e7d32', 'area': 'D3', 'specialty': 'Backend Developer', 'phone': '+51 994 520 022'},
            {'username': 'miembro2@hackthony.com', 'email': 'miembro2@hackthony.com', 'first_name': 'Sofia', 'last_name': 'Frontend', 'password': 'member123', 'role': 'miembro', 'color': '#4caf50', 'area': 'D3', 'specialty': 'Frontend Developer', 'phone': '+51 994 520 023'},
            {'username': 'diego@hackthony.com', 'email': 'diego@hackthony.com', 'first_name': 'Diego', 'last_name': 'Marketing', 'password': 'member123', 'role': 'miembro', 'color': '#ff9800', 'area': 'D2', 'specialty': 'Community Manager', 'phone': '+51 994 520 024'},
            {'username': 'javier@hackthony.com', 'email': 'javier@hackthony.com', 'first_name': 'Javier', 'last_name': 'FullStack', 'password': 'member123', 'role': 'miembro', 'color': '#e91e63', 'area': 'D3', 'specialty': 'FullStack Developer', 'phone': '+51 994 520 025'},
            {'username': 'valeria@hackthony.com', 'email': 'valeria@hackthony.com', 'first_name': 'Valeria', 'last_name': 'QA', 'password': 'member123', 'role': 'miembro', 'color': '#9c27b0', 'area': 'D1', 'specialty': 'QA Engineer', 'phone': '+51 994 520 026'},
            {'username': 'cliente@hackthony.com', 'email': 'cliente@hackthony.com', 'first_name': 'Carlos', 'last_name': 'Mendoza', 'password': 'cliente123', 'role': 'cliente', 'color': '#26a69a', 'area': None, 'specialty': None, 'phone': '+51 994 520 027', 'client': 'Corporacion Minera SAC'},
            {'username': 'auditor@hackthony.com', 'email': 'auditor@hackthony.com', 'first_name': 'Patricia', 'last_name': 'Auditora', 'password': 'audit123', 'role': 'miembro', 'color': '#6d8b7d', 'area': None, 'specialty': None, 'phone': '+51 994 520 028'},
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

            area = areas.get(data['area'])
            specialty = specialties.get(data['specialty'])
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

        projects_data = [
            {'name': 'Consultoria TI - CorpMinera', 'area': 'D1', 'description': 'Consultoria estrategica y diseno de arquitectura de red para 3 sedes.', 'status': 'active', 'lead': 'jp.consultoria@hackthony.com', 'client': 'Corporacion Minera SAC', 'budget': 85000, 'start_date': '2025-01-15', 'end_date': '2025-06-30', 'color': '#00bcd4'},
            {'name': 'Implementacion Cloud - RetailPlus', 'area': 'D1', 'description': 'Migracion completa a nube hibrida AWS + Azure para operaciones de retail.', 'status': 'active', 'lead': 'jp.consultoria@hackthony.com', 'client': 'RetailPlus S.A.C.', 'budget': 42000, 'start_date': '2025-02-01', 'end_date': '2025-05-30', 'color': '#4fc3f7'},
            {'name': 'Tech Summit 2025', 'area': 'D2', 'description': 'Organizacion del evento tecnologico anual con mas de 500 asistentes esperados.', 'status': 'planned', 'lead': 'jp.eventos@hackthony.com', 'client': None, 'budget': 15000, 'start_date': '2025-03-01', 'end_date': '2025-08-30', 'color': '#6554c0'},
            {'name': 'E-commerce - FashionPeru', 'area': 'D3', 'description': 'Plataforma e-commerce con catalogo, carrito y pasarela de pagos integrada.', 'status': 'active', 'lead': 'jp.eventos@hackthony.com', 'client': 'FashionPeru S.R.L.', 'budget': 35000, 'start_date': '2025-01-20', 'end_date': '2025-04-30', 'color': '#2e7d32'},
            {'name': 'App Movil - MediSalud', 'area': 'D3', 'description': 'Aplicacion movil iOS y Android para gestion de citas medicas y expediente digital.', 'status': 'active', 'lead': 'jp.eventos@hackthony.com', 'client': 'MediSalud SAC', 'budget': 62000, 'start_date': '2025-03-10', 'end_date': '2025-09-10', 'color': '#26c6da'},
            {'name': 'Soporte TI - Municipalidad Lima', 'area': 'D1', 'description': 'Mesa de ayuda nivel 1 y 2 para 300 usuarios, mantenimiento de infraestructura.', 'status': 'active', 'lead': 'jp.consultoria@hackthony.com', 'client': 'Municipalidad Metropolitana de Lima', 'budget': 54000, 'start_date': '2025-01-05', 'end_date': '2025-12-31', 'color': '#ab47bc'},
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
            projects[data['name']] = project
            self.stdout.write(f'  Project: {project.name}')

        tasks_data = [
            {'project': 'Consultoria TI - CorpMinera', 'title': 'Reunion kickoff con cliente', 'type': 'task', 'priority': 'high', 'points': 3, 'assignee': 'jp.consultoria@hackthony.com', 'status': 'done', 'description': 'Primera reunion para definir alcance, objetivos y entregables.', 'tags': 'reunion,kickoff'},
            {'project': 'Consultoria TI - CorpMinera', 'title': 'Inventario de activos TI en 3 sedes', 'type': 'story', 'priority': 'high', 'points': 8, 'assignee': 'miembro1@hackthony.com', 'status': 'done', 'description': 'Levantar inventario completo de hardware, software y conectividad.', 'tags': 'consultoria,networking'},
            {'project': 'Consultoria TI - CorpMinera', 'title': 'Disenar arquitectura de red propuesta', 'type': 'story', 'priority': 'high', 'points': 13, 'assignee': 'valeria@hackthony.com', 'status': 'done', 'description': 'Elaborar diagrama de arquitectura de red con redundancia.', 'tags': 'arquitectura,diseno'},
            {'project': 'Implementacion Cloud - RetailPlus', 'title': 'Evaluar proveedores cloud', 'type': 'story', 'priority': 'high', 'points': 8, 'assignee': 'jp.consultoria@hackthony.com', 'status': 'done', 'description': 'Analisis comparativo de AWS, Azure y GCP.', 'tags': 'cloud,evaluacion'},
            {'project': 'Implementacion Cloud - RetailPlus', 'title': 'Migrar base de datos a RDS', 'type': 'task', 'priority': 'high', 'points': 13, 'assignee': 'javier@hackthony.com', 'status': 'in-progress', 'description': 'Migrar PostgreSQL on-premise a Amazon RDS.', 'tags': 'migracion,aws'},
            {'project': 'E-commerce - FashionPeru', 'title': 'Catalogo de productos con filtros', 'type': 'story', 'priority': 'high', 'points': 8, 'assignee': 'miembro2@hackthony.com', 'status': 'done', 'description': 'Pagina de listado con filtros por categoria, talla, color y precio.', 'tags': 'frontend,ecommerce'},
            {'project': 'E-commerce - FashionPeru', 'title': 'Integrar MercadoPago Checkout Pro', 'type': 'task', 'priority': 'high', 'points': 8, 'assignee': 'javier@hackthony.com', 'status': 'in-progress', 'description': 'Implementar flujo de pago con MercadoPago.', 'tags': 'backend,pagos'},
            {'project': 'App Movil - MediSalud', 'title': 'Wireframes de flujos principales', 'type': 'story', 'priority': 'high', 'points': 8, 'assignee': 'diego@hackthony.com', 'status': 'in-progress', 'description': 'Disenar wireframes en Figma.', 'tags': 'ux,figma'},
            {'project': 'Soporte TI - Municipalidad Lima', 'title': 'Inventario y diagnostico de activos TI', 'type': 'story', 'priority': 'high', 'points': 8, 'assignee': 'valeria@hackthony.com', 'status': 'done', 'description': 'Catastro de 847 equipos en 12 oficinas.', 'tags': 'inventario,soporte'},
            {'project': 'Tech Summit 2025', 'title': 'Reservar centro de convenciones', 'type': 'task', 'priority': 'high', 'points': 3, 'assignee': 'jp.eventos@hackthony.com', 'status': 'backlog', 'description': 'Confirmar disponibilidad y firmar contrato.', 'tags': 'logistica,evento'},
            {'project': 'Tech Summit 2025', 'title': 'Landing page y sistema de inscripciones', 'type': 'story', 'priority': 'high', 'points': 8, 'assignee': 'diego@hackthony.com', 'status': 'backlog', 'description': 'Pagina web del evento con formulario de inscripcion.', 'tags': 'web,marketing'},
            {'project': 'Consultoria TI - CorpMinera', 'title': 'Bug en reporte de inventario PDF', 'type': 'bug', 'priority': 'medium', 'points': 3, 'assignee': 'valeria@hackthony.com', 'status': 'todo', 'description': 'El modulo de reportes no genera correctamente el PDF.', 'tags': 'bug,reportes'},
        ]

        tags_cache = {}

        for data in tasks_data:
            project = projects[data['project']]
            assignee = user_objects.get(data['assignee'])
            task, _ = Task.objects.get_or_create(
                title=data['title'],
                project=project,
                defaults={
                    'type': data['type'],
                    'priority': data['priority'],
                    'points': data['points'],
                    'assignee': assignee,
                    'status': data['status'],
                    'description': data['description'],
                }
            )
            for tag_name in data['tags'].split(','):
                tag_name = tag_name.strip()
                if tag_name not in tags_cache:
                    tags_cache[tag_name], _ = Tag.objects.get_or_create(
                        name=tag_name,
                        defaults={'color': '#64748b'}
                    )
                task.tags.add(tags_cache[tag_name])

        service_requests_data = [
            {'client': 'Engie 24', 'service': 'consultoria', 'description': 'Consultoria para optimizar infraestructura de red.', 'status': 'new'},
            {'client': 'Ingelectros Peru', 'service': 'seguridad', 'description': 'Implementacion de seguridad informatica perimetral.', 'status': 'in-progress'},
            {'client': 'Clinica San Marcos', 'service': 'soporte', 'description': 'Contrato de soporte tecnico para 80 equipos.', 'status': 'new'},
        ]

        for data in service_requests_data:
            client, _ = Client.objects.get_or_create(
                name=data['client'],
                defaults={'contact': data['client'], 'email': '', 'phone': '', 'industry': 'Servicios'}
            )
            ServiceRequest.objects.get_or_create(
                client=client,
                service=data['service'],
                defaults={'description': data['description'], 'status': data['status']}
            )

        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))
