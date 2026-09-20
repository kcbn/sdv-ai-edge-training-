from copilot.driver_state import DriverStatePrediction
from copilot.features import load_sample
from copilot.policy import assert_no_actuator_control, evaluate_policy
from copilot.process_io import allowed_hmi_actions, forbidden_actuators


def test_allowlist_has_six_hmi_actions() -> None:
    assert len(allowed_hmi_actions()) == 6


def test_overload_triggers_guardrail() -> None:
    sample = load_sample("overload")
    prediction = DriverStatePrediction(
        state="overload_risk",
        state_ja="認知過多予兆",
        confidence=0.9,
        probabilities={"stable": 0.05, "mild_load": 0.05, "overload_risk": 0.9},
    )
    policy = evaluate_policy(sample, prediction)
    assert policy.safety_mode == "guardrail"
    assert policy.llm_allowed is False
    assert "suppress_noncritical_hud" in policy.actions
    assert_no_actuator_control(policy.actions)


def test_stable_keeps_normal_display() -> None:
    sample = load_sample("stable")
    prediction = DriverStatePrediction(
        state="stable",
        state_ja="安定",
        confidence=0.8,
        probabilities={"stable": 0.8, "mild_load": 0.15, "overload_risk": 0.05},
    )
    policy = evaluate_policy(sample, prediction)
    assert policy.actions == ("keep_normal_display",)
    assert policy.llm_allowed is True


def test_policy_never_mentions_actuators() -> None:
    sample = load_sample("overload")
    prediction = DriverStatePrediction(
        state="overload_risk",
        state_ja="認知過多予兆",
        confidence=0.99,
        probabilities={"stable": 0.0, "mild_load": 0.01, "overload_risk": 0.99},
    )
    policy = evaluate_policy(sample, prediction)
    blob = " ".join(policy.actions)
    for forbidden in forbidden_actuators():
        assert forbidden not in blob
