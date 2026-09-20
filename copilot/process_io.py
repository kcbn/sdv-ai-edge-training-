"""Load human-owned process files. Code must not invent extra actions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROCESS = ROOT / "process"


def load_allowlist() -> dict[str, Any]:
    return json.loads((PROCESS / "allowlist.json").read_text(encoding="utf-8"))


def allowed_hmi_actions() -> frozenset[str]:
    return frozenset(load_allowlist()["allowed_hmi_actions"])


def forbidden_actuators() -> tuple[str, ...]:
    return tuple(load_allowlist()["forbidden_actuators"])


def load_scene(scene_id: str) -> dict[str, Any]:
    path = PROCESS / "scenes" / f"{scene_id}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if not data.get("accepted"):
        raise ValueError(f"scene {scene_id} is not accepted by a human")
    return data


def accepted_scene_ids() -> tuple[str, ...]:
    return tuple(p.stem for p in sorted((PROCESS / "scenes").glob("*.json")))
