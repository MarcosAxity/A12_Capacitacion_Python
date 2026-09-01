"""
data_utils.py
-------------
Funciones de carga y limpieza de datos.

Cubre el contenido clave "NumPy, Polars y Pandas":
  - Pandas: es la herramienta principal usada para cargar el CSV, limpiar
    tipos, imputar nulos y preparar el DataFrame que consume scikit-learn.
  - NumPy: se usa por debajo de Pandas para operaciones vectorizadas
    (cálculo de medianas, máscaras booleanas, np.nan) y aquí se usa también
    de forma explícita para mostrar su uso directo.
  - Polars: se incluye una función equivalente de lectura rápida con Polars
    (motor en Rust, más veloz en datasets grandes) y se muestra cómo
    convertir su resultado a Pandas para seguir el flujo con scikit-learn.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import polars as pl

COLUMNAS_NUMERICAS = ["edad", "antiguedad_meses", "cargo_mensual", "llamadas_soporte"]
COLUMNA_CATEGORICA = "tipo_contrato"
COLUMNA_OBJETIVO = "churn"


def leer_csv_con_polars(ruta_csv: str) -> pd.DataFrame:
    """
    Ejemplo de lectura con Polars (más rápida en CSVs grandes gracias a su
    motor en Rust y ejecución en paralelo). Devolvemos un DataFrame de
    Pandas al final porque scikit-learn trabaja de forma nativa con
    arrays de NumPy / Pandas, no con Polars.
    """
    df_pl = pl.read_csv(ruta_csv, infer_schema_length=1000)
    print(f"[Polars] Filas leídas: {df_pl.height}, columnas: {df_pl.width}")
    return df_pl.to_pandas()


def cargar_csv(ruta_csv: str) -> pd.DataFrame:
    """Carga el CSV con Pandas."""
    df = pd.read_csv(ruta_csv)
    return df


def limpiar_datos(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpieza del dataset "sucio":
      1. Elimina duplicados exactos.
      2. Normaliza texto en la columna categórica (quita espacios, capitaliza).
      3. Convierte 'antiguedad_meses' (a veces guardada como texto, p.ej.
         " 12 meses") a numérico usando extracción de dígitos.
      4. Fuerza tipo numérico en las columnas numéricas (valores no
         convertibles quedan como NaN).
      5. Imputa nulos numéricos con la mediana (usando NumPy para el cálculo).
      6. Descarta filas sin etiqueta (churn nulo), porque no sirven para
         entrenamiento supervisado.
    """
    df = df.copy()

    # 1) Duplicados
    df = df.drop_duplicates(subset=[c for c in df.columns if c != "cliente_id"])

    # 2) Texto categórico
    df[COLUMNA_CATEGORICA] = (
        df[COLUMNA_CATEGORICA].astype(str).str.strip().str.capitalize()
    )

    # 3) 'antiguedad_meses' puede venir como " 12 meses" (texto) o como número
    def _a_numero(valor):
        if pd.isna(valor):
            return np.nan
        if isinstance(valor, (int, float)):
            return float(valor)
        digitos = "".join(ch for ch in str(valor) if ch.isdigit())
        return float(digitos) if digitos else np.nan

    df["antiguedad_meses"] = df["antiguedad_meses"].apply(_a_numero)

    # 4) Forzar numérico en el resto de columnas numéricas
    for col in COLUMNAS_NUMERICAS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 5) Imputar nulos numéricos con la mediana (NumPy)
    for col in COLUMNAS_NUMERICAS:
        mediana = np.nanmedian(df[col].to_numpy())
        df[col] = df[col].fillna(mediana)

    # 6) Descartar filas sin etiqueta objetivo
    df[COLUMNA_OBJETIVO] = pd.to_numeric(df[COLUMNA_OBJETIVO], errors="coerce")
    df = df.dropna(subset=[COLUMNA_OBJETIVO])
    df[COLUMNA_OBJETIVO] = df[COLUMNA_OBJETIVO].astype(int)

    df = df.reset_index(drop=True)
    return df


def cargar_y_limpiar(ruta_csv: str) -> pd.DataFrame:
    """Pipeline completo: cargar con Pandas y limpiar."""
    df_crudo = cargar_csv(ruta_csv)
    df_limpio = limpiar_datos(df_crudo)
    return df_limpio


if __name__ == "__main__":
    # Demostración rápida por consola
    df_limpio = cargar_y_limpiar("data/clientes.csv")
    print(df_limpio.head())
    print(df_limpio.info())

    # Demostración de la lectura equivalente con Polars
    df_polars = leer_csv_con_polars("data/clientes.csv")
    print(df_polars.head())
