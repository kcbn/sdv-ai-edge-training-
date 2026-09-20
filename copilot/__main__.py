from __future__ import annotations

import argparse
import json

from copilot.features import DriverVehicleSample
from copilot.process_io import accepted_scene_ids, load_scene
from copilot.runtime import run_copilot


def main() -> None:
    scenes = accepted_scene_ids()
    parser = argparse.ArgumentParser(description="Run Driver-State HMI Copilot on an accepted scene.")
    parser.add_argument("--scene", choices=scenes, default="overload")
    parser.add_argument("--utterance", default="")
    args = parser.parse_args()
    spec = load_scene(args.scene)
    sample = DriverVehicleSample.from_mapping(spec["sample"])
    utterance = args.utterance or spec.get("utterance") or None
    decision = run_copilot(sample, utterance=utterance)
    print(json.dumps(decision.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
