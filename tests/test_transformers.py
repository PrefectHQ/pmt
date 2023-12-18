from pathlib import Path
import pytest
import ast
import astor
import black

from pmt.transformers import BuildFromFlowTransformer


class TestBuildFromFlowTransformer:
    @pytest.fixture
    def base_scripts_folder(self):
        return Path(__file__).parent / "scripts"

    @pytest.fixture
    def build_from_flow_with_no_infra_no_storage(self):
        start_path = (
            Path(__file__).parent / "scripts" / "no_infra_no_storage" / "start.py"
        )
        start_code = start_path.read_text()
        expected_path = (
            Path(__file__).parent / "scripts" / "no_infra_no_storage" / "expected.py"
        )
        expected_code = expected_path.read_text()
        return start_code, expected_code

    def test_finds_calls(self, base_scripts_folder):
        start_code = (base_scripts_folder / "no_infra_no_storage" / "start.py").read_text()
        tree = ast.parse(start_code)
        transformer = BuildFromFlowTransformer(current_file=Path(__file__))
        transformer.visit(tree)
        assert len(transformer.calls) == 1

    # TODO: figure out what to do when there is infrastructure but no storage
    @pytest.mark.parametrize(
        "scripts_folder,expected_actions",
        [
            (
                "infra_and_storage",
                [
                    "Publish your infrastructure as a work pool by calling the `.publish_as_work_pool()` method on your infrastructure block.",
                    "Pass the name of the new work pool to the `work_pool_name` keyword argument of the `.deploy()` method.",
                ],
            ),
            ("no_infra_no_storage", []),
            ("no_infra_storage", []),
        ],
    )
    def test_visit(self, base_scripts_folder, scripts_folder, expected_actions):
        folder = base_scripts_folder / scripts_folder
        start_path = folder / "start.py"
        start_code = start_path.read_text()
        expected_path = folder / "expected.py"
        expected_code = expected_path.read_text()
        tree = ast.parse(start_code)
        transformer = BuildFromFlowTransformer(current_file=Path(__file__))
        transformer.visit(tree)
        assert tree != ast.parse(start_code)
        assert (
            black.format_str(astor.to_source(tree), mode=black.FileMode())
            == expected_code
        )
        assert transformer.additional_actions == expected_actions