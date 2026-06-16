import xml.etree.ElementTree as ET
from xml.dom import minidom
import uuid

NS_UML = "href://org.omg/UML/1.4"

ET.register_namespace("UML", NS_UML)

xmi = ET.Element("XMI")
xmi.set("xmi.version", "1.2")
xmi.set("xmlns:XMI", "http://www.omg.org/spec/XMI/20110701")

header = ET.SubElement(xmi, "XMI.header")
doc = ET.SubElement(header, "XMI.documentation")
exporter = ET.SubElement(doc, "XMI.exporter")
exporter.text = "Winnie"
exporter_ver = ET.SubElement(doc, "XMI.exporterVersion")
exporter_ver.text = "1.0"

content = ET.SubElement(xmi, "XMI.content")

model = ET.SubElement(content, f"{{{NS_UML}}}Model")
model.set("xmi.id", "M1")
model.set("name", "Casos de Uso Winnie")

owned = ET.SubElement(model, f"{{{NS_UML}}}Namespace.ownedElement")

# ── ACTORS ──
actor_defs = [
    ("super_admin", "Super Admin"),
    ("admin", "Admin"),
    ("jefe_area", "Jefe de Area"),
    ("jefe_proyecto", "Jefe de Proyecto"),
    ("miembro", "Miembro"),
    ("no_auth", "Usuario no autenticado"),
]
actor_ids = {}
for i, (k, name) in enumerate(actor_defs, 1):
    aid = f"A{i}"
    actor_ids[k] = aid
    a = ET.SubElement(owned, f"{{{NS_UML}}}Actor")
    a.set("xmi.id", aid)
    a.set("name", name)

# ── GENERALIZATIONS (role hierarchy) ──
gen_map = [
    ("miembro", "jefe_proyecto", "Z1"),
    ("jefe_proyecto", "jefe_area", "Z2"),
    ("jefe_area", "admin", "Z3"),
    ("admin", "super_admin", "Z4"),
]
for child, parent, gid in gen_map:
    gen = ET.SubElement(owned, f"{{{NS_UML}}}Generalization")
    gen.set("xmi.id", gid)
    gen.set("child", actor_ids[child])
    gen.set("parent", actor_ids[parent])

# ── USE CASES ──
uc_data = [
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

assoc_idx = 1
for i, (actors_str, uc_name) in enumerate(uc_data, 1):
    uid = f"UC{i}"
    uc_elem = ET.SubElement(owned, f"{{{NS_UML}}}UseCase")
    uc_elem.set("xmi.id", uid)
    uc_elem.set("name", uc_name)
    
    for actor_key in actors_str.split(","):
        aid = f"AS{assoc_idx}"
        assoc = ET.SubElement(owned, f"{{{NS_UML}}}Association")
        assoc.set("xmi.id", aid)
        
        conn = ET.SubElement(assoc, f"{{{NS_UML}}}Association.connection")
        end1 = ET.SubElement(conn, f"{{{NS_UML}}}AssociationEnd")
        end1.set("xmi.id", f"E{assoc_idx}.1")
        end1.set("type", actor_ids[actor_key])
        end1.set("isNavigable", "true")
        
        conn2 = ET.SubElement(assoc, f"{{{NS_UML}}}Association.connection")
        end2 = ET.SubElement(conn2, f"{{{NS_UML}}}AssociationEnd")
        end2.set("xmi.id", f"E{assoc_idx}.2")
        end2.set("type", uid)
        end2.set("isNavigable", "true")
        
        assoc_idx += 1

xml_str = ET.tostring(xmi, encoding="unicode")
dom = minidom.parseString(xml_str)
pretty = dom.toprettyxml(indent="  ")

output = "/home/rusitos/Downloads/Scrum_hackthony/docs/casos_de_uso.xmi"
with open(output, "w", encoding="utf-8") as f:
    f.write(pretty)

print(f"XMI 1.2 generated: {len(actor_defs)} actors, {len(uc_data)} use cases, {assoc_idx - 1} associations")
