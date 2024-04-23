from django.core.cache import cache
from django.shortcuts import render, redirect
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from datetime import datetime, timedelta
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



def facturas(request):
    if 'codigo_usu' in request.session:
        user_id = request.session['codigo_usu']
        user_data = get_user_data(user_id)
        if user_data:
            user_name, last_name, perfil_name, path_name = user_data

            with connection.cursor() as cursor:
                cursor.execute("""SELECT 
                    codigo_fac,
                    tasa_interes_fac,
                    valor_factura_fac,
                    fecha_factura_fac,
                    observacion_fac,
                    retencion_fac,
                    valores_pendientes_fac,
                    valor_pendiente_fac,
                    comentario_valores_pendientes_fac,
                    percent1_fac,
                    restante1_fac,
                    percent2_fac,
                    restante2_fac,
                    intereses_fac,
                    total_intereses_fac,
                    total_pendientes_fac,
                    fecha_aprox_pago_fac,
                    estado_fac,
                    adjunto_pago_fac,
                    fk_codigo_veh, 
                    nombre_usu,
                    apellido_usu,
                    tipo_cat,
                    placa_veh,
                    tonelaje_veh,
                    estado_veh
                FROM 
                    facturas
                JOIN 
                    vehiculos ON facturas.fk_codigo_veh = vehiculos.codigo_veh
                JOIN 
                    categorias ON vehiculos.fk_codigo_cat = categorias.codigo_cat
                JOIN 
                    usuario  ON facturas.fk_codigo_usu = usuario.codigo_usu
                ORDER BY 
                    facturas.estado_fac DESC,
                    facturas.fecha_factura_fac ASC;
                """)


                # Obtener todos los datos de facturas
                facturas_data = cursor.fetchall()

            # Formatear los datos obtenidos de la base de datos
            facturas = []
            for row in facturas_data:
                factura = {
                    'codigo': row[0],
                    
                    'tasa_interes': row[1],
                    'valor_factura': row[2],
                    'fecha_factura': row[3],
                    'observacion': row[4],
                    'retencion': row[5],
                    'valores_pendientes': row[6],
                    'valor_pendiente': row[7],
                    'comentario_valores_pendientes': row[8],
                    'percent1': row[9],
                    'restante1': row[10],
                    'percent2': row[11],
                    'restante2': row[12],
                    'intereses': row[13],
                    'total_intereses': row[14],
                    'total_pendientes': row[15],
                    'fecha_aprox_pago': row[16],
                    'estado': row[17],
                    'adjunto_pago': row[18],
                    'codigo_veh': row[19],
                    'nombre_dueno': row[20],
                    'apellido_dueno': row[21],
                    'categoria': row[22],
                    'placa': row[23],
                    'tonelaje': row[24],
                }
                facturas.append(factura)

            # Renderizar la plantilla con los datos de las facturas
            # Obtener los socios activos
            socios_activos = obtener_socios_activos()
            print(socios_activos)  # Imprime los datos obtenidos de los socios activos


            context = {
                'user_name': user_name,
                'last_name': last_name,
                'perfil_name': perfil_name,
                'path_name': path_name,
                'facturas': facturas,  # Cambiar 'usuarios' a 'facturas' para evitar errores
                'socios_activos': socios_activos  # Pasar la lista de socios activos al contexto
            }
            
           
            return render(request, 'administracion/facturas/index.html', context)
    else:
        return HttpResponseNotFound('error')  # Manejar el caso donde no hay un 'codigo_usu' en la sesión
    
    
def obtener_socios_activos():
    with connection.cursor() as cursor:
        cursor.execute("SELECT codigo_usu, nombre_usu, apellido_usu, rol_usu, path_usu FROM usuario WHERE estado_usu = 1;")
        socios_activos_data = cursor.fetchall()
    socios_activos = []
    for row in socios_activos_data:
        socios_activos.append(row)
    return socios_activos

