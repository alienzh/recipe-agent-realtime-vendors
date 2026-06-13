"""
Agent — Realtime Vendors Recipe

High-level API for managing Agora Conversational AI Agents using a single
realtime MLLM, selected from a data-driven vendor registry. The MLLM replaces
the cascading STT->LLM->TTS and is attached via .with_mllm():

  build_vendor(REALTIME_VENDOR)  ->  voice-to-voice MLLM (server_vad)

This recipe is BYO-only: every realtime vendor requires its own API key (the
default `openai` needs OPENAI_API_KEY). The selected vendor's credentials are
validated in start(), not __init__, so the server still boots without them.
"""
import logging
import os
import time
from typing import Any, Dict, Optional

from agora_agent import Area, AsyncAgora
from agora_agent.agentkit import Agent as AgoraAgent
from vendors import build_vendor

logger = logging.getLogger("uvicorn.error")


class Agent:
    """
    High-level wrapper for an Agora Conversational AI Agent using a realtime MLLM.

    The MLLM (voice-to-voice, server_vad) is built from the vendor registry in
    vendors.py and attached via .with_mllm(). No separate STT, LLM, or TTS vendors
    are used. This recipe is BYO-only — the selected vendor's API key is required
    and is validated at start() time.
    """

    def __init__(self):
        self.app_id = os.getenv("AGORA_APP_ID")
        self.app_certificate = os.getenv("AGORA_APP_CERTIFICATE")
        self.greeting = os.getenv(
            "AGENT_GREETING",
            "Hi! I'm a realtime voice assistant — let's just talk.",
        )

        # Which realtime MLLM vendor to build. Default `openai` is BYO-only
        # (needs OPENAI_API_KEY). Do NOT validate vendor creds here — they are
        # validated at start() so the server still boots without them.
        self.vendor = os.getenv("REALTIME_VENDOR", "openai")

        if not self.app_id or not self.app_certificate:
            raise ValueError("AGORA_APP_ID and AGORA_APP_CERTIFICATE are required")

        self.client = AsyncAgora(
            area=Area.US,
            app_id=self.app_id,
            app_certificate=self.app_certificate,
        )

        # Track active sessions by agent_id
        self._sessions: Dict[str, Any] = {}

    async def start(
        self,
        channel_name: str,
        agent_uid: int,
        user_uid: int,
        output_audio_codec: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Start realtime voice agent."""
        if not channel_name or not str(channel_name).strip():
            raise ValueError("channel_name is required and cannot be empty")
        if agent_uid <= 0:
            raise ValueError("agent_uid is required and cannot be empty")
        if user_uid <= 0:
            raise ValueError("user_uid is required and cannot be empty")

        name = f"agent_{channel_name}_{agent_uid}_{int(time.time())}"

        # Build the selected MLLM vendor. This raises ValueError listing the
        # missing env var(s) when a BYO vendor is selected without credentials —
        # validated here (start()), so /get_config and the docker smoke stay
        # key-less.
        mllm = build_vendor(self.vendor)

        parameters = {
            "data_channel": "rtm",
            "enable_error_message": True,
            "enable_metrics": True,
        }
        if isinstance(output_audio_codec, str) and output_audio_codec.strip():
            parameters["output_audio_codec"] = output_audio_codec.strip()

        agora_agent = AgoraAgent(
            name=name,
            greeting=self.greeting,
            failure_message="Please wait a moment.",
            max_history=50,
            advanced_features={"enable_rtm": True},
            parameters=parameters,
        )
        agora_agent = agora_agent.with_mllm(mllm)

        session = agora_agent.create_async_session(
            client=self.client,
            channel=channel_name,
            agent_uid=str(agent_uid),
            remote_uids=[str(user_uid)],
            enable_string_uid=False,
            idle_timeout=30,
            expires_in=3600,
        )

        logger.info(
            "Starting realtime agent channel=%s agent_uid=%s user_uid=%s vendor=%s",
            channel_name,
            agent_uid,
            user_uid,
            self.vendor,
        )

        try:
            agent_id = await session.start()
        except Exception:
            logger.exception(
                "Failed to start realtime agent channel=%s agent_uid=%s user_uid=%s",
                channel_name,
                agent_uid,
                user_uid,
            )
            raise

        # Save session for later stop
        self._sessions[agent_id] = session

        logger.info(
            "Started realtime agent agent_id=%s channel=%s",
            agent_id,
            channel_name,
        )

        return {
            "agent_id": agent_id,
            "channel_name": channel_name,
            "status": "started",
        }

    async def stop(self, agent_id: str) -> None:
        """Stop a running agent. Falls back to the stateless client path."""
        if not agent_id or not str(agent_id).strip():
            raise ValueError("agent_id is required and cannot be empty")

        session = self._sessions.pop(agent_id, None)
        if session:
            try:
                await session.stop()
                logger.info("Stopped agent from active session agent_id=%s", agent_id)
                return
            except Exception:
                logger.warning(
                    "Failed to stop agent from active session; falling back agent_id=%s",
                    agent_id,
                    exc_info=True,
                )

        logger.info("Stopping agent through client.stop_agent agent_id=%s", agent_id)
        await self.client.stop_agent(agent_id)
