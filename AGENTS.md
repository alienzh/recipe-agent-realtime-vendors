# Agent Development Guide

For coding agents working in `recipe-agent-realtime-vendors`. This repository is
the **realtime vendors** recipe in the Agora Conversational AI recipes family:
the realtime MLLM leg is a per-vendor switchboard (one readable `build_<vendor>`
per vendor) defaulted by `REALTIME_VENDOR` and overridable in the UI. The MLLM replaces the cascade and is
attached with `.with_mllm()` only.

## System shape

- **`server/`** — Python FastAPI agent backend (:8000). Owns Agora token
  generation and agent session lifecycle. The realtime MLLM leg is built from the
  per-vendor builder registry in `server/src/vendors.py` and attached via `.with_mllm()`
  — it replaces the STT/LLM/TTS cascade. SDK: `agora-agents>=2.6.0`
  (`import agora_agent`).
- **`web/`** — Next.js 16 / React 19 / TypeScript frontend (:3000).
- Auth: Token007 from `AGORA_APP_ID` + `AGORA_APP_CERTIFICATE`.
- No `llm/` service — single-process, MLLM is **BYO-only** (every vendor,
  including the default `openai`, requires provider credentials).

## Pipeline

`<REALTIME_VENDOR>` MLLM via `.with_mllm()` (default `openai`) — voice-to-voice,
no separate STT/LLM/TTS. Turn detection is MLLM-owned (`server_vad`). No tools
(the realtime MLLM vendors are tool-less).

## Vendor registry

- `server/src/vendors.py` holds `CATEGORY = "REALTIME"`, one readable
  `build_<vendor>(env)` function per vendor (`openai`, `azure`, `gemini`,
  `xai`, `vertexai`), a `REGISTRY: {name: (builder,
  [required_env])}`, and `build_vendor()` / `required_env()` / `needs_key()` /
  `available()`.
- `agent.py` reads `REALTIME_VENDOR` in `__init__` (no validation) and calls
  `build_vendor(selected)` for the MLLM leg **in `start()`** — where `selected`
  is the in-UI `vendor` (from `GET /vendors` + the pre-call dropdown) or
  `REALTIME_VENDOR`. BYO credential validation happens there, so `/get_config`
  stays key-less.
- The MLLM is attached with `.with_mllm()` only; never `.with_stt/.with_llm/.with_tts`.
- Each builder sets `turn_detection={"mode": "server_vad"}` (MLLM-owned).

## Routing / ownership

- UI and RTC/RTM lifecycle live in `web/`.
- Browser-facing `/api/*` paths are Next rewrites (`web/next.config.ts`) to the
  agent backend; do not add `web/app/api/**/route.ts` for agent/token logic.
- Token generation and agent lifecycle live in `server/src/`.
- The realtime vendor registry lives in `server/src/vendors.py`.

## Supported modes

- **Local:** `bun run dev` starts `server` (:8000) and `web` (:3000).
  The web app calls `/api/*`; Next rewrites to
  `AGENT_BACKEND_URL=http://localhost:8000`.
- **Deploy:** deploy `web` (Next) + `server` (reachable FastAPI).
  Set `AGENT_BACKEND_URL` in the web deployment.

## Env vars

| Variable | Default | Notes |
|---|---|---|
| `AGORA_APP_ID` | — | required |
| `AGORA_APP_CERTIFICATE` | — | required |
| `REALTIME_VENDOR` | `openai` | which realtime MLLM vendor to build (see README Vendors table) |
| `REALTIME_MODEL` | per-vendor | optional model override where supported; Azure uses its required deployment setting |
| _vendor creds_ | — | **required** for the selected vendor (BYO-only); `required_env(selected vendor)` |
| `AZURE_OPENAI_API_KEY` / `URL` / `MODEL` | — | required for the Azure vendor |
| `AGENT_GREETING` | built-in | Optional opening line override |

## Patterns

- Keep the web client calling `/api/*`; hide backend placement behind Next rewrites.
- Keep token generation and the App Certificate in `server/`.
- The selected vendor's creds are validated in `agent.start()` via `build_vendor`
  — the server boots without them, but `/startAgent` returns 400 until they are set.
- Add or change realtime vendors by editing the relevant `build_<vendor>`
  function + its `REGISTRY` line in `vendors.py`; the framework
  (`build_vendor`/`required_env`/`needs_key`/`available`) is shared across the
  sibling vendor recipes — keep it identical.
- `turn_detection` is MLLM-owned (`server_vad`); do not set a top-level
  `turn_detection` on `AgoraAgent(...)` when using `.with_mllm()`.

## Anti-patterns

- Do not reintroduce `llm/` or the cascading STT/LLM/TTS vendors, and never call
  `.with_stt/.with_llm/.with_tts` — this recipe uses `.with_mllm()` only.
- Do not hardcode a single realtime vendor in `agent.py`; build it via `build_vendor`.
- Do not validate vendor credentials in `__init__` (it would break key-less
  `/get_config` and the managed docker smoke).
- Do not reintroduce Next Route Handlers for agent/token logic.
- Do not put `PORT` in `server/.env.example` (it would clobber the random port
  that `verify:local:fastapi` injects via `load_dotenv(override=True)`).
- Do not link to `docs/ai/` — that progressive-disclosure tree is not present yet.
- Do not add tools — the realtime MLLM vendors have no tool support.

## Commands

```bash
bun run setup
bun run dev
bun run doctor
bun run doctor:local
bun run verify         # web-only, no creds
bun run verify:local   # full local gate
```

Narrower checks: `bun run verify:backend`, `bun run verify:local:fastapi`,
`bun run verify:web:proxy`.

## Done criteria

1. Run the narrowest relevant verification command.
2. Web-affecting changes: `bun run verify:web` passes.
3. Backend-affecting changes: `bun run verify:local` (or narrower
   `verify:local:fastapi` / `verify:backend`) passes.
4. If you change required env vars or setup steps, update the root README,
   the relevant module README, and `server/.env.example` together.

## Git conventions

- Conventional Commits: `type: description` or `type(scope): description`
  (`feat`, `fix`, `chore`, `test`, `docs`). Lowercase after the prefix, present
  tense.
- No AI tool names in commit messages or PR descriptions. No `Co-Authored-By`
  trailers. No `--no-verify`. No git config changes.
- Branch names: `type/short-description` (e.g. `feat/add-vendor`).
