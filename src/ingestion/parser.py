import ast
import json
from pathlib import Path


class DependencyVisitor(ast.NodeVisitor):
    """
    This class 'walks' through the Abstract Syntax Tree of a Python file.
    It triggers specific methods when it encounters Classes, Functions, and Calls.
    """

    def __init__(self):
        self.classes = []
        self.functions = []
        self.calls = []
        self.current_function = None  # Keeps track of what function we are currently inside

    def visit_ClassDef(self, node):
        self.classes.append(node.name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.functions.append(node.name)
        self.current_function = node.name  # We are now inside this function
        self.generic_visit(node)
        self.current_function = None  # We have exited the function

    def visit_Call(self, node):
        """
        When we hit a function call, we record WHO is calling WHO.
        """
        # Handle direct function calls (e.g., my_function())
        if isinstance(node.func, ast.Name):
            called_name = node.func.id
            if self.current_function:
                self.calls.append({
                    "caller": self.current_function,
                    "callee": called_name
                })

        # Handle method calls (e.g., my_class.my_method())
        elif isinstance(node.func, ast.Attribute):
            called_name = node.func.attr
            if self.current_function:
                self.calls.append({
                    "caller": self.current_function,
                    "callee": called_name
                })

        self.generic_visit(node)


def parse_file(filepath):
    """Reads a Python file and extracts its structure."""
    with open(filepath, 'r', encoding='utf-8') as file:
        file_content = file.read()

    # Parse the text into an AST structure
    tree = ast.parse(file_content)

    # Run our custom visitor over the tree
    visitor = DependencyVisitor()
    visitor.visit(tree)

    return {
        "file": filepath,
        "classes": visitor.classes,
        "functions": visitor.functions,
        "relationships": visitor.calls
    }


# ... [Keep your DependencyVisitor and parse_file functions exactly as they are] ...

def parse_directory(directory_path):
    """Crawls a directory recursively and parses all Python files."""
    from pathlib import Path

    all_parsed_data = []
    path_obj = Path(directory_path)

    # rglob finds all .py files recursively in all subfolders
    for py_file in path_obj.rglob('*.py'):
        print(f"Parsing: {py_file.name}")
        parsed_file = parse_file(str(py_file))
        all_parsed_data.append(parsed_file)

    return all_parsed_data


if __name__ == "__main__":
    from pathlib import Path

    current_dir = Path(__file__).parent.resolve()

    target_dir = current_dir.parent

    print(f"--- Crawling Directory: {target_dir} ---")
    results = parse_directory(target_dir)

    print(f"\nSuccessfully parsed {len(results)} files!")


# if __name__ == "__main__":
#     # 1. Get the absolute path of the directory where parser.py lives
#     current_dir = Path(__file__).parent.resolve()
#
#     # 2. Construct the path to dummy_service.py relative to this file
#     # .parent.parent moves us up from src/ingestion to the project root
#     target_file = current_dir.parent.parent / "data" / "dummy_service.py"
#
#     # 3. Verify the file exists before parsing
#     if target_file.exists():
#         print(f"--- Parsing File: {target_file} ---")
#         result = parse_file(str(target_file))
#         print(json.dumps(result, indent=4))
#     else:
#         print(f"Error: Could not find dummy_service.py at {target_file}")
#         # Helpful debug: Print the current directory to see where we are
#         print(f"Current script directory: {current_dir}")