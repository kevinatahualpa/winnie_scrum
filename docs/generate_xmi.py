import xml.etree.ElementTree as ET
from xml.dom import minidom
import uuid

def make_id():
    return str(uuid.uuid4())

# ---- DATA ----
actors = {
    "no_auth":    {"name": "Usuario no autenticado"},
    "miembro":    {"name": "Miembro"},
    "jefe_proyecto": {"name": "Jefe de Proyecto"},
    "jefe_area":  {"name": "Jefe de Area"},
    "admin":      {"name": "Admin"},
    "super_admin": {"name": "Super Admin"},
}

gen_parent = {
    "miembro": "jefe_proyecto",
    "jefe_proyecto": "jefe_area",
    "jefe_area": "admin",
    "admin": "super_admin",
}

use_cases_by_package = {
    "Autenticacion": [
        ("UC_AUTH_01", "iniciar sesion", ["no_auth"]),
        ("UC_AUTH_02", "registrarse", ["no_auth"]),
        ("UC_AUTH_03", "cerrar sesion", ["super_admin","admin","jefe_area","jefe_proyecto","miembro"]),
    ],
    "Usuario": [
        ("UC_USR_01", "registrar usuario", ["super_admin","admin"]),
        ("UC_USR_02", "editar usuario", ["super_admin","admin"]),
        ("UC_USR_03", "eliminar usuario", ["super_admin","admin"]),
        ("UC_USR_04", "ver registros pendientes", ["super_admin","admin"]),
        ("UC_USR_05", "aprobar registro", ["super_admin","admin"]),
        ("UC_USR_06", "rechazar registro", ["super_admin","admin"]),
        ("UC_USR_07", "ver perfil", ["super_admin","admin","jefe_area","jefe_proyecto","miembro"]),
    ],
    "Proyecto": [
        ("UC_PROJ_01", "crear proyecto", ["super_admin","admin","jefe_area"]),
        ("UC_PROJ_02", "editar proyecto", ["super_admin","admin","jefe_area","jefe_proyecto"]),
        ("UC_PROJ_03", "eliminar proyecto", ["super_admin","admin","jefe_area","jefe_proyecto"]),
        ("UC_PROJ_04", "ver proyectos", ["super_admin","admin","jefe_area","jefe_proyecto","miembro"]),
    ],
    "Tarea": [
        ("UC_TASK_01", "crear tarea", ["super_admin","admin","jefe_area","jefe_proyecto"]),
        ("UC_TASK_02", "editar tarea", ["super_admin","admin","jefe_area","jefe_proyecto","miembro"]),
        ("UC_TASK_03", "eliminar tarea", ["super_admin","admin","jefe_area","jefe_proyecto","miembro"]),
        ("UC_TASK_04", "actualizar estado tarea", ["super_admin","admin","jefe_area","jefe_proyecto","miembro"]),
        ("UC_TASK_05", "comentar tarea", ["super_admin","admin","jefe_area","jefe_proyecto","miembro"]),
        ("UC_TASK_06", "ver tareas", ["super_admin","admin","jefe_area","jefe_proyecto","miembro"]),
        ("UC_TASK_07", "ver backlog", ["super_admin","admin","jefe_area","jefe_proyecto","miembro"]),
    ],
    "Sprint": [
        ("UC_SPR_01", "crear sprint", ["super_admin","admin","jefe_area","jefe_proyecto"]),
        ("UC_SPR_02", "iniciar sprint", ["super_admin","admin","jefe_area","jefe_proyecto"]),
        ("UC_SPR_03", "completar sprint", ["super_admin","admin","jefe_area","jefe_proyecto"]),
        ("UC_SPR_04", "ver sprints", ["super_admin","admin","jefe_area","jefe_proyecto","miembro"]),
    ],
    "Area": [
        ("UC_AREA_01", "crear area", ["super_admin","admin"]),
        ("UC_AREA_02", "editar area", ["super_admin","admin"]),
        ("UC_AREA_03", "eliminar area", ["super_admin","admin"]),
        ("UC_AREA_04", "ver areas", ["super_admin","admin","jefe_area","jefe_proyecto","miembro"]),
    ],
    "Especialidad": [
        ("UC_SPEC_01", "crear especialidad", ["super_admin","admin"]),
        ("UC_SPEC_02", "editar especialidad", ["super_admin","admin"]),
        ("UC_SPEC_03", "eliminar especialidad", ["super_admin","admin"]),
    ],
    "Cliente": [
        ("UC_CLI_01", "crear cliente", ["super_admin","admin"]),
        ("UC_CLI_02", "editar cliente", ["super_admin","admin"]),
        ("UC_CLI_03", "eliminar cliente", ["super_admin","admin"]),
        ("UC_CLI_04", "ver clientes", ["super_admin","admin","jefe_area","jefe_proyecto","miembro"]),
    ],
    "Documento": [
        ("UC_DOC_01", "subir documento", ["super_admin","admin","jefe_area","jefe_proyecto","miembro"]),
        ("UC_DOC_02", "eliminar documento", ["super_admin","admin","jefe_area","jefe_proyecto","miembro"]),
        ("UC_DOC_03", "ver documentos", ["super_admin","admin","jefe_area","jefe_proyecto","miembro"]),
    ],
    "Suplencia": [
        ("UC_SUB_01", "crear suplencia", ["super_admin","admin","jefe_area"]),
        ("UC_SUB_02", "desactivar suplencia", ["super_admin","admin","jefe_area"]),
        ("UC_SUB_03", "ver suplencias", ["super_admin","admin","jefe_area"]),
    ],
    "Solicitud de Servicio": [
        ("UC_SRV_01", "crear solicitud de servicio", ["super_admin","admin","jefe_area"]),
        ("UC_SRV_02", "editar solicitud de servicio", ["super_admin","admin","jefe_area"]),
        ("UC_SRV_03", "eliminar solicitud de servicio", ["super_admin","admin","jefe_area"]),
        ("UC_SRV_04", "ver solicitudes de servicio", ["super_admin","admin","jefe_area","jefe_proyecto","miembro"]),
    ],
    "Generales": [
        ("UC_GEN_01", "ver dashboard", ["super_admin","admin","jefe_area","jefe_proyecto","miembro"]),
        ("UC_GEN_02", "ver tablero Kanban", ["super_admin","admin","jefe_area","jefe_proyecto","miembro"]),
        ("UC_GEN_03", "ver calendario", ["super_admin","admin","jefe_area","jefe_proyecto","miembro"]),
        ("UC_GEN_04", "registrar tiempo", ["super_admin","admin","jefe_area","jefe_proyecto","miembro"]),
        ("UC_GEN_05", "ver notificaciones", ["super_admin","admin","jefe_area","jefe_proyecto","miembro"]),
        ("UC_GEN_06", "ver reportes", ["super_admin","admin","jefe_area","jefe_proyecto","miembro"]),
        ("UC_GEN_07", "ver auditoria", ["super_admin","admin"]),
        ("UC_GEN_08", "buscar", ["super_admin","admin","jefe_area","jefe_proyecto","miembro"]),
        ("UC_GEN_09", "ver configuracion", ["super_admin","admin","jefe_area","jefe_proyecto","miembro"]),
    ],
}

