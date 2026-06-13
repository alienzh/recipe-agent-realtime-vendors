# Architecture — Realtime Vendors Recipe

Two processes. The browser talks only to Next.js `/api/*`, which rewrites to the
agent backend. The agent backend owns Agora tokens and agent lifecycle.

This recipe is **BYO-only** — the selected realtime vendor's key is required and
is validated at agent start, not server boot.

## Request flow

```
Browser
  │  GET /api/get_config            → token + channel/UIDs
  │  POST /api/startAgent           → start agent session
  ▼
Next.js  (rewrites /api/* → AGENT_BACKEND_URL)
  ▼
Agent backend (server/, :8000)
  │  builds the selected MLLM via build_vendor(REALTIME_VENDOR)
  │  attaches it with .with_mllm() (replaces the cascade)
  ▼
Agora ConvoAI Cloud
  │  user speech → <REALTIME_VENDOR> (voice-to-voice, server_vad)
  │  agent speech → user's channel
  ▼
User hears realtime voice response; RTM transcript + metrics → web UI
```

`POST /api/stopAgent { agentId }` ends the session.

## Why no llm/ service

Unlike the cascade recipe family, the realtime recipe attaches a single realtime
MLLM vendor via `agora_agent.with_mllm(mllm)`. This vendor handles the full
voice-to-voice pipeline — STT, reasoning, and TTS are all internal to the
realtime model. No cascading vendors are used (`.with_stt/.with_llm/.with_tts`
are never called), no separate mock service is needed, and no public tunnel is
required.

Trade-off: this recipe is **BYO-only** — every vendor (including the default
`openai`) requires its own API key. The agent is **not zero-key**.

## Vendor registry

`server/src/vendors.py` is a **data-driven switchboard** over the A4.1 realtime
vendors. It holds `CATEGORY = "REALTIME"`, the `SPECS` table (all four realtime
MLLM vendors), and `build_vendor()` / `required_env()` / `available()`. Each spec
maps a vendor to `{cls, creds(env), defaults}`:

| Vendor | `REALTIME_VENDOR` | Required env | Default model |
| --- | --- | --- | --- |
| OpenAI Realtime | `openai` | `OPENAI_API_KEY` | `gpt-4o-realtime-preview` |
| Gemini Live | `gemini` | `GEMINI_API_KEY` | `gemini-2.0-flash-live-001` |
| xAI Grok | `xai` | `XAI_API_KEY` | _(SDK default)_ |
| Vertex AI | `vertexai` | `GOOGLE_APPLICATION_CREDENTIALS_JSON`, `GOOGLE_PROJECT_ID`, `GOOGLE_LOCATION` | `gemini-2.0-flash-live-001` |

- `agent.py` reads `REALTIME_VENDOR` (default `openai`) in `__init__` (no
  validation) and calls `build_vendor(self.vendor)` **in `start()`** — BYO
  credential validation happens there, so `/get_config` and the managed docker
  smoke stay key-less.
- Each spec default sets `turn_detection={"mode": "server_vad"}` — vendor-side
  VAD; the top-level cascading `turn_detection` on `AgoraAgent(...)` is not set.
- The MLLM is attached with `.with_mllm()` only; no cascading STT/LLM/TTS legs.

No tools — the realtime MLLM vendors have no tool support in this SDK.

## API (agent backend, port 8000)

| Endpoint | Method | Description |
| --- | --- | --- |
| `/get_config` | GET | Token + channel/UID config |
| `/startAgent` | POST | Start the realtime agent session |
| `/stopAgent` | POST | Stop the agent by `agent_id` |

The browser calls these as `/api/*`; Next rewrites them to `AGENT_BACKEND_URL`.

## Auth

- Browser → agent backend: none (local dev).
- Agent backend → Agora cloud: Token007, generated from `AGORA_APP_ID` +
  `AGORA_APP_CERTIFICATE`.
- Agora cloud → realtime vendor: the selected vendor's key (BYO — passed at agent start).
