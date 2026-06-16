import xml.etree.ElementTree as ET
from xml.dom import minidom
import uuid

NS_XMI = "http://www.omg.org/spec/XMI/20110701"
NS_UML = "http://www.omg.org/spec/UML/20110701"

ET.register_namespace("xmi", NS_XMI)
ET.register_namespace("uml", NS_UML)

xmi = ET.Element(f"{{{NS_XMI}}}XMI")
xmi.set(f"{{{NS_XMI}}}version", "2.1")

doc = ET.SubElement(xmi, f"{{{NS_XMI}}}Documentation")
exporter = ET.SubElement(doc, f"{{{NS_XMI}}}exporter")
exporter.text = "Winnie"
exporter_ver = ET.SubElement(doc, f"{{{NS_XMI}}}exporterVersion")
exporter_ver.text = "1.0"

model = ET.SubElement(xmi, f"{{{NS_UML}}}Model")
model.set(f"{{{NS_XMI}}}id", str(uuid.uuid4()))
model.set("name", "Casos de Uso Winnie")

ownedElement = ET.SubElement(model, f"{{{NS_UML}}}Namespace.ownedElement")

# ── ACTORS ──
actor_defs = {
    "super_admin": "Super Admin",
    "admin": "Admin",
    "jefe_area": "Jefe de Area",
    "jefe_proyecto": "Jefe de Proyecto",
    "miembro": "Miembro",
    "no_auth": "Usuario no autenticado",
}
actor_ids = {}
for k, name in actor_defs.items():
    aid = "ACT_" + str(uuid.uuid4()).replace("-", "_")
    actor_ids[k] = aid
    a = ET.SubElement(ownedElement, f"{{{NS_UML}}}Actor")
    a.set(f"{{{NS_XMI}}}id", aid)
    a.set("name", name)

# ── USE CASES ──
uc_list = [
    ("no_auth", "iniciar sesion"),
    ("no_auth", "registrarse"),
    ("super_admin,admin,jefe_area,jefe_proyecto,miembro", "cerrar sesion"),
    ("super_admin,admin", "registrar usuario"),
    ("super_admin,admin", "editar usuario"),
    ("super_admin,admin", "eliminar usuario"),
    ("super_admin,admin", "ver registros pendientes"),
    ("super_admin,admin", "aprobar registro"),
    ("super_admin,admin", "rechazar registro"),
    ("super_admin,admin,jefe_area,jefe_proyecto,miembro", "ver perfil"),
    ("super_admin,admin,jefe_area", "crear proyecto"),
    ("super_admin,admin,jefe_area,jefe_proyecto", "editar proyecto"),
    ("super_admin,admin,jefe_area,jefe_proyecto", "eliminar proyecto"),
    ("super_admin,admin,jefe_area,jefe_proyecto,miembro", "ver proyectos"),
    ("super_admin,admin,jefe_area,jefe_proyecto", "crear tarea"),
    ("super_admin,admin,jefe_area,jefe_proyecto,miembro", "editar tarea"),
    ("super_admin,admin,jefe_area,jefe_proyecto,miembro", "eliminar tarea"),
    ("super_admin,admin,jefe_area,jefe_proyecto,miembro", "actualizar estado tarea"),
    ("super_admin,admin,jefe_area,jefe_proyecto,miembro", "comentar tarea"),
    ("super_admin,admin,jefe_area,jefe_proyecto,miembro", "ver tareas"),
    ("super_admin,admin,jefe_area,jefe_proyecto,miembro", "ver backlog"),
    ("super_admin,admin,jefe_area,jefe_proyecto", "crear sprint"),
    ("super_admin,admin,jefe_area,jefe_proyecto", "iniciar sprint"),
    ("super_admin,admin,jefe_area,jefe_proyecto", "completar sprint"),
    ("super_admin,admin,jefe_area,jefe_proyecto,miembro", "ver sprints"),
    ("super_admin,admin", "crear area"),
    ("super_admin,admin", "editar area"),
    ("super_admin,admin", "eliminar area"),
    ("super_admin,admin,jefe_area,jefe_proyecto,miembro", "ver areas"),
    ("super_admin,admin", "crear especialidad"),
    ("super_admin,admin", "editar especialidad"),
    ("super_admin,admin", "eliminar especialidad"),
    ("super_admin,admin", "crear cliente"),
    ("super_admin,admin", "editar cliente"),
    ("super_admin,admin", "eliminar cliente"),
    ("super_admin,admin,jefe_area,jefe_proyecto,miembro", "ver clientes"),
    ("super_admin,admin,jefe_area,jefe_proyecto,miembro", "subir documento"),
    ("super_admin,admin,jefe_area,jefe_proyecto,miembro", "eliminar documento"),
    ("super_admin,admin,jefe_area,jefe_proyecto,miembro", "ver documentos"),
    ("super_admin,admin,jefe_area", "crear suplencia"),
    ("super_admin,admin,jefe_area", "desactivar suplencia"),
    ("super_admin,admin,jefe_area", "ver suplencias"),
    ("super_admin,admin,jefe_area", "crear solicitud de servicio"),
    ("super_admin,admin,jefe_area", "editar solicitud de servicio"),
    ("super_admin,admin,jefe_area", "eliminar solicitud de servicio"),
    ("super_admin,admin,jefe_area,jefe_proyecto,miembro", "ver solicitudes de servicio"),
    ("super_admin,admin,jefe_area,jefe_proyecto,miembro", "ver dashboard"),
    ("super_admin,admin,jefe_area,jefe_proyecto,miembro", "ver tablero Kanban"),
    ("super_admin,admin,jefe_area,jefe_proyecto,miembro", "ver calendario"),
    ("super_admin,admin,jefe_area,jefe_proyecto,miembro", "registrar tiempo"),
    ("super_admin,admin,jefe_area,jefe_proyecto,miembro", "ver notificaciones"),
    ("super_admin,admin,jefe_area,jefe_proyecto,miembro", "ver reportes"),
    ("super_admin,admin", "ver auditoria"),
    ("super_admin,admin,jefe_area,jefe_proyecto,miembro", "buscar"),
    ("super_admin,admin,jefe_area,jefe_proyecto,miembro", "ver configuracion"),
]

