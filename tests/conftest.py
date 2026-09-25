import pytest


@pytest.fixture(autouse=True)
def default_dry_run(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep handler tests offline unless a test explicitly sets DRY_RUN=0."""
    monkeypatch.setenv("DRY_RUN", "1")
