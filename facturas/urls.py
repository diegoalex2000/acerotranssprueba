from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', views.facturas, name='facturas'),
    path('guardar_factura/', views.guardar_factura, name='guardar_factura'),
    path('get_vehiculos_propietario/<int:propietario_id>/', views.get_vehiculos_propietario, name='get_vehiculos_propietario'),
    path('detalle_factura_view/<int:codigo_fac>/', views.detalle_factura_view, name='detalle_factura_view'),
    path('actualizarFacturaPagado/<int:codigo_fac>/', views.actualizarFacturaPagado, name='actualizarFacturaPagado'),
    path('prueba_factura', views.facturas2, name='facturas2'),
    
    
   
]

# Sirve archivos estáticos solo en la primera ruta
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)