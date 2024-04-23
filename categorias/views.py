from django.shortcuts import render, redirect
from django.db import connection
from django.http import HttpResponseBadRequest, HttpResponseServerError, JsonResponse
from django.conf import settings
from datetime import datetime
import os
import psycopg2
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseNotFound, HttpResponseRedirect
from django.db.utils import IntegrityError  # Importa la excepción de integridad de la base de datos si estás utilizando claves únicas o restricciones similares



def get_user_data(user_id):
    with connection.cursor() as cursor:
        cursor.execute("SELECT nombre_usu, apellido_usu, rol_usu, path_usu FROM usuario WHERE codigo_usu = %s", [user_id])
        user_data = cursor.fetchone()
    if user_data:
        user_name = user_data[0]
        last_name = user_data[1]
        perfil_name = user_data[2]
        path_name = user_data[3]
        full_path_name = os.path.join(settings.UPLOADS_DIR, path_name)
        return user_name, last_name, perfil_name, path_name
    return None

def categorias(request):
    if 'codigo_usu' in request.session:
        user_id = request.session['codigo_usu']
        user_data = get_user_data(user_id)
        if user_data:
            user_name, last_name, perfil_name, path_name = user_data

            # Consulta para obtener las categorías
            with connection.cursor() as cursor:
                cursor.execute("SELECT codigo_cat, tipo_cat, estado_cat FROM categorias where estado_cat <> 3;")
                categorias_data = cursor.fetchall()

            # Crear una lista para almacenar los datos de las categorías
            categorias = []
            for row in categorias_data:
                categoria = {
                    'codigo': row[0],
                    'tipo': row[1],
                    'estado': row[2],
                }
                categorias.append(categoria)

            # Contexto con los datos de las categorías y los usuarios
            context = {
                'user_name': user_name,
                'last_name': last_name,
                'perfil_name': perfil_name,
                'path_name': path_name,
                'categorias': categorias,
            }

            return render(request, 'administracion/categorias/index.html', context)
    else:
        return HttpResponseNotFound('error') 

def agregar_categoria(request):
    if request.method == 'POST':
        tipo_cat = request.POST.get('tipo_cat')
        estado_cat = request.POST.get('estado_cat')

        if tipo_cat and estado_cat:
            with connection.cursor() as cursor:
                try:
                    cursor.execute("INSERT INTO categorias (tipo_cat, estado_cat) VALUES (%s, %s);", [tipo_cat, estado_cat])
                    # Realizar commit para guardar los cambios en la base de datos
                    connection.commit()
                    # Redirigir o mostrar un mensaje de éxito
                    messages.add_message(request, messages.SUCCESS, 'Categoría Agregada con exito')
                    return redirect('categorias')
                except Exception as e:
                    # Manejar errores, como violaciones de integridad o errores de base de datos
                     messages.add_message(request, messages.ERROR, 'Error al agregar la categoria'+ str(e))
                     return redirect('categorias')
                    

    # Si la solicitud no es POST o faltan parámetros, mostrar un error
    messages.add_message(request, messages.ERROR, 'Parámetros Faltantes')
    return redirect('categorias')

def validar_tipo_categoria(request):
    if request.method == 'POST':
        tipo_cat = request.POST.get('tipo_cat')

        # Consultar la base de datos para verificar si el tipo de categoría ya existe
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM categorias WHERE tipo_cat = %s", [tipo_cat])
            count = cursor.fetchone()[0]

        # Verificar el resultado de la consulta
        if count > 0:
            return JsonResponse(False, safe=False)
        else:
            return JsonResponse(True, safe=False)

    # Si la solicitud no es AJAX o no es POST, devolver un error
    return JsonResponse({'error': 'Invalid request'}, status=400)

