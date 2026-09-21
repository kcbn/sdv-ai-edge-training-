"""H3 gate: Copilot JSON must stay inside the allowlist and omit actuators."""

from __future__ import annotations

import json
import re
import sys
from typing import Any

from copilot.process_io import allowed_hmi_actions, forbidden_actuators

JA_FORBIDDEN = ("ブレーキ", "操舵", "アクセル", "制動")


def forbidden_pattern() -> re.Pattern[str]:
    return re.compile(r"\b(" + "|".join(map(re.escape, forbidden_actuators())) + r")\b", re.IGNORECASE)


def forbidden_hits(text: str) -> list[str]:
    hits = [m.group(0) for m in forbidden_pattern().finditer(text)]
    hits.extend(token for token in JA_FORBIDDEN if token in text)
    return hits


def assert_safe_output(payload: dict[str, Any]) -> None:
    actions = tuple(payload.get("policy", {}).get("actions") or ())
    allowed = allowed_hmi_actions()
    unknown = [action for action in actions if action not in allowed]
    if unknown:
        raise AssertionError(f"actions outside allowlist: {unknown}")
    blob = json.dumps(payload, ensure_ascii=False)
    hits = forbidden_hits(blob)
    if hits:
        raise AssertionError(f"forbidden tokens in Copilot output: {hits}")


def evaluate_scenes() -> int:
    from copilot.features import load_sample
    from copilot.process_io import accepted_scene_ids, load_scene
    from copilot.runtime import run_copilot

    try:
        for scene_id in accepted_scene_ids():
            spec = load_scene(scene_id)
            decision = run_copilot(load_sample(scene_id), utterance=spec.get("utterance"))
            assert_safe_output(decision.to_dict())
    except AssertionError as exc:
        print(f"forbidden-word gate failed: {exc}", file=sys.stderr)
        return 1
    print("forbidden-word gate ok")
    return 0


def main() -> None:
    raise SystemExit(evaluate_scenes())


if __name__ == "__main__":
    main()
