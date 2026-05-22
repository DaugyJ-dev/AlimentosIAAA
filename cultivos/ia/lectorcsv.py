import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

ruta_csv = BASE_DIR / 'media' / 'csv' / 'Evaluaciones_Agropecuarias_Municipales_EVA_20260518.csv'

df = pd.read_csv(ruta_csv, low_memory=False)

# Convertir rendimiento a número
df['Rendimiento\n(t/ha)'] = pd.to_numeric(
    df['Rendimiento\n(t/ha)'],
    errors='coerce'
)

departamento = 'TOLIMA'

filtro = df[df['DEPARTAMENTO'] == departamento]

top_cultivos = (
    filtro.groupby('CULTIVO')['Rendimiento\n(t/ha)']
    .mean()
    .sort_values(ascending=False)
    .head(10)
)

print(top_cultivos)