import astor
import black


def convert_ast_node_to_source_code(node):
    return black.format_str(astor.to_source(node).strip(), mode=black.FileMode())
