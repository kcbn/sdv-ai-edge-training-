import json
import subprocess
import sys

import pytest

from copilot.features import load_sample
from copilot.policy import assert_no_actuator_control
from copilot.process_io import ROOT, accepted_scene_ids, allowed_hmi_actions, load_scene
from copilot.runtime import run_copilot
from copilot.safety import assert_safe_output, evaluate_scenes, forbidden_hits, main
from dev_platform.bedrock_chat import BedrockChat
from dev_platform.lambda_handler import handler


def test_accepted_scene_outputs_stay_in_allowlist() -> None:
    allowed = allowed_hmi_actions()
    for scene_id in accepted_scene_ids():
        spec = load_scene(scene_id)
        payload = run_copilot(load_sample(scene_id), utterance=spec.get("utterance")).to_dict()
        assert_safe_output(payload)
        for action in payload["policy"]["actions"]:
            assert action in allowed


def test_unknown_actuator_action_is_rejected() -> None:
    with pytest.raises(ValueError, match="forbidden actuator"):
        assert_no_actuator_control(("brake",))
    with pytest.raises(ValueError, match="unknown HMI action"):
        assert_no_actuator_control(("launch_missile",))


def test_serialized_output_rejects_brake_string() -> None:
    payload = {
        "policy": {"actions": ["keep_normal_display"]},
        "driver_message": "apply brake now",
    }
    with pytest.raises(AssertionError, match="forbidden"):
        assert_safe_output(payload)


def test_evaluate_scenes_returns_nonzero_when_output_is_unsafe(monkeypatch: pytest.MonkeyPatch) -> None:
    class UnsafeDecision:
        def to_dict(self) -> dict:
            return {
                "policy": {"actions": ["keep_normal_display"]},
                "driver_message": "apply brake now",
            }

    monkeypatch.setattr("copilot.runtime.run_copilot", lambda *args, **kwargs: UnsafeDecision())
    assert evaluate_scenes() == 1


def test_main_exits_nonzero_when_gate_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("copilot.safety.evaluate_scenes", lambda: 1)
    with pytest.raises(SystemExit) as raised:
        main()
    assert raised.value.code != 0
    assert raised.value.code == 1


def test_python_module_safety_exits_zero_on_accepted_scenes() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "copilot.safety"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr


def test_dev_platform_dry_run_output_has_no_vehicle_command() -> None:
    chat = BedrockChat().complete("少し眠い", dry_run=True).to_dict()
    assert chat["vehicle_command"] is None
    assert forbidden_hits(json.dumps(chat, ensure_ascii=False)) == []
    body = json.loads(handler({"body": json.dumps({"text": "少し眠い", "dry_run": True})})["body"])
    assert body["vehicle_command"] is None
    assert forbidden_hits(json.dumps(body, ensure_ascii=False)) == []
