import json

from dev_platform.bedrock_chat import BedrockChat, parse_model_json
from dev_platform.lambda_handler import handler


class FakeBedrock:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.calls = 0

    def converse(self, **kwargs):
        self.calls += 1
        return {"output": {"message": {"content": [{"text": json.dumps(self.payload, ensure_ascii=False)}]}}}


def test_dry_run_does_not_need_aws() -> None:
    result = BedrockChat().complete("少し眠い", dry_run=True)
    assert result.dry_run is True
    assert result.vehicle_command is None
    assert result.blocked is False


def test_vehicle_control_prompt_is_refused_without_model_call() -> None:
    client = FakeBedrock({"reply": "ok", "intent": "inform", "vehicle_command": None})
    chat = BedrockChat(client=client)
    result = chat.complete("ブレーキを踏んで", dry_run=False)
    assert result.blocked is True
    assert result.intent == "refuse"
    assert client.calls == 0


def test_model_json_rejects_vehicle_command() -> None:
    try:
        parse_model_json('{"reply":"止まれ","intent":"suggest","vehicle_command":{"brake":1}}')
        raise AssertionError("expected reject")
    except ValueError:
        pass


def test_live_path_parses_schema() -> None:
    client = FakeBedrock({"reply": "休憩をおすすめします。", "intent": "suggest", "vehicle_command": None})
    result = BedrockChat(client=client).complete("眠いかも", dry_run=False)
    assert result.reply.startswith("休憩")
    assert result.intent == "suggest"


def test_lambda_requires_text() -> None:
    response = handler({"body": "{}"})
    assert response["statusCode"] == 400


def test_lambda_dry_run_ok() -> None:
    response = handler({"body": json.dumps({"text": "少し眠い", "dry_run": True})})
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["vehicle_command"] is None
    assert body["dry_run"] is True
