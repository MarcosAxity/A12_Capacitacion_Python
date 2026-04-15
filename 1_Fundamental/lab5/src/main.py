def sumar(a: int, b: int) -> int:
    """Suma dos números enteros."""
    return a + b


def saludar(nombre: str) -> str:
    """Genera un saludo personalizado."""
    return f"Hola {nombre}"


def buscar_en_lista(items: list[str], valor: str) -> str | None:
    """Busca un valor en una lista.

    Returns:
        El valor si se encuentra, None si no existe.
    """
    for item in items:
        if item == valor:
            return item
    return None


def calcular_promedio(numeros: list[float]) -> float:
    """Calcula el promedio de una lista de números.

    Returns:
        Promedio o 0.0 si la lista está vacía.
    """
    if not numeros:
        return 0.0
    return sum(numeros) / len(numeros)


class Persona:
    """Representa una persona con nombre y edad."""

    def __init__(self, nombre: str, edad: int) -> None:
        """Inicializa una persona.

        Args:
            nombre: Nombre completo
            edad: Edad en años
        """
        self.nombre = nombre
        self.edad = edad

    def presentarse(self) -> str:
        """Retorna una presentación de la persona."""
        return f"Soy {self.nombre} y tengo {self.edad} años"

    def es_mayor_edad(self) -> bool:
        """Verifica si es mayor de edad."""
        return self.edad >= 18