# ---- XML BUILDING ----
NS_XMI = "http://www.omg.org/spec/XMI/20110701"
NS_UML = "http://www.omg.org/spec/UML/20110701"
NS_VP = "http://www.visual-paradigm.com/"

ET.register_namespace("xmi", NS_XMI)
ET.register_namespace("uml", NS_UML)
ET.register_namespace("vp", NS_VP)

xmi = ET.Element(f"{{{NS_XMI}}}XMI", attrib={
    f"{{{NS_XMI}}}version": "2.4.2",
})

model = ET.SubElement(xmi, f"{{{NS_UML}}}Model", attrib={
    f"{{{NS_XMI}}}id": make_id(),
    "name": "Casos de Uso Winnie",
})

# Actor definitions
actor_elements = {}
for key, info in actors.items():
    actor_id = make_id()
    actor_elem = ET.SubElement(model, f"{{{NS_UML}}}packagedElement",
                               attrib={f"{{{NS_XMI}}}type": "uml:Actor",
                                       f"{{{NS_XMI}}}id": actor_id,
                                       "name": info["name"]})
    actor_elements[key] = actor_id

# Actor generalizations (role hierarchy)
for child_key, parent_key in gen_parent.items():
    gen_id = make_id()
    gen_elem = ET.SubElement(model, f"{{{NS_UML}}}packagedElement",
                             attrib={f"{{{NS_XMI}}}type": "uml:Generalization",
                                     f"{{{NS_XMI}}}id": gen_id})
    ET.SubElement(gen_elem, f"{{{NS_UML}}}general",
                  attrib={f"{{{NS_XMI}}}idref": actor_elements[parent_key]})
    ET.SubElement(gen_elem, f"{{{NS_UML}}}specific",
                  attrib={f"{{{NS_XMI}}}idref": actor_elements[child_key]})

