# Agora Agent Backend — Realtime Vendors Recipe

FastAPI service that owns Agora token generation and agent session lifecycle for
the realtime vendors recipe. It is the service the web client reaches through the
Next.js `/api/*` rewrite proxy (port 8000).

## What this service does

Runs a single realtime MLLM via `.with_mllm()`, selected from a data-driven
vendor registry — **BYO-only, not zero-key**:

**Pipeline:** `<REALTIME_VENDOR>` MLLM (voice-to-voice, server_vad turn detection)

The realtime MLLM vendor replaces the cascading STT→LLM→TTS with a single
realtime model. The leg is built from `server/src/vendors.py` (`build_vendor`)
and attached with `.with_mllm()` only — no `.with_stt/.with_llm/.with_tts`. The
selected vendor's provider credentials are required and are validated at agent start
(not server boot), so the server starts even if they are absent, but `/startAgent`
returns 400 until they are configured.

There is **no separate `llm/` service** in this recipe.

## Vendors

`server/src/vendors.py` holds `CATEGORY = "REALTIME"` and the registry for
OpenAI Realtime, Azure OpenAI Realtime, Gemini Live, xAI Grok, and Vertex AI. Select one with `REALTIME_VENDOR` (default
`openai`); the UI may override this per request; optionally override the model with
`REALTIME_MODEL` where supported.
Azure uses its required `AZURE_OPENAI_REALTIME_MODEL` deployment setting.

| `REALTIME_VENDOR` | Required env | Default model |
| --- | --- | --- |
| `openai` | `OPENAI_API_KEY` | `gpt-4o-realtime-preview` |
| `azure` | `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_REALTIME_URL`, `AZURE_OPENAI_REALTIME_MODEL` | Azure deployment |
| `gemini` | `GEMINI_API_KEY` | `gemini-2.0-flash-live-001` |
| `xai` | `XAI_API_KEY` | _(SDK default)_ |
| `vertexai` | `GOOGLE_APPLICATION_CREDENTIALS_JSON`, `GOOGLE_PROJECT_ID`, `GOOGLE_LOCATION` | `gemini-2.0-flash-live-001` |

## Run

Use the repo-root `README.md` for the full local flow (`bun run dev`). To work on
this module directly:

```bash
cd server
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python src/server.py
```

## Environment

`server/.env.example` is the template. Required:

- `AGORA_APP_ID` — Agora project App ID.
- `AGORA_APP_CERTIFICATE` — Agora project App Certificate.
- The selected vendor's credentials — see the [Vendors](#vendors) table (BYO-only;
  validated at agent start).

Optional:

| Variable | Default | Notes |
| --- | :---: | --- |
| `REALTIME_VENDOR` | `openai` | Which realtime MLLM vendor to build |
| `REALTIME_MODEL` | per-vendor | Optional model override where supported; Azure uses its deployment setting |
| `AZURE_OPENAI_API_KEY` / `AZURE_OPENAI_REALTIME_URL` / `AZURE_OPENAI_REALTIME_MODEL` | — | Required Azure key, complete WebSocket URL, and deployment/model name |
| `AGENT_GREETING` | built-in | Optional opening line override |

## API

- `GET /vendors` — list vendor options and the configured default
- `GET /get_config` — token + channel/UID config
- `POST /startAgent` — start an agent session
- `POST /stopAgent` — stop an agent session

The repo-root `bun run verify:local:fastapi` exercises these routes through the
Next proxy using a fake agent (`scripts/run_fake_server.py`), so no live Agora
session is required.
