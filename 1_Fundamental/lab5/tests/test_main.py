from src.main import (
    Persona,
    buscar_en_lista,
    calcular_promedio,
    saludar,
    sumar,
)


def test_sumar() -> None:
    """Prueba suma de números."""
    assert sumar(2, 3) == 5
    assert sumar(0, 0) == 0


def test_saludar() -> None:
    """Prueba generación de saludo."""
    assert saludar("Ana") == "Hola Ana"


def test_buscar_en_lista() -> None:
    """Prueba búsqueda en lista."""
    items = ["manzana", "pera", "naranja"]
    assert buscar_en_lista(items, "pera") == "pera"
    assert buscar_en_lista(items, "uva") is None


def test_calcular_promedio() -> None:
    """Prueba cálculo de promedio."""
    assert calcular_promedio([10.0, 20.0, 30.0]) == 20.0
    assert calcular_promedio([]) == 0.0


def test_persona() -> None:
    """Prueba clase Persona."""
    persona = Persona("Luis", 25)
    assert persona.nombre == "Luis"
    assert persona.es_mayor_edad() is True
    assert "Luis" in persona.presentarse()