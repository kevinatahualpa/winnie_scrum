# Proceso 01 — Identidad y Acceso

Secuencia oficial de cómo un visitante externo se convierte en un miembro
activo del equipo Winnie, ordenada de mayor a menor privilegio y de
fuera hacia adentro del sistema.

Inspirado en los flujos de LinkedIn (wizard por pasos), Trello (preview
de tarjeta) y Notion (auto-servicio sin intervención manual innecesaria).

---

## 1. Actores y jerarquía

```
┌──────────────────────────────────────────────────────────────────────┐
│  super-admin         →  ve todo, asigna roles elevados, configura    │
│  admin               →  aprueba candidatos, gestiona recursos       │
│  jefe-area           →  gestiona proyectos de su area               │
│  jefe-proyecto       →  gestiona proyectos que lidera               │
│  miembro             →  trabaja en sus tareas                       │
│  cliente             →  portal read-only de sus proyectos           │
│  observer            →  lectura global sin edicion                  │
└──────────────────────────────────────────────────────────────────────┘
         ▲
         │  (candidato en transicion)
         │
   ┌─────────────┐
   │  Candidato  │  estado: pending   (aun no tiene rol)
   └─────────────┘
```

Solo `super-admin` y `admin` participan en este proceso. El resto
recibe al usuario ya activado.

---

## 2. Secuencia del proceso

### Vista del candidato (visitante externo)

| # | Actor              | Pantalla                         | Accion                                                |
|---|--------------------|----------------------------------|-------------------------------------------------------|
| 1 | Visitante          | `/iniciar_sesion/`               | Click pestana **Solicitar Acceso**                    |
| 2 | Visitante          | `/registro/` (Paso 1 de 3)       | Email, contraseña, nombre, apellido, acepta terminos  |
| 3 | Sistema            | (sesion)                         | Valida email duplicado, longitud de password, etc.    |
| 4 | Visitante          | `/registro/paso-2/` (Paso 2 de 3)| Headline, bio, años, LinkedIn, GitHub, especialidad   |
| 5 | Visitante          | `/registro/paso-3/` (Paso 3 de 3)| Busca tecnologia, marca nivel (basico→experto), CV     |
| 6 | Sistema            | (transaccion atomica)            | Crea User + UserProfile(pending) + CandidateProfile   |
| 7 | Sistema            | (notificaciones)                 | Avisa a TODOS los super-admin y admin activos         |
| 8 | Visitante          | `/iniciar_sesion/`               | Ve mensaje: "espera aprobacion"                       |

**Estado resultante**: el candidato NO puede iniciar sesion todavia
(`auth_views.py:28-30` bloquea login si `status='pending'`).

### Vista del admin (revisor)

| #  | Actor        | Pantalla              | Accion                                                       |
|----|--------------|-----------------------|--------------------------------------------------------------|
| 9  | super-admin  | `/iniciar_sesion/`    | Login con credenciales                                       |
| 10 | super-admin  | `/` (dashboard)       | Ve badge con pendientes en topbar                            |
| 11 | super-admin  | `/ver_pendientes/`    | Ve cards con: nombre, titular, especialidad, techs, boton CV |
| 12 | super-admin  | (modal)               | Asigna rol, area, especialidad, notas internas              |
| 13 | Sistema      | (transaccion)         | Activa UserProfile, guarda notas en CandidateProfile         |
| 14 | Sistema      | (notificacion)        | Email al candidato: "fuiste aprobado como <rol>"            |
| 15 | Candidato    | (su email)            | Inicia sesion y entra al dashboard segun su rol             |

### Estados que se mueven

```
Visitante ──wizard──> User(pending)
                        │
                        ├── admin aprueba ──> User(active, role=miembro) ──> Login
                        │
                        └── admin rechaza ─> User(eliminado) + audit log
```

---

## 3. Modelos de datos

### `auth_user` (Django)
`username = email`, `first_name`, `last_name`, `password` (hasheado).

### `core_userprofile`
| Campo    | Tipo   | Valor inicial | Valor al aprobar                  |
|----------|--------|---------------|-----------------------------------|
| role     | str    | `miembro`     | `miembro`/`jefe-proyecto`/etc.   |
| status   | str    | `pending`     | `active`                          |
| area     | FK     | null          | asignada por admin (opcional)     |
| specialty| FK     | null          | sugerida por la declarada         |

### `core_candidateprofile` (nuevo)
| Campo                | Descripcion                                            |
|----------------------|--------------------------------------------------------|
| headline             | "Backend Developer con 3 años en Django"               |
| bio                  | Resumen libre                                          |
| years_experience     | Entero 0-50                                            |
| portfolio_url        | URL opcional                                           |
| linkedin_url         | URL opcional                                           |
| github_url           | URL opcional                                           |
| cv_file              | FileField (PDF/DOC/DOCX, max 5MB)                      |
| primary_specialty    | FK a Specialty (la que mejor domina)                   |
| secondary_specialties| M2M a Specialty (las que también maneja)               |
| technologies         | M2M via `CandidateTechnology` con nivel y años         |
| submitted_at         | auto_now_add                                           |
| reviewed_at/by       | se llena al aprobar                                    |
| review_notes         | notas internas del admin                               |

