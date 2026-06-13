"""Compiled graph singleton accessor."""

from functools import lru_cache


@lru_cache(maxsize=1)
def get_compiled_graph():
    from app.adapters.deps import get_deps
    from app.graph.build import build_graph

    return build_graph(get_deps())
