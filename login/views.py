# views.py
import json
from django.contrib import messages
from django.db import connection
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import render, redirect
import os
from django.conf import settings

import pandas as pd
import numpy as np
from django.db import connection
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import LSTM, Dense
import pandas as pd
import numpy as np
from django.db import connection
from sklearn.preprocessing import MinMaxScaler
from sklearn.svm import SVR

from django.shortcuts import render
from django.db import connection
import json
from datetime import datetime, timedelta

def administracion(request):
    context = {}
    
    if 'codigo_usu' in request.session:
        user_id = request.session['codigo_usu']
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM usuario WHERE codigo_usu = %s", [user_id])
            user_data = cursor.fetchone()
        
        if user_data:
            user_name = user_data[1]
            last_name = user_data[2]
            path_name = user_data[6]
            rol_name = user_data[7]
            full_path_name = os.path.join(settings.UPLOADS_DIR, path_name)
    
            context = {
                'user_name': user_name,
                'last_name': last_name,
                'perfil_name': rol_name,
                'path_name': path_name
            }
            with connection.cursor() as cursor:
                # Realizar la consulta SQL para obtener todas las facturas
                cursor.execute("SELECT fecha_factura_fac, intereses_fac FROM facturas")
                facturas = cursor.fetchall()

               # Inicializar un diccionario para almacenar los intereses por mes
                intereses_por_mes = {}

                # Iterar a través de las facturas
                for factura in facturas:
                    fecha_factura = factura[0]
                    mes_anio = fecha_factura.strftime('%B %Y')

                    # Si el mes aún no existe en el diccionario, inicializarlo en 0
                    if mes_anio not in intereses_por_mes:
                        intereses_por_mes[mes_anio] = 0

                    # Sumar los intereses de la factura al mes correspondiente
                    intereses_por_mes[mes_anio] += float(factura[1])

                # Convertir el diccionario a JSON, ordenando las claves (meses) cronológicamente
                intereses_json = json.dumps({k: intereses_por_mes[k] for k in sorted(intereses_por_mes, key=lambda x: datetime.strptime(x, '%B %Y'))})

                # Agregar al contexto
                context['intereses_json'] = intereses_json
                #print(intereses_json)

                # Crear una lista de fechas de las facturas
                fechas_facturas = [factura[0] for factura in facturas]

                # Crear una lista de meses y años únicos a partir de las fechas de las facturas
                meses_anios = list(set([fecha.strftime('%B %Y') for fecha in fechas_facturas]))

                # Ordenar los meses y años de menor a mayor
                meses_anios.sort(key=lambda fecha: datetime.strptime(fecha, '%B %Y'))

                # Pasar los meses y años al contexto
                context['meses_anios'] = json.dumps(meses_anios)

                # Agregar otros datos al contexto
                context['total_fact'] = total_facturas()  # Asegúrate de definir esta función
                context['total_compradas'] = facturas_compradas()  # Asegúrate de definir esta función
                context['total_pagadas'] = facturas_pagadas()  # Asegúrate de definir esta función
            
    return render(request, 'administracion/admin.html', context)


def total_facturas():
    with connection.cursor() as cursor:
        
        cursor.execute("SELECT COUNT(codigo_fac) FROM facturas")
        total = cursor.fetchone()[0]
            
        return total

def facturas_compradas():
    
    with connection.cursor() as cursor:
        
        cursor.execute("SELECT COUNT(codigo_fac) FROM facturas where estado_fac = '1'")
        total_compradas = cursor.fetchone()[0]
            
        return total_compradas

def facturas_pagadas():
    
    with connection.cursor() as cursor:
        
        cursor.execute("SELECT COUNT(codigo_fac) FROM facturas where estado_fac = '0'")
        total_pagadas = cursor.fetchone()[0]
            
        return total_pagadas
    
def fecha_intereses():
    # Inicializar listas para almacenar fechas e intereses
    fechas = []
    intereses = []

    # Realizar la consulta SQL para obtener los datos necesarios
    with connection.cursor() as cursor:
        cursor.execute("SELECT fecha_factura_fac, intereses_fac FROM facturas")
        rows = cursor.fetchall()

        # Iterar sobre los resultados y agregar datos a las listas
        for row in rows:
            fechas.append(row[0])
            intereses.append(row[1])

    return fechas, intereses

def iniciar_sesion(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Consulta directa a la base de datos para verificar las credenciales
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM usuario WHERE identificacion_usu = %s AND password_usu = %s AND estado_usu = 1", [username, password])
            user_row = cursor.fetchone()
        
        if user_row:
            # Si las credenciales son válidas, iniciar sesión
            user_id = user_row[0]
            user_name = user_row[1]
            last_name = user_row[2]
            path_name = user_row[7]
            rol_name = user_row[8]
            
            request.session['codigo_usu'] = user_id  # Guardar el ID del usuario en la sesión
            request.session['nombre_usu'] = user_name  # Guardar el nombre de usuario en la sesión
            request.session['apellido_usu'] = last_name  # Guardar el apellido del usuario en la sesión
            request.session['path_usu'] = path_name  # Guardar el apellido del usuario en la sesión
            request.session['rol_usu'] = rol_name  # Guardar el apellido del usuario en la sesión
            
            messages.add_message(request, messages.SUCCESS, 'Bienvenido al Sistema')
            return redirect('/administracion/')  # Éxito en la autenticación
        else:
            messages.add_message(request, messages.ERROR, 'Datos Incorrectos o usuario Inactivo, vuelve a intentarlo.')
            return render(request,'registration/login.html')  # Falló la autenticación
    else: 
      
        return render(request,'registration/login.html')
    
def index(request):
    
    return render(request, 'registration/login.html')

from django.http import HttpResponseNotFound
from django.shortcuts import render
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from keras.layers import Dropout


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

def prediccion_facturacion_general(request):
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