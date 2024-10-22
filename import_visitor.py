import ast


class ImportVisitor(ast.NodeVisitor):
    def __init__(self):
        self.imports = set()

    def visit_Import(self, node: ast.Import) -> None:
        for name in node.names:
            self.imports.add(name.name.split('.')[0])

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            self.imports.add(node.module.split('.')[0])
