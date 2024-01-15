# views.py
from django.shortcuts import render
from rest_framework import viewsets
from .serializer import FeedbackSerializer
from .models import Feedback

import pandas as pd
import matplotlib.pyplot as plt
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
import tempfile
from decouple import config

# Importar las librerías necesarias para la IA
from langchain.agents.agent_types import AgentType
from langchain.chat_models import ChatOpenAI
from langchain_experimental.agents import create_pandas_dataframe_agent

# Crear y configurar el bot (Anthea)
Anthea = create_pandas_dataframe_agent(
    ChatOpenAI(
        temperature=0,
        model="gpt-3.5-turbo",  # Cambiar el modelo a "gpt-3.5-turbo"
        api_key="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"  # Utiliza la variable de entorno openai_api_key, copiar aqui la clave
    ),
    pd.DataFrame(),  # Inicializar DataFrame vacío
    verbose=True,
    agent_type=AgentType.OPENAI_FUNCTIONS
)

formato = """
¡Hola! Eres Anthea, una asistente de análisis de datos creada en Marte para apoyar a todos los analistas y no analistas de todo el universo que deseen obtener conocimiento de sus datos:
1. ¿Podrías proporcionar más detalles sobre {question}?
2. Realiza un análisis exploratorio de datos EDA para el archivo {question} y proporciona un reporte con los resultados.
Si ves espacios vacíos o errores en el documento, corrígelos y realiza el análisis con los datos que estén.
3. ¿Hay algo específico que te gustaría destacar en estos datos tras realizar el análisis exploratorio de datos EDA?
4. ¿Has notado algún patrón o tendencia interesante en los datos tras realizar el análisis exploratorio de datos EDA?
5. Después de tu análisis exploratorio de datos EDA, crea Insights Valiosos para el archivo {question}
¡Recuerda, debes proporcionar un reporte como si fueras un analista de datos en tercera persona y en español!
#{question}
"""

def consulta(input_usuario, dataframe, insights=False):
    # Personalizar el formato de la consulta a Anthea
    if insights:
        formato_insights = """
        6. Insights Valiosos de los Datos:
        """
        pregunta_completa = formato.format(question=input_usuario) + formato_insights
    else:
        pregunta_completa = formato.format(question=input_usuario)

    prompt = f"{pregunta_completa}\n\nDataFrame:\n{dataframe.to_string(index=False)}"

    # Realizar la consulta al agente
    resultado = Anthea.run(prompt)
    return resultado

def obtener_insights(df):
    try:
        # Consultar al agente para insights valiosos
        respuesta_insights = consulta("Insights Valiosos de los Datos.", df, insights=True)
    except Exception as e:
        # Manejar excepciones relacionadas con la consulta
        respuesta_insights = f"Lo siento, hubo un error al obtener insights valiosos: {e}"

    return respuesta_insights

def generar_pdf_reporte(df):
    # Verificar si el DataFrame tiene columnas
    if df.empty or df.columns.empty:
        mensaje_error = "El DataFrame no contiene datos o columnas. Por favor, verifica que el DataFrame se ha cargado correctamente y vuelve a intentarlo."
        return mensaje_error

    # Inicializar objeto de documento
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)

    # Lista para almacenar los elementos del PDF
    elementos = []

    try:
        # Estilos de párrafo
        estilos = getSampleStyleSheet()
        estilo_titulo = estilos['Title']
        estilo_normal = estilos['Normal']

        # Añadir título al PDF
        elementos.append(Paragraph("REPORTE: INSIGHTS VALIOSOS DE LOS DATOS", estilo_titulo))

        # Añadir prefacio al PDF
        elementos.append(Paragraph("Este reporte fue generado por Anthea, una asistente de análisis de datos creada en Marte para apoyar a todos los analistas y no analistas de todo el universo que deseen obtener conocimiento de sus datos.", estilo_normal))

        # Obtener insights valiosos
        respuesta_insights = obtener_insights(df)

        # Dividir la respuesta en párrafos y añadir al PDF
        elementos.extend([Paragraph(parrafo, estilo_normal) for parrafo in respuesta_insights.split('\n')])
        

        # Añadir marca de agua al PDF
        logo_path = os.path.join(settings.MEDIA_ROOT, 'Logo.jpeg')
        watermark = Image(logo_path, width=300, height=300)
        watermark.drawHeight = 100
        watermark.drawWidth = 100
        watermark.opacity = 0.1
        elementos.append(watermark)

    except Exception as e:
        # Manejar excepciones durante la generación del PDF
        mensaje_error = f"Error durante la generación del PDF: {e}"
        return mensaje_error

    finally:
        # Construir el PDF
        doc.build(elementos)

        # Guardar el PDF en el archivo (usa una ruta relativa al directorio 'media')
        buffer.seek(0)
        with open(os.path.join(settings.MEDIA_ROOT, 'Reporte.pdf'), 'wb') as f:
            f.write(buffer.read())

    return os.path.join(settings.MEDIA_ROOT, 'Reporte.pdf')

# ...

@csrf_exempt
def cargar_analizar_datos(request):
    if request.method == 'POST' and request.FILES.get('archivo'):
        archivo = request.FILES['archivo']

        # Manejar el archivo correctamente
        try:
            # Crear un archivo temporal con extensión .csv
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_file:
                temp_file.write(archivo.read())

            # Imprimir el contenido del archivo temporal
            with open(temp_file.name, 'r') as temp_file_read:
                print("Contenido del archivo temporal:")
                print(temp_file_read.read())

            # Leer el DataFrame desde el archivo temporal sin incluir el índice
            df = pd.read_csv(temp_file.name, index_col=False)

            # Imprimir las primeras filas del DataFrame para verificar
            print("Primeras filas del DataFrame:")
            print(df.head())

            # Visualizar el DataFrame antes de la descripción
            print("DataFrame antes de la descripción:")
            print(df)

            # Verificar si el DataFrame tiene columnas
            if df.empty or df.columns.empty:
                mensaje_error = "El DataFrame no contiene datos o columnas. Por favor, verifica que el DataFrame se ha cargado correctamente y vuelve a intentarlo."
                return JsonResponse({'error': mensaje_error})

            # Realizar el análisis de datos y generar el PDF
            reporte_pdf = generar_pdf_reporte(df)

        finally:
            # Eliminar el archivo temporal después del procesamiento
            os.remove(temp_file.name)

        # Devolver el PDF como respuesta
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="Reporte.pdf"'
        response.write(reporte_pdf)

        return response

    return JsonResponse({'error': 'Se esperaba un archivo en la solicitud POST.'})


# Vista para el modelo Feedback
class FeedbackView(viewsets.ModelViewSet):
    serializer_class = FeedbackSerializer
    queryset = Feedback.objects.all()