# Use Cases by package
use_case_ids = {}
association_ids = []
all_uc_refs = {}

for pkg_name, usecases in use_cases_by_package.items():
    pkg_id = make_id()
    pkg_elem = ET.SubElement(model, f"{{{NS_UML}}}packagedElement",
                             attrib={f"{{{NS_XMI}}}type": "uml:Package",
                                     f"{{{NS_XMI}}}id": pkg_id,
                                     "name": pkg_name})
    for uc_id_str, uc_name, actor_keys in usecases:
        uc_id = make_id()
        uc_elem = ET.SubElement(pkg_elem, f"{{{NS_UML}}}packagedElement",
                                attrib={f"{{{NS_XMI}}}type": "uml:UseCase",
                                        f"{{{NS_XMI}}}id": uc_id,
                                        "name": uc_name})
        use_case_ids[uc_id_str] = uc_id
        all_uc_refs[uc_id_str] = uc_id

        # Create Association from actor to this use case
        for actor_key in actor_keys:
            assoc_id = make_id()
            assoc_elem = ET.SubElement(model, f"{{{NS_UML}}}packagedElement",
                                       attrib={f"{{{NS_XMI}}}type": "uml:Association",
                                               f"{{{NS_XMI}}}id": assoc_id})
            # First end: actor
            end_id1 = make_id()
            end1 = ET.SubElement(assoc_elem, f"{{{NS_UML}}}memberEnd",
                                 attrib={f"{{{NS_XMI}}}id": end_id1})
            ET.SubElement(end1, f"{{{NS_UML}}}type",
                          attrib={f"{{{NS_XMI}}}idref": actor_elements[actor_key]})
            # Second end: use case
            end_id2 = make_id()
            end2 = ET.SubElement(assoc_elem, f"{{{NS_UML}}}memberEnd",
                                 attrib={f"{{{NS_XMI}}}id": end_id2})
            ET.SubElement(end2, f"{{{NS_UML}}}type",
                          attrib={f"{{{NS_XMI}}}idref": uc_id})
            association_ids.append(assoc_id)

# Pretty print
xml_str = ET.tostring(xmi, encoding="unicode")
dom = minidom.parseString(xml_str)
pretty = dom.toprettyxml(indent="  ")

with open("/home/rusitos/Downloads/Scrum_hackthony/docs/casos_de_uso.xmi", "w", encoding="utf-8") as f:
    f.write(pretty)

print(f"XMI generated: {len(actor_elements)} actors, {len(use_case_ids)} use cases, {len(association_ids)} associations")
