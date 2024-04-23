from django.shortcuts import render, redirect
from django.db import connection
from django.http import JsonResponse
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

def vehiculos(request):
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
                    WHERE v.estado_veh <> 3 ;")

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

            return render(request, 'administracion/vehiculos/index.html', context)
    else:
        return HttpResponseNotFound('error')


def agregar_vehiculo(request):
    if request.method == 'POST':
        dueño_id = request.POST.get('dueño_veh')
        placa = request.POST.get('placa_veh')
        tonelaje = request.POST.get('tonelaje_veh')
        estado = request.POST.get('estado_veh')
        categoria = request.POST.get('categoria_veh')

        try:
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO vehiculos (fk_codigo_usu, placa_veh, tonelaje_veh, estado_veh, fk_codigo_cat) VALUES (%s, %s, %s, %s, %s)",
                               [dueño_id, placa, tonelaje, estado, categoria])
        except IntegrityError as e:
            # Maneja el error de integridad, por ejemplo, si hay una violación de clave única
            # Puedes redirigir a una página de error o mostrar un mensaje al usuario
         
            messages.add_message(request, messages.ERROR, 'Error al agregar el vehículo: {}'.format(str(e)))


        messages.add_message(request, messages.SUCCESS, 'Vehiculo Agregado con éxito')
        return redirect('vehiculos')  # Redirige a alguna página después de agregar el vehículo


def eliminar_vehiculo_logico(request, vehiculo_id):
    try:
        
        with connection.cursor() as cursor:
             # Consulta para eliminar al usuario
            cursor.execute("UPDATE  VEHICULOS SET estado_veh=3 WHERE codigo_veh = %s", (vehiculo_id,))
            connection.commit()

        # Cerrar el cursor y la conexión
            cursor.close()
            connection.close()

            messages.add_message(request, messages.SUCCESS, 'Registro eliminado con exito')

        return redirect('vehiculos')
        #mensaje = f'Usuario eliminado y la imagen asociada también fue eliminada. Ruta de la imagen eliminada: {ruta_imagen_absoluta}'
        #return HttpResponseNotFound(mensaje)

    except Exception as e:
        # Mensaje de error
        messages.add_message(request, messages.ERROR, f'Error al eliminar registro, posibles dependencias. {e}')
        
        return redirect('vehiculos')
    
def obtener_vehiculo(request, vehiculoId):
    try:
        with connection.cursor() as cursor:
            # Ejecutar la consulta SQL para obtener los datos del usuario por su ID
            cursor.execute("SELECT codigo_veh, placa_veh, tonelaje_veh, estado_veh, fk_codigo_usu, fk_codigo_cat FROM vehiculos WHERE codigo_veh = %s", [vehiculoId])
            vehiculo_data = cursor.fetchone()

            if vehiculo_data:
                # Crear un diccionario con los datos del usuario
                vehiculo = {
                    
                    'codigo': vehiculo_data[0],
                    'placa': vehiculo_data[1],
                    'tonelaje': vehiculo_data[2],
                    'estado': vehiculo_data[3],
                    'cod_usu': vehiculo_data[4],
                    'cod_cat': vehiculo_data[5],
                   
                    # Agrega otros campos del usuario si es necesario
                }
                # Devolver los datos del usuario en formato JSON
                return JsonResponse(vehiculo)
            else:
                return JsonResponse({'error': 'Vehiculo no encontrado'}, status=404)

    except Exception as e:
        # Manejar otros errores si es necesario
        return JsonResponse({'error': str(e)}, status=500)
    
def editar_vehiculo(request):
    if request.method == 'POST':
        vehiculo_id = request.POST.get('edit_vehiculo_id')
        print(vehiculo_id)
        dueño = request.POST.get('edit_dueño_veh')
        categoria = request.POST.get('edit_categoria_veh')
        placa = request.POST.get('edit_placa_veh')
        tonelaje = request.POST.get('edit_tonelaje_veh')
        estado = request.POST.get('edit_estado_veh')

        with connection.cursor() as cursor:
            # Ejecutar la consulta SQL para actualizar el vehículo
            cursor.execute(
                "UPDATE vehiculos SET fk_codigo_usu = %s, fk_codigo_cat = %s, placa_veh = %s, tonelaje_veh = %s, estado_veh = %s WHERE codigo_veh = %s",
                [dueño, categoria, placa, tonelaje, estado, vehiculo_id]
            )

        messages.add_message(request, messages.SUCCESS, 'Registro actualizado con éxito')
        return redirect(vehiculos)
    else:
        messages.add_message(request, messages.ERROR, 'Ocurrio un error, intenta de nuevo')
        return redirect(vehiculos)
    
def validar_placa_edicion(request):
    try:
        placa = request.POST.get('edit_placa_veh')
        print(placa)
        codigo_veh = request.POST.get('codigo')
        print('codigo: ' + str(codigo_veh))  # Asegúrate de convertir 'codigo' a cadena si esperas imprimirlo como tal
        
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) AS count FROM vehiculos WHERE placa_veh = %s AND codigo_veh != %s", [placa, codigo_veh])
        
        row = cursor.fetchone()
        
        if row and row[0] > 0:
            return JsonResponse(False, safe=False)
        else:
            return JsonResponse(True, safe=False)
    except Exception as e:
        # Manejo de excepciones
        print(str(e))
        return JsonResponse({'error': str(e)}, status=500)
