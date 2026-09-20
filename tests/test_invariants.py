import re

from copilot.process_io import ROOT, forbidden_actuators

SCAN_DIRS = ("copilot", "process", "tests")
SKIP_NAMES = {
    "allowlist.json",
    "test_invariants.py",
    "hazards.md",
    "test_dev_platform.py",
    "test_forbidden_output.py",
    "bedrock_chat.py",
}


def test_source_tree_has_no_actuator_command_tokens() -> None:
    pattern = re.compile(r"\b(" + "|".join(map(re.escape, forbidden_actuators())) + r")\b", re.I)
    hits: list[str] = []
    for folder in SCAN_DIRS:
        for path in (ROOT / folder).rglob("*"):
            if path.suffix not in {".py", ".json", ".md"} or path.name in SKIP_NAMES:
                continue
            text = path.read_text(encoding="utf-8")
            if pattern.search(text):
                hits.append(str(path.relative_to(ROOT)))
    assert hits == [], hits
