from __future__ import annotations

import subprocess
import sys
import zipfile

from copilot.process_io import ROOT


def test_lambda_zip_contains_only_dev_platform() -> None:
    script = ROOT / "scripts" / "package_lambda.py"
    completed = subprocess.run(
        [sys.executable, str(script)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    dest = ROOT / "build" / "lambda.zip"
    assert dest.is_file()
    assert "wrote" in completed.stdout
    with zipfile.ZipFile(dest) as archive:
        names = [name.replace("\\", "/") for name in archive.namelist()]
    assert "dev_platform/lambda_handler.py" in names
    assert "dev_platform/bedrock_chat.py" in names
    assert names
    assert all(name.startswith("dev_platform/") for name in names)
    assert not any(name.startswith("copilot/") for name in names)
    assert not any("__pycache__" in name or name.endswith(".pyc") for name in names)
