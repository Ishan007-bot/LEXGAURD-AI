"""LangGraph per-clause state machine.

Flow per clause:

    Prosecutor → Defender → Judge → [Negotiator? if severity >= medium] → END

Multiple clauses are fanned out concurrently by the analyzer service (not
inside the graph), so this graph stays focused on the linear adversarial
debate for a single clause.

LangGraph 0.2+ disallows node names that match state keys, so the nodes are
named `*_step` while the state keys stay `prosecutor`/`defender`/...
"""

from __future__ import annotations

from functools import partial

from langgraph.graph import END, StateGraph

from app.agents.defender import run_defender
from app.agents.judge import run_judge
from app.agents.negotiator import run_negotiator, should_negotiate
from app.agents.prosecutor import run_prosecutor
from app.agents.state import ClauseState
from app.services.vertex import LLMClient


def _route_after_judge(state: ClauseState) -> str:
    return "negotiate_step" if should_negotiate(state) else END


def build_clause_graph(client: LLMClient):
    """Return a compiled LangGraph for one clause analysis run."""
    graph: StateGraph = StateGraph(ClauseState)

    graph.add_node("prosecute_step", partial(run_prosecutor, client=client))
    graph.add_node("defend_step", partial(run_defender, client=client))
    graph.add_node("judge_step", partial(run_judge, client=client))
    graph.add_node("negotiate_step", partial(run_negotiator, client=client))

    graph.set_entry_point("prosecute_step")
    graph.add_edge("prosecute_step", "defend_step")
    graph.add_edge("defend_step", "judge_step")
    graph.add_conditional_edges(
        "judge_step",
        _route_after_judge,
        {"negotiate_step": "negotiate_step", END: END},
    )
    graph.add_edge("negotiate_step", END)

    return graph.compile()
