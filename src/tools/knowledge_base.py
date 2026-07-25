"""
Procurement Knowledge Base client.

Queries the shared ChromaDB vectorstore built by the Procurement RAG app.
Scope is Bangladesh e-GP: PPR 2025, the e-GP Guidelines 2025 gazette, and BPPA
e-GP portal documentation. Donor-funded frameworks (World Bank, ADB) are not
indexed — re-ingest those sources before relying on this for such tenders.
Set RAG_VECTORSTORE_PATH in your .env to point at the vectorstore/ folder,
e.g.: RAG_VECTORSTORE_PATH=C:/Users/misla/Documents/Claude Cowork/Procurement RAG/vectorstore
"""

import os
from pathlib import Path

# ── Vectorstore location ──────────────────────────────────────────────────────

_DEFAULT_PATH = str(
    Path(__file__).parent.parent.parent.parent / "Procurement RAG" / "vectorstore"
)
VECTORSTORE_PATH = os.getenv("RAG_VECTORSTORE_PATH", _DEFAULT_PATH)
COLLECTION_NAME = "procurement_kb"
EMBEDDING_MODEL = "text-embedding-3-small"


# ── Tool schema for Claude tool_use ──────────────────────────────────────────

QUERY_REGULATIONS_TOOL = {
    "name": "query_procurement_regulations",
    "description": (
        "Search the Bangladesh e-GP procurement knowledge base for relevant rules, "
        "guidelines, and system procedures. Scope is Bangladesh public procurement "
        "only: the Public Procurement Rules (PPR) 2025, the e-GP Guidelines 2025 "
        "gazette, and BPPA e-GP portal documentation (Procuring Entity user and admin "
        "manuals, FAQ, module release notes, portal overview). Use this to "
        "cross-reference tender requirements against Bangladesh procurement law and "
        "e-GP system workflow. This knowledge base does NOT cover World Bank, ADB, or "
        "other donor-funded procurement frameworks — do not use it to answer questions "
        "about those regimes. Returns verbatim passages with source citations."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "A specific Bangladesh procurement or e-GP question, e.g. "
                    "'tender security amount and release process' or "
                    "'two envelope tender opening and evaluation committee procedure'"
                ),
            },
            "k": {
                "type": "integer",
                "description": "Number of passages to retrieve (default 4, max 8)",
                "default": 4,
            },
        },
        "required": ["query"],
    },
}


# ── Query function ────────────────────────────────────────────────────────────

def query_procurement_regulations(query: str, k: int = 4) -> str:
    """
    Query the ChromaDB knowledge base and return formatted passages.
    Returns a plain-text string with cited excerpts, ready to be sent
    back to Claude as a tool_result.
    """
    try:
        import chromadb
        from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
    except ImportError:
        return (
            "Knowledge base unavailable: chromadb or openai package not installed. "
            "Run: pip install chromadb openai"
        )

    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        return "Knowledge base unavailable: OPENAI_API_KEY not set in environment."

    if not Path(VECTORSTORE_PATH).exists():
        return (
            f"Knowledge base not found at {VECTORSTORE_PATH}. "
            "Upload documents in the Procurement RAG app first."
        )

    try:
        db = chromadb.PersistentClient(path=VECTORSTORE_PATH)
        ef = OpenAIEmbeddingFunction(
            api_key=openai_key,
            model_name=EMBEDDING_MODEL,
        )
        collection = db.get_collection(name=COLLECTION_NAME, embedding_function=ef)
        k = min(max(k, 1), 8)
        results = collection.query(
            query_texts=[query],
            n_results=k,
            include=["documents", "metadatas"],
        )
    except Exception as exc:
        return f"Knowledge base query failed: {exc}"

    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]

    if not docs:
        return "No relevant passages found in the knowledge base for this query."

    passages = []
    for doc, meta in zip(docs, metas):
        source = meta.get("source_name", "Unknown document")
        page = meta.get("page", "?")
        passages.append(f"[{source} | page {page}]\n{doc.strip()}")

    return "\n\n---\n\n".join(passages)
