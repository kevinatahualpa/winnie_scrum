# API REST v1

La API REST de Winnie expone el dominio (proyectos, tareas, sprints, etc.) de
forma independiente a las vistas HTML, usando Django REST Framework + JWT.

## Base URL

```
/api/v1/
```

## Autenticacion

La API soporta dos metodos de autenticacion:

| Metodo | Uso |
|---|---|
| **JWT (Bearer)** | `Authorization: Bearer <access_token>` — recomendado para clientes externos |
| **Session** | Cookie de sesion Django — util para el Browsable API y el frontend Django existente |

### Obtener un token JWT

```bash
POST /api/v1/auth/token/
Content-Type: application/json

{
  "username": "admin@hackthony.com",
  "password": "123456"
}
```

Respuesta:

```json
{
  "refresh": "eyJ...",
  "access": "eyJ..."
}
```

### Refrescar el token

```bash
POST /api/v1/auth/token/refresh/
{ "refresh": "eyJ..." }
```

### Verificar un token

```bash
POST /api/v1/auth/token/verify/
{ "token": "eyJ..." }
```

## Endpoints

Todos los endpoints siguen el patron REST del router de DRF:

| Recurso | URL | Metodos |
|---|---|---|
| Areas | `/api/v1/areas/` | GET, POST, PUT, PATCH, DELETE |
| Clientes | `/api/v1/clients/` | GET, POST, PUT, PATCH, DELETE |
| Especialidades | `/api/v1/specialties/` | GET, POST, PUT, PATCH, DELETE |
| Tecnologias | `/api/v1/technologies/` | GET, POST, PUT, PATCH, DELETE |
| Perfiles | `/api/v1/profiles/` | GET (solo lectura) |
| **Proyectos** | `/api/v1/projects/` | GET, POST, PUT, PATCH, DELETE |
| Sprints | `/api/v1/sprints/` | GET, POST, PUT, PATCH, DELETE |
| **Tareas** | `/api/v1/tasks/` | GET, POST, PUT, PATCH, DELETE |
| Tags | `/api/v1/tags/` | GET, POST, PUT, PATCH, DELETE |
| Comentarios | `/api/v1/comments/` | GET, POST, PUT, PATCH, DELETE |

### Acciones personalizadas

| Accion | URL | Descripcion |
|---|---|---|
| Tareas de un proyecto | `GET /api/v1/projects/{id}/tasks/` | Lista paginada de tareas del proyecto |
| Sprints de un proyecto | `GET /api/v1/projects/{id}/sprints/` | Lista de sprints del proyecto |
| Cambiar estado de tarea | `POST /api/v1/tasks/{id}/cambiar_estado/` | Aplica la maquina de estados (backlog → todo → in-progress → done) |

## Filtros, busqueda y orden

Todos los endpoints de listado soportan:

- `?search=<texto>` — busqueda full-text (campos definidos por `search_fields`)
- `?ordering=<campo>` o `?ordering=-<campo>` — orden ascendente/descendente
- `?<field>=<value>` — filtro exacto (campos definidos por `filterset_fields`)
- `?page=2&page_size=20` — paginacion (default 50 por pagina)

### Ejemplo

```bash
GET /api/v1/tasks/?status=in-progress&ordering=-priority&search=login&page_size=10
Authorization: Bearer eyJ...
```

## RBAC (Role-Based Access Control)

La API **reutiliza el `permission_service` existente**, no redefine permisos:

| Recurso | Lectura | Escritura | Eliminacion |
|---|---|---|---|
| Proyectos | `filter_queryset_by_role` | `can_manage_area` / `can_manage_project` | `can_delete_project` (solo super-admin) |
| Tareas | `filter_queryset_by_role` | `can_manage_task` | `can_manage_task` |
| Sprints | `filter_queryset_by_role` | `ReadOnlyIfNotManager` | `ReadOnlyIfNotManager` |
| Perfiles | `filter_queryset_by_role` (user) | — (solo lectura) | — |

El servicio `ProjectService`, `TaskService`, etc. se invocan desde los viewsets,
por lo que toda la logica de negocio (auditoria, notificaciones, validaciones)
se mantiene centralizada en la capa de dominio.

## Ejemplos completos

### Crear un proyecto

```bash
POST /api/v1/projects/
Authorization: Bearer eyJ...
Content-Type: application/json

{
  "name": "Proyecto API",
  "area": 1,
  "description": "Creado via API",
  "status": "planned",
  "budget": "1500.00",
  "color": "#ff0000",
  "members": [2, 3]
}
```

### Crear una tarea

```bash
POST /api/v1/tasks/
Authorization: Bearer eyJ...
Content-Type: application/json

{
  "project": 1,
  "title": "Implementar login JWT",
  "type": "task",
  "priority": "high",
  "points": 3,
  "assignee": 2,
  "sprint": 1,
  "tags_csv": "auth,backend,urgent"
}
```

> Nota: las tags se envian como string CSV en `tags_csv` (comma-separated), no
> como array. Esto delega al `TaskService.crear_tarea` que ya maneja el split y
> el `get_or_create`.

### Avanzar una tarea de estado

```bash
POST /api/v1/tasks/42/cambiar_estado/
Authorization: Bearer eyJ...
Content-Type: application/json

{ "status": "in-progress" }
```

Respuesta 400 si la transicion no esta permitida por la maquina de estados:

```json
{ "detail": "No se puede mover de \"done\" a \"backlog\". Flujo: Backlog → Por Hacer → En Progreso → Completado" }
```

## Browsable API

En desarrollo, visita `http://127.0.0.1:8000/api/v1/` en el navegador. DRF
ofrece una interfaz HTML interactiva para explorar y probar endpoints (requiere
login por sesion).

## Throttling

- 1000 requests/hora por usuario autenticado (`DEFAULT_THROTTLE_RATES['user']`).

## Estructura del codigo

```
apps/core/infrastructure/api/
├── __init__.py
├── permissions.py      # Permission classes que envuelven permission_service
├── serializers.py      # Serializers por entidad (ModelSerializer + campos calculados)
├── views.py            # ViewSets (ModelViewSet + acciones custom)
└── urls.py             # DefaultRouter + endpoints JWT
```

## Testing

```bash
python manage.py test apps.core.tests.test_api -v 2
```

Cubre: autenticacion JWT, RBAC (admin vs miembro vs anon), CRUD de proyectos,
acciones anidadas y maquina de estados de tareas.
