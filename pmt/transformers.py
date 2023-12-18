import ast
from pathlib import Path
from typing import List


class BuildFromFlowCall:
    def __init__(self, node: ast.Call, from_file: Path):
        self._node = node
        self._kwargs = {
            kw.arg: kw.value
            for kw in node.keywords
            if kw.arg
            not in [
                "flow_name",
                "path",
                "timestamp",
                "parameter_openapi_schema",
                "manifest_path",
            ]
        }
        self._flow = self._kwargs.pop("flow", None) or node.args[0]
        self._storage = self._kwargs.pop("storage", None)
        self._infrastructure = self._kwargs.pop("infrastructure", None)
        self._file = from_file
        self._entrypoint = self._kwargs.pop("entrypoint", None) or ast.Constant(
            s=f"{self.from_file}:{self.flow.id}"
        )

        self._infra_overrides = self._kwargs.pop("infra_overrides", None)
        if self._infra_overrides:
            self._kwargs["job_variables"] = self._infra_overrides

    key_order = [
        "name",
        "description",
        "version",
        "tags",
        "schedule",
        "parameters",
        "is_schedule_active",
        "work_pool_name",
        "work_queue_name",
        "job_variables",
        "triggers",
    ]

    @property
    def node(self):
        return self._node
    
    @property
    def deployment_name(self):
        name_kwarg = self._kwargs.get("name", None)
        if name_kwarg:
            return ast.unparse(name_kwarg)

    @property
    def flow(self):
        return self._flow

    @property
    def storage(self):
        return self._storage

    @property
    def infrastructure(self):
        return self._infrastructure

    @property
    def entrypoint(self):
        return self._entrypoint

    @property
    def kwargs(self):
        return {
            key: self._kwargs[key]
            for key in self.__class__.key_order
            if key in self._kwargs
        }

    @property
    def from_file(self):
        return self._file

    @property
    def required_actions(self):
        required_actions = []
        if self.infrastructure:
            required_actions.extend(
                [
                    "Publish your infrastructure as a work pool by calling the `.publish_as_work_pool()` method on your infrastructure block.",
                    "Pass the name of the new work pool to the `work_pool_name` keyword argument of the `.deploy()` method.",
                ]
            )
        return required_actions

    @property
    def updated_node(self):
        new_node = self.flow
        if self.storage:
            # Create a new AST node for 'flow.deploy' call
            new_node = ast.Call(
                func=ast.Attribute(
                    value="flow",
                    attr="from_source",
                    ctx=ast.Load(),
                ),
                args=[],
                keywords=[
                    ast.keyword(arg="source", value=self.storage),
                    ast.keyword(
                        arg="entrypoint",
                        value=self.entrypoint,
                    ),
                ],
            )
        if not self.infrastructure:
            # Create a new AST node for 'flow.serve' call
            new_node = ast.Call(
                func=ast.Attribute(
                    value=new_node,
                    attr="serve",
                    ctx=ast.Load(),
                ),
                args=[],
                keywords=[ast.keyword(arg=k, value=v) for k, v in self.kwargs.items()],
            )
        else:
            # Create a new AST node for 'flow.deploy' call
            new_node = ast.Call(
                func=ast.Attribute(
                    value=new_node,
                    attr="deploy",
                    ctx=ast.Load(),
                ),
                args=[],
                keywords=[ast.keyword(arg=k, value=v) for k, v in self.kwargs.items()],
            )
        return new_node


class BuildFromFlowTransformer(ast.NodeTransformer):
    """
    A node transformer that will discover and transform any calls to
    `Deployment.build_from_flow` to `flow.deploy` or `flow.serve` depending on the
    usage.
    """

    def __init__(self, current_file: Path):
        self._current_file = current_file
        self._calls = []

    @property
    def current_file(self):
        return self._current_file

    @property
    def calls(self) -> List[BuildFromFlowCall]:
        return self._calls

    @property
    def additional_actions(self):
        return [action for call in self._calls for action in call.required_actions]

    def visit_Call(self, node):
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.value.id == "Deployment"
            and node.func.attr == "build_from_flow"
        ):
            build_from_flow_call = BuildFromFlowCall(node, self.current_file)
            self._calls.append(build_from_flow_call)
            return ast.copy_location(build_from_flow_call.updated_node, node)

        return self.generic_visit(node)
