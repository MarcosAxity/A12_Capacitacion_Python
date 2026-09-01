import pytest
from src.creational.patterns import (
    ConfiguracionApp,
    ConstructorConsultaSQL,
    FabricaNotificaciones,
    FabricaUIClara,
    FabricaUIOscura,
    construir_formulario,
)


def test_factory_method_crea_la_clase_correcta():
    notificacion = FabricaNotificaciones.crear("email")
    assert notificacion.enviar("hola") == "[EMAIL] hola"


def test_factory_method_lanza_error_en_tipo_desconocido():
    with pytest.raises(ValueError):
        FabricaNotificaciones.crear("telegrama")


def test_abstract_factory_mantiene_consistencia_de_familia():
    html_claro = construir_formulario(FabricaUIClara())
    html_oscuro = construir_formulario(FabricaUIOscura())
    assert "claro" in html_claro
    assert "oscuro" in html_oscuro


def test_builder_construye_sql_encadenado():
    consulta = (
        ConstructorConsultaSQL("usuarios")
        .seleccionar("id", "nombre")
        .donde("activo = true")
        .ordenar_por("nombre")
        .limitar(10)
        .build()
    )
    assert consulta.to_sql() == (
        "SELECT id, nombre FROM usuarios WHERE activo = true ORDER BY nombre LIMIT 10"
    )


def test_singleton_devuelve_siempre_la_misma_instancia():
    ConfiguracionApp.reset_para_pruebas()
    a = ConfiguracionApp(entorno="test")
    b = ConfiguracionApp(entorno="otro-valor-ignorado")
    assert a is b
    assert b.entorno == "test"  # el segundo __init__ no sobrescribe
    ConfiguracionApp.reset_para_pruebas()
