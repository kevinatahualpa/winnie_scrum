"""Diagnostico de conexion a Cloudflare R2 (almacenamiento de archivos).

Sube un archivo temporal, lo lee, muestra su URL publica y lo borra.
No deja basura en el bucket.

Uso:
    python manage.py check_r2
"""
import datetime

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Verifica la conexion con el almacenamiento de archivos (Cloudflare R2).'

    def handle(self, *args, **options):
        self.stdout.write('Backend de storage: %s' % type(default_storage).__name__)
        self.stdout.write('Bucket: %s' % (settings.AWS_STORAGE_BUCKET_NAME or '(vacio)'))
        self.stdout.write('Endpoint: %s' % (settings.AWS_S3_ENDPOINT_URL or '(vacio)'))

        name = 'diagnostico/check_r2_%s.txt' % datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        contenido = b'check_r2 - prueba de conexion Winnie'

        try:
            saved = default_storage.save(name, ContentFile(contenido))
            self.stdout.write(self.style.SUCCESS('1) Subida OK -> %s' % saved))

            if not default_storage.exists(saved):
                raise RuntimeError('El archivo subido no existe en el bucket.')
            self.stdout.write(self.style.SUCCESS('2) Existe en bucket OK'))

            with default_storage.open(saved) as f:
                data = f.read()
            if data != contenido:
                raise RuntimeError('El contenido leido no coincide con el subido.')
            self.stdout.write(self.style.SUCCESS('3) Lectura OK (%d bytes)' % len(data)))

            self.stdout.write('4) URL publica -> %s' % default_storage.url(saved))

            default_storage.delete(saved)
            if default_storage.exists(saved):
                raise RuntimeError('El archivo no se pudo borrar.')
            self.stdout.write(self.style.SUCCESS('5) Borrado OK'))

            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('==> CONEXION A CLOUDFLARE R2: FUNCIONANDO'))
        except Exception as exc:
            self.stderr.write(self.style.ERROR('==> ERROR DE CONEXION: %s' % exc))
            raise
