import base64
import io
import csv
import json
import pandas as pd
import matplotlib
from .ia.predictor import recomendar_cultivo
from .models import CultivoCSV, HistorialPrediccion

matplotlib.use('Agg')

import matplotlib.pyplot as plt

from django.shortcuts import (
    render,
    redirect,
    get_object_or_404
)

from django.contrib import messages

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    r2_score,
    mean_squared_error
)

from .models import (
    CultivoCSV,
    PrediccionResultado
)

from .forms import (
    CSVUploadForm,
    PrediccionForm
)

from .ia.predictor import recomendar_cultivo


def home(request):

    archivos = CultivoCSV.objects.all().order_by(
        '-fecha_subida'
    )

    return render(
        request,
        'cultivos/home.html',
        {'archivos': archivos}
    )


def cargar_csv(request):

    if request.method == 'POST':

        form = CSVUploadForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            archivo_subido = request.FILES.get(
                'archivo'
            )

            if (
                archivo_subido and
                not archivo_subido.name.lower().endswith('.csv')
            ):

                messages.error(
                    request,
                    'Solo se permiten archivos .csv'
                )

                return render(
                    request,
                    'cultivos/cargar_csv.html',
                    {'form': form}
                )

            obj = form.save()

            messages.success(
                request,
                'Archivo CSV cargado correctamente.'
            )

            return redirect(
                'explorar_datos',
                csv_id=obj.id
            )

    else:
        form = CSVUploadForm()

    return render(
        request,
        'cultivos/cargar_csv.html',
        {'form': form}
    )


def explorar_datos(request, csv_id):

    csv_obj = get_object_or_404(
        CultivoCSV,
        id=csv_id
    )

    try:

        df, separador_usado, encoding_usado = (
            leer_csv_seguro(
                csv_obj.archivo.path
            )
        )

        df.columns = df.columns.str.strip()

        columnas = df.columns.tolist()

        total_filas = len(df)

        preview_df = df.head(10).fillna('')

        preview_filas = preview_df.values.tolist()

        cultivos = []

        departamentos = []

        anios = []

        columnas_mayus = [
            c.upper().strip()
            for c in columnas
        ]

        if 'CULTIVO' in columnas_mayus:

            col = columnas[
                columnas_mayus.index('CULTIVO')
            ]

            cultivos = (
                df[col]
                .dropna()
                .astype(str)
                .unique()
                .tolist()[:20]
            )

        if 'DEPARTAMENTO' in columnas_mayus:

            col = columnas[
                columnas_mayus.index('DEPARTAMENTO')
            ]

            departamentos = (
                df[col]
                .dropna()
                .astype(str)
                .unique()
                .tolist()[:20]
            )

        if 'AÑO' in columnas_mayus:

            col = columnas[
                columnas_mayus.index('AÑO')
            ]

            anios = (
                df[col]
                .dropna()
                .astype(str)
                .unique()
                .tolist()[:20]
            )

        elif 'ANIO' in columnas_mayus:

            col = columnas[
                columnas_mayus.index('ANIO')
            ]

            anios = (
                df[col]
                .dropna()
                .astype(str)
                .unique()
                .tolist()[:20]
            )

        contexto = {
            'csv_obj': csv_obj,
            'error': None,
            'info': {
                'filas': total_filas,
                'columnas': columnas,
                'preview_filas': preview_filas,
                'cultivos': cultivos,
                'departamentos': departamentos,
                'anios': anios,
                'separador': separador_usado,
                'encoding': encoding_usado,
            }
        }

    except Exception as e:

        contexto = {
            'csv_obj': csv_obj,
            'error': f'Error al leer el archivo: {e}',
            'info': {
                'filas': 0,
                'columnas': [],
                'preview_filas': [],
                'cultivos': [],
                'departamentos': [],
                'anios': [],
                'separador': '',
                'encoding': '',
            }
        }

    return render(
        request,
        'cultivos/explorar.html',
        contexto
    )


def leer_csv_seguro(ruta):

    separadores = [';', ',', '\t', '|']

    encodings = [
        'utf-8',
        'latin-1',
        'utf-16'
    ]

    ultimo_error = None

    for encoding in encodings:

        for sep in separadores:

            try:

                df = pd.read_csv(
                    ruta,
                    sep=sep,
                    encoding=encoding,
                    engine='python',
                    on_bad_lines='skip'
                )

                if (
                    not df.empty and
                    len(df.columns) > 1
                ):

                    df.columns = (
                        df.columns.str.strip()
                    )

                    return df, sep, encoding

            except Exception as e:
                ultimo_error = e

    raise Exception(
        f'No se pudo leer el CSV. '
        f'Último error: {ultimo_error}'
    )


