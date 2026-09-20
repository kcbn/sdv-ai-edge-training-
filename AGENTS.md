# Agent rules

Source of truth: `docs/HMI-AI_30日統合計画.md`. Follow `process/README.md`. Do not revive deleted lab scripts.

- Claude: plan and review. Cursor: implement.
- Never add brake, steer, throttle, or other actuators to Copilot output.
- Change `process/allowlist.json` or `process/scenes/` only when the user explicitly owns that change.
- Vehicle path (`copilot/`) must not call cloud LLMs. `dev_platform/` may call Bedrock for the Week 1 development API only.
- LLM/SLM may produce `driver_message` / `reply` text only.
- Branch rule: `main` stays releasable. Land on `dev` via PR, then `main`.
