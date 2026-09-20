"""Keyword intent parser. Placeholder until a quantized classifier is wired."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DriverIntent:
    intent: str
    parameters: dict[str, object]
    confidence: float
    utterance: str


def parse_driver_utterance(utterance: str) -> DriverIntent:
    if any(token in utterance for token in ("暑", "寒", "エアコン")):
        return DriverIntent(
            intent="control_ac",
            parameters={
                "target": "temperature",
                "action": "adjust",
                "value": -1 if "暑" in utterance else 1,
            },
            confidence=0.95,
            utterance=utterance,
        )
    if any(token in utterance for token in ("コンビニ", "休憩", "寄り道")):
        return DriverIntent(
            intent="navigation_search",
            parameters={"category": "convenience_store", "action": "add_waypoint"},
            confidence=0.91,
            utterance=utterance,
        )
    return DriverIntent(intent="unknown", parameters={}, confidence=0.4, utterance=utterance)
