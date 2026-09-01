# Módulo 14 — Ciencia de Datos

Laboratorio práctico: limpieza de un CSV, entrenamiento de un clasificador con
scikit-learn, serialización con `joblib` y una inferencia mínima.

---

## 1. Contenidos clave — qué se revisa y por qué

### NumPy, Polars y Pandas
Son las tres librerías base para trabajar con datos tabulares en Python, y
cada una cumple un rol distinto en este proyecto:

- **Pandas** es la herramienta principal de manipulación de datos: se usa
  para leer el CSV, detectar y corregir tipos incorrectos, quitar
  duplicados, normalizar texto e imputar valores nulos (`src/data_utils.py`).
- **NumPy** es el motor numérico que está por debajo de Pandas (todo
  `DataFrame` se apoya en arrays de NumPy). Además de usarse implícitamente,
  se usa de forma explícita para calcular la mediana (`np.nanmedian`) al
  imputar valores faltantes.
- **Polars** es una alternativa moderna a Pandas, escrita en Rust, más
  rápida en datasets grandes gracias a su ejecución en paralelo y su
  optimizador de consultas ("lazy evaluation"). Se incluye la función
  `leer_csv_con_polars` para mostrar su sintaxis y cómo convertir el
  resultado a Pandas para seguir el flujo con scikit-learn.

### scikit-learn: modelos clásicos
Se entrena un **`RandomForestClassifier`**, un modelo clásico de ensamble
(combina muchos árboles de decisión). Se eligió porque:
- Funciona bien "out of the box" sin mucho ajuste de hiperparámetros.
- Maneja de forma natural variables numéricas y categóricas (tras
  codificarlas).
- Es robusto frente a valores atípicos y relaciones no lineales, algo común
  en datos reales.

El modelo se integra en un **`Pipeline`** de scikit-learn junto con el
preprocesamiento (`StandardScaler` para numéricas, `OneHotEncoder` para
categóricas mediante un `ColumnTransformer`). Esto es una buena práctica
porque garantiza que **exactamente la misma transformación** aplicada en
entrenamiento se aplique después en inferencia, sin duplicar lógica.

### Serialización de modelos e inferencia básica
Un modelo entrenado en memoria no sirve de nada si no puede reutilizarse.
Por eso:
- El pipeline completo (preprocesamiento + modelo) se guarda en disco con
  **`joblib`**, la librería estándar recomendada por scikit-learn para
  serializar objetos que contienen arrays de NumPy (más eficiente que
  `pickle` para este caso).
- Se guarda además un archivo `metadata.json` con las columnas esperadas,
  las clases del modelo y la métrica obtenida, para que el script de
  inferencia sepa qué formato de entrada requiere sin tener que adivinarlo.
- El script `predict.py` carga ese modelo guardado y expone una función de
  **inferencia mínima**: recibe los datos de un cliente nuevo y devuelve la
  predicción de churn y sus probabilidades.

---

## 2. Objetivos — por qué deben cumplirse

**Objetivo 1: "Manipular datos y entrenar un modelo simple"**
Este objetivo se cumple porque es la habilidad central de cualquier
proyecto de ciencia de datos: los datos del mundo real casi nunca llegan
limpios (nulos, tipos mezclados, texto inconsistente, duplicados). Un
modelo, por más sofisticado que sea, produce resultados incorrectos si se
entrena con datos sucios ("garbage in, garbage out"). Por eso el
laboratorio parte de un CSV deliberadamente sucio: obliga a practicar la
limpieza antes de poder entrenar cualquier modelo de forma confiable.

**Objetivo 2: "Exponer inferencia mínima"**
Entrenar un modelo no es el final del proceso: en un entorno productivo el
modelo necesita poder **usarse** para predecir sobre datos nuevos, sin
tener que volver a entrenarlo cada vez. Cumplir este objetivo demuestra el
ciclo completo de un proyecto de ML aplicado: **datos → modelo entrenado →
modelo persistido → modelo consumido**, que es la base de cualquier
sistema de ML en producción (una API, un batch job, etc.).

---

## 3. Descripción de la solución

