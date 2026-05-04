# Graph-RAG Architect
### An AI Agent That Understands Your Codebase — Not Just Searches It

> **Ask your code questions in plain English. Get architectural answers backed by a Knowledge Graph + Vector Database.**

---

## The Idea

Most code search tools are keyword-based. They tell you *where* a word appears.

**Graph-RAG Architect goes further.** It combines the semantic understanding of a vector database with the relational power of a graph database to answer questions that actually matter during development:

> *"If I change this function — what else breaks?"*

---

## Demo

```
User Query: "If I change the _create_function_node method, what other functions or files are affected?"

[Agent Action] Searching Vector DB for: '_create_function_node method'...
[Agent Action] Found matching function: _create_function_node

[Agent Action] Traversing Knowledge Graph for: '_create_function_node'...

[Final Architectural Report]:
The `_create_function_node` method does not have any upstream or downstream
dependencies, meaning it is not called by any other functions, nor does it
call any other functions. Therefore, changing this method will not directly
affect other functions or files...
```

The agent found the right function **semantically** (without an exact name match), then traversed the **call graph** to report its full architectural impact.

---

## Architecture

```
Your Codebase (.py files)
        │
        ▼
┌───────────────────┐
│   parser.py       │  AST parsing → extracts functions, classes & call relationships
└────────┬──────────┘
         │
    ┌────┴─────┐
    ▼           ▼
┌──────────┐  ┌─────────────┐
│vector_   │  │graph_       │
│builder.py│  │builder.py   │
│          │  │             │
│ChromaDB  │  │Neo4j        │
│(Semantic │  │(Structural  │
│Search)   │  │Relationships│
└────┬─────┘  └──────┬──────┘
     │                │
     └──────┬─────────┘
            ▼
   ┌─────────────────┐
   │ orchestrator.py │  LangGraph ReAct Agent (GPT-4o)
   │                 │  Tool 1: find_function_by_meaning()
   │                 │  Tool 2: map_dependencies()
   └────────┬────────┘
            ▼
   Architectural Report
```

**Dual-database design** is the core innovation:

| Layer | Technology | Purpose |
|---|---|---|
| **Semantic** | ChromaDB | "What function handles X?" — natural language lookup |
| **Structural** | Neo4j | "What calls/is called by Y?" — dependency traversal |
| **Reasoning** | LangGraph + GPT-4o | Orchestrates both tools, synthesizes the answer |

---

## How It Works

### Step 1 — Parse (`parser.py`)
Uses Python's `ast` module to walk the Abstract Syntax Tree of every `.py` file. Extracts:
- All **function and class definitions**
- All **call relationships** (who calls whom)

No regex. No heuristics. Pure AST — 100% accurate.

### Step 2a — Vector Ingestion (`vector_builder.py`)
Embeds each function's **raw source code** into ChromaDB using its default embedding model. At query time, a natural language question is compared semantically against this store to find the most relevant function — even if the user doesn't know its exact name.

### Step 2b — Graph Ingestion (`graph_builder.py`)
Writes every function as a **Node** and every call relationship as a **directed edge** (`CALLS`) into Neo4j. Uses `MERGE` for idempotent, safe re-runs.

### Step 3 — Agent (`orchestrator.py`)
A **LangGraph ReAct agent** with two custom tools:

1. `find_function_by_meaning(semantic_query)` — queries ChromaDB
2. `map_dependencies(function_name)` — runs a Cypher query on Neo4j

The agent decides which tools to use, in what order, and synthesizes a final report.

---

## Project Structure

```
graph-rag-architect/
├── data/
│   └── dummy_service.py        # Sample codebase for ingestion
├── src/
│   ├── agent/
│   │   └── orchestrator.py     # LangGraph ReAct agent + tool definitions
│   └── ingestion/
│       ├── parser.py           # AST-based code parser
│       ├── graph_builder.py    # Neo4j graph ingestion
│       └── vector_builder.py   # ChromaDB vector ingestion
├── chroma_db/                  # Persisted vector store (auto-generated)
├── neo4j/                      # Neo4j data volume (via Docker)
├── docker-compose.yml          # Spins up Neo4j
├── .env                        # API keys & DB credentials
└── requirements.txt
```

---

## Setup & Usage

### Prerequisites
- Python 3.10+
- Docker Desktop
- An OpenAI API key

### 1. Clone & Install

```bash
git clone https://github.com/your-username/graph-rag-architect.git
cd graph-rag-architect
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# .env
OPENAI_API_KEY=sk-...
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123
```

### 3. Start Neo4j

```bash
docker-compose up -d
```

### 4. Ingest Your Codebase

```bash
# Build the vector store
python src/ingestion/vector_builder.py

# Build the knowledge graph
python src/ingestion/graph_builder.py
```

### 5. Run the Agent

```bash
python src/agent/orchestrator.py
```

Edit the `user_query` variable in `orchestrator.py` to ask your own questions.

---

## Tech Stack

| Technology | Role |
|---|---|
| **Python** | Core language |
| **LangGraph** | ReAct agent loop |
| **LangChain** | Tool/LLM abstractions |
| **OpenAI GPT-4o** | Reasoning engine |
| **ChromaDB** | Persistent vector store |
| **Neo4j** | Graph database |
| **Docker** | Neo4j containerization |
| **Python `ast`** | Zero-dependency code parsing |

---

## Graph Visualizations

The project generates interactive Neo4j visualizations of your codebase's call graph.

**Full codebase node map** — every function as a node:

> *(See `/assets/graph_all_nodes.png`)*

**Filtered dependency view** — showing the `parse_directory → parse_file` call chain:

> *(See `/assets/graph_call_chain.png`)*

---

## What Makes This Interesting

- **Hybrid retrieval** — combines fuzzy semantic search with precise graph traversal. Neither alone is sufficient.
- **Language-agnostic ingestion design** — the AST parsing layer is easily extensible to other languages.
- **Idempotent ingestion** — Neo4j `MERGE` and ChromaDB `upsert` make it safe to re-run ingestion after code changes.
- **Agentic tool use** — the LLM decides how to use the tools; it's not a hardcoded pipeline.