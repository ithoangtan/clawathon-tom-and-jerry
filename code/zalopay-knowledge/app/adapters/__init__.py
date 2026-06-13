from __future__ import annotations

"""Concrete port implementations + the deps wiring factory.

Graph/node code depends only on the ``app.ports.*`` Protocols; this package
holds the runnable adapters that satisfy them and the one factory
(:func:`build_deps`) that selects local vs AgentBase wiring.
"""

from app.adapters.agentbase_checkpointer import AgentBaseCheckpointer
from app.adapters.agentbase_memory import make_agentbase_recall
from app.adapters.deps import build_deps, get_deps
from app.adapters.embeddings import Embedder
from app.adapters.faiss_retriever import FaissRetriever
from app.adapters.maas_llm import VngMaasLLM
from app.adapters.sqlite_checkpointer import SqliteCheckpointer

__all__ = [
    "AgentBaseCheckpointer",
    "Embedder",
    "FaissRetriever",
    "SqliteCheckpointer",
    "VngMaasLLM",
    "build_deps",
    "get_deps",
    "make_agentbase_recall",
]
