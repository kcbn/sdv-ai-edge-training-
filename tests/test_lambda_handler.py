import json
import logging
from typing import Any

import pytest

from dev_platform.bedrock_chat import BedrockChat
from dev_platform.lambda_handler import handler


class FakeBedrockRuntime:
    """Matches BedrockRuntime.converse without calling AWS."""

    def __init__(self, payload: dict[str, Any] | None = None, error: Exception | None = None) -> None:
        self.payload = payload or {
            "reply": "休憩をおすすめします。",
            "intent": "suggest",
            "vehicle_command": None,
        }
        self.error = error
        self.calls = 0
        self.last_kwargs: dict[str, Any] = {}

    def converse(self, **kwargs: Any) -> dict[str, Any]:
        self.calls += 1
        self.last_kwargs = kwargs
        if self.error is not None:
            raise self.error
        return {
            "output": {
                "message": {"content": [{"text": json.dumps(self.payload, ensure_ascii=False)}]}
            }
        }


def _event(body: dict[str, Any]) -> dict[str, str]:
    return {"body": json.dumps(body, ensure_ascii=False)}


def test_lambda_requires_text() -> None:
    response = handler(_event({}))
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert body["blocked"] is True


def test_dry_run_comes_from_env_not_body(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DRY_RUN", "1")
    runtime = FakeBedrockRuntime()
    response = handler(
        _event({"text": "少し眠い", "dry_run": False}),
        chat=BedrockChat(client=runtime),
    )
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["dry_run"] is True
    assert body["blocked"] is False
    assert runtime.calls == 0


def test_live_path_uses_bedrock_runtime_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DRY_RUN", "0")
    runtime = FakeBedrockRuntime()
    response = handler(_event({"text": "眠いかも"}), chat=BedrockChat(client=runtime))
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["dry_run"] is False
    assert body["blocked"] is False
    assert body["intent"] == "suggest"
    assert body["vehicle_command"] is None
    assert runtime.calls == 1


def test_bedrock_exception_returns_200_blocked(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    monkeypatch.setenv("DRY_RUN", "0")
    runtime = FakeBedrockRuntime(error=RuntimeError("bedrock unavailable"))
    secret = "個人情報を含む発話"
    with caplog.at_level(logging.ERROR, logger="dev_platform.lambda_handler"):
        response = handler(_event({"text": secret}), chat=BedrockChat(client=runtime))
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["blocked"] is True
    assert body["intent"] == "refuse"
    assert body["vehicle_command"] is None
    assert runtime.calls == 1
    assert "Bedrock HMI handler failed" in caplog.text
    assert "bedrock unavailable" in caplog.text
    assert secret not in caplog.text


def test_invalid_json_body_returns_200_blocked() -> None:
    response = handler({"body": "{"})
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["blocked"] is True


def test_vehicle_control_is_blocked_by_bedrock_chat(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DRY_RUN", "0")
    runtime = FakeBedrockRuntime()
    response = handler(_event({"text": "ブレーキを踏んで"}), chat=BedrockChat(client=runtime))
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["blocked"] is True
    assert runtime.calls == 0
