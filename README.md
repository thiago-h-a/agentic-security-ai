# SecOps Graph Demo

This repository contains a lightweight demo of a SecOps / threat-hunting
pipeline implemented as a sequence of agents (collector, intel, hypothesis,
query builder, detector, correlator, responder) connected via **LangGraph**.

The `patches.py` script (this repo) writes demo helpers, a centralized `.env`,
Docker Compose artifacts for demo runs, and example scripts.

## Getting started (local, minimal)

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
python patches.py      # ensures demo files exist
bash demo/run_demo_ai.sh
```

4. Run the WebSocket demo (requires a running FastAPI app exposing
`/ws/ingest`):

```bash
bash demo/run_demo_websocket.sh
```

## Files created by this patch
- `demo/demo_ai.py` - runs synthetic pipeline and prints outputs
- `demo/demo_websocket.py` - streams telemetry to a websocket
- `docker-compose-demo-ai.yml`, `docker-compose-demo-websocket.yml`
- `.env`, `.env.example`, `.gitignore`
- `docs/` with overview and usage docs
- `summary_executive_of_one_paragraph_of_the_project.txt`
- `analysis_expansion.txt`

## Notes on OpenAI model choice
For cost-effective demos choose a small-capacity model compatible with
LangChain such as `gpt-4o-mini` (if available) or `gpt-3.5-turbo`. The code
will default to simulated responses if no `OPENAI_API_KEY` is present.

