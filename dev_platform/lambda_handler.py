"""API Gateway + Lambda entry. Safety stays in BedrockChat."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from dev_platform.bedrock_chat import BedrockChat, ChatResult

logger = logging.getLogger(__name__)

_HEADERS = {"Content-Type": "application/json"}
_FALLBACK_REPLY = "一時的に応答できません。運転に集中してください。"


def dry_run_from_env() -> bool:
    raw = os.environ.get("DRY_RUN", "1").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _json_response(status: int, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status,
        "headers": _HEADERS,
        "body": json.dumps(payload, ensure_ascii=False),
    }


def _fallback(chat: BedrockChat, dry_run: bool) -> dict[str, Any]:
    return ChatResult(
        reply=_FALLBACK_REPLY,
        intent="refuse",
        vehicle_command=None,
        model_id=chat.model_id,
        dry_run=dry_run,
        blocked=True,
    ).to_dict()


def _body(event: dict[str, Any]) -> dict[str, Any]:
    raw = event.get("body", event)
    if isinstance(raw, str):
        return json.loads(raw or "{}")
    if isinstance(raw, dict):
        return raw
    return {}


def handler(
    event: dict[str, Any],
    _context: Any = None,
    chat: BedrockChat | None = None,
) -> dict[str, Any]:
    chat = chat or BedrockChat()
    dry_run = dry_run_from_env()
    try:
        payload = _body(event)
        text = str(payload.get("text") or "").strip()
        if not text:
            return _json_response(400, {"error": "text is required", "blocked": True})
        result = chat.complete(text, dry_run=dry_run)
        return _json_response(200, result.to_dict())
    except Exception:
        logger.exception("Bedrock HMI handler failed")
        return _json_response(200, _fallback(chat, dry_run))
