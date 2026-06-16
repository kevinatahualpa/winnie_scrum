# Casos de Uso - Winnie

## Actores

| Actor | Rol en BD | Descripción |
|-------|-----------|-------------|
| **Usuario no autenticado** | — | Sin sesión iniciada |
| **Miembro** | `miembro` | Usuario básico del equipo |
| **Jefe de Proyecto** | `jefe-proyecto` | Líder de uno o más proyectos |
| **Jefe de Área** | `jefe-area` | Responsable de un área organizacional |
| **Admin** | `admin` | Administrador del sistema |
| **Super Admin** | `super-admin` | Máximo nivel de acceso |

---

## Autenticación

| Código | Caso de Uso | Actor | Descripción |
|--------|-------------|-------|-------------|
| `UC-AUTH-01` | iniciar sesión | Usuario no autenticado | Autenticarse con email y password |
| `UC-AUTH-02` | registrarse | Usuario no autenticado | Crear cuenta con estado "pendiente" |
| `UC-AUTH-03` | cerrar sesión | Usuario autenticado | Finalizar sesión activa |

---

## Usuario / Miembro

| Código | Caso de Uso | Actor | Descripción |
|--------|-------------|-------|-------------|
| `UC-USR-01` | registrar usuario | Admin, Super Admin | Crear usuario con perfil completo |
| `UC-USR-02` | editar usuario | Admin, Super Admin | Modificar datos de usuario y perfil |
| `UC-USR-03` | eliminar usuario | Admin, Super Admin | Borrar usuario y su perfil |
| `UC-USR-04` | ver registros pendientes | Admin, Super Admin | Lista de auto-registros en estado "pending" |
| `UC-USR-05` | aprobar registro | Admin, Super Admin | Activar usuario pendiente y asignar área |
| `UC-USR-06` | rechazar registro | Admin, Super Admin | Rechazar y eliminar usuario pendiente |
| `UC-USR-07` | ver perfil | Usuario autenticado | Consultar datos propios |

---

## Proyecto

| Código | Caso de Uso | Actor | Descripción |
|--------|-------------|-------|-------------|
| `UC-PROJ-01` | crear proyecto | Jefe de Área, Admin, Super Admin | Crear nuevo proyecto con miembros |
| `UC-PROJ-02` | editar proyecto | Jefe de Proyecto, Jefe de Área, Admin, Super Admin | Modificar proyecto existente |
| `UC-PROJ-03` | eliminar proyecto | Jefe de Proyecto, Jefe de Área, Admin, Super Admin | Eliminar proyecto |
| `UC-PROJ-04` | ver proyectos | Todos los autenticados | Listar proyectos según el rol |

---

## Tarea

| Código | Caso de Uso | Actor | Descripción |
|--------|-------------|-------|-------------|
| `UC-TASK-01` | crear tarea | Jefe de Proyecto, Jefe de Área, Admin, Super Admin | Crear tarea en un proyecto |
| `UC-TASK-02` | editar tarea | Jefe de Proyecto, Jefe de Área, Admin, Super Admin, Miembro (asignado) | Modificar tarea |
| `UC-TASK-03` | eliminar tarea | Jefe de Proyecto, Jefe de Área, Admin, Super Admin, Miembro (asignado) | Eliminar tarea |
| `UC-TASK-04` | actualizar estado tarea | Jefe de Proyecto, Jefe de Área, Admin, Super Admin, Miembro (asignado) | Cambiar estado (Kanban drag-and-drop) |
| `UC-TASK-05` | comentar tarea | Jefe de Proyecto, Jefe de Área, Admin, Super Admin, Miembro (asignado) | Agregar comentario a tarea |
| `UC-TASK-06` | ver tareas | Todos los autenticados | Listar tareas según el rol |
| `UC-TASK-07` | ver backlog | Todos los autenticados | Listar tareas en backlog priorizadas |

---

## Sprint

| Código | Caso de Uso | Actor | Descripción |
|--------|-------------|-------|-------------|
| `UC-SPR-01` | crear sprint | Jefe de Proyecto, Jefe de Área, Admin, Super Admin | Crear sprint en un proyecto |
| `UC-SPR-02` | iniciar sprint | Jefe de Proyecto, Jefe de Área, Admin, Super Admin | Activar sprint planificado |
| `UC-SPR-03` | completar sprint | Jefe de Proyecto, Jefe de Área, Admin, Super Admin | Finalizar sprint y mover tareas incompletas a backlog |
| `UC-SPR-04` | ver sprints | Todos los autenticados | Listar sprints según el rol |

