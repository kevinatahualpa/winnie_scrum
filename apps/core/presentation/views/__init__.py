from .auth_views import iniciar_sesion, cerrar_sesion, registrarse
from .archived_views import ver_archivados, restaurar
from .dashboard_views import ver_dashboard
from .project_views import ver_proyectos, ver_detalle_proyecto, crear_proyecto, editar_proyecto, eliminar_proyecto, comentar_proyecto
from .task_views import crear_tarea, editar_tarea, eliminar_tarea, actualizar_estado_tarea, comentar_tarea
from .sprint_views import ver_sprints, crear_sprint, iniciar_sprint, completar_sprint
from .team_views import ver_equipo, registrar_usuario, editar_usuario, desactivar_usuario, reactivar_usuario, ver_equipo_desactivados
from .area_views import ver_areas, crear_area, editar_area, eliminar_area
from .specialty_views import ver_especialidades, crear_especialidad, editar_especialidad, eliminar_especialidad
from .technology_views import ver_tecnologias, crear_tecnologia, editar_tecnologia, eliminar_tecnologia
from .client_views import ver_clientes, crear_cliente, editar_cliente, eliminar_cliente
from .service_views import ver_servicios, crear_servicio, editar_servicio, eliminar_servicio
from .board_views import ver_tablero
from .backlog_views import ver_backlog
from .document_views import ver_documentos, subir_documento, eliminar_documento, subir_documento_proyecto, eliminar_documento_proyecto
from .time_tracking_views import ver_tiempo, registrar_tiempo
from .calendar_views import ver_calendario
from .report_views import ver_reportes
from .audit_views import ver_auditoria
from .profile_views import ver_perfil
from .notification_views import ver_notificaciones, marcar_notificacion_leida, marcar_todas_leidas
from .search_views import buscar
from .substitution_views import ver_suplencias, crear_suplencia, desactivar_suplencia
from .registration_views import ver_pendientes, aprobar_registro, rechazar_registro
from .settings_views import ver_configuracion
from .health_views import verificar_salud, verificar_disponibilidad
from .message_views import ver_mensajes, ver_conversacion, enviar_mensaje, buscar_usuarios
from .client_portal_views import ver_portal_cliente, ver_detalle_proyecto_cliente, crear_solicitud_cliente
from .project_views import gestionar_miembros_proyecto

__all__ = [
    'iniciar_sesion', 'cerrar_sesion', 'registrarse',
    'ver_archivados', 'restaurar',
    'ver_dashboard',
    'ver_proyectos', 'ver_detalle_proyecto', 'crear_proyecto', 'editar_proyecto', 'eliminar_proyecto', 'comentar_proyecto',
    'crear_tarea', 'editar_tarea', 'eliminar_tarea', 'actualizar_estado_tarea', 'comentar_tarea',
    'ver_sprints', 'crear_sprint', 'iniciar_sprint', 'completar_sprint',
    'ver_equipo', 'registrar_usuario', 'editar_usuario', 'desactivar_usuario', 'reactivar_usuario', 'ver_equipo_desactivados',
    'ver_areas', 'crear_area', 'editar_area', 'eliminar_area',
    'ver_especialidades', 'crear_especialidad', 'editar_especialidad', 'eliminar_especialidad',
    'ver_tecnologias', 'crear_tecnologia', 'editar_tecnologia', 'eliminar_tecnologia',
    'ver_clientes', 'crear_cliente', 'editar_cliente', 'eliminar_cliente',
    'ver_servicios', 'crear_servicio', 'editar_servicio', 'eliminar_servicio',
    'ver_tablero',
    'ver_backlog',
    'ver_documentos', 'subir_documento', 'eliminar_documento', 'subir_documento_proyecto', 'eliminar_documento_proyecto',
    'ver_tiempo', 'registrar_tiempo',
    'ver_calendario',
    'ver_reportes',
    'ver_auditoria',
    'ver_perfil',
    'ver_notificaciones', 'marcar_notificacion_leida', 'marcar_todas_leidas',
    'buscar',
    'ver_suplencias', 'crear_suplencia', 'desactivar_suplencia',
    'ver_pendientes', 'aprobar_registro', 'rechazar_registro',
    'ver_configuracion',
    'verificar_salud', 'verificar_disponibilidad',
    'ver_mensajes', 'ver_conversacion', 'enviar_mensaje', 'buscar_usuarios',
    'ver_portal_cliente', 'ver_detalle_proyecto_cliente', 'crear_solicitud_cliente',
]
