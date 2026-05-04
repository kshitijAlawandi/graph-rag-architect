from neo4j import GraphDatabase
from parser import parse_file
from pathlib import Path


class GraphBuilder:
    def __init__(self, uri, user, password):
        # Establish the connection to the Neo4j database
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def build_graph(self, parsed_data):
        """Takes the parsed JSON and creates Nodes and Edges in Neo4j."""
        with self.driver.session() as session:
            # 1. Create the Nodes (Functions)
            print("Creating Nodes...")
            for func_name in parsed_data["functions"]:
                session.execute_write(self._create_function_node, func_name, parsed_data["file"])

            # 2. Create the Edges (Relationships)
            print("Creating Relationships...")
            for rel in parsed_data["relationships"]:
                session.execute_write(self._create_call_relationship, rel["caller"], rel["callee"])

            print("Graph successfully built!")

    @staticmethod
    def _create_function_node(tx, func_name, file_path):
        # We use MERGE instead of CREATE. MERGE acts like an "Upsert".
        # If the node exists, it does nothing. If it doesn't, it creates it.
        # This makes our ingestion script idempotent (safe to run multiple times).
        query = """
        MERGE (f:Function {name: $func_name})
        ON CREATE SET f.file = $file_path
        RETURN f
        """
        tx.run(query, func_name=func_name, file_path=file_path)

    @staticmethod
    def _create_call_relationship(tx, caller, callee):
        # MATCH finds the two existing nodes. MERGE creates the relationship between them.
        query = """
        MATCH (caller:Function {name: $caller})
        MATCH (callee:Function {name: $callee})
        MERGE (caller)-[:CALLS]->(callee)
        """
        tx.run(query, caller=caller, callee=callee)


if __name__ == "__main__":
    from parser import parse_directory

    current_dir = Path(__file__).parent.resolve()
    target_dir = current_dir.parent  # Points to the src/ folder

    parsed_files = parse_directory(target_dir)

    URI = "bolt://localhost:7687"
    USER = "neo4j"
    PASSWORD = "password123"

    builder = GraphBuilder(URI, USER, PASSWORD)
    try:
        # Loop through every file we parsed and add it to the graph
        for file_data in parsed_files:
            builder.build_graph(file_data)
    finally:
        builder.close()

# if __name__ == "__main__":
#     # 1. Parse the dummy service (reusing our code from Step 1)
#     current_dir = Path(__file__).parent.resolve()
#     target_file = current_dir.parent.parent / "data" / "dummy_service.py"
#
#     if not target_file.exists():
#         print(f"Error: Cannot find {target_file}")
#         exit(1)
#
#     print(f"Parsing {target_file}...")
#     parsed_data = parse_file(str(target_file))
#
#     # 2. Connect to Neo4j and build the graph
#     # (Using the default Docker credentials we set up)
#     URI = "bolt://localhost:7687"
#     USER = "neo4j"
#     PASSWORD = "password123"
#
#     print("Connecting to Neo4j...")
#     builder = GraphBuilder(URI, USER, PASSWORD)
#
#     try:
#         builder.build_graph(parsed_data)
#     finally:
#         builder.close()