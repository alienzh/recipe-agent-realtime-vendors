"""Vendor registry — data-driven switchboard over the A4.1 REALTIME vendors."""
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from agora_agent.agentkit import vendors as V

CATEGORY = "REALTIME"   # one of: STT | LLM | TTS | REALTIME  (per repo)


@dataclass
class VendorSpec:
    cls: Callable[..., Any]
    creds: Dict[str, str] = field(default_factory=dict)   # sdk_field -> ENV_VAR (required, no default)
    defaults: Dict[str, Any] = field(default_factory=dict)  # sdk_field -> default value
    model_field: Optional[str] = None   # field overridden by {CATEGORY}_MODEL
    voice_field: Optional[str] = None   # field overridden by {CATEGORY}_VOICE


TD = {"mode": "server_vad"}
SPECS: Dict[str, VendorSpec] = {
  "openai":   VendorSpec(V.OpenAIRealtime, {"api_key": "OPENAI_API_KEY"},
                {"model": "gpt-4o-realtime-preview", "turn_detection": TD}, model_field="model"),
  "gemini":   VendorSpec(V.GeminiLive, {"api_key": "GEMINI_API_KEY"},
                {"model": "gemini-2.0-flash-live-001", "turn_detection": TD}, model_field="model"),
  "xai":      VendorSpec(V.XaiGrok, {"api_key": "XAI_API_KEY"},
                {"turn_detection": TD}),
  "vertexai": VendorSpec(V.VertexAI,
                {"adc_credentials_string": "GOOGLE_APPLICATION_CREDENTIALS_JSON",
                 "project_id": "GOOGLE_PROJECT_ID", "location": "GOOGLE_LOCATION"},
                {"model": "gemini-2.0-flash-live-001", "turn_detection": TD}, model_field="model"),
}


def available() -> List[str]:
    return sorted(SPECS)


def required_env(name: str) -> List[str]:
    return list(SPECS[name].creds.values())


def build_vendor(name: str, env: Optional[Dict[str, str]] = None):
    env = env if env is not None else os.environ
    if name not in SPECS:
        raise ValueError(f"unknown {CATEGORY} vendor '{name}'; choose one of {available()}")
    spec = SPECS[name]
    kwargs: Dict[str, Any] = dict(spec.defaults)
    # generic model/voice overrides
    if spec.model_field and env.get(f"{CATEGORY}_MODEL"):
        kwargs[spec.model_field] = env[f"{CATEGORY}_MODEL"]
    if spec.voice_field and env.get(f"{CATEGORY}_VOICE"):
        kwargs[spec.voice_field] = env[f"{CATEGORY}_VOICE"]
    # required creds + infra from env
    missing: List[str] = []
    for sdk_field, var in spec.creds.items():
        val = env.get(var)
        if not val:
            missing.append(var)
        else:
            kwargs[sdk_field] = val
    if missing:
        raise ValueError(
            f"{CATEGORY} vendor '{name}' requires environment variable(s): {', '.join(missing)}"
        )
    return spec.cls(**kwargs)
