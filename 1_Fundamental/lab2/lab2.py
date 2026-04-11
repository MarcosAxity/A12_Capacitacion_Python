import json
from pathlib import Path


def load_json(filepath: str) -> dict | list:
    """Carga y valida un archivo JSON.

    Raises:
        FileNotFoundError: si el archivo no existe.
        json.JSONDecodeError: si el contenido no es JSON válido.
        PermissionError: si no hay permisos de lectura.
    """
    path = Path(filepath)

    if not path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {filepath}")

    if not path.is_file():
        raise ValueError(f"La ruta no apunta a un archivo: {filepath}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Formato JSON inválido en '{filepath}': {e.msg}", e.doc, e.pos
        )
    except PermissionError:
        raise PermissionError(f"Sin permisos para leer: {filepath}")


def filter_records(data: list[dict], **criteria) -> list[dict]:
    """Filtra registros por campos clave=valor arbitrarios."""
    results = []
    for record in data:
        if all(record.get(k) == v for k, v in criteria.items()):
            results.append(record)
    return results


def aggregate(data: list[dict], group_by: str, sum_field: str) -> dict:
    """Agrupa registros y suma un campo numérico por grupo."""
    totals: dict[str, float] = {}
    counts: dict[str, int] = {}

    for record in data:
        key = record.get(group_by, "unknown")
        value = record.get(sum_field, 0)

        if not isinstance(value, (int, float)):
            continue  # omite registros con tipo incorrecto

        totals[key] = totals.get(key, 0) + value
        counts[key] = counts.get(key, 0) + 1

    return {
        k: {"total": round(totals[k], 2), "count": counts[k]} for k in sorted(totals)
    }


def process_file(filepath: str) -> None:
    """Pipeline principal: carga → filtra → agrega → reporta."""
    print(f"\n{'='*50}")
    print(f"Procesando: {filepath}")
    print("=" * 50)

    try:
        data = load_json(filepath)
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        return
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON malformado — {e}")
        return
    except (PermissionError, ValueError) as e:
        print(f"[ERROR] {e}")
        return

    # Valida que sea una lista de dicts
    if not isinstance(data, list) or not all(isinstance(r, dict) for r in data):
        print("[ERROR] Se esperaba una lista de objetos JSON.")
        return

    print(f"[OK] {len(data)} registros cargados.")

    # --- Filtrado ---
    activos = filter_records(data, status="active")
    print(f"\nFiltro status='active': {len(activos)} resultado(s)")
    for r in activos:
        print(f"  · {r.get('name', 'N/A')} — ${r.get('amount', 0):.2f}")

    # --- Agregación ---
    print("\nAgregación por región (suma de 'amount'):")
    resumen = aggregate(data, group_by="region", sum_field="amount")
    for region, stats in resumen.items():
        print(f"  {region}: total=${stats['total']:.2f}, n={stats['count']}")


# ------------------------------------------------------------------ #
# Punto de entrada: prueba con tres escenarios distintos
# ------------------------------------------------------------------ #
if __name__ == "__main__":
    test_files = [
        "ventas.json",  # caso feliz
        "no_existe.json",  # archivo faltante
        "corrupto.json",  # JSON inválido
    ]
    for f in test_files:
        process_file(f)