def predecir(request, csv_id):

    csv_obj = get_object_or_404(
        CultivoCSV,
        id=csv_id
    )

    contexto = {
        'csv_obj': csv_obj,
        'cultivos': [],
        'departamentos': [],
        'resultado': None,
        'grafico_b64': None,
    }

    try:

        df = pd.read_csv(
            csv_obj.archivo.path,
            sep=None,
            engine='python'
        )

        df.columns = df.columns.str.strip()

        columnas = [
            c.upper()
            for c in df.columns
        ]

        if 'CULTIVO' in columnas:

            col_cultivo = df.columns[
                columnas.index('CULTIVO')
            ]

            contexto['cultivos'] = (
                df[col_cultivo]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

        if 'DEPARTAMENTO' in columnas:

            col_departamento = df.columns[
                columnas.index('DEPARTAMENTO')
            ]

            contexto['departamentos'] = (
                df[col_departamento]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

    except Exception as e:

        messages.error(
            request,
            f'No se pudo leer el CSV: {e}'
        )

    return render(
        request,
        'cultivos/predecir.html',
        contexto
    )


def resultados(request):
    preds = HistorialPrediccion.objects.all()
    return render(request, 'cultivos/resultados.html', {'preds': preds})


def prediccion(request, csv_id):
    resultado = None
    csv_obj = get_object_or_404(CultivoCSV, id=csv_id)

    try:
        depto_mun = obtener_departamentos_municipios(csv_obj.archivo.path)
        departamentos = sorted(depto_mun.keys())
    except Exception as e:
        depto_mun = {}
        departamentos = []
        messages.error(request, f'Error leyendo CSV: {e}')

    depto_choices = [('', '— Selecciona departamento —')] + [(d, d.title()) for d in departamentos]

    if request.method == 'POST':
        form = PrediccionForm(request.POST)
        form.fields['departamento'].choices = depto_choices

        departamento_post = request.POST.get('departamento', '').strip().upper()
        municipios_post = depto_mun.get(departamento_post, [])
        form.fields['municipio'].choices = [('', '— Selecciona municipio —')] + [
            (m, m.title()) for m in municipios_post
        ]

        if form.is_valid():
            departamento = form.cleaned_data['departamento']
            municipio = form.cleaned_data['municipio']
            anio = form.cleaned_data['periodo']
            hectareas = form.cleaned_data['hectareas']

            try:
                resultado = recomendar_cultivo(
                    csv_obj.archivo.path,
                    departamento,
                    municipio,
                    anio,
                    hectareas
                )

                if resultado is None:
                    messages.warning(request, 'No se encontraron datos para ese municipio.')
                else:
                    HistorialPrediccion.objects.create(
                        csv=csv_obj,
                        departamento=departamento,
                        municipio=municipio,
                        anio=anio,
                        hectareas=hectareas,
                        cultivo_principal=resultado['principal']['cultivo'],
                        rendimiento_principal=resultado['principal']['rendimiento'],
                        nivel_principal=resultado['principal']['nivel'],
                        produccion_principal=resultado['principal']['produccion_estimada'],
                        cultivo_alternativo=resultado['alternativo']['cultivo'] if resultado.get('alternativo') else None,
                        rendimiento_alternativo=resultado['alternativo']['rendimiento'] if resultado.get('alternativo') else None,
                        nivel_alternativo=resultado['alternativo']['nivel'] if resultado.get('alternativo') else None,
                        produccion_alternativa=resultado['alternativo']['produccion_estimada'] if resultado.get('alternativo') else None,
                    )

            except Exception as e:
                messages.error(request, f'Error en la predicción: {e}')
    else:
        form = PrediccionForm()
        form.fields['departamento'].choices = depto_choices
        form.fields['municipio'].choices = [('', '— Selecciona municipio —')]

    return render(
        request,
        'cultivos/prediccion.html',
        {
            'form': form,
            'resultado': resultado,
            'csv_obj': csv_obj,
            'depto_mun_json': json.dumps(depto_mun),
        }
    )

def historial(request):
    registros = PrediccionResultado.objects.all().order_by('-fecha_generacion')[:50]

    return render(
        request,
        'cultivos/historial.html',
        {
            'registros': registros
        }
    )


def obtener_departamentos_municipios(csv_path):
    df, _, _ = leer_csv_seguro(csv_path)
    df.columns = df.columns.str.strip()

    columnas_mayus = [c.upper().strip() for c in df.columns]

    if 'DEPARTAMENTO' not in columnas_mayus or 'MUNICIPIO' not in columnas_mayus:
        return {}

    col_departamento = df.columns[columnas_mayus.index('DEPARTAMENTO')]
    col_municipio = df.columns[columnas_mayus.index('MUNICIPIO')]

    df[col_departamento] = df[col_departamento].astype(str).str.strip().str.upper()
    df[col_municipio] = df[col_municipio].astype(str).str.strip().str.upper()

    depto_mun = (
        df.groupby(col_departamento)[col_municipio]
        .apply(lambda x: sorted(x.dropna().unique().tolist()))
        .to_dict()
    )

    return depto_mun