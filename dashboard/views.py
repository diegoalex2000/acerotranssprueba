import calendar
from datetime import datetime, timedelta
import os
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import pandas as pd
import numpy as np
from django.conf import settings
from django.db import connection
from django.http import HttpResponseNotFound, JsonResponse
from django.shortcuts import redirect, render
from sklearn.preprocessing import MinMaxScaler
from sklearn.svm import SVR
import matplotlib.pyplot as plt
import io
import base64
from django.http import JsonResponse


class FacturacionPredictorSVRGeneral:
    def __init__(self):
        self.df_mes = None
        self.svr = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.sequence_length = 3

    def cargar_datos_desde_bd_general(self):
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
    
    def cargar_datos_desde_bd_inversion(self):
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    fecha_factura_fac,
                    intereses_fac
                FROM 
                    facturas
            """)
            rows = cursor.fetchall()
        
        data = [{'fecha_factura_fac': row[0], 'intereses_fac': row[1]} for row in rows]
        df = pd.DataFrame(data)
        df['fecha_factura_fac'] = pd.to_datetime(df['fecha_factura_fac'])
        return df

    def obtener_datos_usuario(self, request):
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

                return {
                    'user_name': user_name,
                    'last_name': last_name,
                    'perfil_name': rol_name,
                    'path_name': path_name
                }
        return {}

    def preprocesar_datos_general(self, df):
        df['fecha_factura_fac'] = pd.to_datetime(df['fecha_factura_fac'])
        df['anio'] = df['fecha_factura_fac'].dt.year
        df['mes'] = df['fecha_factura_fac'].dt.month
        self.df_mes = df.groupby(['anio', 'mes']).agg({'fecha_factura_fac': 'min', 'valor_factura_fac': 'sum'}).reset_index()

    def train_model(self):
        scaled_data = self.scaler.fit_transform(self.df_mes['valor_factura_fac'].values.reshape(-1, 1))
        X = self.create_sequences_general(scaled_data)
        y_train = scaled_data[self.sequence_length:]

        self.svr = SVR(kernel='rbf', C=100, gamma=0.1, epsilon=0.1)
        self.svr.fit(X, y_train)

    def create_sequences_general(self, data):
        sequences = []
        for i in range(len(data) - self.sequence_length):  
            sequence = data[i:i+self.sequence_length].reshape(-1)
            sequences.append(sequence)
        return np.array(sequences)

    from datetime import datetime, timedelta

    def predict(self):
  
        if self.svr is None or self.df_mes is None:
            raise ValueError("Modelo no entrenado o datos no preprocesados")

        ultimos_meses = self.scaler.transform(self.df_mes['valor_factura_fac'].tail(self.sequence_length).values.reshape(-1, 1)).reshape(1, -1)
        predicciones_por_mes = []

        # Agregar datos históricos a las predicciones
        for _, row in self.df_mes.iterrows():
            fecha = f"{calendar.month_abbr[row['mes']]} {row['anio']}"
            predicciones_por_mes.append({'fecha': fecha, 'prediccion': round(row['valor_factura_fac'], 2)})

        # Calcular el último mes y año de facturación
        ultimo_mes = self.df_mes['fecha_factura_fac'].max()
        ultimo_mes = ultimo_mes.replace(day=1)  # Asegurar que sea el primer día del mes
        ultimo_anio = ultimo_mes.year
        meses_restantes = (datetime(2024, 12, 31) - ultimo_mes).days // 30  # Calcular los meses restantes hasta diciembre de 2024

        # Predicciones para los meses futuros
        fecha_prediccion = ultimo_mes
        for _ in range(meses_restantes):
            if fecha_prediccion.year == 2024 and fecha_prediccion.month == 12:
                break  # Salir del bucle si llegamos a diciembre de 2024
            fecha_prediccion += timedelta(days=30)
            prediccion = self.svr.predict(ultimos_meses)
            prediccion_real = self.scaler.inverse_transform(prediccion.reshape(-1, 1))[0][0]
            fecha_prediccion_str = fecha_prediccion.strftime('%B %Y')
            if fecha_prediccion_str not in [p['fecha'] for p in predicciones_por_mes]:  # Verificar si la fecha ya existe en las predicciones
                predicciones_por_mes.append({'fecha': fecha_prediccion_str, 'prediccion': round(prediccion_real, 2)})
            ultimos_meses = np.append(ultimos_meses[:, 1:], prediccion.reshape(-1, 1), axis=1)

        return predicciones_por_mes





def dashboard_general(request):
    context = {}

    # Obtener datos de usuario
    predictor = FacturacionPredictorSVRGeneral()
    context.update(predictor.obtener_datos_usuario(request))

    # Obtener predicciones de facturación
    predictor.preprocesar_datos_general(predictor.cargar_datos_desde_bd_general())
    predictor.train_model()
    predicciones_por_mes = predictor.predict()

    if predicciones_por_mes:
        context['predicciones_por_mes'] = predicciones_por_mes
        print("Predicciones por mes:", predicciones_por_mes)
        return render(request, 'administracion/predicciones/prediccion_general.html', context)
    else:
        return redirect(dashboard)

def dashboard_socio(request):
    context = {}

    # Función para buscar socios
    def buscar_socios():
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM usuario WHERE estado_usu = 1")
            rows = cursor.fetchall()
            data = [{'id': row[0], 'nombre': row[1], 'apellido': row[2]} for row in rows]
            return data

    # Llamar a la función para buscar socios
    socios = buscar_socios()
    context['socios'] = socios

    # Obtener datos de usuario
    predictor = FacturacionPredictorSVRGeneral()
    context.update(predictor.obtener_datos_usuario(request))

    # Obtener predicciones de facturación
    predictor.preprocesar_datos_general(predictor.cargar_datos_desde_bd_general())
    predictor.train_model()
    predicciones_por_mes = predictor.predict()

    if predicciones_por_mes:
        context['predicciones_por_mes'] = predicciones_por_mes
        print("Predicciones por mes:", predicciones_por_mes)
        return render(request, 'administracion/predicciones/prediccion_socio.html', context)
    else:
        return redirect(dashboard)
    
def dashboard(request):
    context = {}
    # Obtener datos de usuario
    predictor = FacturacionPredictorSVRGeneral()
    context.update(predictor.obtener_datos_usuario(request))
    return render(request, 'administracion/predicciones/predicciones.html', context)

def cargar_datos_desde_bd_socio(socioId):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                fecha_factura_fac,
                valor_factura_fac
            FROM 
                facturas
            WHERE 
                fk_codigo_usu = %s
        """, [socioId])
        rows = cursor.fetchall()
    
    data = [{'fecha_factura_fac': row[0], 'valor_factura_fac': row[1]} for row in rows]
    df = pd.DataFrame(data)
    df['fecha_factura_fac'] = pd.to_datetime(df['fecha_factura_fac'])
    return df

