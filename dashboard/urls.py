
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', views.dashboard, name = 'dashboard'),
    path('dashboard_general/', views.dashboard_general, name = 'dashboard_general'),
    path('dashboard_inversion/', views.dashboard_inversion, name = 'dashboard_inversion'),
    path('dashboard_socio_ajax/<int:socioId>/', views.dashboard_socio_ajax, name = 'dashboard_socio_ajax'),
    path('dashboard_socio/', views.dashboard_socio, name = 'dashboard_socio'),
    
]
#Sirve archivos estáticos solo en la primera ruta
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)