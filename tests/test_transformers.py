from pathlib import Path
import pytest
import ast
import astor
import black

from pmt.transformers import (
    INFRA_ADDITIONAL_INFO,
    NO_INFRA_ADDITIONAL_INFO,
    BuildFromFlowTransformer,
)


def is_matching_import(node, module, name):
    """
    Check if the AST node is an ImportFrom node matching the specified module and name.
    """
    return (
        isinstance(node, ast.ImportFrom)
        and node.module == module
        and any(alias.name == name for alias in node.names)
    )


def set_contains_import(node_set, module, name):
    """
    Check if the set of nodes contains an ImportFrom node matching the specified
    module and name.
    """
    return any(is_matching_import(node, module, name) for node in node_set)


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
        start_code = (
            base_scripts_folder / "no_infra_no_storage" / "start.py"
        ).read_text()
        tree = ast.parse(start_code)
        transformer = BuildFromFlowTransformer(current_file=Path(__file__))
        transformer.visit(tree)
        assert len(transformer.calls) == 1

    # TODO: figure out what to do when there is infrastructure but no storage
    @pytest.mark.parametrize(
        "scripts_folder,expected_actions,required_imports",
        [
            ("infra_and_storage", [INFRA_ADDITIONAL_INFO], set()),
            ("no_infra_no_storage", [NO_INFRA_ADDITIONAL_INFO], set()),
            ("no_infra_storage", [NO_INFRA_ADDITIONAL_INFO], set()),
            (
                "infra_slug_and_storage_slug",
                [INFRA_ADDITIONAL_INFO],
                {
                    ast.ImportFrom(
                        module="prefect.blocks.core",
                        names=[ast.alias(name="Block", asname=None)],
                        level=0,
                    )
                },
            ),
        ],
    )
    def test_visit(
        self, base_scripts_folder, scripts_folder, expected_actions, required_imports
    ):
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
        assert transformer.additional_info == expected_actions
        assert len(transformer.required_imports) == len(required_imports)
        for required_import in required_imports:
            assert set_contains_import(
                transformer.required_imports,
                required_import.module,
                required_import.names[0].name,
            )
