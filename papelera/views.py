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

def papelera(request):
    if 'codigo_usu' in request.session:
        user_id = request.session['codigo_usu']
        user_data = get_user_data(user_id)
        if user_data:
            user_name, last_name, perfil_name, path_name = user_data

            # Contexto con los datos del usuario
            context = {
                'user_name': user_name,
                'last_name': last_name,
                'perfil_name': perfil_name,
                'path_name': path_name
            }

            return render(request, 'administracion/papelera/index.html', context)
    else:
        return HttpResponseNotFound('error')
    
# def vehiculos_mostrar(request):
    
#      if 'codigo_usu' in request.session:
#         user_id = request.session['codigo_usu']
#         user_data = get_user_data(user_id)
#         if user_data:
#             user_name, last_name, perfil_name, path_name = user_data

#             # Contexto con los datos del usuario
#             context = {
#                 'user_name': user_name,
#                 'last_name': last_name,
#                 'perfil_name': perfil_name,
#                 'path_name': path_name
#             }

#             return render(request, 'administracion/papelera/vehiculos_papelera.html', context)
#      else:
#         return HttpResponseNotFound('error')
    
def vehiculos_borrados(request):
    if 'codigo_usu' in request.session:
        user_id = request.session['codigo_usu']
        user_data = get_user_data(user_id)
        if user_data:
            user_name, last_name, perfil_name, path_name = user_data

            # Consulta para obtener los vehículos
            with connection.cursor() as cursor:
                cursor.execute("SELECT v.codigo_veh, v.placa_veh, v.tonelaje_veh, v.estado_veh, c.nombre_usu, c.apellido_usu, c.codigo_usu, cat.codigo_cat, cat.tipo_cat \
                    FROM vehiculos v \
                    INNER JOIN usuario c ON v.fk_codigo_usu = c.codigo_usu \
                    INNER JOIN categorias cat ON v.fk_codigo_cat = cat.codigo_cat\
                    WHERE v.estado_veh=3;")

                vehiculos_data = cursor.fetchall()

            # Consulta para obtener los usuarios
            with connection.cursor() as cursor:
                cursor.execute("SELECT codigo_usu, nombre_usu, apellido_usu FROM usuario where estado_usu=1;")
                usuarios_data = cursor.fetchall()

            # Consulta para obtener las categorías
            with connection.cursor() as cursor:
                cursor.execute("SELECT codigo_cat, tipo_cat, estado_cat FROM categorias where estado_cat=1;")
                categorias_data = cursor.fetchall()

            # Crear una lista para almacenar los datos de los vehículos
            vehiculos = []
            for row in vehiculos_data:
                vehiculo = {  
                    'codigo': row[0],
                    'placa': row[1],
                    'tonelaje': row[2],
                    'estado': row[3],
                    'usuario_nombre': row[4],
                    'usuario_apellido': row[5],
                    'fkcodigo': row[6],
                    'categoria_codigo': row[7],
                    'categoria_tipo': row[8],
                }
                vehiculos.append(vehiculo)

            # Crear una lista para almacenar los datos de los usuarios
            usuarios = []
            for row in usuarios_data:
                usuario = {
                    'codigo': row[0],
                    'nombre': row[1],
                    'apellido': row[2],
                }
                usuarios.append(usuario)

            # Crear una lista para almacenar los datos de las categorías
            categorias = []
            for row in categorias_data:
                categoria = {
                    'codigo': row[0],
                    'tipo': row[1],
                    'estado': row[2],
                }
                categorias.append(categoria)

            context = {
                'user_name': user_name,
                'last_name': last_name,
                'perfil_name': perfil_name,
                'path_name': path_name,
                'vehiculos': vehiculos,
                'usuarios': usuarios,
                'categorias': categorias,
            }

            return render(request, 'administracion/papelera/vehiculos_papelera.html', context)
    else:
        return HttpResponseNotFound('error')
    
    