```
modulo14/
├── README.md
├── requirements.txt
├── data/
│   ├── generate_data.py      # genera el CSV sintético "sucio"
│   └── clientes.csv          # dataset generado (se crea al ejecutar el script)
├── models/                   # se crea al entrenar
│   ├── model.joblib          # pipeline (preprocesamiento + modelo) serializado
│   └── metadata.json         # columnas esperadas, clases y accuracy
└── src/
    ├── data_utils.py         # carga y limpieza (Pandas / NumPy / Polars)
    ├── train.py               # entrenamiento + evaluación + guardado con joblib
    └── predict.py              # carga del modelo + inferencia mínima
```

**Problema de negocio simulado:** predecir si un cliente va a **cancelar su
servicio (`churn`)** en función de su edad, antigüedad, cargo mensual,
número de llamadas a soporte y tipo de contrato.

**Flujo de datos:**
1. `generate_data.py` crea `data/clientes.csv`: un dataset de ~600 clientes
   con problemas típicos de datos reales (nulos, texto con espacios y
   mayúsculas inconsistentes, una columna numérica guardada a veces como
   texto, filas duplicadas y algunas etiquetas faltantes).
2. `data_utils.py` carga ese CSV con Pandas y lo limpia: normaliza texto,
   convierte tipos, imputa nulos numéricos con la mediana y descarta filas
   sin etiqueta.
3. `train.py` toma los datos limpios, separa entrenamiento/prueba, entrena
   un `RandomForestClassifier` dentro de un `Pipeline` de scikit-learn,
   imprime accuracy y un reporte de clasificación, y guarda el pipeline
   entrenado con `joblib` junto con un `metadata.json`.
4. `predict.py` carga ese pipeline guardado y predice sobre un cliente
   nuevo (de ejemplo o pasado por línea de comandos en JSON), mostrando la
   clase predicha (0 = no cancela, 1 = cancela) y las probabilidades.

---

## 4. Cómo ejecutar el laboratorio, paso a paso

### Requisitos
- Python 3.10 o superior.

### Paso 1 — Instalar dependencias
Desde la carpeta raíz del proyecto (`modulo14/`):

```bash
pip install -r requirements.txt
```

### Paso 2 — Generar el dataset (cargar/preparar el CSV)

```bash
python data/generate_data.py
```

Esto crea `data/clientes.csv`. Puedes inspeccionar el archivo con
cualquier editor de texto o abrirlo con Pandas/Excel: notarás celdas
vacías, espacios en `tipo_contrato` y valores como `" 12 meses"` en
`antiguedad_meses`: eso es lo que el paso de limpieza corregirá.

*(Opcional)* Ver la limpieza por separado, sin entrenar todavía:

```bash
python src/data_utils.py
```

Esto imprime el `DataFrame` ya limpio y una demostración de lectura con
Polars.

### Paso 3 — Entrenar el clasificador y guardarlo

```bash
python src/train.py
```

Este comando:
- Carga y limpia `data/clientes.csv`.
- Divide los datos en 80% entrenamiento / 20% prueba.
- Entrena el `RandomForestClassifier` dentro del `Pipeline`.
- Imprime el `accuracy` y el reporte de precisión/recall/F1 por clase.
- Guarda el modelo en `models/model.joblib` y sus metadatos en
  `models/metadata.json`.

### Paso 4 — Probar la inferencia

Con el ejemplo por defecto incluido en el script:

```bash
python src/predict.py
```

O pasando los datos de un cliente propio en formato JSON:

```bash
python src/predict.py --json '{"edad": 45, "antiguedad_meses": 30, "cargo_mensual": 55, "llamadas_soporte": 1, "tipo_contrato": "Anual"}'
```

Salida esperada (ejemplo):

```json
{
  "prediccion_churn": 0,
  "probabilidades": {
    "0": 0.83,
    "1": 0.17
  }
}
```

Donde `prediccion_churn = 1` significa que el modelo predice que el
cliente cancelará el servicio, y `0` que se mantendrá activo.

### Notas
- Si se vuelve a generar el dataset (`generate_data.py`), los datos
  cambiarán ligeramente porque se usa una semilla fija (`RANDOM_SEED = 42`)
  solo para reproducibilidad del ejemplo; el flujo sigue siendo el mismo.
- Para reentrenar con nuevos datos, basta con reemplazar
  `data/clientes.csv` (respetando las mismas columnas) y volver a ejecutar
  `python src/train.py`.
