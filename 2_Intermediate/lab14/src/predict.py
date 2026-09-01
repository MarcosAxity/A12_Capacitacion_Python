"""
predict.py
----------
Cubre el contenido clave "inferencia básica" y el objetivo
"exponer inferencia mínima".

Carga el pipeline entrenado (preprocesamiento + modelo) guardado con
joblib, y lo usa para predecir sobre uno o varios clientes nuevos.

Uso 1 - Ejemplo de demostración (sin argumentos):
    python src/predict.py

Uso 2 - Pasando un cliente como JSON por línea de comandos:
    python src/predict.py --json '{"edad": 30, "antiguedad_meses": 5, "cargo_mensual": 90, "llamadas_soporte": 4, "tipo_contrato": "Mensual"}'
"""

from __future__ import annotations

import argparse
import json

import joblib
import pandas as pd

RUTA_MODELO = "models/model.joblib"
RUTA_METADATA = "models/metadata.json"

CLIENTE_EJEMPLO = {
    "edad": 30,
    "antiguedad_meses": 5,
    "cargo_mensual": 95.5,
    "llamadas_soporte": 4,
    "tipo_contrato": "Mensual",
}


def cargar_modelo():
    modelo = joblib.load(RUTA_MODELO)
    with open(RUTA_METADATA, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    return modelo, metadata


def predecir(modelo, metadata, registro: dict) -> dict:
    """Recibe un dict con los datos de un cliente y devuelve la predicción."""
    columnas = metadata["columnas_features"]
    faltantes = [c for c in columnas if c not in registro]
    if faltantes:
        raise ValueError(f"Faltan columnas requeridas: {faltantes}")

    df_nuevo = pd.DataFrame([registro])[columnas]

    prediccion = modelo.predict(df_nuevo)[0]
    probabilidades = modelo.predict_proba(df_nuevo)[0]
    clases = modelo.classes_

    resultado = {
        "prediccion_churn": int(prediccion),
        "probabilidades": {
            str(clase): round(float(prob), 4)
            for clase, prob in zip(clases, probabilidades)
        },
    }
    return resultado


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inferencia mínima del modelo de churn."
    )
    parser.add_argument(
        "--json",
        type=str,
        default=None,
        help="Datos del cliente en formato JSON. Si se omite, se usa un ejemplo por defecto.",
    )
    args = parser.parse_args()

    registro = json.loads(args.json) if args.json else CLIENTE_EJEMPLO

    modelo, metadata = cargar_modelo()
    resultado = predecir(modelo, metadata, registro)

    print("Datos de entrada:")
    print(json.dumps(registro, indent=2, ensure_ascii=False))
    print("\nResultado de la inferencia:")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
