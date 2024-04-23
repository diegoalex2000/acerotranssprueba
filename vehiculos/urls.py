from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', views.vehiculos, name='vehiculos'),
    path('agregar_vehiculo/', views.agregar_vehiculo, name='agregar_vehiculo'),
    path('eliminar_vehiculo_logico/<int:vehiculo_id>', views.eliminar_vehiculo_logico, name='eliminar_vehiculo_logico'),
    path('obtener_vehiculo/<int:vehiculoId>', views.obtener_vehiculo, name='obtener_vehiculo'),
    path('editar_vehiculo/', views.editar_vehiculo, name='editar_vehiculo'),
    path('validar_placa_edicion/', views.validar_placa_edicion, name='validar_placa_edicion'),
    
    
    
    
   
]

# Sirve archivos estáticos solo en la primera ruta
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)