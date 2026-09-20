"""Deterministic HMI policy from the human-owned allowlist."""

from __future__ import annotations

from dataclasses import dataclass

from copilot.driver_state import DriverStatePrediction
from copilot.features import DriverVehicleSample
from copilot.process_io import allowed_hmi_actions, forbidden_actuators


@dataclass(frozen=True)
class HmiPolicy:
    actions: tuple[str, ...]
    reason: str
    safety_mode: str
    llm_allowed: bool


def evaluate_policy(sample: DriverVehicleSample, prediction: DriverStatePrediction) -> HmiPolicy:
    if sample.time_to_collision_s < 2.0 or prediction.state == "overload_risk":
        return HmiPolicy(
            actions=(
                "suppress_noncritical_hud",
                "mute_entertainment_audio",
                "defer_navi_prompt",
                "request_driver_attention",
            ),
            reason="前方余裕が小さい、または認知過多予兆。情報量を落として前方注視を優先する。",
            safety_mode="guardrail",
            llm_allowed=False,
        )
    if prediction.state == "mild_load":
        return HmiPolicy(
            actions=("reduce_hud_density", "defer_navi_prompt"),
            reason="軽度負荷。追加タスクとHUD密度を下げる。",
            safety_mode="assist",
            llm_allowed=True,
        )
    return HmiPolicy(
        actions=("keep_normal_display",),
        reason="安定。通常HMIを維持する。",
        safety_mode="normal",
        llm_allowed=True,
    )


def assert_no_actuator_control(actions: tuple[str, ...]) -> None:
    allowed = allowed_hmi_actions()
    joined = " ".join(actions).lower()
    for forbidden in forbidden_actuators():
        if forbidden in joined:
            raise ValueError(f"policy attempted forbidden actuator: {forbidden}")
    unknown = [a for a in actions if a not in allowed]
    if unknown:
        raise ValueError(f"unknown HMI action: {unknown}")
