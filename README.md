# Winnie - Gestion de Proyectos Scrum

Sistema de gestion de proyectos Scrum con roles jerarquicos, tablero Kanban, sprints, backlog, seguimiento de tiempo y mas.

## Stack Tecnologico

| Capa | Tecnologia |
|---|---|
| **Backend** | Django 5.x + Python 3.12+ |
| **Base de datos** | PostgreSQL |
| **Frontend** | Django Templates + Bootstrap 5.3.3 + Font Awesome 6.5.1 |
| **Arquitectura** | Clean Architecture parcial (domain/infrastructure/presentation) |

## Roles del Sistema

| Rol | Descripcion |
|---|---|
| `super-admin` | Acceso total al sistema |
| `admin` | Administracion de usuarios y recursos |
| `jefe-area` | Gestion de areas y proyectos asignados |
| `jefe-proyecto` | Gestion de proyectos y tareas |
| `miembro` | Visualizacion y gestion de tareas asignadas |

## Requisitos

- Python 3.12+
- PostgreSQL
- pip

## Instalacion

### 1. Clonar el repositorio

```bash
git clone <repository-url>
cd Scrum_hackthony
```

### 2. Crear entorno virtual

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Crear archivo `.env` en la raiz del proyecto:

```env
SECRET_KEY=<tu-secret-key>
DEBUG=True
DB_NAME=winnie_db
DB_USER=tu_usuario
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=5432
```

### 5. Configurar PostgreSQL

```bash
sudo -u postgres psql
CREATE DATABASE winnie_db;
CREATE USER tu_usuario WITH PASSWORD 'tu_password';
GRANT ALL PRIVILEGES ON DATABASE winnie_db TO tu_usuario;
\q
```

### 6. Ejecutar migraciones

```bash
python3 manage.py makemigrations
python3 manage.py migrate
```

### 7. Cargar datos de prueba (seed data)

```bash
python3 manage.py loaddata apps/core/management/commands/seed_data.json
```

### 8. Ejecutar servidor de desarrollo

```bash
python3 manage.py runserver
```

Acceder a: `http://127.0.0.1:8000/`

## Estructura del Proyecto

```
Scrum_hackthony/
├── config/                      # Configuracion de Django
│   ├── settings/
│   │   ├── base.py              # Settings compartidos
│   │   ├── local.py             # Settings desarrollo
│   │   └── production.py        # Settings produccion
│   └── urls.py                  # URL routing principal
├── apps/
│   └── core/
│       ├── domain/              # Capa de dominio
│       │   ├── repositories.py  # Interfaces de repositorio
│       │   └── services/        # Logica de negocio
│       │       ├── permission_service.py
│       │       ├── notification_service.py
│       │       ├── project_service.py
│       │       ├── task_service.py
│       │       ├── sprint_service.py
│       │       └── user_service.py
│       ├── infrastructure/      # Capa de infraestructura
│       │   ├── models/          # Modelos Django
│       │   └── repositories/    # Implementaciones de repositorios
│       ├── presentation/        # Capa de presentacion
│       │   ├── views/           # Vistas modulares por entidad
│       │   ├── templates/       # Templates HTML
│       │   ├── static/          # Archivos estaticos
│       │   └── urls.py          # URL routing de la app
│       ├── templatetags/        # Template tags personalizados
│       └── tests/               # Tests
│           ├── test_models.py
│           ├── test_services/
│           ├── test_views/
│           └── test_templatetags/
├── informe/                     # Documentacion de mejoras
│   ├── README.md
│   ├── TODO.md
│   └── CHANGELOG.md
├── .env                         # Variables de entorno (no commitear)
├── .gitignore
├── requirements.txt
└── manage.py
```

## Ejecutar Tests

```bash
python3 manage.py test apps.core.tests -v 2
```

## Produccion

### Variables de entorno requeridas

```env
SECRET_KEY=<clave-segura-generada>
DEBUG=False
ALLOWED_HOSTS=tudominio.com,www.tudominio.com
DB_NAME=winnie_db
DB_USER=tu_usuario
DB_PASSWORD=<password-seguro>
DB_HOST=localhost
DB_PORT=5432
```

### Recopilar archivos estaticos

```bash
python3 manage.py collectstatic
```

## Credenciales por Defecto (Solo Desarrollo)

| Email | Password | Rol |
|---|---|---|
| super@gmail.com | 123456 | Super Admin |
| admin@gmail.com | 123456 | Admin |
| jefe.areas@hackthony.com | area123 | Jefe de Area |
| jp.consultoria@hackthony.com | jp123 | Jefe de Proyecto |
| miembro1@hackthony.com | member123 | Miembro |

## Funcionalidades

- **Dashboard** con estadisticas por rol
- **Tablero Kanban** con drag-and-drop
- **Backlog** de tareas priorizadas
- **Sprints** con inicio/completado
- **Gestion de proyectos** CRUD completo
- **Gestion de equipo** con roles y areas
- **Seguimiento de tiempo** por tarea
- **Documentos** por proyecto
- **Solicitudes de servicio** para clientes
- **Suplencias** temporales de roles
- **Notificaciones** en tiempo real
- **Audit log** de acciones
- **Calendario** de sprints
- **Reportes** por estado, tipo y prioridad
