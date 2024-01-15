import ast
from pathlib import Path
import typer
from rich import print
from rich.rule import Rule
from rich.markdown import Markdown

from typing import Annotated, Optional

from pmt.transformers import BuildFromFlowTransformer
from pmt.utils import convert_ast_node_to_source_code


app = typer.Typer()


@app.callback()
def callback():
    pass


@app.command()
def build_from_flow(
    file: Annotated[
        Path,
        typer.Argument(
            help="File containing Deployment.build_from_flow calls to update."
        ),
    ],
    output: Annotated[
        Optional[Path],
        typer.Option(
            "--output",
            "-o",
            help=(
                "File to write updated code to. If not provided, updates will be"
                " printed to stdout."
            ),
        ),
    ] = None,
):
    """
    Updates any calls to Deployment.build_from_flow to flow.serve or flow.deploy
    """
    current_code = file.read_text()
    tree = ast.parse(current_code)

    transformer = BuildFromFlowTransformer(current_file=file, tree=tree)
    transformer.visit(tree)
    if not transformer.calls:
        print(
            "No calls to [blue]Deployment.build_from_flow[/] found in the provided"
            " file."
        )
        return

    for required_import in transformer.required_imports:
        tree.body.insert(0, required_import)

    if output:
        output.write_text(convert_ast_node_to_source_code(tree))
        print(f"Updated code written to [blue]{output}[/].")
        markdown = "## Additional Info\n"
        additional_info = {
            action
            for call in transformer.calls
            for action in call.additional_info
            if call.additional_info
        }
        for action in additional_info:
            markdown += f"- {action}\n"

        print(
            Markdown(markdown),
        )

    else:
        print(
            "Refer to the output below to see how to update your code in"
            f" [blue]{file}[/]"
        )

        for i, call in enumerate(transformer.calls):
            markdown = (
                f"# Call {i + 1} of {len(transformer.calls)}: {call.deployment_name}\n"
            )
            markdown += "\n"
            markdown += (
                "To upgrade to the new deployment API, replace your original code with"
                " the updated code below.\n"
            )
            markdown += "\n"
            markdown += "## Original Code\n"
            markdown += (
                f"```python\n{convert_ast_node_to_source_code(call.node)}\n```\n"
            )
            markdown += "\n"
            markdown += "## Updated Code\n"
            markdown += f"```python\n{convert_ast_node_to_source_code(call.updated_node)}\n```\n"  # noqa
            markdown += "\n"
            if call.additional_info:
                markdown += "## Additional Info\n"
                markdown += "\n"
                for action in call.additional_info:
                    markdown += f"- {action}\n"
                markdown += "\n"
            print(
                Rule(),
                Markdown(markdown),
            )
        print(Rule())
