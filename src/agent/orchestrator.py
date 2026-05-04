import os
import chromadb
from neo4j import GraphDatabase
from pathlib import Path
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI  # Swap with ChatAnthropic if using Claude
from langgraph.prebuilt import create_react_agent
import os
from dotenv import load_dotenv

# --- 1. Initialize Database Clients ---
current_dir = Path(__file__).parent.resolve()
db_path = current_dir.parent.parent / "chroma_db"

load_dotenv()

# Connect to ChromaDB (Vector)
chroma_client = chromadb.PersistentClient(path=str(db_path))
vector_collection = chroma_client.get_collection(name="codebase_vectors")

# Connect to Neo4j (Graph)
neo4j_driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password123"))


# --- 2. Define the Agent's Tools ---

@tool
def find_function_by_meaning(semantic_query: str) -> str:
    """
    Use this tool FIRST when you need to find the name of a function based on a natural language description.
    For example, if the user asks about 'handling money', use this to find 'process_payment'.
    """
    print(f"\n[Agent Action] Searching Vector DB for: '{semantic_query}'...")
    results = vector_collection.query(query_texts=[semantic_query], n_results=1)

    if results['metadatas'][0]:
        func_name = results['metadatas'][0][0]['function_name']
        code = results['documents'][0][0]
        print(f"[Agent Action] Found matching function: {func_name}")
        return f"Function Name: {func_name}\nSource Code: {code}"
    return "No matching function found."


@tool
def map_dependencies(function_name: str) -> str:
    """
    Use this tool SECOND to find the architectural dependencies of a specific function.
    It queries the Neo4j graph to find which functions call this function (upstream impact)
    and which functions it calls (downstream dependencies).
    """
    print(f"\n[Agent Action] Traversing Knowledge Graph for: '{function_name}'...")

    # Cypher query to find parents (callers) and children (callees)
    query = """
    MATCH (f:Function {name: $func_name})
    OPTIONAL MATCH (caller)-[:CALLS]->(f)
    OPTIONAL MATCH (f)-[:CALLS]->(callee)
    RETURN 
        collect(DISTINCT caller.name) AS callers,
        collect(DISTINCT callee.name) AS callees
    """

    with neo4j_driver.session() as session:
        result = session.run(query, func_name=function_name).single()

    if not result:
        return "Function not found in graph."

    callers = result["callers"]
    callees = result["callees"]

    return f"Dependencies for '{function_name}':\n- Called by (Upstream): {callers}\n- Calls out to (Downstream): {callees}"


# --- 3. Build the LangGraph Agent ---

def run_agent():
    # Initialize the LLM (Must support tool-calling)
    llm = ChatOpenAI(model="gpt-4o", temperature=0)  # Or ChatAnthropic(model="claude-3-5-sonnet-20240620")

    # Give the LLM access to our custom database tools
    tools = [find_function_by_meaning, map_dependencies]

    # LangGraph prebuilds a "ReAct" (Reasoning + Acting) loop for us
    agent_executor = create_react_agent(llm, tools)

    # --- 4. The Query ---
    print("==================================================")
    print("Graph-RAG Architect Agent Initialized.")
    print("==================================================\n")

    user_query = "If I change the _create_function_node method, what other functions or files are affected?"
    print(f"User Query: {user_query}\n")

    # Stream the agent's thought process
    events = agent_executor.stream(
        {"messages": [("user", user_query)]},
        stream_mode="values",
    )

    for event in events:
        # Print the final output from the AI
        message = event["messages"][-1]
        if message.type == "ai" and not message.tool_calls:
            print(f"\n[Final Architectural Report]:\n{message.content}")


if __name__ == "__main__":
    try:
        run_agent()
    finally:
        neo4j_driver.close()