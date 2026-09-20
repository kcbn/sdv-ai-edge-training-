"""AWS Bedrock chat for the Week 1 development API.

Vehicle motion commands are rejected before and after the model call.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass
from typing import Any, Protocol

CONTROL_PATTERN = re.compile(
    r"\b(brake|steer|steering|throttle|accelerate|airbag|adas_override)\b",
    re.I,
)
JA_CONTROL_HINTS = ("ブレーキ", "操舵", "アクセル", "制動")

ALLOWED_INTENTS = frozenset({"inform", "confirm", "suggest", "refuse"})


class BedrockRuntime(Protocol):
    def converse(self, **kwargs: Any) -> dict[str, Any]: ...


@dataclass(frozen=True)
class ChatResult:
    reply: str
    intent: str
    vehicle_command: None
    model_id: str
    dry_run: bool
    blocked: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def looks_like_vehicle_control(text: str) -> bool:
    if CONTROL_PATTERN.search(text):
        return True
    return any(token in text for token in JA_CONTROL_HINTS)


def parse_model_json(raw: str) -> dict[str, Any]:
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("model output is not an object")
    reply = data.get("reply")
    intent = data.get("intent")
    if not isinstance(reply, str) or not reply.strip():
        raise ValueError("reply must be a non-empty string")
    if intent not in ALLOWED_INTENTS:
        raise ValueError(f"intent must be one of {sorted(ALLOWED_INTENTS)}")
    if data.get("vehicle_command") not in (None, ""):
        raise ValueError("vehicle_command is not allowed")
    if looks_like_vehicle_control(reply):
        raise ValueError("reply attempted vehicle control")
    return {"reply": reply.strip(), "intent": intent, "vehicle_command": None}


def _system_prompt() -> str:
    return (
        "You are an HMI development assistant for in-cabin conversation. "
        "Reply in Japanese. Output JSON only with keys reply, intent, vehicle_command. "
        "intent must be inform, confirm, suggest, or refuse. "
        "vehicle_command must always be null. "
        "Never instruct braking, steering, or throttle."
    )


class BedrockChat:
    def __init__(
        self,
        client: BedrockRuntime | None = None,
        model_id: str | None = None,
        region: str | None = None,
    ) -> None:
        self.model_id = model_id or os.environ.get(
            "BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0"
        )
        self.region = region or os.environ.get("AWS_REGION", "ap-southeast-2")
        self._client = client

    def _client_or_create(self) -> BedrockRuntime:
        if self._client is not None:
            return self._client
        import boto3

        return boto3.client("bedrock-runtime", region_name=self.region)

    def complete(self, user_text: str, *, dry_run: bool = True) -> ChatResult:
        if looks_like_vehicle_control(user_text):
            return ChatResult(
                reply="車両の運転操作には対応できません。状態の確認と案内だけ行います。",
                intent="refuse",
                vehicle_command=None,
                model_id=self.model_id,
                dry_run=dry_run,
                blocked=True,
            )
        if dry_run:
            return ChatResult(
                reply="（dry-run）眠気や注視の話なら、休憩や表示を減らす提案ができます。",
                intent="inform",
                vehicle_command=None,
                model_id=self.model_id,
                dry_run=True,
                blocked=False,
            )
        response = self._client_or_create().converse(
            modelId=self.model_id,
            system=[{"text": _system_prompt()}],
            messages=[{"role": "user", "content": [{"text": user_text}]}],
            inferenceConfig={"maxTokens": 256, "temperature": 0},
        )
        raw = response["output"]["message"]["content"][0]["text"]
        parsed = parse_model_json(raw)
        return ChatResult(
            reply=parsed["reply"],
            intent=parsed["intent"],
            vehicle_command=None,
            model_id=self.model_id,
            dry_run=False,
            blocked=False,
        )