### `core_technology` (nuevo)
Catalogo fijo de la empresa: 53 tecnologias pre-cargadas por
`seed_technologies`. El admin no las marca al aprobar — el candidato
ya lo hizo en el wizard.

### `core_candidatetechnology` (through)
| Campo        | Tipo   | Rango                  |
|--------------|--------|------------------------|
| technology   | FK     | tecnologia declarada   |
| level        | 1-4    | Basico/Intermedio/Avanzado/Experto |
| years_using  | int    | años de experiencia    |

---

## 4. URLs del proceso

| URL                            | Vista                          | Quien         |
|--------------------------------|--------------------------------|---------------|
| `/iniciar_sesion/`             | `iniciar_sesion`               | publico       |
| `/registro/`                   | `registro_paso1`               | publico       |
| `/registro/paso-2/`            | `registro_paso2`               | publico       |
| `/registro/paso-3/`            | `registro_paso3`               | publico       |
| `/registro/cancelar/`          | `registro_cancelar`            | publico       |
| `/ver_pendientes/`             | `ver_pendientes`               | admin         |
| `/pending/<pk>/approve/`       | `aprobar_registro`             | admin         |
| `/pending/<pk>/reject/`        | `rechazar_registro`            | admin         |
| `/pending/<pk>/review/`        | `candidato_detalle` (drawer)   | admin         |
| `/pending/<pk>/checklist/`     | `candidato_save_checklist` AJAX| admin         |
| `/pending/<pk>/decidir/`       | `candidato_decidir` AJAX       | admin         |
| `/pending/<pk>/cv/`            | `cv_embed` (PDF para iframe)   | admin         |

---

## 5. Validaciones

**Paso 1 (datos)**:
- email formato valido
- password >= 8 caracteres
- password_confirm == password
- email no registrado
- checkbox terminos aceptado

**Paso 2 (perfil)**:
- years_experience entre 0 y 50
- URLs con formato valido (opcionales)
- primary_specialty del catalogo (opcional)

**Paso 3 (skills + CV)**:
- tecnologias del catalogo activo
- level entre 1 y 4
- CV: extension .pdf/.doc/.docx y <= 5MB

**Aprobacion**:
- solo super-admin puede asignar rol `super-admin` o `admin`
- solo admin+ puede aprobar/rechazar
- audited: cada accion queda en `core_auditlog`

---

## 6. Notificaciones generadas

| Evento                  | recipients              | type                    |
|-------------------------|-------------------------|-------------------------|
| Registro completado     | todos los super-admin/admin activos | `new_registration`     |
| Registro aprobado       | el candidato            | `registration_approved` |
| Registro rechazado      | el candidato            | `registration_rejected` |

---

## 7. Comandos utiles

```bash
# Cargar/actualizar catalogo de tecnologias
python manage.py seed_technologies

# Cargar datos demo (incluye 4 areas, 15 specialties, 8 clientes, ...)
python manage.py seed
```

---

## 8. Decisiones de diseno

- **Wizard en sesion, no en BBDD**: nada se persiste hasta el paso 3.
  Si el candidato cierra la pestaña, no quedan registros huerfanos.
- **Transaccion atomica en paso 3**: si falla cualquier cosa (CV, techs,
  perfil), no se crea User. Consistencia total.
- **Tecnologias pre-cargadas**: la empresa controla el stack. El admin
  no tiene que evaluar "que sabe Python?", eso ya lo declaro el
  candidato.
- **Sugerencia automatica**: al aprobar, el modal pre-selecciona la
  `primary_specialty` que el candidato declaro. El admin solo confirma.
- **Tono del candidato**: el wizard no usa palabras como "postular" o
  "aplicar" — usa "solicitar acceso" y "registrar skills", porque
  Winnie es un sistema interno, no un ATS externo.

---

## 9. Validacion manual del CV

El admin revisa el CV embebido en el PDF viewer a la derecha del drawer
y marca manualmente los 4 checks de validacion:

| Check              | Criterio                                                              |
|--------------------|-----------------------------------------------------------------------|
| `cv_coherente`     | El CV describe las tecnologias y nivel que el candidato declaro       |
| `experiencia`      | Los anos de experiencia declarados son consistentes con el CV         |
| `tecnologias`      | Las tecnologias marcadas como Avanzado/Experto son plausibles         |
| `documentacion`    | Hay certificados, titulos u otra documentacion que respalde el perfil |

### Score y aprobacion

- Minimo para aprobar: **3/4 checks** marcados como validos
- El admin tambien puede escribir una nota interna libre

### Persistencia

- Cada cambio se guarda via AJAX en `core_candidateprofile.review_checklist`
  (JSONField) con `{value, confidence: 100, evidence: 'Marcado manualmente'}`
- El `checklist_score` lleva el conteo de checks validados
- La nota se guarda en `review_notes`
