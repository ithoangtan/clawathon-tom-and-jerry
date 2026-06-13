"""LangGraph application package — state, nodes, and graph assembly.

Public entry points:
    * :class:`app.graph.state.GraphState` — the checkpointed top-level state.
    * :func:`app.graph.build.build_graph` — compile the runnable agent graph.
    * :class:`app.graph.build.GraphDeps` — the injected port bundle.
"""

from app.graph.build import GraphDeps, build_dept_subgraph, build_graph

__all__ = ["GraphDeps", "build_graph", "build_dept_subgraph"]
