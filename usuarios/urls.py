from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.usuarios, name='usuarios'),
    path('agregar_usuario/', views.agregar_usuario, name='agregar_usuario'),
    path('eliminar_usuario_logico/<int:usuario_id>/', views.eliminar_usuario_logico, name='eliminar_usuario_logico'),
    path('obtener_usuario/<int:usuario_id>/', views.obtener_usuario, name='obtener_usuario'),
    path('actualizar_usuario/', views.actualizar_usuario, name='actualizar_usuario'),
    path('validar_cedula/', views.validar_cedula, name='validar_cedula'),
    path('validar_correo/', views.validar_correo, name='validar_correo'),
    path('validar_cedula_edicion/', views.validar_cedula_edicion, name='validar_cedula_edicion'),
    path('validar_correo_edicion/', views.validar_correo_edicion, name='validar_correo_edicion'),
    path('obtener_vehiculos_usuario/<int:usuario_id>/', views.obtener_vehiculos_usuario, name='obtener_vehiculos_usuario'),

    
    
    
    
]

# Sirve archivos estáticos solo en la primera ruta
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)