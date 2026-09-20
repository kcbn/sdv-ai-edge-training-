"""API Gateway + Lambda entry. Deploy is Day 6; this file is the handler contract."""

from __future__ import annotations

import json
from typing import Any

from dev_platform.bedrock_chat import BedrockChat


def _body(event: dict[str, Any]) -> dict[str, Any]:
    raw = event.get("body", event)
    if isinstance(raw, str):
        return json.loads(raw or "{}")
    if isinstance(raw, dict):
        return raw
    return {}


def handler(event: dict[str, Any], _context: Any = None) -> dict[str, Any]:
    payload = _body(event)
    text = str(payload.get("text") or "").strip()
    if not text:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "text is required"}, ensure_ascii=False),
        }
    dry_run = bool(payload.get("dry_run", True))
    result = BedrockChat().complete(text, dry_run=dry_run)
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(result.to_dict(), ensure_ascii=False),
    }