def guardar_factura(request):
    if request.method == 'POST':
        # Obtener los datos del formulario
        selected_socio = request.POST.get('selectedSocio', '')
        socioId = request.POST.get('idSoc','')
        tasa_interes = request.POST.get('tasa_interesFac','')
        valor_factura = request.POST.get('valorFac','')# Eliminar el signo de dólar
        fecha_factura = request.POST.get('fechaFac', '')
        observacion = request.POST.get('obsFac', '')
        retencion = request.POST.get('1_percent', '').replace('$', '') # Eliminar el signo de dólar
        valores_pendientes = request.POST.get('restante2', '').replace('$', '') # Eliminar el signo de dólar
        valor_pendiente = request.POST.get('total_pendientes', '').replace('$', '') # Eliminar el signo de dólar
        comentario_valores_pendientes = request.POST.get('total_pendientes_detalle', '')
        percent1_fac = request.POST.get('1_percent', '').replace('$', '') # Eliminar el signo de dólar
        restante1_fac = request.POST.get('restante_1', '').replace('$', '') # Eliminar el signo de dólar
        percent2_fac = request.POST.get('2_percent', '').replace('$', '') # Eliminar el signo de dólar
        restante2_fac = request.POST.get('restante_2', '').replace('$', '') # Eliminar el signo de dólar
        intereses_fac = request.POST.get('intereses_modal', '').replace('$', '') # Eliminar el signo de dólar
        total_intereses_fac = request.POST.get('total_intereses', '').replace('$', '') # Eliminar el signo de dólar
        total_pendientes_fac = request.POST.get('total_pendientes', '').replace('$', '') # Eliminar el signo de dólar
        # Calcular la fecha aproximada de pago
        fecha_aprox_pago_fac = calcular_fecha_aproximada_pago(fecha_factura)
        estado_fac = 1
        vehiculoId = request.POST.get('idVeh', '')
        adjunto_pago = request.FILES.get('adjunto_pago')
            
        if adjunto_pago:
            fecha_hora_actual = datetime.now().strftime("%Y%m%d%H%M%S")
            nombre_archivo_con_fecha = f"{fecha_hora_actual}_{adjunto_pago.name}"

            ruta_foto = os.path.join('templates/assets/uploads/facturas/', nombre_archivo_con_fecha)
            para_save = os.path.join('uploads/facturas/', nombre_archivo_con_fecha)
            with open(ruta_foto, 'wb') as destino:
                for chunk in adjunto_pago.chunks():
                    destino.write(chunk)
        else:
    # Si no se adjunta ninguna imagen, asigna un valor predeterminado a para_save
            para_save = " "        
            # Conectar a la base de datos y ejecutar la consulta SQL
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO FACTURAS ( tasa_interes_fac, fk_codigo_usu, valor_factura_fac, fecha_factura_fac, observacion_fac, fk_codigo_veh, valor_pendiente_fac, comentario_valores_pendientes_fac, percent1_fac, restante1_fac, percent2_fac, restante2_fac, intereses_fac, total_intereses_fac, total_pendientes_fac, fecha_aprox_pago_fac, estado_fac, adjunto_pago_fac ) VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s, %s,%s, %s,%s, %s,%s, %s)",
                            [tasa_interes, socioId, valor_factura, fecha_factura, observacion, vehiculoId, valor_pendiente, comentario_valores_pendientes, percent1_fac, restante1_fac, percent2_fac, restante2_fac, intereses_fac, total_intereses_fac, total_pendientes_fac, fecha_aprox_pago_fac, estado_fac, para_save])
            messages.add_message(request, messages.SUCCESS, 'Factura registrada con éxito')
            cache.delete('predicciones_facturacion')
        return redirect('facturas')
        
    else:
        messages.add_message(request, messages.ERROR, 'Error: Intenta nuevamente')
        return redirect('facturas')

def calcular_fecha_aproximada_pago(fecha_factura):
    # Convertir la cadena de fecha a objeto datetime
    fecha_factura = datetime.strptime(fecha_factura, '%Y-%m-%d')
    
    # Sumar 21 días para obtener la fecha aproximada de pago
    fecha_aproximada_pago = fecha_factura + timedelta(days=21)
    
    # Ajustar la fecha para que coincida con el próximo lunes
    dias_para_lunes = (7 - fecha_aproximada_pago.weekday()) % 7
    fecha_aproximada_pago += timedelta(days=dias_para_lunes)
    
    return fecha_aproximada_pago

    
