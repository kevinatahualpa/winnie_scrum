import os
import dj_database_url
from .base import *

DEBUG = False

SECRET_KEY = os.getenv('SECRET_KEY', os.getenv('DJANGO_SECRET_KEY'))

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

if os.getenv('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.config(conn_max_age=600, conn_health_checks=True)
    }

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = 'DENY'

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SECURE_CSP_DEFAULT_SRC = ("'self'",)
SECURE_CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net")
SECURE_CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net", "https://fonts.googleapis.com")
SECURE_CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com", "https://cdn.jsdelivr.net")
SECURE_CSP_IMG_SRC = ("'self'", "data:", "blob:", "https://pub-069cf22e3b994ff890598d2754897279.r2.dev")
SECURE_CSP_CONNECT_SRC = ("'self'",)
SECURE_CSP_FRAME_SRC = ("'self'",)
SECURE_CSP_OBJECT_SRC = ("'none'",)
