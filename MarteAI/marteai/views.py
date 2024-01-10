# views.py
from django.shortcuts import render
from rest_framework import viewsets
from .serializer import FeedbackSerializer
from .models import Feedback

import pandas as pd

from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
import tempfile  # Agregar import para manejar archivos temporales
from decouple import config

# Importar las librerías necesarias para la IA
from langchain.agents.agent_types import AgentType
from langchain.chat_models import ChatOpenAI
from langchain_experimental.agents import create_pandas_dataframe_agent



# Obtener la clave API de la variable de entorno
#openai_api_key = config("OPENAI_API_KEY")

# Conectar API
#os.environ["OPENAI_API_KEY"] = openai_api_key

# Crear y configurar el bot (Anthea)
Anthea = create_pandas_dataframe_agent(
    ChatOpenAI(
        temperature=0,
        model="gpt-4",
        api_key= "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" # Utiliza la variable de entorno openai_api_key
    ),
    pd.DataFrame(),  # Inicializar DataFrame vacío
    verbose=True,
    agent_type=AgentType.OPENAI_FUNCTIONS
)

formato = """
Data una pregunta del usuario:
1. Crea una consulta para DataFrame.
2. Revisa los resultados e interpretalos.
3. Devuelve el dato.
4. si tienes que hacer alguna aclaración o devolver cualquier texto que sea siempre en español y claro.
Observacion: No preguntes al final si necesito ayuda para seguir.
#{question}
"""

def consulta(input_usuario):
    consulta = formato.format(question=input_usuario)
    resultado = Anthea.run(consulta)
    return resultado

def obtener_prompt_especifico(ruta_archivo):
    nombre_archivo = os.path.basename(ruta_archivo)

    return {
        "Inicio": f"Aplica su conocimiento de los principios de la ciencia de datos para el archivo {nombre_archivo}.",
        "Relevantes": f"¿Qué información útil hay en estos datos para el archivo {nombre_archivo}?",
        "Que_Hacer": f"¿Cómo debería limpiarlos teóricamente sin utilizar código para el archivo {nombre_archivo}?",
    }

def generar_pdf_reporte(df):
    # Realizar la consulta con el DataFrame proporcionado
    respuestas = {
        "Inicio": consulta("Inicio"),  
        "Relevantes": consulta("Relevantes"),
        "Que_Hacer": consulta("Que_Hacer"),
    }

    # Inicializar objeto de documento
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)

    # Lista para almacenar los elementos del PDF
    elementos = []

    # Estilos de párrafo
    estilos = getSampleStyleSheet()
    estilo_titulo = estilos['Title']
    estilo_normal = estilos['Normal']

    # Añadir título al PDF
    elementos.append(Paragraph("REPORTE: ANALISIS EXPLORATORIO DE DATOS", estilo_titulo))

    # Añadir prefacio al PDF
    elementos.append(Paragraph("Este reporte fue generado por Anthea, una asistente de análisis de datos creada en Marte para apoyar a todos los analistas y no analistas de todo el universo que deseen obtener conocimiento de sus datos.", estilo_normal))

    # Añadir respuestas al PDF
    for pregunta, respuesta in respuestas.items():
        elementos.append(Paragraph(f"{pregunta}: {respuesta}", estilo_normal))

    # Añadir marca de agua al PDF
    logo_path = os.path.join(settings.MEDIA_ROOT, 'Logo.jpeg')
    watermark = Image(logo_path, width=300, height=300)
    watermark.drawHeight = 100
    watermark.drawWidth = 100
    watermark.opacity = 0.1
    elementos.append(watermark)

    # Construir el PDF
    doc.build(elementos)

    # Guardar el PDF en el archivo (usa una ruta relativa al directorio 'media')
    buffer.seek(0)
    with open(os.path.join(settings.MEDIA_ROOT, 'Reporte.pdf'), 'wb') as f:
        f.write(buffer.read())

    return os.path.join(settings.MEDIA_ROOT, 'Reporte.pdf')

@csrf_exempt
def cargar_analizar_datos(request):
    if request.method == 'POST' and request.FILES.get('archivo'):
        archivo = request.FILES['archivo']

        # Manejar el archivo correctamente
        try:
            # Crear un archivo temporal con extensión .csv
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_file:
                temp_file.write(archivo.read())

            # Leer el DataFrame desde el archivo temporal
            df = pd.read_csv(temp_file.name)
            
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
