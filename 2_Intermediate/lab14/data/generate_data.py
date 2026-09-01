"""
generate_data.py
-----------------
Genera un dataset sintético de "cancelación de clientes" (churn) con datos
intencionalmente sucios (valores nulos, texto con espacios, tipos mezclados)
para que el laboratorio tenga sentido: primero hay que limpiar, luego entrenar.

Ejecutar:
    python data/generate_data.py

Genera:
    data/clientes.csv
"""

import numpy as np
import pandas as pd

RANDOM_SEED = 42
N_ROWS = 600


def generar_dataset(n_rows: int = N_ROWS, seed: int = RANDOM_SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    edad = rng.integers(18, 75, size=n_rows).astype(float)
    antiguedad_meses = rng.integers(0, 72, size=n_rows).astype(float)
    cargo_mensual = np.round(rng.normal(60, 20, size=n_rows), 2)
    cargo_mensual = np.clip(cargo_mensual, 10, None)
    llamadas_soporte = rng.poisson(1.5, size=n_rows).astype(float)

    tipo_contrato = rng.choice(
        ["Mensual", "Anual", "Bianual"], size=n_rows, p=[0.55, 0.30, 0.15]
    )

    # La probabilidad de cancelar (churn) depende de forma lógica de las
    # variables anteriores, para que el modelo tenga patrones reales que aprender.
    logit = (
        -1.5
        + 0.04 * (cargo_mensual - 60)
        - 0.02 * antiguedad_meses
        + 0.35 * llamadas_soporte
        + np.where(tipo_contrato == "Mensual", 0.8, 0.0)
        + np.where(tipo_contrato == "Bianual", -0.8, 0.0)
    )
    prob_churn = 1 / (1 + np.exp(-logit))
    churn = rng.binomial(1, prob_churn)

    df = pd.DataFrame(
        {
            "cliente_id": np.arange(1, n_rows + 1),
            "edad": edad,
            "antiguedad_meses": antiguedad_meses,
            "cargo_mensual": cargo_mensual,
            "llamadas_soporte": llamadas_soporte,
            "tipo_contrato": tipo_contrato,
            "churn": churn,
        }
    )

    # --- Ensuciamos el dataset a propósito (esto es lo que se debe limpiar) ---

    # 1) Valores nulos aleatorios en columnas numéricas
    for col in ["edad", "cargo_mensual", "llamadas_soporte"]:
        idx_nulos = rng.choice(n_rows, size=int(n_rows * 0.05), replace=False)
        df.loc[idx_nulos, col] = np.nan

    # 2) Texto con espacios/mayúsculas inconsistentes en tipo_contrato
    idx_texto_sucio = rng.choice(n_rows, size=int(n_rows * 0.15), replace=False)
    df.loc[idx_texto_sucio, "tipo_contrato"] = (
        df.loc[idx_texto_sucio, "tipo_contrato"]
        .str.lower()
        .str.pad(width=10, side="both")
    )

    # 3) 'antiguedad_meses' guardada como texto en algunas filas (tipo mixto)
    idx_texto_num = rng.choice(n_rows, size=int(n_rows * 0.08), replace=False)
    df["antiguedad_meses"] = df["antiguedad_meses"].astype(object)
    df.loc[idx_texto_num, "antiguedad_meses"] = df.loc[
        idx_texto_num, "antiguedad_meses"
    ].apply(lambda x: f" {x:.0f} meses")

    # 4) Algunas filas duplicadas
    duplicados = df.sample(n=8, random_state=seed)
    df = pd.concat([df, duplicados], ignore_index=True)

    # 5) Unas pocas filas sin etiqueta (churn nulo) — se descartan al entrenar
    idx_sin_etiqueta = rng.choice(len(df), size=5, replace=False)
    df["churn"] = df["churn"].astype(object)
    df.loc[idx_sin_etiqueta, "churn"] = np.nan

    return df


if __name__ == "__main__":
    df = generar_dataset()
    out_path = "data/clientes.csv"
    df.to_csv(out_path, index=False)
    print(f"Dataset generado: {out_path} ({len(df)} filas)")
