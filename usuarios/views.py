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



def usuarios(request):
    if 'codigo_usu' in request.session:
        user_id = request.session['codigo_usu']
        user_data = get_user_data(user_id)
        if user_data:
            user_name, last_name, perfil_name, path_name = user_data

            with connection.cursor() as cursor:
                cursor.execute("SELECT codigo_usu, nombre_usu, apellido_usu, identificacion_usu, estado_usu, path_usu, rol_usu, email_usu, telefono_usu FROM usuario where estado_usu <> 3")
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
            return render(request, 'administracion/usuarios/index.html', context)
    else:
        return HttpResponseNotFound('error')  # Manejar el caso donde no hay un 'codigo_usu' en la sesión


# Obtiene la fecha y hora actual
fecha_hora_actual = datetime.now().strftime("%Y%m%d%H%M%S")

def agregar_usuario(request):
    if request.method == 'POST':
        try:
            cedula_usu = request.POST.get('cedula_usu')
            nombre = request.POST.get('nombre')
            apellido_usu = request.POST.get('apellido_usu')
            telefono_usu = request.POST.get('telefono_usu')
            estado_usu = request.POST.get('estado_usu')
            email_usu = request.POST.get('email_usu')
            foto_usu = request.FILES.get('foto_usu')
            
            if foto_usu:
                fecha_hora_actual = datetime.now().strftime("%Y%m%d%H%M%S")
                nombre_archivo_con_fecha = f"{fecha_hora_actual}_{foto_usu.name}"

                ruta_foto = os.path.join( 'templates/assets/uploads/', nombre_archivo_con_fecha)
                para_save= os.path.join( 'uploads/', nombre_archivo_con_fecha)
                with open(ruta_foto, 'wb') as destino:
                    for chunk in foto_usu.chunks():
                        destino.write(chunk)
                
                connection = psycopg2.connect(
                    dbname=settings.DATABASES['default']['NAME'],
                    user=settings.DATABASES['default']['USER'],
                    password=settings.DATABASES['default']['PASSWORD'],
                    host=settings.DATABASES['default']['HOST'],
                    port=settings.DATABASES['default']['PORT']
                )
                cursor = connection.cursor()
                
                cursor.execute("""
                    INSERT INTO usuario (identificacion_usu, password_usu, rol_usu, nombre_usu, apellido_usu, telefono_usu, estado_usu, email_usu, path_usu)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (cedula_usu, cedula_usu,'TRANSPORTISTA', nombre, apellido_usu, telefono_usu, estado_usu, email_usu, para_save))
                
                connection.commit()
                messages.add_message(request, messages.SUCCESS, 'Registro Agregado con éxito')
                return redirect('usuarios')
        except Exception as e:
            messages.add_message(request, messages.ERROR, f'Error al agregar el usuario: {e}')
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'connection' in locals():
                connection.close()
            return redirect('usuarios')
    else:
        try:
            messages.add_message(request, messages.ERROR, 'Error al procesar la petición')
            return redirect('usuarios')
        except Exception as e:
            messages.add_message(request, messages.ERROR, f'Error al procesar la petición: {e}')
            return redirect('usuarios')
        
    
    

# def eliminar_usuario(request, usuario_id):
#     
def eliminar_usuario(request, usuario_id):
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

        # Consulta para obtener la ruta de la imagen del usuario
        cursor.execute("SELECT path_usu FROM usuario WHERE codigo_usu = %s", (usuario_id,))
        resultado = cursor.fetchone()
        if resultado:
            foto_usuario = resultado[0]
            print("Nombre de archivo de la imagen:", foto_usuario)  # Agregar esta línea para verificar el nombre de archivo
            # Eliminar la imagen asociada al usuario si existe
            ruta_imagen = os.path.join(settings.BASE_DIR, 'templates/assets/', foto_usuario)
            ruta_imagen_absoluta = os.path.abspath(ruta_imagen)
            print("Ruta de la imagen a eliminar:", ruta_imagen_absoluta)  # Agregar esta línea para verificar la ruta absoluta
            if os.path.exists(ruta_imagen_absoluta):
                os.remove(ruta_imagen_absoluta)
            # else:
            #     messages.add_message(request, messages.ERROR, 'Error al eliminar imagen'+ruta_imagen_absoluta)
        


        # Consulta para eliminar al usuario
        cursor.execute("DELETE FROM usuario WHERE codigo_usu = %s", (usuario_id,))
        connection.commit()

        # Cerrar el cursor y la conexión
        cursor.close()
        connection.close()

        messages.add_message(request, messages.SUCCESS, 'Registro eliminado con exito')

        return redirect('usuarios')
        #mensaje = f'Usuario eliminado y la imagen asociada también fue eliminada. Ruta de la imagen eliminada: {ruta_imagen_absoluta}'
        #return HttpResponseNotFound(mensaje)
    except Exception as e:
        # Mensaje de error
        messages.add_message(request, messages.ERROR, 'Error al eliminar usuario, posibles dependencias.')
        
        return redirect('usuarios')

def eliminar_usuario_logico(request, usuario_id):
    try:
        # Consulta para contar los registros asociados en otras tablas
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM vehiculos WHERE fk_codigo_usu = %s", (usuario_id,))
            count = cursor.fetchone()[0]

            # Verificar si hay registros asociados
            if count > 0:
                messages.add_message(request, messages.ERROR, 'No se puede eliminar este usuario porque tiene registros asociados en otras tablas.')
                return redirect('usuarios')

            # Si no hay registros asociados, procedemos con la eliminación lógica del usuario
            cursor.execute("UPDATE usuario SET estado_usu = 3 WHERE codigo_usu = %s", (usuario_id,))
            connection.commit()

        messages.add_message(request, messages.SUCCESS, 'Registro eliminado con éxito')
        return redirect('usuarios')
    
    except Exception as e:
        # Mensaje de error
        messages.add_message(request, messages.ERROR, 'Error al eliminar usuario, posibles dependencias.')
        return redirect('usuarios')
        

def obtener_usuario(request, usuario_id):
    try:
        with connection.cursor() as cursor:
            # Ejecutar la consulta SQL para obtener los datos del usuario por su ID
            cursor.execute("SELECT codigo_usu, nombre_usu, apellido_usu, email_usu, path_usu, rol_usu, estado_usu, identificacion_usu, telefono_usu FROM usuario WHERE codigo_usu = %s", [usuario_id])
            usuario_data = cursor.fetchone()

            if usuario_data:
                # Crear un diccionario con los datos del usuario
                usuario = {
                    
                    'codigo': usuario_data[0],
                    'nombre': usuario_data[1],
                    'apellido': usuario_data[2],
                    'correo': usuario_data[3],
                    'foto': usuario_data[4],
                    'rol': usuario_data[5],
                    'estado': usuario_data[6],
                    'cedula': usuario_data[7],
                    'telefono': usuario_data[8]
                    # Agrega otros campos del usuario si es necesario
                }
                # Devolver los datos del usuario en formato JSON
                return JsonResponse(usuario)
            else:
                return JsonResponse({'error': 'Usuario no encontrado'}, status=404)

    except Exception as e:
        # Manejar otros errores si es necesario
        return JsonResponse({'error': str(e)}, status=500)
    
def actualizar_usuario(request):
    if request.method == 'POST':
        usuario_cod = request.POST.get('usuario_cod')
        cedula_usu = request.POST.get('cedula_usu')
        nombre_usu = request.POST.get('nombre_usu')
        apellido_usu = request.POST.get('apellido_usu')
        telefono_usu = request.POST.get('telefono_usu')
        estado_usu = request.POST.get('estado_usu')
        email_usu = request.POST.get('email_usu')
        foto_usu = request.FILES.get('foto_usu')

        # Consultar la ruta de la foto antigua del usuario
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT path_usu FROM usuario WHERE codigo_usu = %s", (usuario_cod,))
                resultado = cursor.fetchone()
                if resultado:
                    foto_antigua = resultado[0]
                    if foto_antigua and foto_usu:
                        # Construir la ruta absoluta de la foto antigua
                        ruta_antigua_absoluta = os.path.join(settings.BASE_DIR, 'templates/assets/', foto_antigua)
                        # Verificar si la foto antigua existe y eliminarla
                        if os.path.exists(ruta_antigua_absoluta):
                            os.remove(ruta_antigua_absoluta)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

        # Guardar la nueva foto y actualizar la información del usuario en la base de datos
        if foto_usu:
            try:
                fecha_hora_actual = datetime.now().strftime("%Y%m%d%H%M%S")
                nombre_archivo_con_fecha = f"{fecha_hora_actual}_{foto_usu.name}"
                ruta_foto_nueva = os.path.join('templates/assets/uploads/', nombre_archivo_con_fecha)
                para_save = os.path.join('uploads/', nombre_archivo_con_fecha)
                
                with open(ruta_foto_nueva, 'wb') as destino:
                    for chunk in foto_usu.chunks():
                        destino.write(chunk)
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
        else:
            # Si no se proporciona una nueva foto, mantener la misma foto
            para_save = foto_antigua

        try:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE usuario SET identificacion_usu = %s, nombre_usu = %s, apellido_usu = %s, telefono_usu = %s, estado_usu = %s, email_usu = %s, path_usu=%s WHERE codigo_usu = %s", [cedula_usu, nombre_usu, apellido_usu, telefono_usu, estado_usu, email_usu, para_save, usuario_cod])
                messages.add_message(request, messages.SUCCESS, 'Registro actualizado con éxito')
                return redirect(usuarios)
        except Exception as e:
            messages.add_message(request, messages.ERROR, 'Error al actualizar')
            return redirect(usuarios)
        
    else:
        messages.add_message(request, messages.ERROR, 'Error al actualizar')
        return redirect(usuarios)
    
# def validar_cedula(request=None, cedula=None):
#     try:
#         if cedula is not None:
#             cursor = connection.cursor()
#             cursor.execute("SELECT COUNT(*) AS count FROM usuario WHERE identificacion_usu = %s", [cedula])
#             row = cursor.fetchone()
#             if row and row[0] > 0:
#                 return False
#             else:
#                 return True
#         elif request is not None:
#             try:
#                 if request.method == 'GET' and 'cedula_usu' in request.GET:
#                     cedula = request.GET['cedula_usu']
#                     return JsonResponse({'valid': validar_cedula(cedula=cedula)})
#                 elif request.method == 'POST' and 'cedula_usu' in request.POST:
#                     cedula = request.POST['cedula_usu']
#                     return JsonResponse({'valid': validar_cedula(cedula=cedula)})
#                 else:
#                     return JsonResponse({'error': 'Método no permitido'})
#             except Exception as e:
#                 return JsonResponse({'error': str(e)})
#     except Exception as e:
#         return JsonResponse({'error': str(e)})

def validar_cedula(request):
    if request.method == 'POST' and 'cedula_usu' in request.POST:
        cedula = request.POST['cedula_usu']
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) AS count FROM usuario WHERE identificacion_usu = %s", [cedula])
        row = cursor.fetchone()
        if row and row[0] > 0:
             return JsonResponse(False, safe=False)
        else:
            return JsonResponse(True, safe=False)
    return JsonResponse(False, safe=False)

def validar_correo(request):
    if request.method == 'POST' and 'email_usu' in request.POST:
        correo = request.POST['email_usu']
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) AS count FROM usuario WHERE email_usu = %s", [correo])
        row = cursor.fetchone()
        if row and row[0] > 0:
             return JsonResponse(False, safe=False)
        else:
            return JsonResponse(True, safe=False)
    return JsonResponse(False, safe=False)

def validar_cedula_edicion(request):
    if request.method == 'POST':
        cedula = request.POST.get('cedula_usu', None)
        print(cedula)
        usuario_id = request.POST.get('usuario_id', None)
        print(usuario_id)
        if cedula and usuario_id:
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) AS count FROM usuario WHERE identificacion_usu = %s AND codigo_usu != %s", [cedula, usuario_id])
            
            # Obtener el resultado de la consulta
            row = cursor.fetchone()
            
            # Imprimir el resultado de la consulta
            print(row)
            
            if row and row[0] > 0:
                return JsonResponse(False, safe=False)
            else:
                return JsonResponse(True, safe=False)
    
    return JsonResponse(False, safe=False)

def validar_correo_edicion(request):
    if request.method == 'POST':
        correo = request.POST.get('email_usu', None)
        print(correo)
        usuario_id = request.POST.get('usuario_id', None)
        print(usuario_id)
        if correo and usuario_id:
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) AS count FROM usuario WHERE email_usu = %s AND codigo_usu != %s", [correo, usuario_id])
            
            # Obtener el resultado de la consulta
            row = cursor.fetchone()
            
            # Imprimir el resultado de la consulta
            print(row)
            
            if row and row[0] > 0:
                return JsonResponse(False, safe=False)
            else:
                return JsonResponse(True, safe=False)
    
    return JsonResponse(False, safe=False)
    
import psycopg2
from django.shortcuts import render
from django.conf import settings

from django.http import JsonResponse
from django.db import connection

def obtener_vehiculos_usuario(request, usuario_id):
    print(usuario_id)
    try:
        # Realizar la conexión a la base de datos
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT v.placa_veh, v.tonelaje_veh, v.estado_veh, c.tipo_cat, u.nombre_usu, u.apellido_usu
                FROM vehiculos v
                INNER JOIN usuario u ON v.fk_codigo_usu = u.codigo_usu
                LEFT JOIN categorias c ON v.fk_codigo_cat = c.codigo_cat
                WHERE u.codigo_usu = %s
            """, (usuario_id,))
            vehiculos_data = cursor.fetchall()
            
            print(vehiculos_data)

            if vehiculos_data:
                vehiculos = []
                for vehiculo_data in vehiculos_data:
                    vehiculo = {
                        'placa': vehiculo_data[0],
                        'tonelaje': vehiculo_data[1],
                        'estado': vehiculo_data[2],
                        'categoria': vehiculo_data[3],
                        'nombre_prop': vehiculo_data[4],
                        'apellido_prop': vehiculo_data[5]
                    }
                    vehiculos.append(vehiculo)

                return JsonResponse({'vehiculos': vehiculos})
            else:
                # Devolver un error si no se encuentra ningún vehículo asociado al usuario
                return JsonResponse({'error': 'No se encontraron vehículos asociados a este usuario'}, status=404)

    except Exception as e:
        # Manejar otros errores si es necesario
        return JsonResponse({'error': str(e)}, status=500)
    
