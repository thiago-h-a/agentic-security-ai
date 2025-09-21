# SecOps

This repository contains a lightweight demo of a SecOps / threat-hunting
pipeline implemented as a sequence of agents (collector, intel, hypothesis,
query builder, detector, correlator, responder) connected via **LangGraph**.

The code is modular and orchestrates the sequence of agents to transform raw telemetry into
actionable incidents. 

The demo supports synthetic data runs and a websocket
telemetry stream, centralizes secrets in a `.env` file, and provides
lightweight Docker Compose files. 

The core is designed for clarity and extensibility: components include CTI enrichment, query compilation, alert
scoring, incident correlation, and SOAR invocation, with an LLM-backed
augmentation layer that falls back to deterministic simulated responses when
no API key is present.

## Getting started 

1. Create a Python virtual environment and install requirements:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Populate `.env` from `.env.example` and add your `OPENAI_API_KEY` if you
want the demo to call OpenAI. For offline demos or CI, leaving it empty will
use deterministic simulated LLM responses.

3. Run the AI demo:

```bash
python demo_ai.py
```
