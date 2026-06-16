from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.shortcuts import render

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.presentation.urls')),
    path('robots.txt', lambda r: HttpResponse(
        'User-agent: *\nDisallow: /admin/\nDisallow: /pending/\nDisallow: /ver_auditoria/\nSitemap: https://127.0.0.1/sitemap.xml\n',
        content_type='text/plain'
    )),
    path('sitemap.xml', lambda r: HttpResponse(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        '<url><loc>https://127.0.0.1/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>\n'
        '<url><loc>https://127.0.0.1/ver_proyectos/</loc><changefreq>daily</changefreq><priority>0.8</priority></url>\n'
        '<url><loc>https://127.0.0.1/ver_tablero/</loc><changefreq>always</changefreq><priority>0.9</priority></url>\n'
        '<url><loc>https://127.0.0.1/ver_backlog/</loc><changefreq>daily</changefreq><priority>0.7</priority></url>\n'
        '<url><loc>https://127.0.0.1/ver_sprints/</loc><changefreq>daily</changefreq><priority>0.8</priority></url>\n'
        '<url><loc>https://127.0.0.1/ver_equipo/</loc><changefreq>weekly</changefreq><priority>0.6</priority></url>\n'
        '<url><loc>https://127.0.0.1/ver_servicios/</loc><changefreq>weekly</changefreq><priority>0.5</priority></url>\n'
        '</urlset>',
        content_type='application/xml'
    )),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


handler400 = 'apps.core.presentation.views.error_views.handler400'
handler403 = 'apps.core.presentation.views.error_views.handler403'
handler404 = 'apps.core.presentation.views.error_views.handler404'
handler500 = 'apps.core.presentation.views.error_views.handler500'