def recovery_vehiculos_logico(request, vehiculo_id):
    try:
        
        with connection.cursor() as cursor:
             # Consulta para eliminar al usuario
            cursor.execute("UPDATE  VEHICULOS SET estado_veh=1 WHERE codigo_veh = %s", (vehiculo_id,))
            connection.commit()

        # Cerrar el cursor y la conexión
            cursor.close()
            connection.close()

            messages.add_message(request, messages.SUCCESS, 'Registro recuperado con exito')

        return redirect('vehiculos_borrados')
        #mensaje = f'Usuario eliminado y la imagen asociada también fue eliminada. Ruta de la imagen eliminada: {ruta_imagen_absoluta}'
        #return HttpResponseNotFound(mensaje)

    except Exception as e:
        # Mensaje de error
        messages.add_message(request, messages.ERROR, f'Error al recuperar el registro, posibles dependencias. {e}')
        
        return redirect('vehiculos_borrados')
    
def eliminar_vehiculos_def(request, vehiculo_id):
    try:
 
        with connection.cursor() as cursor:
            
        # Consulta para eliminar al usuario
            cursor.execute("DELETE FROM vehiculos WHERE codigo_veh = %s", (vehiculo_id,))
            connection.commit()

        # Cerrar el cursor y la conexión
            cursor.close()
            connection.close()

            messages.add_message(request, messages.INFO, 'Registro eliminado de forma permanente con exito')

            return redirect('vehiculos_borrados')
        #mensaje = f'Usuario eliminado y la imagen asociada también fue eliminada. Ruta de la imagen eliminada: {ruta_imagen_absoluta}'
        #return HttpResponseNotFound(mensaje)
    except Exception as e:
        # Mensaje de error
        messages.add_message(request, messages.ERROR, f'Error al eliminar el registro: {str(e)}')
        
        return redirect('vehiculos_borrados')
    
def categorias_borrados(request):
    if 'codigo_usu' in request.session:
        user_id = request.session['codigo_usu']
        user_data = get_user_data(user_id)
        if user_data:
            user_name, last_name, perfil_name, path_name = user_data

            # Consulta para obtener las categorías borradas
            with connection.cursor() as cursor:
                cursor.execute("SELECT codigo_cat, tipo_cat, estado_cat FROM categorias where estado_cat=3;")
                categorias_data = cursor.fetchall()

            categorias = []
            for row in categorias_data:
                categoria = {  
                    'codigo': row[0],
                    'tipo': row[1],
                    'estado': row[2],
                }
                categorias.append(categoria)

            context = {
                'user_name': user_name,
                'last_name': last_name,
                'perfil_name': perfil_name,
                'path_name': path_name,
                'categorias': categorias,
            }

            return render(request, 'administracion/papelera/categorias_papelera.html', context)
    else:
        return HttpResponseNotFound('error')
    
def recovery_categorias_logico(request, categoria_id):
    try:
        with connection.cursor() as cursor:
            # Consulta para recuperar lógicamente la categoría
            cursor.execute("UPDATE  categorias SET estado_cat=1 WHERE codigo_cat = %s", (categoria_id,))
            connection.commit()

        # Cerrar el cursor y la conexión
        cursor.close()
        connection.close()

        messages.add_message(request, messages.SUCCESS, 'Categoría recuperada con éxito')

        return redirect('categorias_borrados')

    except Exception as e:
        # Mensaje de error
        messages.add_message(request, messages.ERROR, f'Error al recuperar la categoría, posibles dependencias. {e}')
        
        return redirect('categorias_borrados')

def eliminar_categorias_def(request, categoria_id):
    try:
        with connection.cursor() as cursor:
            # Consulta para eliminar definitivamente la categoría
            cursor.execute("DELETE FROM categorias WHERE codigo_cat = %s", (categoria_id,))
            connection.commit()

        # Cerrar el cursor y la conexión
        cursor.close()
        connection.close()

        messages.add_message(request, messages.INFO, 'Categoría eliminada de forma permanente con éxito')

        return redirect('categorias_borrados')

    except Exception as e:
        # Mensaje de error
        messages.add_message(request, messages.ERROR, f'Error al eliminar la categoría: {str(e)}')
        
        return redirect('categorias_borrados')
    
    
