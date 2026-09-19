# Herald

[![CI](https://github.com/venkatesh16180/herald/actions/workflows/ci.yml/badge.svg)](https://github.com/venkatesh16180/herald/actions)

A local-first, agentic morning briefing assistant. Herald pulls live weather and news, composes a short spoken briefing with a local LLM (bounded by a retry loop that enforces a spoken-length budget), voices it with a local TTS model, and serves the whole thing over a real HTTP API — no cloud LLM calls, no API keys sent anywhere but OpenWeatherMap.

Built and tested end-to-end on a constrained 8-year-old laptop (Core i3-4005U, 8GB RAM, no dedicated GPU) — every model choice picked deliberately as the smallest one that reliably does the job. Runtime will be substantially faster on more capable hardware; see [Known Limitations](#known-limitations).

## Architecture at a Glance

| Layer | Technology | Role |
|---|---|---|
| Data | `weather.py`, `news.py`, `clock.py` | Deterministic collectors — no LLM, no judgment calls, pure fetch-and-parse |
| Brain | LangGraph + Ollama | Two-node state graph: compose the briefing, then enforce a spoken-length budget with a bounded retry |
| Voice | Kokoro-82M (Apache 2.0) | Local neural TTS, renders the final script to a `.wav` file |
| Service | FastAPI + Pydantic | Exposes `/briefing/generate` over HTTP |
| Storage | SQLite (`history.db`) | One row per generated briefing — queryable history |
| Config/Logging | python-dotenv + logging | Centralized config, rotating file logs |
| Automation | Docker Compose | Reproducible container, ready for cron/Task Scheduler |
| Dependencies | pip-tools | `requirements.in` (direct deps) → `requirements.txt` (fully pinned lock file) |

## Setup

### Option A — Docker Compose (recommended, fully self-contained)

This spins up **both** Herald and Ollama in containers — the only thing you need pre-installed is Docker Desktop. Works on a machine that's never touched this project before.

```bash
git clone https://github.com/venkatesh16180/herald.git
cd herald
cp .env.example .env   # fill in your OpenWeatherMap API key
docker compose up
```

First run will pull the Ollama image and build the Herald image — expect this to take a while (torch + spacy + kokoro is a heavy dependency tree). The Ollama container starts with no models loaded; pull one into it before your first request:

```bash
docker exec -it herald-ollama-1 ollama pull qwen3:4b
```

Then hit the API — see [API Reference](#api-reference) below.

### Option B — Docker Compose, host Ollama (for RAM-constrained machines)

If you already run Ollama on your host machine and want to avoid running two full model-serving processes in memory at once, use the lighter single-container variant instead:

```bash
cp docker-compose.local.yml.example docker-compose.local.yml
docker compose -f docker-compose.local.yml up
```

This requires Ollama already installed and running on your **host** (not containerized), with the model already pulled:

```bash
ollama pull qwen3:4b
```

### Option C — Local Python (no Docker)

```bash
py -3.10 -m venv venv
.\venv\Scripts\Activate.ps1        # Windows
pip install pip-tools
pip-sync requirements.txt
cp .env.example .env               # fill in your OpenWeatherMap API key
ollama pull qwen3:4b
uvicorn main:app --reload
```

Adding a new dependency at any point: add it to `requirements.in`, then run `pip-compile requirements.in && pip-sync requirements.txt` — never a bare `pip install` into the venv.

## API Reference

### `GET /health`

```bash
curl http://localhost:8000/health
```

```json
{"status": "ok"}
```

### `POST /briefing/generate`

Runs the full pipeline: fetches current weather and headlines, composes a briefing through the LangGraph brain, synthesizes it with Kokoro, and logs it to `history.db`.

```bash
curl -X POST http://localhost:8000/briefing/generate \
  -H "Content-Type: application/json" \
  -d "{}"
```

```json
{
  "script": "Good morning. It's 11:32 AM Friday. Overcast with a temperature of 30C, but it feels like 34C today. Reports show three dead and eight injured in a Philippines school shooting, at least 16 killed in a Pakistan mosque attack, a new wild cat species discovered with only one living specimen, dozens of suspected illegal miners who died in custody in Nigeria, and Japan raising interest rates to a 31-year high to curb rising prices.",
  "audio_path": "data/briefing_20260918_1146.wav",
  "word_count": 74,
  "generated_at": "2026-09-18T11:46:17.067590"
}
```

Interactive API docs (Swagger UI) are available at `http://localhost:8000/docs` once the server is running.

## Testing

```bash
pytest -v
```

The suite runs with **no live Ollama server and no network access** — `ollama.chat` and `requests.get` are mocked, so CI tests the actual control flow (word-budget enforcement, the bounded retry loop, response parsing) rather than depending on a model being available.

## Known Limitations

- **Performance on constrained hardware.** This project was built and tested on an 8GB, no-GPU laptop. Running the containerized pipeline (Herald in Docker + a host or containerized Ollama) on this hardware is noticeably slower than running it directly in a local Python environment, since both the container runtime and the LLM are competing for a small memory budget. On a machine with more RAM and/or a GPU, this should run substantially faster.
- **`BriefingRequest.city` is accepted but not yet wired through** — the endpoint validates the field but always uses the configured default city. Left as a documented, deliberate gap rather than a bug.

## License

MIT