import csv
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression


def leer_csv_seguro(ruta_csv):
    separadores = [';', ',', '\t', '|']
    encodings = ['utf-8', 'latin-1', 'utf-16']
    ultimo_error = None

    for encoding in encodings:
        for sep in separadores:
            try:
                df = pd.read_csv(
                    ruta_csv,
                    sep=sep,
                    encoding=encoding,
                    engine='python',
                    on_bad_lines='skip'
                )
                if not df.empty and len(df.columns) > 1:
                    return df
            except Exception as e:
                ultimo_error = e

            try:
                df = pd.read_csv(
                    ruta_csv,
                    sep=sep,
                    encoding=encoding,
                    engine='python',
                    on_bad_lines='skip',
                    quoting=csv.QUOTE_NONE
                )
                if not df.empty and len(df.columns) > 1:
                    return df
            except Exception as e:
                ultimo_error = e

    raise Exception(f'No se pudo leer el CSV. Último error: {ultimo_error}')


def normalizar_columnas(df):
    df.columns = (
        df.columns
        .str.strip()
        .str.replace('\n', ' ', regex=False)
        .str.replace('\r', ' ', regex=False)
        .str.replace('  ', ' ', regex=False)
    )
    return df


def clasificar_rendimiento(valor, serie_historica):
    q1 = float(serie_historica.quantile(0.25))
    q2 = float(serie_historica.quantile(0.50))
    q3 = float(serie_historica.quantile(0.75))

    if valor >= q3:
        return "MUY ALTO"
    elif valor >= q2:
        return "ALTO"
    elif valor >= q1:
        return "MEDIO"
    return "BAJO"


def explicar_rendimiento(valor):
    return (
        f"Esto significa que, por cada hectárea sembrada, se podrían producir "
        f"aproximadamente {round(valor, 2)} toneladas del cultivo."
    )


def estimar_cultivo(df_cultivo, anio_objetivo):
    df_cultivo = df_cultivo.copy()
    df_cultivo['AÑO'] = pd.to_numeric(df_cultivo['AÑO'], errors='coerce')
    df_cultivo['Rendimiento (t/ha)'] = pd.to_numeric(df_cultivo['Rendimiento (t/ha)'], errors='coerce')
    df_cultivo = df_cultivo.dropna(subset=['AÑO', 'Rendimiento (t/ha)'])

    if len(df_cultivo) < 2:
        return None

    anio_max_hist = int(df_cultivo['AÑO'].max())
    anio_min_hist = int(df_cultivo['AÑO'].min())

    # Limitar el año objetivo al rango histórico + máximo 3 años
    anio_clamped = min(anio_objetivo, anio_max_hist + 3)
    anio_clamped = max(anio_clamped, anio_min_hist)

    X = df_cultivo[['AÑO']].values
    y = df_cultivo['Rendimiento (t/ha)'].values

    modelo = LinearRegression()
    modelo.fit(X, y)

    pred_lineal = float(modelo.predict(np.array([[anio_clamped]]))[0])

    media_hist = float(df_cultivo['Rendimiento (t/ha)'].mean())
    max_hist = float(df_cultivo['Rendimiento (t/ha)'].max())
    min_hist = max(0.0, float(df_cultivo['Rendimiento (t/ha)'].min()))

    # Mezcla 40% tendencia lineal + 60% promedio histórico
    pred_ajustada = (pred_lineal * 0.4) + (media_hist * 0.6)

    # Acotar entre mínimo y máximo histórico del cultivo ± 20%
    limite_superior = max_hist * 1.2
    limite_inferior = min_hist * 0.8

    pred_ajustada = min(pred_ajustada, limite_superior)
    pred_ajustada = max(pred_ajustada, limite_inferior)

    return pred_ajustada

def recomendar_cultivo(ruta_csv, departamento, municipio, anio, hectareas):
    df = leer_csv_seguro(ruta_csv)
    df = normalizar_columnas(df)

    columnas_necesarias = [
        'DEPARTAMENTO',
        'MUNICIPIO',
        'AÑO',
        'CULTIVO',
        'Rendimiento (t/ha)'
    ]

    for col in columnas_necesarias:
        if col not in df.columns:
            raise Exception(f"No existe la columna requerida: {col}")

    df = df[columnas_necesarias].copy()

    df['DEPARTAMENTO'] = df['DEPARTAMENTO'].astype(str).str.strip().str.upper()
    df['MUNICIPIO'] = df['MUNICIPIO'].astype(str).str.strip().str.upper()
    df['CULTIVO'] = df['CULTIVO'].astype(str).str.strip().str.upper()
    df['AÑO'] = pd.to_numeric(df['AÑO'], errors='coerce')
    df['Rendimiento (t/ha)'] = pd.to_numeric(df['Rendimiento (t/ha)'], errors='coerce')

    df = df.dropna(subset=['DEPARTAMENTO', 'MUNICIPIO', 'CULTIVO', 'AÑO', 'Rendimiento (t/ha)'])

    departamento = str(departamento).strip().upper()
    municipio = str(municipio).strip().upper()
    anio = int(anio)
    hectareas = float(hectareas)

    df_local = df[
        (df['DEPARTAMENTO'] == departamento) &
        (df['MUNICIPIO'] == municipio)
    ].copy()

    if df_local.empty:
        return None

    resultados = []

    for cultivo in df_local['CULTIVO'].unique():
        df_cultivo = df_local[df_local['CULTIVO'] == cultivo].copy()

        pred = estimar_cultivo(df_cultivo, anio)
        if pred is None:
            continue

        nivel = clasificar_rendimiento(pred, df_local['Rendimiento (t/ha)'])
        produccion_estimada = pred * hectareas

        resultados.append({
            'cultivo': cultivo,
            'rendimiento': round(float(pred), 2),
            'nivel': nivel,
            'produccion_estimada': round(float(produccion_estimada), 2),
            'explicacion': explicar_rendimiento(pred)
        })

    if not resultados:
        return None

    resultados = sorted(resultados, key=lambda x: x['rendimiento'], reverse=True)

    principal = resultados[0]
    alternativo = resultados[1] if len(resultados) > 1 else None

    mensaje = (
        f"Para {municipio.title()}, {departamento.title()}, se recomienda sembrar "
        f"{principal['cultivo'].title()} porque presenta el mejor rendimiento estimado "
        f"para el año {anio}."
    )

    return {
        'principal': principal,
        'alternativo': alternativo,
        'anio': anio,
        'hectareas': hectareas,
        'mensaje': mensaje
    }