def get_vehiculos_propietario(request, propietario_id):
    # Establecer la conexión con la base de datos
    with connection.cursor() as cursor:
        # Ejecutar la consulta SQL para obtener los vehículos del propietario
        cursor.execute("""SELECT codigo_veh, placa_veh, tipo_cat FROM vehiculos
                       join categorias on vehiculos.fk_codigo_cat = categorias.codigo_cat
                       WHERE fk_codigo_usu = %s""", [propietario_id])
        
        # Obtener los resultados de la consulta
        vehiculos = cursor.fetchall()
        
        # Serializar los resultados en formato JSON
        vehiculos_json = [{'codigo': vehiculo[0], 'placa': vehiculo[1], 'categoria': vehiculo[2]} for vehiculo in vehiculos]
    
    # Devolver la respuesta JSON
    return JsonResponse(vehiculos_json, safe=False)

def detalle_factura_view(request, codigo_fac):
    with connection.cursor() as cursor:
        cursor.execute("""SELECT 
                            facturas.codigo_fac,
                            tasa_interes_fac,
                            valor_factura_fac,
                            fecha_factura_fac,
                            observacion_fac,
                            retencion_fac,
                            valores_pendientes_fac,
                            valor_pendiente_fac,
                            comentario_valores_pendientes_fac,
                            percent1_fac,
                            restante1_fac,
                            percent2_fac,
                            restante2_fac,
                            intereses_fac,
                            total_intereses_fac,
                            total_pendientes_fac,
                            fecha_aprox_pago_fac,
                            estado_fac,
                            adjunto_pago_fac,
                            fk_codigo_veh, 
                            nombre_usu,
                            apellido_usu,
                            tipo_cat,
                            placa_veh,
                            tonelaje_veh,
                            estado_veh
                        FROM 
                            facturas
                        JOIN 
                            vehiculos ON facturas.fk_codigo_veh = vehiculos.codigo_veh
                        JOIN 
                            categorias ON vehiculos.fk_codigo_cat = categorias.codigo_cat
                        JOIN 
                            usuario  ON facturas.fk_codigo_usu = usuario.codigo_usu 
                        WHERE 
                            facturas.codigo_fac = %s;
                        """, [codigo_fac])

        # Obtener todos los datos de la factura
        factura_data = cursor.fetchone()

        # Verificar si se encontró la factura
        if factura_data:
            # Formatear los datos obtenidos de la base de datos
            factura_detalle = {
                'codigo': factura_data[0],
                'tasa_interes': factura_data[1],
                'valor_factura': factura_data[2],
                'fecha_factura': factura_data[3],
                'observacion': factura_data[4],
                'retencion': factura_data[5],
                'valores_pendientes': factura_data[6],
                'valor_pendiente': factura_data[7],
                'comentario_valores_pendientes': factura_data[8],
                'percent1': factura_data[9],
                'restante1': factura_data[10],
                'percent2': factura_data[11],
                'restante2': factura_data[12],
                'intereses': factura_data[13],
                'total_intereses': factura_data[14],
                'total_pendientes': factura_data[15],
                'fecha_aprox_pago': factura_data[16],
                'estado': factura_data[17],
                'adjunto_pago': factura_data[18],
                'codigo_veh': factura_data[19],
                'nombre_dueno': factura_data[20],
                'apellido_dueno': factura_data[21],
                'categoria': factura_data[22],
                'placa': factura_data[23],
                'tonelaje': factura_data[24],
            }
            # Devolver los datos de la factura en formato JSON
            return JsonResponse(factura_detalle)
        else:
            # Si no se encuentra la factura, devolver un error
            return JsonResponse({'error': 'No se encontró la factura'}, status=404)
        
        
def actualizarFacturaPagado(request, codigo_fac):
    with connection.cursor() as cursor:
        # Ejecutar la consulta SQL para actualizar el estado de la factura
        cursor.execute("""
            UPDATE facturas
            SET estado_fac ='0'
            WHERE codigo_fac = %s
        """, [codigo_fac])
        
