from copilot.process_io import ROOT


def test_copilot_does_not_import_dev_platform() -> None:
    hits = []
    for path in (ROOT / "copilot").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "dev_platform" in text:
            hits.append(str(path.relative_to(ROOT)))
    assert hits == []
