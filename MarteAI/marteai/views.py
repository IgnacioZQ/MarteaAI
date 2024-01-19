from django.shortcuts import render
from rest_framework import viewsets
from .serializer import FeedbackSerializer
from .models import Feedback

import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Usar el backend 'Agg' que no requiere interfaz gráfica
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

# Definir estilos de párrafo en el ámbito global
estilos = getSampleStyleSheet()
estilo_titulo = estilos['Title']
estilo_normal = estilos['Normal']

# Crear y configurar el bot (Anthea)
Anthea = create_pandas_dataframe_agent(
    ChatOpenAI(
        temperature=0,
        model="gpt-3.5-turbo",  # Cambiar el modelo a "gpt-3.5-turbo"
        api_key=  # Utiliza la variable de entorno openai_api_key, copiar aquí la clave
    ),
    pd.DataFrame(),  # Inicializar DataFrame vacío
    verbose=True,
    agent_type=AgentType.OPENAI_FUNCTIONS
)

formato = """
¡Hola! Eres Anthea, una asistente de análisis de datos creada en Marte para apoyar a todos los analistas y no analistas de todo el universo que deseen obtener conocimiento de sus datos:
1. ¿Podrías proporcionar una descripción sobre {question}?
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

def generar_grafico(df, columna, elementos):
    plt.switch_backend('Agg')  # Cambiar a 'Agg' para evitar problemas con GUI

    plt.figure(figsize=(8, 6))
    temp_img_path = None

    # Lógica para generar gráfico según el tipo de datos en la columna
    if pd.api.types.is_numeric_dtype(df[columna]):
        df[columna].plot(kind='hist', bins=20)
        plt.title(f'Distribución de {columna}')
        plt.xlabel(columna)
        plt.ylabel('Frecuencia')
        plt.tight_layout()

        # Guardar el gráfico como una imagen temporal
        temp_img_path = os.path.join(settings.MEDIA_ROOT, f'grafico_{columna}.png')
        plt.savefig(temp_img_path)
        plt.close()

        # Añadir gráfico al PDF si temp_img_path está definido
        if temp_img_path is not None and os.path.exists(temp_img_path):
            img = Image(temp_img_path, width=400, height=300)
            elementos.append(img)  # Añadir el elemento a la lista

    return temp_img_path

def obtener_insights(df, elementos):
    try:
        # Consultar al agente para insights valiosos
        respuesta_insights = consulta("Insights Valiosos de los Datos.", df, insights=True)

        # Dividir la respuesta en párrafos y añadir al PDF
        parrafos_insights = respuesta_insights.split('\n')

        # Evitar agregar el saludo de Anthea nuevamente si ya está presente en la respuesta
        if parrafos_insights and parrafos_insights[0].startswith("¡Hola! Soy Anthea"):
            parrafos_insights = parrafos_insights[1:]

        elementos.extend([Paragraph(parrafo, estilo_normal) for parrafo in parrafos_insights])

        # Generar gráficos y descripciones para columnas específicas
        columnas_para_graficos = df.select_dtypes(include=['number', 'category']).columns.tolist()
        for columna in columnas_para_graficos:
            temp_img_path = generar_grafico(df, columna, elementos)  # Pasar la lista elementos
            if temp_img_path:
                elementos.append(Paragraph(f'Gráfico relacionado con la columna {columna}.', estilo_normal))

    except Exception as e:
        # Manejar excepciones relacionadas con la consulta y generación del gráfico
        respuesta_error = f"Lo siento, hubo un error al obtener insights valiosos: {e}"
        elementos.append(Paragraph(respuesta_error, estilo_normal))

    return elementos


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
        # Añadir título al PDF
        elementos.append(Paragraph("REPORTE: INSIGHTS VALIOSOS DE LOS DATOS", estilo_titulo))

        # Añadir prefacio al PDF
        prefacio = """
        Este reporte fue generado por Anthea, una asistente de análisis de datos creada en Marte para apoyar
        a todos los analistas y no analistas de todo el universo que deseen obtener conocimiento de sus datos.
        ¡Hola! Soy Anthea, tu asistente de análisis de datos. Aquí tienes el análisis exploratorio de datos (EDA)
        para el archivo "Insights Valiosos de los Datos":
        """
        elementos.append(Paragraph(prefacio, estilo_normal))

        # Obtener insights valiosos
        elementos = obtener_insights(df, elementos)

        # Añadir marca de agua al PDF
        logo_path = os.path.join(settings.MEDIA_ROOT, 'Logo.png')
        watermark = Image(logo_path, width=300, height=300)
        watermark.drawHeight = 100
        watermark.drawWidth = 100
        watermark.opacity = 0.1
        elementos.append(watermark)

        # Construir el PDF
        doc.build(elementos)

        # Guardar el PDF en el archivo (usa una ruta relativa al directorio 'media')
        buffer.seek(0)
        pdf_path = os.path.join(settings.MEDIA_ROOT, 'Reporte.pdf')
        with open(pdf_path, 'wb') as f:
            f.write(buffer.read())

    except Exception as e:
        # Manejar excepciones durante la generación del PDF
        mensaje_error = f"Error durante la generación del PDF: {e}"
        return mensaje_error

    finally:
        buffer.close()  # Cerrar el buffer después de usarlo

    return pdf_path  # Devolver la ruta del PDF generado

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
