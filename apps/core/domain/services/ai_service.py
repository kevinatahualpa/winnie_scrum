"""Servicio de inteligencia artificial para revision de candidatos.

Usa la API de DeepSeek para analizar perfiles de postulantes y generar
recomendaciones para el revisor (admin). Extrae texto del CV (PDF)
para verificar que la informacion declarada coincida con el CV real.
"""

import json
import logging
import os

import fitz  # PyMuPDF
import requests

logger = logging.getLogger(__name__)

DEEPSEEK_API_URL = 'https://api.deepseek.com/v1/chat/completions'
DEEPSEEK_MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
MAX_CV_CHARS = 4000  # maximo caracteres del CV a incluir en el prompt

SYSTEM_PROMPT = """Eres un asistente de RRHH para Winnie, una consultora de desarrollo de software.
Analiza el perfil del candidato y su CV, verificando que la informacion declarada en el formulario sea consistente con lo que dice su CV.

Evalua estos 4 puntos del checklist de validacion:

1. cv_coherente: El CV describe las tecnologias y nivel que el candidato declaro.
2. experiencia: Los años de experiencia declarados son plausibles segun el CV.
3. tecnologias: Las tecnologias marcadas como Avanzado/Experto tienen respaldo en el CV.
4. documentacion: Hay evidencia en el CV de certificados, titulos u otra documentacion que respalde el perfil.

Para cada punto, asigna true si pasa la validacion o false si no.

Indica si hay discrepancias entre el formulario y el CV (ej: el formulario dice "Avanzado en React" pero el CV no menciona React, o viceversa).

Devuelve SOLO un JSON valido con esta estructura exacta (sin markdown, sin texto extra):
{
  "summary": "resumen breve del perfil",
  "strengths": ["fortaleza 1", "fortaleza 2"],
  "discrepancies": ["discrepancia 1 entre formulario y CV"] o [],
  "checklist": {
    "cv_coherente": true/false,
    "experiencia": true/false,
    "tecnologias": true/false,
    "documentacion": true/false
  },
  "suggested_area": "area sugerida o null",
  "role_recommendation": "miembro/jefe-proyecto/jefe-area o null",
  "comment": "comentario sugerido para el reclutador"
}"""


def _extract_cv_text(candidate) -> str:
    """Extrae texto del archivo CV PDF del candidato.

    Args:
        candidate: instancia de CandidateProfile con cv_file

    Returns:
        str con el texto extraido (max MAX_CV_CHARS caracteres), o cadena vacia si no hay CV.
    """
    if not candidate or not candidate.cv_file:
        return ''

    try:
        cv = candidate.cv_file
        # Abrir desde el storage (local o R2)
        cv.open('rb')
        doc = fitz.open(stream=cv.read(), filetype='pdf')
        text_parts = []
        total = 0
        for page in doc:
            page_text = page.get_text()
            if total + len(page_text) > MAX_CV_CHARS:
                remaining = MAX_CV_CHARS - total
                if remaining > 0:
                    text_parts.append(page_text[:remaining])
                break
            text_parts.append(page_text)
            total += len(page_text)
        doc.close()
        return '\n'.join(text_parts).strip()
    except Exception as e:
        logger.warning(f'No se pudo extraer texto del CV: {e}')
        return ''


def _call_deepseek(messages: list) -> dict:
    """Llama a la API de DeepSeek y devuelve el mensaje del asistente."""
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        raise ValueError('DEEPSEEK_API_KEY no configurada')

    payload = {
        'model': DEEPSEEK_MODEL,
        'messages': messages,
        'temperature': 0.3,
        'max_tokens': 700,
        'stream': False,
    }
    resp = requests.post(
        DEEPSEEK_API_URL,
        json=payload,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        timeout=40,
    )
    resp.raise_for_status()
    data = resp.json()
    return data['choices'][0]['message']


def _parse_ai_response(content: str) -> dict:
    """Parsea la respuesta JSON de DeepSeek, con fallback."""
    try:
        content = content.strip()
        if content.startswith('```'):
            content = content.split('\n', 1)[1]
            if content.endswith('```'):
                content = content[:-3]
        return json.loads(content)
    except (json.JSONDecodeError, ValueError):
        logger.warning(f'No se pudo parsear respuesta IA: {content[:200]}')
        return {
            'summary': 'No se pudo generar el analisis.',
            'strengths': [],
            'discrepancies': [],
            'checklist': {},
            'suggested_area': None,
            'role_recommendation': None,
            'comment': '',
        }


def analyze_candidate(candidate) -> dict:
    """Analiza un CandidateProfile (incluyendo CV) y devuelve recomendaciones.

    Args:
        candidate: instancia de CandidateProfile con relaciones precargadas
                   (.user, .primary_specialty, .candidatetechnology_set, .cv_file)

    Returns:
        dict con summary, strengths, discrepancies, suggested_area,
        role_recommendation, comment
    """
    user = candidate.user

    # Construir perfil en texto
    name = user.get_full_name() or user.username
    specialty = candidate.primary_specialty.name if candidate.primary_specialty else 'No definida'
    years = candidate.years_experience or 0
    bio = (candidate.bio or '')[:300]

    techs = []
    for ct in candidate.candidatetechnology_set.all():
        techs.append(f"{ct.technology.name} ({ct.get_level_display()})")
    techs_str = ', '.join(techs) if techs else 'No declaradas'

    links = []
    if candidate.portfolio_url:
        links.append(f"Portfolio: {candidate.portfolio_url}")
    if candidate.linkedin_url:
        links.append(f"LinkedIn: {candidate.linkedin_url}")
    if candidate.github_url:
        links.append(f"GitHub: {candidate.github_url}")
    links_str = ', '.join(links) if links else 'Ninguno'

    # Extraer texto del CV
    cv_text = _extract_cv_text(candidate)

    user_message = f"""Analiza este candidato para Winnie:

Nombre: {name}
Especialidad declarada: {specialty}
Años de experiencia declarados: {years}
Tecnologias declaradas: {techs_str}
Links: {links_str}
Bio: {bio or 'No proporcionada'}

{f'--- CV (texto extraido, primeras {MAX_CV_CHARS} caracteres) ---'
 if cv_text else '--- CV: NO ADJUNTO ---'}

{cv_text if cv_text else '(Sin CV disponible para verificar)'}"""

    try:
        message = _call_deepseek([
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': user_message},
        ])
        return _parse_ai_response(message['content'])
    except Exception as e:
        logger.exception(f'Error al llamar a DeepSeek: {e}')
        return {
            'summary': f'Error al analizar: {str(e)[:100]}',
            'strengths': [],
            'discrepancies': [],
            'checklist': {},
            'suggested_area': None,
            'role_recommendation': None,
            'comment': '',
        }
