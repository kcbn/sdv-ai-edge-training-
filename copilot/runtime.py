"""Compose state model + policy + optional utterance. Edge-safe by default."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from copilot.driver_state import (
    DriverCognitiveLoadPredictor,
    DriverStatePrediction,
    predict,
    train_synthetic,
)
from copilot.features import DriverVehicleSample
from copilot.intent import DriverIntent, parse_driver_utterance
from copilot.policy import HmiPolicy, assert_no_actuator_control, evaluate_policy

_MODEL: DriverCognitiveLoadPredictor | None = None


@dataclass(frozen=True)
class CopilotDecision:
    state: DriverStatePrediction
    policy: HmiPolicy
    intent: DriverIntent | None
    driver_message: str
    cloud_llm_blocked: bool

    def to_dict(self) -> dict:
        return {
            "state": asdict(self.state),
            "policy": asdict(self.policy),
            "intent": asdict(self.intent) if self.intent else None,
            "driver_message": self.driver_message,
            "cloud_llm_blocked": self.cloud_llm_blocked,
        }


def get_model() -> DriverCognitiveLoadPredictor:
    global _MODEL
    if _MODEL is None:
        _MODEL = train_synthetic()
    return _MODEL


def render_driver_message(policy: HmiPolicy, intent: DriverIntent | None) -> str:
    if policy.safety_mode == "guardrail":
        return "今は前方の運転に集中してください。案内とエンターテインメントを一時停止します。"
    if intent and intent.intent == "control_ac" and policy.llm_allowed:
        return "空調を調整します。"
    if intent and intent.intent == "navigation_search" and policy.llm_allowed:
        return "休憩候補を探します。安全なタイミングで提案します。"
    if intent and intent.intent != "unknown" and not policy.llm_allowed:
        return "運転負荷が高いため、その操作は少し待ってから実行します。"
    if policy.safety_mode == "assist":
        return "表示を簡潔にします。必要なら音声で指示してください。"
    return "通常表示です。"


def run_copilot(
    sample: DriverVehicleSample,
    utterance: str | None = None,
    model: DriverCognitiveLoadPredictor | None = None,
) -> CopilotDecision:
    model = model or get_model()
    state = predict(model, sample)
    policy = evaluate_policy(sample, state)
    assert_no_actuator_control(policy.actions)
    intent = parse_driver_utterance(utterance) if utterance else None
    message = render_driver_message(policy, intent)
    return CopilotDecision(
        state=state,
        policy=policy,
        intent=intent,
        driver_message=message,
        cloud_llm_blocked=not policy.llm_allowed,
    )
