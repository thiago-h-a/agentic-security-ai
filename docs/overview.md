# Overview

SecOps-Graph is an agent-driven pipeline designed as a learning/demo platform
for threat hunting workflows. The pipeline is intentionally modular:

1. Collector: ingest and normalize events.
2. Intel: enrich events with CTI and derived context.
3. Hypothesis: generate investigation hypotheses from signals.
4. Query Builder: compile hypotheses into executable ESQL queries.
5. Detector: execute queries or inspect raw events and produce alerts.
6. Correlator: group alerts into incidents.
7. Responder: create analyst narratives and trigger SOAR actions.

Each agent is a pure Python callable that accepts a mutable `state` object and
returns a `langgraph.types.Command` directing the next node.
