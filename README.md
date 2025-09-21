# SecOps

This repository contains a lightweight demo of a SecOps / threat-hunting
pipeline implemented as a sequence of agents (collector, intel, hypothesis,
query builder, detector, correlator, responder) connected via **LangGraph**.

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