---

## Área

| Código | Caso de Uso | Actor | Descripción |
|--------|-------------|-------|-------------|
| `UC-AREA-01` | crear área | Admin, Super Admin | Crear área organizacional |
| `UC-AREA-02` | editar área | Admin, Super Admin | Modificar área existente |
| `UC-AREA-03` | eliminar área | Admin, Super Admin | Eliminar área |
| `UC-AREA-04` | ver áreas | Todos los autenticados | Listar áreas según el rol |

---

## Especialidad

| Código | Caso de Uso | Actor | Descripción |
|--------|-------------|-------|-------------|
| `UC-SPEC-01` | crear especialidad | Admin, Super Admin | Crear especialidad técnica |
| `UC-SPEC-02` | editar especialidad | Admin, Super Admin | Modificar especialidad |
| `UC-SPEC-03` | eliminar especialidad | Admin, Super Admin | Eliminar especialidad |

---

## Cliente

| Código | Caso de Uso | Actor | Descripción |
|--------|-------------|-------|-------------|
| `UC-CLI-01` | crear cliente | Admin, Super Admin | Crear cliente |
| `UC-CLI-02` | editar cliente | Admin, Super Admin | Modificar cliente |
| `UC-CLI-03` | eliminar cliente | Admin, Super Admin | Eliminar cliente |
| `UC-CLI-04` | ver clientes | Todos los autenticados | Listar clientes según el rol |

---

## Documento

| Código | Caso de Uso | Actor | Descripción |
|--------|-------------|-------|-------------|
| `UC-DOC-01` | subir documento | Jefe de Proyecto, Miembro, Jefe de Área, Admin, Super Admin | Subir archivo a proyecto |
| `UC-DOC-02` | eliminar documento | Jefe de Proyecto, Miembro, Jefe de Área, Admin, Super Admin | Eliminar archivo de proyecto |
| `UC-DOC-03` | ver documentos | Todos los autenticados | Listar documentos según el rol |

---

## Sustitución

| Código | Caso de Uso | Actor | Descripción |
|--------|-------------|-------|-------------|
| `UC-SUB-01` | crear sustitución | Jefe de Área, Admin, Super Admin | Asignar un suplente temporal |
| `UC-SUB-02` | desactivar sustitución | Jefe de Área, Admin, Super Admin | Finalizar una suplencia activa |
| `UC-SUB-03` | ver sustituciones | Jefe de Área, Admin, Super Admin | Listar suplencias activas y pasadas |

---

## Solicitud de Servicio

| Código | Caso de Uso | Actor | Descripción |
|--------|-------------|-------|-------------|
| `UC-SRV-01` | crear solicitud de servicio | Jefe de Área, Admin, Super Admin | Crear solicitud para un cliente |
| `UC-SRV-02` | editar solicitud de servicio | Jefe de Área, Admin, Super Admin | Actualizar estado o asignación |
| `UC-SRV-03` | eliminar solicitud de servicio | Jefe de Área, Admin, Super Admin | Eliminar solicitud |
| `UC-SRV-04` | ver solicitudes de servicio | Jefe de Área, Jefe de Proyecto, Miembro, Admin, Super Admin | Listar solicitudes según el rol |

---

## Generales

| Código | Caso de Uso | Actor | Descripción |
|--------|-------------|-------|-------------|
| `UC-GEN-01` | ver dashboard | Usuario autenticado | Panel principal con estadísticas por rol |
| `UC-GEN-02` | ver tablero Kanban | Todos los autenticados | Tablero con drag-and-drop |
| `UC-GEN-03` | ver calendario | Todos los autenticados | Calendario de sprints |
| `UC-GEN-04` | registrar tiempo | Todos los autenticados | Seguimiento de tiempo por tarea |
| `UC-GEN-05` | ver notificaciones | Usuario autenticado | Lista de notificaciones |
| `UC-GEN-06` | ver reportes | Todos los autenticados | Reportes por estado, tipo y prioridad |
| `UC-GEN-07` | ver auditoría | Admin, Super Admin | Auditoría completa del sistema |
| `UC-GEN-08` | buscar | Usuario autenticado | Búsqueda global |
| `UC-GEN-09` | ver configuración | Usuario autenticado | Preferencias de usuario |
