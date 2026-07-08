import json
import logging
import os

import requests
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)

DEEPSEEK_API_URL = 'https://api.deepseek.com/v1/chat/completions'
DEEPSEEK_MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')

SYSTEM_PROMPT = """Eres Winnie AI Assistant, un asistente inteligente integrado en Winnie, 
una plataforma de gestion de proyectos Scrum para consultoras de desarrollo de software.

Tu funcion es ayudar a los usuarios con:
- Gestion de proyectos, sprints, backlog y tablero Kanban
- Asignacion de tareas y seguimiento de tiempo
- Revision de candidatos y proceso de reclutamiento
- Reportes, metricas y auditoria
- Configuracion del sistema

Responde en español, de forma clara y concisa. Si no sabes algo, dilo honestamente.
Usa formato Markdown cuando sea util (listas, negritas, codigo)."""


@require_POST
@login_required
def winnie_ai_chat(request):
    try:
        body = json.loads(request.body.decode('utf-8'))
        messages = body.get('messages', [])

        if not messages:
            return JsonResponse({'error': 'messages es requerido'}, status=400)

        api_key = os.getenv('DEEPSEEK_API_KEY')
        if not api_key:
            return JsonResponse({'error': 'API key no configurada'}, status=500)

        full_messages = [
            {'role': 'system', 'content': SYSTEM_PROMPT},
        ] + messages[-20:]

        payload = {
            'model': DEEPSEEK_MODEL,
            'messages': full_messages,
            'temperature': 0.7,
            'max_tokens': 1000,
            'stream': False,
        }

        resp = requests.post(
            DEEPSEEK_API_URL,
            json=payload,
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            timeout=45,
        )
        resp.raise_for_status()
        data = resp.json()
        assistant_message = data['choices'][0]['message']

        return JsonResponse({
            'message': {
                'role': 'assistant',
                'content': assistant_message['content'],
            }
        })

    except requests.Timeout:
        return JsonResponse({'error': 'Timeout al contactar DeepSeek'}, status=504)
    except requests.RequestException as e:
        logger.error(f'DeepSeek error: {e}')
        return JsonResponse({'error': 'Error al comunicarse con el asistente'}, status=502)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON invalido en la solicitud'}, status=400)
    except Exception as e:
        logger.exception(f'AI chat error: {e}')
        return JsonResponse({'error': 'Error interno'}, status=500)
