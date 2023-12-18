import ast
from pathlib import Path
from textwrap import dedent
import typer
from rich import print
from rich.syntax import Syntax
from rich.rule import Rule
from rich.markdown import Markdown

from typing import Annotated

from pmt.transformers import BuildFromFlowTransformer
from pmt.utils import convert_ast_node_to_source_code


app = typer.Typer()


@app.callback()
def callback():
    pass


@app.command()
def build_from_flow(file: Annotated[Path, typer.Argument()]):
    """
    Updates any calls to Deployment.build_from_flow to flow.serve or flow.deploy
    """
    current_code = file.read_text()
    tree = ast.parse(current_code)
    transformer = BuildFromFlowTransformer(current_file=file)
    transformer.visit(tree)
    if not transformer.calls:
        print(
            "No calls to [blue]Deployment.build_from_flow[/] found in the provided file."
        )
        return

    print(f"Refer to the output below to see how to update your code in [blue]{file}[/]")

    for i, call in enumerate(transformer.calls):
        markdown=f"# Call {i + 1} of {len(transformer.calls)}: {call.deployment_name}\n"
        markdown += "\n"
        markdown += "To upgrade to the new deployment API, replace your original code with the updated code below.\n"
        markdown += "\n"
        markdown += "## Original Code\n"
        markdown += f"```python\n{convert_ast_node_to_source_code(call.node)}\n```\n"
        markdown += "\n"
        markdown += "## Updated Code\n"
        markdown += f"```python\n{convert_ast_node_to_source_code(call.updated_node)}\n```\n"
        markdown += "\n"
        if call.required_actions:
            markdown += "## Additional Actions\n"
            markdown += "\n"
            markdown += "You will also need to take the following actions to complete the migration for this call:\n"
            for action in call.required_actions:
                markdown += f"- {action}\n"
            markdown += "\n"
        print(
            Rule(),
            Markdown(
                markdown
            ),
        )
    print(Rule())
