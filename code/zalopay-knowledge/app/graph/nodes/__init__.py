"""Graph node factories for the Zalopay Wiki Agent Agent.

Each node is built by a ``make_*_node(...)`` factory that closes over its port
dependencies (LLM, retriever, …) and returns a plain LangGraph node callable.
This keeps nodes pure and dependency-injected so the graph assembly module can
wire local vs. AgentBase adapters without touching node code.

Top-level (GraphState):  ingest_context → router → … → reconcile → respond → suggest
Per-department (DeptState):           retrieve → grade → synthesize → verify
"""

from app.graph.nodes.compress import make_compress_node
from app.graph.nodes.grade import make_grade_node
from app.graph.nodes.ingest_context import make_ingest_context_node
from app.graph.nodes.reconcile import make_reconcile_node
from app.graph.nodes.respond import make_respond_node
from app.graph.nodes.retrieve import make_retrieve_node
from app.graph.nodes.router import SHORT_CIRCUIT_INTENTS, make_router_node
from app.graph.nodes.synthesize import CANNOT_ANSWER, make_synthesize_node
from app.graph.nodes.verify import make_verify_node

__all__ = [
    "make_ingest_context_node",
    "make_router_node",
    "make_retrieve_node",
    "make_grade_node",
    "make_compress_node",
    "make_synthesize_node",
    "make_verify_node",
    "make_reconcile_node",
    "make_respond_node",
    "SHORT_CIRCUIT_INTENTS",
    "CANNOT_ANSWER",
]
