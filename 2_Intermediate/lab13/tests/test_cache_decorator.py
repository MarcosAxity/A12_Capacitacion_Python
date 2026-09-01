import pytest
from src.lab.cache_decorator import cache_con_ttl


class RelojFalso:
    """Reloj controlable manualmente para probar el TTL sin usar
    time.sleep real (pruebas rapidas y deterministas)."""

    def __init__(self, inicio: float = 0.0):
        self._ahora = inicio

    def __call__(self) -> float:
        return self._ahora

    def avanzar(self, segundos: float) -> None:
        self._ahora += segundos


def test_segunda_llamada_con_mismos_argumentos_usa_cache():
    contador_llamadas = {"n": 0}

    @cache_con_ttl(ttl_segundos=60)
    def calcular_costoso(x: int) -> int:
        contador_llamadas["n"] += 1
        return x * x

    assert calcular_costoso(4) == 16
    assert calcular_costoso(4) == 16
    assert contador_llamadas["n"] == 1  # solo se ejecuto una vez


def test_argumentos_distintos_no_comparten_cache():
    contador_llamadas = {"n": 0}

    @cache_con_ttl(ttl_segundos=60)
    def calcular_costoso(x: int) -> int:
        contador_llamadas["n"] += 1
        return x * x

    calcular_costoso(2)
    calcular_costoso(3)
    assert contador_llamadas["n"] == 2


def test_expira_despues_del_ttl():
    reloj = RelojFalso()

    @cache_con_ttl(ttl_segundos=10, reloj=reloj)
    def obtener_valor(x: int) -> int:
        obtener_valor.llamadas += 1  # type: ignore[attr-defined]
        return x

    obtener_valor.llamadas = 0  # type: ignore[attr-defined]

    obtener_valor(1)
    reloj.avanzar(5)
    obtener_valor(1)  # todavia dentro del TTL
    assert obtener_valor.llamadas == 1  # type: ignore[attr-defined]

    reloj.avanzar(6)  # total 11s > ttl de 10s
    obtener_valor(1)
    assert obtener_valor.llamadas == 2  # type: ignore[attr-defined]


def test_estadisticas_de_hits_y_misses():
    @cache_con_ttl(ttl_segundos=60)
    def identidad(x: int) -> int:
        return x

    identidad(1)  # miss
    identidad(1)  # hit
    identidad(2)  # miss
    identidad(1)  # hit

    stats = identidad.cache_info()
    assert stats.hits == 2
    assert stats.misses == 2
    assert stats.tasa_aciertos == pytest.approx(0.5)


def test_invalidar_una_entrada_especifica():
    contador = {"n": 0}

    @cache_con_ttl(ttl_segundos=60)
    def calcular(x: int) -> int:
        contador["n"] += 1
        return x

    calcular(5)
    calcular.invalidar(5)
    calcular(5)
    assert contador["n"] == 2


def test_limpiar_cache_elimina_todas_las_entradas():
    @cache_con_ttl(ttl_segundos=60)
    def calcular(x: int) -> int:
        return x

    calcular(1)
    calcular(2)
    assert calcular.tamano_actual() == 2

    calcular.limpiar_cache()
    assert calcular.tamano_actual() == 0


def test_respeta_tamano_maximo_con_politica_fifo():
    reloj = RelojFalso()

    @cache_con_ttl(ttl_segundos=60, tamano_maximo=2, reloj=reloj)
    def calcular(x: int) -> int:
        return x

    calcular(1)
    calcular(2)
    calcular(3)  # deberia desalojar la entrada de x=1 (la mas antigua)

    assert calcular.tamano_actual() == 2