def actualizarFacturaPagado(request, codigo_fac):
    try:
        with connection.cursor() as cursor:

           
            # Si no hay vehículos relacionados, proceder con la eliminación lógica de la categoría
            cursor.execute("UPDATE facturas SET estado_fac=0 WHERE codigo_fac = %s", [codigo_fac])
            connection.commit()

            # Cerrar la conexión
            connection.close()

            messages.add_message(request, messages.SUCCESS, 'Registro actualizado con éxito')
            return redirect('facturas')

    except Exception as e:
        # Mensaje de error
        messages.add_message(request, messages.ERROR, f'Error al actualizar el registro, posibles dependencias. {e}')
        return redirect('facturas')
    
import pandas as pd
import numpy as np
from django.db import connection
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import LSTM, Dense
import pandas as pd
import numpy as np
from django.db import connection
from django.http import HttpResponseNotFound
from django.shortcuts import render



def cargar_datos_desde_bd_general():
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                fecha_factura_fac,
                valor_factura_fac
            FROM 
                facturas
        """)
        rows = cursor.fetchall()
    
    data = [{'fecha_factura_fac': row[0], 'valor_factura_fac': row[1]} for row in rows]
    df = pd.DataFrame(data)
    df['fecha_factura_fac'] = pd.to_datetime(df['fecha_factura_fac'])
    return df

def preprocesar_datos_general(df):
    df['fecha_factura_fac'] = pd.to_datetime(df['fecha_factura_fac'])
    df['anio'] = df['fecha_factura_fac'].dt.year
    df['mes'] = df['fecha_factura_fac'].dt.month
    df_mes = df.groupby(['anio', 'mes'])['valor_factura_fac'].sum().reset_index()
    return df_mes
# Crear secuencias de tiempo para entrenar el modelo
def create_sequences_general(data, seq_length):
    sequences = []
    for i in range(len(data) - seq_length):  # Cambiado para predecir los próximos valores
        sequence = data[i:i+seq_length]
        sequences.append(sequence)
    return np.array(sequences)

def facturas2(request):
    if 'codigo_usu' in request.session:
        datos_facturacion = cargar_datos_desde_bd_general()
        df_mes = preprocesar_datos_general(datos_facturacion)
        
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(df_mes['valor_factura_fac'].values.reshape(-1, 1))

        sequence_length = 3  # Longitud de la secuencia de tiempo
        X = create_sequences_general(scaled_data, sequence_length)
        y_train = scaled_data[sequence_length:]

        # Modelado de la red LSTM
        model = Sequential()
        model.add(LSTM(units=50, return_sequences=True, input_shape=(sequence_length, 1)))
        model.add(LSTM(units=50))
        model.add(Dense(units=1))
        model.compile(optimizer='adam', loss='mean_squared_error')

        # Entrenar el modelo
        model.fit(X, y_train, epochs=100, batch_size=32)

        # Predicción para los próximos 8 meses
        ultimos_meses = scaled_data[-sequence_length:].reshape(1, sequence_length, 1)
        predicciones_por_mes = []
        fecha_prediccion = datetime(2024, 5, 1)  # Inicializar en mayo de 2024
        for _ in range(8):  # Predicción para los 8 meses restantes
            prediccion = model.predict(ultimos_meses)
            prediccion_real = scaler.inverse_transform(prediccion)[0][0]  # Desescalar la predicción
            predicciones_por_mes.append(round(prediccion_real, 2))
            ultimos_meses = np.append(ultimos_meses[:, 1:, :], prediccion.reshape(1, 1, 1), axis=1)
            
            # Incrementar la fecha de predicción en un mes
            fecha_prediccion += timedelta(days=30)  # Asumiendo un mes de 30 días
        
        predicciones_formateadas = []
        for prediccion, i in zip(predicciones_por_mes, range(5, 13)):
            predicciones_formateadas.append({'fecha': fecha_prediccion.replace(month=i).strftime('%B %Y'), 'prediccion': prediccion})
        
        context = {
            'predicciones_por_mes': predicciones_formateadas,
        }
        print("Predicciones por mes:", predicciones_formateadas)

        return render(request, 'administracion/admin.html', context)
    else:
        return HttpResponseNotFound('error')