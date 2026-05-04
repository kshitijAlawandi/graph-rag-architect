import chromadb
import ast
import os
from pathlib import Path


class SourceCodeExtractor(ast.NodeVisitor):
    """Visits the AST to extract the actual text/code of each function."""

    def __init__(self, source_text):
        self.source_text = source_text
        self.functions_data = []

    def visit_FunctionDef(self, node):
        # Extract the raw string of the function's code
        code_snippet = ast.get_source_segment(self.source_text, node)
        self.functions_data.append({
            "name": node.name,
            "code": code_snippet
        })
        self.generic_visit(node)


def build_vector_db():
    current_dir = Path(__file__).parent.resolve()
    target_dir = current_dir.parent  # Points to the src/ folder
    db_path = current_dir.parent.parent / "chroma_db"

    client = chromadb.PersistentClient(path=str(db_path))
    collection = client.get_or_create_collection(name="codebase_vectors")

    # Iterate through all .py files
    for py_file in target_dir.rglob('*.py'):
        with open(py_file, 'r', encoding='utf-8') as f:
            source_text = f.read()

        tree = ast.parse(source_text)
        extractor = SourceCodeExtractor(source_text)
        extractor.visit(tree)

        documents, metadatas, ids = [], [], []
        for func in extractor.functions_data:
            documents.append(func["code"])
            # We add a unique prefix to IDs so functions with the same name in different files don't overwrite
            unique_id = f"{py_file.stem}_{func['name']}"
            ids.append(unique_id)
            metadatas.append({"function_name": func["name"], "file": str(py_file)})

        if documents:  # Only upsert if we found functions in the file
            collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
            print(f"Embedded {len(documents)} functions from {py_file.name}")


# def build_vector_db():
#     # 1. Setup paths
#     current_dir = Path(__file__).parent.resolve()
#     target_file = current_dir.parent.parent / "data" / "dummy_service.py"
#     db_path = current_dir.parent.parent / "chroma_db"
#
#     if not target_file.exists():
#         print(f"Error: Cannot find {target_file}")
#         return
#
#     # 2. Read the source code
#     with open(target_file, 'r', encoding='utf-8') as f:
#         source_text = f.read()
#
#     # 3. Extract function code using AST
#     print("Extracting code snippets...")
#     tree = ast.parse(source_text)
#     extractor = SourceCodeExtractor(source_text)
#     extractor.visit(tree)
#
#     # 4. Initialize ChromaDB (Persistent storage on your hard drive)
#     print(f"Initializing ChromaDB at {db_path}...")
#     client = chromadb.PersistentClient(path=str(db_path))
#
#     # Get or create a collection (like a table in SQL)
#     # Chroma automatically uses an embedding model under the hood to convert text to vectors!
#     collection = client.get_or_create_collection(name="codebase_vectors")
#
#     # 5. Insert data into ChromaDB
#     print("Generating embeddings and inserting into Vector DB...")
#
#     documents = []  # The actual code
#     metadatas = []  # Info about the code
#     ids = []  # Unique identifiers
#
#     for func in extractor.functions_data:
#         documents.append(func["code"])
#         metadatas.append({"function_name": func["name"], "file": str(target_file)})
#         ids.append(func["name"])  # Using function name as the ID
#
#     # Add to collection (this handles the embedding math automatically)
#     collection.upsert(
#         documents=documents,
#         metadatas=metadatas,
#         ids=ids
#     )
#
#     print(f"Successfully embedded {len(documents)} functions into ChromaDB!")
#
#     # 6. Let's do a quick test query to prove it works
#     print("\n--- Testing Semantic Search ---")
#     query_text = "How is the payment processed?"
#     print(f"Query: '{query_text}'")
#
#     results = collection.query(
#         query_texts=[query_text],
#         n_results=1  # Bring back the top 1 most relevant result
#     )
#
#     top_match = results['metadatas'][0][0]['function_name']
#     print(f"Top Semantic Match: {top_match}")


if __name__ == "__main__":
    build_vector_db()
