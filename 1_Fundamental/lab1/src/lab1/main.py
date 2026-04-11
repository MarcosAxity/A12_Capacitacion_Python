# main.py - CÓDIGO CON INFRACCIONES PEP 8


def calcular_area(base, altura):
    """Calcula el área de un rectángulo"""
    return base * altura


class CalculadoraAvanzada:
    def __init__(self, valor_inicial):
        self.valor = valor_inicial

    def sumar(self, x, y):
        resultado = x + y
        return resultado

    def dividir(self, a, b):
        if b == 0:
            raise ValueError("No se puede dividir por cero")
        return a / b


def procesar_datos(datos):
    resultado = []
    for item in datos:
        if item > 0:
            resultado.append(item * 2)
        else:
            resultado.append(item)
    return resultado


if __name__ == "__main__":
    print("Hola Mundo")
    area = calcular_area(5, 10)
    print(f"Área: {area}")

    calc = CalculadoraAvanzada(100)
    suma = calc.sumar(5, 3)
    print(f"Suma: {suma}")
