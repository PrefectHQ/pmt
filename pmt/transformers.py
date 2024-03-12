import ast
from pathlib import Path
from typing import List, Union

import astor

INFRA_ADDITIONAL_INFO = (
    "When deploying flows with `flow.deploy`, work pools replace"
    " infrastructure blocks as the source of infrastructure"
    " configuration. To upgrade from an infrastructure block to a"
    " work pool, publish your infrastructure as a work pool by"
    " calling the `.publish_as_work_pool()` method on your"
    " infrastructure block.and pass the name of the new work pool"
    " to the `work_pool_name` keyword argument of the `.deploy()`"
    " method. To learn more about work pools, see"
    " https://docs.prefect.io/latest/concepts/work-pools/"
)

IMAGE_ADDITIONAL_INFO = (
    "Your new deploy script will build a Docker image to use as the execution"
    " environment for your flow. You can change the image by updating the"
    " `image` keyword argument to the `.deploy()` method."
)

NO_INFRA_ADDITIONAL_INFO = (
    "Your `Deployment.build_from_flow` call was upgraded to a"
    " `flow.serve()` call because your script does not use an"
    " infrastructure block. You can use `flow.serve` to create a"
    " deployment for your flow and poll for and execute scheduled runs. To"
    " learn more about serving flows, see"
    " https://docs.prefect.io/latest/concepts/deployments/#serving-flows-on-long-lived-infrastructure"
)


class StorageKwarg:
    def __init__(self, node: Union[ast.Call, ast.Constant, ast.Name]):
        self._node = node

    @property
    def node(self):
        return self._node

    @property
    def required_import(self):
        if isinstance(self.node, ast.Constant):
            return ast.ImportFrom(
                module="prefect.blocks.core",
                names=[ast.alias(name="Block", asname=None)],
                level=0,
            )
        return None

    @property
    def new_node(self):
        if isinstance(self.node, ast.Constant):
            return ast.Call(
                func=ast.Attribute(
                    value="Block",
                    attr="load",
                    ctx=ast.Load(),
                ),
                args=[self.node],
                keywords=[],
            )
        return self.node


class InfrastructureKwarg:
    def __init__(
        self, node: Union[ast.Call, ast.Constant, ast.Name], call: "BuildFromFlowCall"
    ):
        self._node = node
        self._call = call

    @property
    def node(self):
        return self._node

    @property
    def block_document_data(self):
        # using block slug like kubernetes-job/my-job
        if isinstance(self.node, ast.Constant):
            from prefect.blocks.core import Block

            block = Block.load(self.node.value)
            return block.dict(exclude_unset=True, exclude_defaults=True)
        # using a loaded block object like Block.load("kubernetes-job/my-job")
        # or KubernetesJob.load("my-job") or a variable like infra
        elif isinstance(self.node, ast.Call) or isinstance(self.node, ast.Name):
            for found_import in self._call.found_imports:
                # import all found imports so that we can run the block load code
                exec(astor.to_source(found_import))
            # load the block
            if isinstance(self.node, ast.Call):
                block = eval(astor.to_source(self.node))
            else:
                for node in ast.walk(self._call._transformer._tree):
                    if (
                        isinstance(node, ast.Assign)
                        and node.targets[0].id == self.node.id
                    ):
                        exec(astor.to_source(node))
                        break
                block = eval(astor.to_source(self.node))
            return block.dict(exclude_unset=True, exclude_defaults=True)
        else:
            return {}

    @property
    def configured_image(self):
        image = self.block_document_data.get("image")
        if isinstance(image, str) and image.startswith("prefecthq/prefect"):
            return None
        return image


