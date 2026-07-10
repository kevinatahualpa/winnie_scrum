"""Utilidades para validar archivos subidos por el usuario.

Django NO impone un limite de tamano a los FileField/ImageField por
defecto (FILE_UPLOAD_MAX_MEMORY_SIZE solo controla memoria vs disco, y
DATA_UPLOAD_MAX_MEMORY_SIZE excluye los campos de archivo). Por eso el
tamano y el tipo se validan explicitamente aqui.
"""

# Extensiones permitidas para imagenes (avatar, etc.)
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp'}

# Extensiones permitidas para adjuntos de chat.
CHAT_EXTENSIONS = {
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.txt', '.csv', '.zip', '.rar', '.7z',
    '.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp',
    '.mp4', '.avi', '.mov', '.mp3', '.wav',
    '.json', '.xml', '.md',
}

MB = 1024 * 1024


def _extension(filename):
    if filename and '.' in filename:
        return '.' + filename.rsplit('.', 1)[1].lower()
    return ''


def validate_upload(file, max_bytes, allowed_extensions):
    """Valida un archivo subido por tamano y extension.

    Retorna None si es valido, o un mensaje de error (str) si no lo es.
    """
    if file is None:
        return None

    ext = _extension(file.name)
    if ext not in allowed_extensions:
        permitidas = ', '.join(sorted(allowed_extensions))
        return f'Tipo de archivo no permitido ({ext or "sin extension"}). Permitidos: {permitidas}'

    if file.size > max_bytes:
        return (
            f'Archivo demasiado grande ({file.size / MB:.1f}MB). '
            f'Maximo: {max_bytes / MB:.0f}MB'
        )

    return None