def eliminar_categoria_logico(request, categoria_id):
    try:
        with connection.cursor() as cursor:

            # Consulta para verificar si la categoría tiene vehículos relacionados
            cursor.execute("SELECT COUNT(*) FROM vehiculos WHERE fk_codigo_cat = %s", [categoria_id])
            vehiculos_relacionados = cursor.fetchone()[0]

            # Si hay vehículos relacionados, mostrar mensaje de error y redirigir
            if vehiculos_relacionados > 0:
                messages.add_message(request, messages.ERROR, 'No se puede eliminar la categoría porque existen vehículos relacionados con esta categoría.')
                return redirect('categorias')

            # Si no hay vehículos relacionados, proceder con la eliminación lógica de la categoría
            cursor.execute("UPDATE CATEGORIAS SET estado_cat=3 WHERE codigo_cat = %s", [categoria_id])
            connection.commit()

            # Cerrar la conexión
            connection.close()

            messages.add_message(request, messages.SUCCESS, 'Registro eliminado con éxito')
            return redirect('categorias')

    except Exception as e:
        # Mensaje de error
        messages.add_message(request, messages.ERROR, f'Error al eliminar registro, posibles dependencias. {e}')
        return redirect('categorias')
    
def obtener_categorias(request, categoriaId):
    try:
        with connection.cursor() as cursor:
            # Ejecutar la consulta SQL para obtener los datos del usuario por su ID
            cursor.execute("SELECT codigo_cat, tipo_cat, estado_cat FROM categorias WHERE codigo_cat = %s", [categoriaId])
            categoria_data = cursor.fetchone()

            if categoria_data:
                # Crear un diccionario con los datos del usuario
                categorias = {
                    
                    'codigo': categoria_data[0],
                    'tipo': categoria_data[1],
                    'estado': categoria_data[2],
                  
                }
                # Devolver los datos del usuario en formato JSON
                return JsonResponse(categorias)
            else:
                return JsonResponse({'error': 'Categoria no encontrada'}, status=404)

    except Exception as e:
        # Manejar otros errores si es necesario
        return JsonResponse({'error': str(e)}, status=500)
    
def editar_categorias(request):
    if request.method == 'POST':
        codigo = request.POST.get('edit_categoria_id')
        print(codigo)
        tipo = request.POST.get('edit_tipo_cat')
        estado = request.POST.get('edit_estado_cat')
       

        with connection.cursor() as cursor:
            # Ejecutar la consulta SQL para actualizar el vehículo
            cursor.execute(
                "UPDATE categorias SET tipo_cat= %s, estado_cat = %s WHERE codigo_cat = %s",
                [tipo, estado, codigo]
            )

        messages.add_message(request, messages.SUCCESS, 'Registro actualizado con éxito')
        return redirect(categorias)
    else:
        messages.add_message(request, messages.ERROR, 'Ocurrio un error, intenta de nuevo')
        return redirect(categorias)
    
# def validar_placa_edicion(request):
#     try:
#         placa = request.POST.get('edit_placa_veh')
#         print(placa)
#         codigo_veh = request.POST.get('codigo')
#         print('codigo: ' + str(codigo_veh))  # Asegúrate de convertir 'codigo' a cadena si esperas imprimirlo como tal
        
#         cursor = connection.cursor()
#         cursor.execute("SELECT COUNT(*) AS count FROM vehiculos WHERE placa_veh = %s AND codigo_veh != %s", [placa, codigo_veh])
        
#         row = cursor.fetchone()
        
#         if row and row[0] > 0:
#             return JsonResponse(False, safe=False)
#         else:
#             return JsonResponse(True, safe=False)
#     except Exception as e:
#         # Manejo de excepciones
#         print(str(e))
#         return JsonResponse({'error': str(e)}, status=500)

def validar_tipo_categoria_editar(request):
    if request.method == 'POST':
        tipo_cat = request.POST.get('tipo_cat')
        categoria_id = request.POST.get('categoria_id')
        print(tipo_cat)
        print(categoria_id)
        # Consultar la base de datos para verificar si el tipo de categoría ya existe
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM categorias WHERE tipo_cat = %s and codigo_cat != %s ", [tipo_cat, categoria_id])
            count = cursor.fetchone()[0]

        # Verificar el resultado de la consulta
        if count > 0:
            return JsonResponse(False, safe=False)
        else:
            return JsonResponse(True, safe=False)

    # Si la solicitud no es AJAX o no es POST, devolver un error
    return JsonResponse({'error': 'Invalid request'}, status=400)


 