from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .views import administracion, index, iniciar_sesion

urlpatterns = [
    path('', index, name='index'),
    path('administracion/', administracion, name='administracion'),  # Asigna un nombre a esta URL
    
    path('iniciar_sesion/', iniciar_sesion, name='iniciar_sesion'),
   
    # Otras URLs de tu aplicación...
]

# Sirve archivos estáticos solo en la primera ruta
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
