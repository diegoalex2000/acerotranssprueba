from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.papelera, name='papelera'),
    #path('vehiculos_mostrar/', views.vehiculos_mostrar, name='vehiculos_mostrar'),
    path('vehiculos_borrados/', views.vehiculos_borrados, name='vehiculos_borrados'),
    path('recovery_vehiculos_logico/<int:vehiculo_id>', views.recovery_vehiculos_logico, name='recovery_vehiculos_logico'),
    path('eliminar_vehiculos_def/<int:vehiculo_id>', views.eliminar_vehiculos_def, name='eliminar_vehiculos_def'),
    path('categorias_borrados/', views.categorias_borrados, name='categorias_borrados'),
    path('recovery_categorias_logico/<int:categoria_id>', views.recovery_categorias_logico, name='recovery_categorias_logico'),
    path('eliminar_categorias_def/<int:categoria_id>', views.eliminar_categorias_def, name='eliminar_categorias_def'),
    path('usuarios_borrados/', views.usuarios_borrados, name='usuarios_borrados'),
    path('recovery_usuarios_logico/<int:usuario_id>', views.recovery_usuarios_logico, name='recovery_usuarios_logico'),
    path('eliminar_usuarios_def/<int:usuario_id>', views.eliminar_usuarios_def, name='eliminar_usuarios_def'),
    
   
   
    # Otras URLs de tu aplicación...
]

# Sirve archivos estáticos solo en la primera ruta
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
