"""
train.py
--------
Cubre los contenidos clave "scikit-learn: modelos clásicos" y
"Serialización de modelos".

Flujo:
  1. Cargar y limpiar el CSV (data_utils.py).
  2. Separar variables predictoras (X) y variable objetivo (y).
  3. Dividir en train/test.
  4. Construir un Pipeline de scikit-learn:
       - Preprocesamiento: escalado de numéricas + one-hot de categóricas
         (ColumnTransformer).
       - Modelo: RandomForestClassifier (modelo clásico de ensamble,
         robusto y sin necesidad de mucho ajuste fino).
  5. Entrenar y evaluar (accuracy + reporte de clasificación).
  6. Guardar el pipeline completo (preprocesamiento + modelo) con joblib,
     de modo que la inferencia posterior no necesite repetir la limpieza
     manual de columnas.

Ejecutar:
    python src/train.py
"""

from __future__ import annotations

import json
import os

import joblib
from data_utils import (
    COLUMNA_CATEGORICA,
    COLUMNA_OBJETIVO,
    COLUMNAS_NUMERICAS,
    cargar_y_limpiar,
)
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

RUTA_CSV = "data/clientes.csv"
RUTA_MODELO = "models/model.joblib"
RUTA_METADATA = "models/metadata.json"
RANDOM_SEED = 42


def construir_pipeline() -> Pipeline:
    """Arma el preprocesamiento + el modelo en un único Pipeline de sklearn."""
    preprocesador = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), COLUMNAS_NUMERICAS),
            ("cat", OneHotEncoder(handle_unknown="ignore"), [COLUMNA_CATEGORICA]),
        ]
    )

    modelo = RandomForestClassifier(
        n_estimators=200,
        max_depth=6,
        random_state=RANDOM_SEED,
        class_weight="balanced",
    )

    pipeline = Pipeline(
        steps=[
            ("preprocesamiento", preprocesador),
            ("clasificador", modelo),
        ]
    )
    return pipeline


def main() -> None:
    os.makedirs("models", exist_ok=True)

    print("1) Cargando y limpiando datos...")
    df = cargar_y_limpiar(RUTA_CSV)
    print(f"   Filas utilizables tras limpieza: {len(df)}")

    columnas_features = COLUMNAS_NUMERICAS + [COLUMNA_CATEGORICA]
    X = df[columnas_features]
    y = df[COLUMNA_OBJETIVO]

    print("2) Dividiendo train/test...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_SEED, stratify=y
    )

    print("3) Entrenando RandomForestClassifier dentro de un Pipeline...")
    pipeline = construir_pipeline()
    pipeline.fit(X_train, y_train)

    print("4) Evaluando en el conjunto de prueba...")
    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"   Accuracy: {acc:.3f}")
    print(classification_report(y_test, y_pred))

    print("5) Guardando modelo con joblib...")
    joblib.dump(pipeline, RUTA_MODELO)

    metadata = {
        "columnas_features": columnas_features,
        "columnas_numericas": COLUMNAS_NUMERICAS,
        "columna_categorica": COLUMNA_CATEGORICA,
        "columna_objetivo": COLUMNA_OBJETIVO,
        "clases": sorted(y.unique().tolist()),
        "accuracy_test": round(float(acc), 4),
        "modelo": "RandomForestClassifier",
    }
    with open(RUTA_METADATA, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"   Modelo guardado en: {RUTA_MODELO}")
    print(f"   Metadata guardada en: {RUTA_METADATA}")


if __name__ == "__main__":
    main()
