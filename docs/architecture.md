# Architecture

The system follows a linear pipeline model implemented with LangGraph:

- Data flows as a `HuntState` object across nodes.
- Agents are responsible for one concern each and communicate via
  `state.evidence`.
- Tools (CTI feeds, Elasticsearch, SOAR) are encapsulated in `secops.tools`.
- Metrics are gathered in-memory via `agents.utils.Metrics` for quick
  inspection.

Design goals: defensive programming, observability, and extensibility.