class BuildFromFlowCall:
    def __init__(
        self, node: ast.Call, from_file: Path, transformer: "BuildFromFlowTransformer"
    ):
        self._node = node
        self._transformer = transformer
        self._kwargs = {
            kw.arg: kw.value
            for kw in node.keywords
            if kw.arg
            not in [
                "flow_name",
                "timestamp",
                "parameter_openapi_schema",
                "manifest_path",
            ]
        }
        self._flow = self._kwargs.pop("flow", None) or node.args[0]
        self._storage = self._kwargs.pop("storage", None)
        self._infrastructure = self._kwargs.pop("infrastructure", None)
        self._file = from_file
        self._entrypoint = self._kwargs.pop("entrypoint", None)
        self._path = self._kwargs.pop("path", None)

        self._from_file = from_file

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
        "image",
    ]

    @property
    def node(self):
        return self._node

    @property
    def deployment_name(self):
        name_kwarg = self._kwargs.get("name", None)
        if name_kwarg:
            return astor.to_source(name_kwarg)

    @property
    def flow(self):
        return self._flow

    @property
    def storage(self):
        if self._storage:
            return StorageKwarg(self._storage)
        return None

    @property
    def required_imports(self):
        if self.storage and self.storage.required_import:
            return [self.storage.required_import]
        return []

    @property
    def found_imports(self):
        return self._transformer.found_imports

    @property
    def infrastructure(self):
        if self._infrastructure:
            return InfrastructureKwarg(self._infrastructure, self)
        return None

    @property
    def entrypoint(self):
        if self._entrypoint:
            entrypoint_str = self._entrypoint.value
            if self._path:
                entrypoint_str = str(Path(self._path.value).joinpath(entrypoint_str))
            return ast.Constant(value=entrypoint_str)
        return ast.Constant(s=f"{self._from_file}:{self.flow.id}")

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
    def additional_info(self):
        additional_info = []
        if self.infrastructure:
            additional_info.append(INFRA_ADDITIONAL_INFO)
            if self.infrastructure.configured_image:
                additional_info.append(IMAGE_ADDITIONAL_INFO)
        else:
            additional_info.append(NO_INFRA_ADDITIONAL_INFO)

        return additional_info

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
                    ast.keyword(arg="source", value=self.storage.new_node),
                    ast.keyword(
                        arg="entrypoint",
                        value=self.entrypoint,
                    ),
                ],
            )
        if not self.infrastructure:
            excluded_kwargs = ["work_pool_name", "work_queue_name", "job_variables"]
            # Create a new AST node for 'flow.serve' call
            new_node = ast.Call(
                func=ast.Attribute(
                    value=new_node,
                    attr="serve",
                    ctx=ast.Load(),
                ),
                args=[],
                keywords=[
                    ast.keyword(arg=k, value=v)
                    for k, v in self.kwargs.items()
                    if k not in excluded_kwargs
                ],
            )
        else:
            # Create a new AST node for 'flow.deploy' call
            if self.infrastructure.configured_image:
                self._kwargs["image"] = ast.Constant(
                    s=self.infrastructure.configured_image
                )
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

    def __init__(self, current_file: Path, tree: ast.AST):
        self._current_file = current_file
        self._calls = []
        self._found_imports = []
        self._tree = tree

    @property
    def current_file(self):
        return self._current_file

    @property
    def calls(self) -> List[BuildFromFlowCall]:
        return self._calls

    @property
    def additional_info(self):
        return [action for call in self.calls for action in call.additional_info]

    @property
    def required_imports(self):
        return {
            require_import
            for call in self.calls
            for require_import in call.required_imports
        }

    @property
    def found_imports(self):
        return self._found_imports

    def visit_Call(self, node):
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.value.id == "Deployment"
            and node.func.attr == "build_from_flow"
        ):
            build_from_flow_call = BuildFromFlowCall(node, self.current_file, self)
            self._calls.append(build_from_flow_call)
            return ast.copy_location(build_from_flow_call.updated_node, node)

        return self.generic_visit(node)

    def visit_Import(self, node):
        self._found_imports.append(node)
        return self.generic_visit(node)

    def visit_ImportFrom(self, node):
        self._found_imports.append(node)
        return self.generic_visit(node)
