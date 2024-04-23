from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', views.categorias, name='categorias'),
    path('agregar_categoria/', views.agregar_categoria, name='agregar_categoria'),
    path('validar_tipo_categoria/', views.validar_tipo_categoria, name='validar_tipo_categoria'),
    path('eliminar_categoria_logico/<int:categoria_id>', views.eliminar_categoria_logico, name='eliminar_categoria_logico'),
    path('obtener_categorias/<int:categoriaId>', views.obtener_categorias, name='obtener_categorias'),
    path('editar_categorias/', views.editar_categorias, name='editar_categorias'),
    path('validar_tipo_categoria_editar/', views.validar_tipo_categoria_editar, name='validar_tipo_categoria_editar'),
   
]

# Sirve archivos estáticos solo en la primera ruta
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)