for actors_str, uc_name in uc_list:
    uid = "UC_" + str(uuid.uuid4()).replace("-", "_")
    uc_elem = ET.SubElement(ownedElement, f"{{{NS_UML}}}UseCase")
    uc_elem.set(f"{{{NS_XMI}}}id", uid)
    uc_elem.set("name", uc_name)
    
    for actor_key in actors_str.split(","):
        assoc_id = "AS_" + str(uuid.uuid4()).replace("-", "_")
        assoc = ET.SubElement(ownedElement, f"{{{NS_UML}}}Association")
        assoc.set(f"{{{NS_XMI}}}id", assoc_id)
        
        end1_id = "END_" + str(uuid.uuid4()).replace("-", "_")
        end1 = ET.SubElement(assoc, f"{{{NS_UML}}}Association.connection")
        end1_prop = ET.SubElement(end1, f"{{{NS_UML}}}AssociationEnd")
        end1_prop.set(f"{{{NS_XMI}}}id", end1_id)
        end1_prop.set("type", actor_ids[actor_key])
        end1_prop.set("isNavigable", "true")
        
        end2_id = "END_" + str(uuid.uuid4()).replace("-", "_")
        end2 = ET.SubElement(assoc, f"{{{NS_UML}}}Association.connection")
        end2_prop = ET.SubElement(end2, f"{{{NS_UML}}}AssociationEnd")
        end2_prop.set(f"{{{NS_XMI}}}id", end2_id)
        end2_prop.set("type", uid)
        end2_prop.set("isNavigable", "true")

xml_str = ET.tostring(xmi, encoding="unicode")
dom = minidom.parseString(xml_str)
pretty = dom.toprettyxml(indent="  ")

output = "/home/rusitos/Downloads/Scrum_hackthony/docs/casos_de_uso.xmi"
with open(output, "w", encoding="utf-8") as f:
    f.write(pretty)

print(f"XMI 1.4 generated: {len(actor_defs)} actors, {len(uc_list)} use cases")
