from typer.testing import CliRunner

from orders_cli.cli import app

runner = CliRunner()


def test_list_empty(patch_orders_client) -> None:
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "No hay órdenes registradas" in result.stdout


def test_create_and_list(patch_orders_client) -> None:
    create_result = runner.invoke(
        app,
        ["create", "--customer", "Marcos", "--item", "laptop", "--item", "mouse", "--total", "1500"],
    )
    assert create_result.exit_code == 0
    assert "Orden creada" in create_result.stdout

    list_result = runner.invoke(app, ["list"])
    assert list_result.exit_code == 0
    assert "Marcos" in list_result.stdout


def test_delete_order(patch_orders_client) -> None:
    import re

    create_result = runner.invoke(
        app, ["create", "--customer", "Ana", "--item", "teclado", "--total", "500"]
    )
    match = re.search(r"Orden creada:\s*(\S+)", create_result.stdout)
    order_id = match.group(1)

    delete_result = runner.invoke(app, ["delete", order_id, "--yes"])
    assert delete_result.exit_code == 0
    assert "eliminada" in delete_result.stdout


def test_delete_without_confirmation_is_cancelled(patch_orders_client) -> None:
    create_result = runner.invoke(
        app, ["create", "--customer", "Luis", "--item", "monitor", "--total", "300"]
    )
    # Extraer el id real desde la respuesta
    import re

    match = re.search(r"Orden creada:\s*(\S+)", create_result.stdout)
    order_id = match.group(1)

    result = runner.invoke(app, ["delete", order_id], input="n\n")
    assert result.exit_code == 0
    assert "cancelada" in result.stdout


def test_config_command(patch_orders_client) -> None:
    result = runner.invoke(app, ["config"])
    assert result.exit_code == 0
    assert "API base URL" in result.stdout
