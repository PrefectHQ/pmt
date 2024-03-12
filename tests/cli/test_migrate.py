import pytest

from typer.testing import CliRunner

from pmt.cli.app import app

cli_runner = CliRunner()


@pytest.mark.parametrize(
    "scripts_folder",
    [
        "infra_and_storage",
        "infra_var_and_storage_var",
        "no_infra_no_storage",
        "no_infra_storage",
        "infra_and_no_storage",
        "infra_slug_and_storage_slug",
    ],
)
def test_upgrade_build_from_flow(base_scripts_folder, scripts_folder):
    folder = base_scripts_folder / scripts_folder
    start_path = folder / "start.py"
    result = cli_runner.invoke(app, ["upgrade", "build-from-flow", str(start_path)])
    assert result.exit_code == 0
    assert (
        f"Refer to the output below to see how to update your code in {start_path}"
        in result.stdout.replace("\n", "")
    )
    assert "Original Code" in result.stdout
    assert "Updated Code" in result.stdout
    assert "Additional Info" in result.stdout


@pytest.mark.parametrize(
    "scripts_folder",
    [
        "infra_and_storage",
        "infra_var_and_storage_var",
        "no_infra_no_storage",
        "no_infra_storage",
        "infra_and_no_storage",
        "infra_slug_and_storage_slug",
    ],
)
def test_upgrade_build_from_flow_with_output(
    tmp_path, base_scripts_folder, scripts_folder
):
    folder = base_scripts_folder / scripts_folder
    start_path = folder / "start.py"
    result = cli_runner.invoke(
        app,
        [
            "upgrade",
            "build-from-flow",
            str(start_path),
            "-o",
            str(tmp_path / "output.py"),
        ],
    )
    assert result.exit_code == 0
    assert f"Updated code written to {tmp_path / 'output.py'}" in result.stdout.replace(
        "\n", ""
    )
    assert "Additional Info" in result.stdout
    output_code = (tmp_path / "output.py").read_text()
    expected_code = (folder / "expected.py").read_text()
    assert output_code == expected_code
