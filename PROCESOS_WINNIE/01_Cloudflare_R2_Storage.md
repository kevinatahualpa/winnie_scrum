# Parte 1: Cloudflare R2 Storage para archivos multimedia

**Objetivo:** Migrar el almacenamiento de archivos (media) de disco local a Cloudflare R2 (S3-compatible).

---

## 1. Crear Bucket en Cloudflare R2

1. Entrar a Cloudflare Dashboard
2. Menú lateral → **R2 Object Storage**
3. Click **"Create bucket"**
4. Nombre: `winnie-media-hackthony`
5. **Enable Public Access** (para URLs públicas)

---

## 2. Configurar CORS

En Settings del bucket → CORS Policy:

```json
[
  {
    "AllowedOrigins": [
      "http://localhost:8000",
      "http://127.0.0.1:8000"
    ],
    "AllowedMethods": [
      "GET",
      "PUT",
      "POST",
      "HEAD"
    ],
    "AllowedHeaders": ["*"],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3000
  }
]
```

---

## 3. Crear API Token

1. R2 → **"Manage R2 API Tokens"**
2. **User API Tokens** → **"Create API Token"**
3. Nombre: `winnie-django`
4. Permisos: `Object Read & Write`
5. Bucket específico: `winnie-media-hackthony`
6. TTL: sin límite

**Copiar los 4 valores** (el Secret se muestra una sola vez):

| Valor | Descripción |
|---|---|
| Account ID | ID de la cuenta Cloudflare |
| Access Key ID | Como un usuario |
| Secret Access Key | Como una contraseña |
| Endpoint URL | `https://<account-id>.r2.cloudflarestorage.com` |

URL pública `r2.dev` del bucket (aparece en Settings del bucket).

---

## 4. Guardar credenciales en `.env`

```
R2_ACCESS_KEY_ID=c9111d84eb8607cf403fa73928fafbc9
R2_SECRET_ACCESS_KEY=ca005cdb1d2f639d59857e0ede8e6cc73a071719c98a1466e096c0b5c3476dec
R2_ENDPOINT_URL=https://29de26df8e79a4bd6ead57dcf138da04.r2.cloudflarestorage.com
R2_BUCKET_NAME=winnie-media-hackthony
R2_PUBLIC_URL=https://pub-069cf22e3b994ff890598d2754897279.r2.dev
```

---

## 5. Instalar dependencias

Agregar a `requirements.txt`:

```
boto3>=1.34,<2.0
django-storages[s3]>=1.14,<2.0
```

Instalar:

```bash
pip install boto3 "django-storages[s3]"
```

---

## 6. Configurar Django

### `config/settings/base.py`

```python
# En INSTALLED_APPS agregar 'storages'
INSTALLED_APPS = [
    ...
    'storages',
    ...
]

# STORAGES
STORAGES = {
    "default": {
        "BACKEND": "apps.core.infrastructure.storage.MediaStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Cloudflare R2 (S3-compatible)
AWS_ACCESS_KEY_ID = os.getenv('R2_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('R2_SECRET_ACCESS_KEY')
AWS_S3_ENDPOINT_URL = os.getenv('R2_ENDPOINT_URL')
AWS_STORAGE_BUCKET_NAME = os.getenv('R2_BUCKET_NAME')
AWS_S3_REGION_NAME = 'auto'
AWS_S3_SIGNATURE_VERSION = 's3v4'
AWS_S3_ADDRESSING_STYLE = 'virtual'
AWS_QUERYSTRING_AUTH = False
AWS_S3_CUSTOM_DOMAIN = os.getenv('R2_PUBLIC_URL', '').replace('https://', '')
```

### `apps/core/infrastructure/storage.py` (NUEVO)

```python
from storages.backends.s3boto3 import S3Boto3Storage

class MediaStorage(S3Boto3Storage):
    pass
```

---

## 7. Migrar archivos existentes

Subir los archivos locales de `media/` a R2:

```python
from apps.core.infrastructure.storage import MediaStorage
storage = MediaStorage()

for local_file in Path('media').rglob('*'):
    if local_file.is_file():
        storage.save(str(local_file.relative_to('media')), open(local_file, 'rb'))
```

---

## 8. Fix: Sidebar avatar

En `sidebar.html`, el footer solo mostraba iniciales. Se cambió para mostrar la foto si `user.profile.avatar` existe:

```django
{% if user.profile.avatar %}
<img src="{{ user.profile.avatar.url }}" ...>
{% else %}
<div ...>{{ user.first_name|first }}{{ user.last_name|first }}</div>
{% endif %}
```

---

## Resultado

- Archivos nuevos se guardan automáticamente en R2
- Archivos viejos fueron migrados
- URLs de archivos usan el dominio público `r2.dev`
- Avatares se muestran en sidebar, perfil, mensajes, proyectos, etc.

---

**Fecha:** 2026-06-18
