"""
graph.py – compiles a LangGraph pipeline from agent nodes.

This version uses package-local (relative) imports and exposes the
compiled `hunt_graph` and `HuntState` dataclass.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from langgraph.graph import StateGraph, END

from team_agents.agents.a_collector import collector_agent
from team_agents.agents.b_intel import intel_agent
from team_agents.agents.c_hypothesis import hypothesis_agent
from team_agents.agents.d_query_builder import query_builder_agent
from team_agents.agents.e_detector import detector_agent
from team_agents.agents.f_correlator import correlator_agent
from team_agents.agents.g_responder import responder_agent


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class HuntState:
    messages: List[Any] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)
    alerts: List[Any] = field(default_factory=list)
    story: Optional[Dict[str, Any]] = None


# Build the LangGraph
g = StateGraph(HuntState)
g.add_node("collector_node", collector_agent)
g.add_node("intel_agent", intel_agent)
g.add_node("hypothesis_agent", hypothesis_agent)
g.add_node("query_builder_agent", query_builder_agent)
g.add_node("detector_node", detector_agent)
g.add_node("correlator_node", correlator_agent)
g.add_node("responder_node", responder_agent)

# Wire up the pipeline
g.add_edge("collector_node", "intel_agent")
g.add_edge("intel_agent", "hypothesis_agent")
g.add_edge("hypothesis_agent", "query_builder_agent")
g.add_edge("query_builder_agent", "detector_node")
g.add_edge("detector_node", "correlator_node")
g.add_edge("correlator_node", "responder_node")
g.add_edge("responder_node", END)
g.set_entry_point("collector_node")

hunt_graph = g.compile(checkpointer=None)


def _pretty_print_results(state: HuntState) -> None:
    logger.info("Alerts: %s", state.alerts or "none")
    if state.story:
        logger.info("Story: %s", state.story.get("summary"))


if __name__ == "__main__":
    try:
        result = hunt_graph.invoke(HuntState())
    except Exception as exc:
        logger.exception("Graph execution failed: %s", exc)
        raise
    else:
        _pretty_print_results(result)


def build_graph():
    return g