def dashboard_inversion(request):
    context = {}

    # Obtener datos de usuario
    predictor = FacturacionPredictorSVRGeneral()
    context.update(predictor.obtener_datos_usuario(request))

    # Obtener predicciones de facturación
    predictor.preprocesar_datos_general(predictor.cargar_datos_desde_bd_inversion())
    predictor.train_model()
    predicciones_por_mes = predictor.predict()

    if predicciones_por_mes:
        context['predicciones_por_mes'] = predicciones_por_mes
        print("Predicciones por mes:", predicciones_por_mes)
        return render(request, 'administracion/predicciones/prediccion_inversion.html', context)
    else:
        return redirect(dashboard)

from scipy.interpolate import make_interp_spline

def dashboard_socio_ajax(request, socioId):
    # Obtener datos de usuario
    predictor = FacturacionPredictorSVRGeneral()
    user_data = predictor.obtener_datos_usuario(request)

    # Cargar datos de facturas para el socio específico
    datos_socio = cargar_datos_desde_bd_socio(socioId)

    # Preprocesar datos específicos del socio
    predictor.preprocesar_datos_general(datos_socio)
    predictor.train_model()
    predicciones_por_mes_socio = predictor.predict()

    if predicciones_por_mes_socio:
        # Construir los datos de la tabla
        tabla_html = '<div class="table-responsive"><table class="table table-bordered table-striped">'
        tabla_html += '<thead class="alert-success"><tr>'
        for prediccion in predicciones_por_mes_socio:
            tabla_html += f'<th>{prediccion["fecha"]}</th>'
        tabla_html += '</tr></thead><tbody><tr>'
        for prediccion in predicciones_por_mes_socio:
            tabla_html += f'<td>{prediccion["prediccion"]}</td>'
        tabla_html += '</tr></tbody></table></div>'

        # Generar el gráfico
        meses = [prediccion["fecha"] for prediccion in predicciones_por_mes_socio]
        predicciones = [prediccion["prediccion"] for prediccion in predicciones_por_mes_socio]

        # Configurar el tamaño del gráfico
        plt.figure(figsize=(12, 8))

        # Configurar colores para las barras
        colores_barras = []
        for prediccion in predicciones_por_mes_socio:
            if prediccion['prediccion'] == max(predicciones):
                colores_barras.append('#B4F6A4')  # Verde pastel para el mes con mayor facturación
            elif prediccion['prediccion'] == min(predicciones):
                colores_barras.append('#F6A4B4')  # Rosado para el mes con menor facturación
            elif prediccion['fecha'] in meses[-8:]:
                colores_barras.append('#CCCCCC')  # Gris para los últimos 8 meses
            else:
                colores_barras.append('#83C4F0')  # Azul predeterminado

        # Crear el gráfico de barras
        plt.bar(meses, predicciones, color=colores_barras)

        # Ajustar el espacio entre las barras
        plt.subplots_adjust(bottom=0.2)

        # Suavizar la línea de tendencia con interpolación cúbica
        spline = make_interp_spline(range(len(meses)), predicciones, k=2)  # Cambio de k=3 a k=2 para una curva más suave
        x_new = np.linspace(0, len(meses) - 1, 300)
        y_smooth = spline(x_new)

        # Añadir la línea de tendencia suavizada
        plt.plot(x_new, y_smooth, color='#E91E63', label='Tendencia')


        # Configurar el título y etiquetas
        plt.title('Predicción de facturación por mes')
        plt.xlabel('Mes')
        plt.ylabel('Predicción de facturación')
        plt.xticks(rotation=45, ha='right')  # Rotar las etiquetas de los meses

        # Mostrar las leyendas
        plt.legend(loc='upper left')

        # Mostrar los valores en las barras
        for i in range(len(meses)):
            plt.text(i, predicciones[i], str(predicciones[i]), ha='center', va='bottom')

        # Agregar puntos de referencia para los valores (rojos)
        plt.scatter(range(len(meses)), predicciones, color='red', zorder=5)

        # Agregar leyendas personalizadas
        leyendas = [
            Patch(facecolor='#B4F6A4', label='Mayor Facturación'),
            Patch(facecolor='#F6A4B4', label='Menor Facturación'),
            Patch(facecolor='#CCCCCC', label='Predicción'),
            Line2D([0], [0], color='#E91E63', lw=2, label='Tendencia')
        ]

        plt.legend(handles=leyendas)

        # Guardar el gráfico en un buffer de bytes
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)

        # Codificar el gráfico en base64 para incrustarlo en la página web
        grafico_codificado = base64.b64encode(buffer.getvalue()).decode()

        # Cerrar la figura para liberar recursos
        plt.close()

        # Devolver los datos en formato JSON
        return JsonResponse({'tabla_html': tabla_html, 'grafico_codificado': grafico_codificado, 'predicciones_por_mes': predicciones_por_mes_socio})
    else:
        # Si no hay predicciones, devolver un JSON vacío o un mensaje de error
        return JsonResponse({'error': 'No se encontraron predicciones'})
