from __future__ import annotations

"""deps.py — the one place that decides local-vs-AgentBase adapter wiring.

``build_graph`` ([app/graph/build.py]) takes a :class:`GraphDeps` bundle of
ports and callables.  This module constructs that bundle for the active
environment (``APP_ENV``), so the graph and node code never know which concrete
adapter they're talking to:

| Port            | VECTOR_STORE=faiss    | VECTOR_STORE=opensearch       |
|-----------------|-----------------------|-------------------------------|
| LLMPort         | VngMaasLLM            | VngMaasLLM (same MaaS API)    |
| RetrieverPort   | FaissRetriever        | OpenSearchRetriever           |
| CheckpointerPort| SqliteCheckpointer    | AgentBaseCheckpointer         |
| recall (STM)    | None (stateless)      | make_agentbase_recall(...)    |

``get_deps()`` memoizes the bundle for the process: constructing the retriever
loads the embedding model (and FAISS partitions when vector_store=faiss), which
is expensive and must happen exactly once at boot — never per request.
"""

import logging
from functools import lru_cache
from pathlib import Path

from app.adapters.agentbase_checkpointer import AgentBaseCheckpointer
from app.adapters.agentbase_memory import make_agentbase_recall
from app.adapters.faiss_retriever import FaissRetriever
from app.adapters.maas_llm import VngMaasLLM
from app.adapters.mysql_checkpointer import MySQLCheckpointer
from app.adapters.sqlite_checkpointer import SqliteCheckpointer
from app.config import Settings, get_settings
from app.graph.build import GraphDeps

logger = logging.getLogger(__name__)


def build_deps(settings: Settings | None = None) -> GraphDeps:
    """Construct a fully-wired :class:`GraphDeps` for the active environment.

    Args:
        settings: Injectable settings (defaults to the cached singleton).  Pass
            an explicit ``Settings`` in tests to exercise both environments.

    Returns:
        A :class:`GraphDeps` ready to hand to ``build_graph``.
    """
    cfg = settings or get_settings()

    llm = VngMaasLLM(cfg)

    if cfg.vector_store == "opensearch":
        from app.adapters.opensearch_retriever import OpenSearchRetriever
        retriever = OpenSearchRetriever(cfg)
        logger.info("Using OpenSearchRetriever (VECTOR_STORE=opensearch)")
    else:
        retriever = FaissRetriever(cfg)
        logger.info("Using FaissRetriever (VECTOR_STORE=faiss)")

    # --- AgentBase checkpointer/memory (commented out — using MySQL + OpenAI) ---
    # if cfg.is_agentbase:
    #     checkpointer = AgentBaseCheckpointer(cfg)
    #     recall = make_agentbase_recall(cfg)
    #     logger.info("Wired AgentBase deps (platform Memory checkpointer + recall)")
    # --- end AgentBase ---

    if cfg.db_host and cfg.db_user:
        checkpointer = MySQLCheckpointer(cfg)
        recall = None
        logger.info("Wired local deps (MySQLCheckpointer, stateless recall)")
    else:
        checkpoints_db = Path(cfg.index_dir) / "checkpoints.db"
        checkpointer = SqliteCheckpointer(checkpoints_db)
        recall = None
        logger.info("Wired local deps (SqliteSaver checkpointer, stateless recall)")

    return GraphDeps(
        llm=llm,
        retriever=retriever,
        checkpointer=checkpointer,
        recall=recall,
        settings=cfg,
    )


@lru_cache(maxsize=1)
def get_deps() -> GraphDeps:
    """Return the process-wide :class:`GraphDeps` singleton (built once).

    Call ``get_deps.cache_clear()`` in tests to rebuild from fresh settings.
    """
    return build_deps()