def usuarios_borrados(request):
    if 'codigo_usu' in request.session:
        user_id = request.session['codigo_usu']
        user_data = get_user_data(user_id)
        if user_data:
            user_name, last_name, perfil_name, path_name = user_data

            with connection.cursor() as cursor:
                cursor.execute("SELECT codigo_usu, nombre_usu, apellido_usu, identificacion_usu, estado_usu, path_usu, rol_usu, email_usu, telefono_usu FROM usuario where estado_usu =3")
                usuarios_data = cursor.fetchall()

            usuarios = []
            for row in usuarios_data:
                usuario = {
                    'codigo': row[0],
                    'nombre': row[1],
                    'apellido': row[2],
                    'cedula': row[3],
                    'estado': row[4],
                    'foto': row[5],  # Utilizar la ruta completa de la imagen
                    'rol': row[6],
                    'correo': row[7],
                    'telefono': row[8]
                }
                usuarios.append(usuario)

            context = {'user_name': user_name, 'last_name': last_name, 'perfil_name': perfil_name, 'path_name':path_name, 'usuarios': usuarios}
            return render(request, 'administracion/papelera/usuarios_papelera.html', context)
    else:
        return HttpResponseNotFound('error')  # Manejar el caso donde no hay un 'codigo_usu' en la sesión

def recovery_usuarios_logico(request, usuario_id):
    try:
        
        with connection.cursor() as cursor:
             # Consulta para eliminar al usuario
            cursor.execute("UPDATE  USUARIO SET estado_usu=1 WHERE codigo_usu = %s", (usuario_id,))
            connection.commit()

        # Cerrar el cursor y la conexión
            cursor.close()
            connection.close()

            messages.add_message(request, messages.SUCCESS, 'Registro recuperado con exito')

        return redirect('usuarios_borrados')
        #mensaje = f'Usuario eliminado y la imagen asociada también fue eliminada. Ruta de la imagen eliminada: {ruta_imagen_absoluta}'
        #return HttpResponseNotFound(mensaje)

    except Exception as e:
        # Mensaje de error
        messages.add_message(request, messages.ERROR, f'Error al recuperar el registro, posibles dependencias. {e}')
        
        return redirect('usuarios_borrados')

def eliminar_usuarios_def(request, usuario_id):
    try:
        # Realizar la conexión a la base de datos
        connection = psycopg2.connect(
            dbname=settings.DATABASES['default']['NAME'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT']
        )

        # Crear un cursor para ejecutar consultas
        cursor = connection.cursor()

        # Consulta para verificar si el usuario puede ser eliminado
        cursor.execute("SELECT path_usu FROM usuario WHERE codigo_usu = %s", (usuario_id,))
        resultado = cursor.fetchone()

        if resultado:
            foto_usuario = resultado[0]
            print("Nombre de archivo de la imagen:", foto_usuario)  # Agregar esta línea para verificar el nombre de archivo
            # Consulta para eliminar al usuario
            cursor.execute("DELETE FROM usuario WHERE codigo_usu = %s", (usuario_id,))
            connection.commit()
            # Eliminar la imagen asociada al usuario si existe
            ruta_imagen = os.path.join(settings.BASE_DIR, 'templates/assets/', foto_usuario)
            ruta_imagen_absoluta = os.path.abspath(ruta_imagen)
            print("Ruta de la imagen a eliminar:", ruta_imagen_absoluta)  # Agregar esta línea para verificar la ruta absoluta
            if os.path.exists(ruta_imagen_absoluta):
                os.remove(ruta_imagen_absoluta)
        
        # Cerrar el cursor y la conexión
        cursor.close()
        connection.close()

        messages.add_message(request, messages.SUCCESS, 'Registro eliminado con éxito')

        return redirect('usuarios_borrados')

    except Exception as e:
        # Mensaje de error
        messages.add_message(request, messages.ERROR, 'Error al eliminar usuario, posibles dependencias.')

        return redirect('usuarios_borrados')