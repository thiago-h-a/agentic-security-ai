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

Additionally, the repository provides a **demo AI streaming API** (`demo_stream_api.py`), allowing you
to see an infinite sequence of demo cases served over HTTP. Each page refresh
resets the counting from "Case 1".

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

3. Run the AI demo locally:

```bash
python demo_ai.py
```

4. Run the **demo streaming API**:

```bash
python demo_stream_api.py
```

Then open your browser and navigate to [http://localhost:8000/demo](http://localhost:8000/demo) to see the live stream.

## Docker and Docker Compose

1. Build and run using Docker Compose:

```bash
docker-compose up --build
```

2. The API will be available at [http://localhost:8000/demo](http://localhost:8000/demo).

This setup automatically installs dependencies and runs the demo streaming API.

## Note

- Refreshing the browser will reset the demo stream counter to "Case 1".
