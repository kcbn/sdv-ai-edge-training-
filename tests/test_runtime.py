from copilot.driver_state import predict, train_synthetic
from copilot.features import load_sample
from copilot.process_io import load_scene
from copilot.runtime import run_copilot


def test_trained_model_matches_accepted_overload_scene() -> None:
    spec = load_scene("overload")
    prediction = predict(train_synthetic(), load_sample("overload"))
    assert prediction.state == spec["expected_state"]


def test_overload_scene_blocks_cloud_llm() -> None:
    spec = load_scene("overload")
    decision = run_copilot(load_sample("overload"), utterance=spec["utterance"])
    assert decision.cloud_llm_blocked is True
    assert decision.policy.safety_mode == "guardrail"
    assert decision.intent is not None
    assert "前方" in decision.driver_message


def test_stable_scene_can_handle_ac_intent() -> None:
    spec = load_scene("stable")
    decision = run_copilot(load_sample("stable"), utterance=spec["utterance"])
    assert decision.state.state == spec["expected_state"]
    assert decision.intent is not None
    assert decision.intent.intent == "control_ac"
    assert decision.policy.llm_allowed
    assert "空調" in decision.driver_message
