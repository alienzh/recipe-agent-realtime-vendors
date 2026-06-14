"""Realtime MLLM vendor registry — one readable builder per Agora-supported
realtime (voice-to-voice) vendor.

Each `build_<vendor>(env)` is a self-contained, copy-pasteable example of wiring
that vendor into an Agora Conversational AI agent as a single realtime MLLM: it
shows the real SDK constructor call, the `server_vad` turn detection it owns, and
exactly which env vars it needs. `build_vendor(name)` selects one by
`REALTIME_VENDOR`. Optional `REALTIME_MODEL` overrides the model.

This recipe is BYO-only: every vendor (including the default `openai`) requires
its own credentials, so every builder reads at least one required env var.

Add or change a vendor by editing its builder below + the REGISTRY line.
"""
import os
from typing import Callable, Dict, List, Optional, Tuple

from agora_agent.agentkit.vendors import (
    OpenAIRealtime, GeminiLive, XaiGrok, VertexAI,
)

CATEGORY = "REALTIME"

# Turn detection is owned by the realtime MLLM (no top-level cascading VAD).
TURN_DETECTION = {"mode": "server_vad"}


def _model(env, default: str) -> str:
    """The selected model, overridable with REALTIME_MODEL."""
    return env.get("REALTIME_MODEL") or default


# --- one builder per vendor (these are the samples) -------------------------

def build_openai(env):
    """OpenAI Realtime — set OPENAI_API_KEY (platform.openai.com)."""
    return OpenAIRealtime(
        api_key=env["OPENAI_API_KEY"],
        model=_model(env, "gpt-4o-realtime-preview"),
        turn_detection=TURN_DETECTION,
    )


def build_gemini(env):
    """Google Gemini Live — set GEMINI_API_KEY (aistudio.google.com)."""
    return GeminiLive(
        api_key=env["GEMINI_API_KEY"],
        model=_model(env, "gemini-2.0-flash-live-001"),
        turn_detection=TURN_DETECTION,
    )


def build_xai(env):
    """xAI Grok realtime — set XAI_API_KEY (console.x.ai)."""
    return XaiGrok(
        api_key=env["XAI_API_KEY"],
        turn_detection=TURN_DETECTION,
    )


def build_vertexai(env):
    """Google Vertex AI realtime — set GOOGLE_APPLICATION_CREDENTIALS_JSON,
    GOOGLE_PROJECT_ID, GOOGLE_LOCATION (service-account ADC)."""
    return VertexAI(
        adc_credentials_string=env["GOOGLE_APPLICATION_CREDENTIALS_JSON"],
        project_id=env["GOOGLE_PROJECT_ID"],
        location=env["GOOGLE_LOCATION"],
        model=_model(env, "gemini-2.0-flash-live-001"),
        turn_detection=TURN_DETECTION,
    )


# --- registry: name -> (builder, required env vars) -------------------------
# BYO-only: every vendor requires at least one env var (no key-less default).
REGISTRY: Dict[str, Tuple[Callable, List[str]]] = {
    "openai":   (build_openai,   ["OPENAI_API_KEY"]),
    "gemini":   (build_gemini,   ["GEMINI_API_KEY"]),
    "xai":      (build_xai,      ["XAI_API_KEY"]),
    "vertexai": (build_vertexai, ["GOOGLE_APPLICATION_CREDENTIALS_JSON", "GOOGLE_PROJECT_ID", "GOOGLE_LOCATION"]),
}


def available() -> List[str]:
    return sorted(REGISTRY)


def required_env(name: str) -> List[str]:
    return list(REGISTRY[name][1])


def needs_key(name: str) -> bool:
    return bool(REGISTRY[name][1])


def build_vendor(name: str, env: Optional[Dict[str, str]] = None):
    """Build the selected vendor; raises ValueError naming any missing env vars."""
    env = env if env is not None else os.environ
    if name not in REGISTRY:
        raise ValueError(f"unknown {CATEGORY} vendor '{name}'; choose one of {available()}")
    builder, required = REGISTRY[name]
    missing = [var for var in required if not env.get(var)]
    if missing:
        raise ValueError(
            f"{CATEGORY} vendor '{name}' requires environment variable(s): {', '.join(missing)}"
        )
    return builder(env)
