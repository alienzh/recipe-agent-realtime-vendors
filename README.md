# Agora Conversational AI — Realtime Vendors Recipe (Python)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/python-%3E%3D3.10-blue)](https://www.python.org/)
[![Bun](https://img.shields.io/badge/bun-latest-black)](https://bun.sh/)

The **realtime vendors** recipe in the Agora Conversational AI recipes family.
Voice-to-voice conversation using a single **realtime MLLM** — no separate STT,
LLM, or TTS. The MLLM leg is a **data-driven switchboard** over every A4.1
realtime vendor, selected via `REALTIME_VENDOR`. The MLLM replaces the cascade,
so it is attached with `.with_mllm()` only (no `.with_stt/.with_llm/.with_tts`).

**BYO-only — NOT zero-key.** Every realtime vendor requires its own API key,
including the default `openai` (needs `OPENAI_API_KEY`). The selected vendor's
credentials are validated **when the agent starts** (not at construction), so
`/get_config` always works key-less.

**Pipeline:** **`<REALTIME_VENDOR>`** MLLM via `.with_mllm()` (default `openai`, server_vad turn detection)

## Vendors

Two ways to pick a vendor:
- **In the UI** — the pre-call screen has a **Realtime vendor dropdown**; choose
  one and start. No restart needed. (This recipe is BYO-only, so every vendor
  still requires its env vars set on the server; if they're missing, startup
  reports exactly which.)
- **By env** — set `REALTIME_VENDOR` (the default for the dropdown) + the vendor's
  keys in `server/.env.local`; optionally override the model with `REALTIME_MODEL`.
  Turn detection (`server_vad`) is owned by the MLLM.

| Vendor | `REALTIME_VENDOR` | Required env | Default model |
| --- | --- | --- | --- |
| OpenAI Realtime | `openai` | `OPENAI_API_KEY` | `gpt-4o-realtime-preview` |
| Gemini Live | `gemini` | `GEMINI_API_KEY` | `gemini-2.0-flash-live-001` |
| xAI Grok | `xai` | `XAI_API_KEY` | _(SDK default)_ |
| Vertex AI | `vertexai` | `GOOGLE_APPLICATION_CREDENTIALS_JSON`, `GOOGLE_PROJECT_ID`, `GOOGLE_LOCATION` | `gemini-2.0-flash-live-001` |

This recipe is **BYO-only**: there is no keyless default — every vendor (including
the default `openai`) needs its own key. The selected vendor's credentials are
validated **when the agent starts**, so `/get_config` works key-less.

### Sample code — how each vendor is wired

Every vendor is a small, copy-pasteable builder in [`server/src/vendors.py`](server/src/vendors.py)
that shows the real SDK constructor and the `server_vad` turn detection the MLLM
owns. For example:

```python
from agora_agent.agentkit.vendors import OpenAIRealtime, GeminiLive, XaiGrok

TURN_DETECTION = {"mode": "server_vad"}

# OpenAI Realtime — set OPENAI_API_KEY:
OpenAIRealtime(
    api_key=env["OPENAI_API_KEY"],
    model="gpt-4o-realtime-preview",
    turn_detection=TURN_DETECTION,
)

# Gemini Live — set GEMINI_API_KEY:
GeminiLive(
    api_key=env["GEMINI_API_KEY"],
    model="gemini-2.0-flash-live-001",
    turn_detection=TURN_DETECTION,
)

# xAI Grok — set XAI_API_KEY:
XaiGrok(
    api_key=env["XAI_API_KEY"],
    turn_detection=TURN_DETECTION,
)
```

The agent attaches the chosen one with `.with_mllm(build_vendor(name))` — there is
no STT/LLM/TTS cascade. To add or change a vendor, edit its `build_<vendor>`
function + the `REGISTRY` line.

## Prerequisites

- [Python 3.10+](https://www.python.org/)
- [Bun](https://bun.sh/)
- [Agora CLI](https://github.com/AgoraIO/cli) — makes generating an App ID + App Certificate easy
- **An API key for your chosen realtime vendor** — set the env vars from the
  [Vendors](#vendors) table in `server/.env.local`

## Run It

```bash
# 1. Install web deps + create the Python venv
bun run setup

# 2. Add Agora credentials (CLI), or edit server/.env.local by hand
agora login
agora project use <your-project>          # select which project to use
agora project env write server/.env.local # writes App ID + Certificate

# 3. Pick a realtime vendor + add its key to server/.env.local (BYO-only)
#    REALTIME_VENDOR=openai            (default — see the Vendors table)
#    OPENAI_API_KEY=sk-...             (required for the openai vendor)
#    REALTIME_MODEL=gpt-4o-realtime-preview  (optional model override)

# 4. Run backend + web
bun run dev
```

Open [http://localhost:3000](http://localhost:3000) → **Start Conversation** → speak.

To try a different realtime vendor, pick it from the **dropdown** on the pre-call
screen (no restart). Because this recipe is BYO-only, set that vendor's keys in
`server/.env.local` first (see [Vendors](#vendors)).

### Working from a clone

If you cloned this repo (rather than scaffolding via the Agora CLI), the steps
above are complete as written: `bun run setup` creates the Python venv and
installs web dependencies, then `bun run dev` brings up both services. You
still need Agora credentials and the selected vendor's key in `server/.env.local`
before a conversation can connect.

Services:

- Frontend — http://localhost:3000
- Backend — http://localhost:8000
- Mock LLM — N/A (single realtime MLLM, no mock service)
- API docs — http://localhost:8000/docs

## Deploy

Deploy `web` (Next.js) and `server` (a reachable FastAPI backend). Set
`AGENT_BACKEND_URL` in the web deployment so the Next rewrites reach the backend.

A backend-only Docker image is published to
`ghcr.io/AgoraIO-Conversational-AI/recipe-agent-realtime-vendors` on `v*` tags.
It exposes **BACKEND-ONLY** (:8000). No separate service is needed.

## Environment variables

Backend env file: [`server/.env.example`](server/.env.example).

| Variable | Required | Default | Notes |
| --- | :---: | :---: | --- |
| `AGORA_APP_ID` | ✅ | — | Agora Console → Project → App ID |
| `AGORA_APP_CERTIFICATE` | ✅ | — | Agora Console → Project → App Certificate |
| `REALTIME_VENDOR` | | `openai` | Which realtime MLLM vendor to build (see [Vendors](#vendors)) |
| `REALTIME_MODEL` | | per-vendor | Optional model override for the selected vendor |
| _vendor creds_ | ✅ | — | Required for the selected vendor (BYO-only); validated at agent start |
| `AGENT_GREETING` | | built-in | Optional opening line override |

## Commands

```bash
bun run setup            # install web deps + create server/ venv
bun run dev              # run backend (:8000) + web (:3000)

bun run doctor           # prerequisite check (no creds needed)
bun run doctor:local     # + .env.local + credentials checks

bun run verify           # web-only gate (no Agora creds needed)
bun run verify:local     # full local gate: backend compile + smoke tests + web build
bun run clean            # remove venvs and build artifacts
```

Tests run standalone (no Agora cloud needed): `pytest` in `server/`, plus
`bun run verify` in `web/`. CI runs them on Linux/macOS/Windows × Python 3.10 & 3.13.

## Architecture

```
Browser (localhost:3000)
  │  fetch /api/*
  ▼
Next.js  ──rewrite──▶  Agent backend  (server/, localhost:8000)
                          │  starts agent session
                          │  MLLM leg = build_vendor(REALTIME_VENDOR)
                          │  attached via .with_mllm() (replaces the cascade)
                          ▼
                       Agora ConvoAI Cloud
                          │  <REALTIME_VENDOR> (voice-to-voice, server_vad)
                          ▼
                       User hears realtime voice response
```

The realtime vendor switchboard lives in `server/src/vendors.py` — one readable
`build_<vendor>` function per vendor (the sample code) plus a `REGISTRY` mapping
name → builder + required env. No cascading STT/LLM/TTS vendors. No `llm/`
service. See [ARCHITECTURE.md](./ARCHITECTURE.md).

## What You Get

- A **vendor switchboard** for the realtime MLLM leg: one readable `build_<vendor>`
  builder per vendor plus a `REGISTRY`, covering all four A4.1 realtime vendors,
  selected via `REALTIME_VENDOR` or the in-UI dropdown.
- A **Next.js** web client (:3000) that drives the RTC/RTM lifecycle and only ever calls `/api/*`.
- A **FastAPI** agent backend (:8000) that owns Agora token generation and the agent session lifecycle.
- **Realtime MLLM** attached via `.with_mllm()` — replaces the cascading STT→LLM→TTS with a single voice-to-voice model.
- **Server-side VAD** (`server_vad`) turn detection — owned by the MLLM, no top-level cascading VAD config needed.
- **BYO key** — every vendor (including the default `openai`) requires its own key; validated at agent start.

## How It Works

1. The browser calls `/api/get_config`, which Next rewrites to the backend; the
   backend mints an Agora token from `AGORA_APP_ID` + `AGORA_APP_CERTIFICATE`.
   This works key-less even though the recipe is BYO-only — vendor credentials
   are only checked at agent start.
2. The browser joins the RTC channel, then calls `/api/startAgent`; the backend
   builds the selected MLLM via `build_vendor(REALTIME_VENDOR)` (raising a clear
   error if the vendor's credentials are missing) and starts the agent session.
3. The user speaks. Agora routes audio to the selected realtime endpoint.
4. The realtime MLLM processes voice-to-voice and streams the response audio back.
5. The agent's voice plays in the channel. RTM transcript + metrics arrive in the web UI.
6. `/api/stopAgent` ends the session.

## Repo Map

- `web/` — Next.js frontend (:3000); RTC/RTM lifecycle and UI.
- `server/` — FastAPI agent backend (:8000); Agora tokens + agent lifecycle, realtime MLLM.
- `server/src/vendors.py` — one readable builder per realtime vendor + the registry.
- `ARCHITECTURE.md` — system shape and component boundaries.
- `AGENTS.md` — guide for coding agents working in this repo.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `REALTIME vendor '<x>' requires environment variable(s): ...` at start | Set the listed env vars for that `REALTIME_VENDOR` (see [Vendors](#vendors)). |
| `/startAgent` returns 400 | Check the selected vendor's key is set and has realtime API access. |
| Agent starts but no audio | Ensure the model (`REALTIME_MODEL`) supports realtime voice for that vendor. |
| Local calls fail under a global proxy (Clash, etc.) | Configure your proxy to send `127.0.0.1`, `localhost`, and RFC-1918 ranges DIRECT. |

## More Docs

- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [AGENTS.md](./AGENTS.md)

## License

Released under the [MIT License](./LICENSE).
