"""Build build/lambda.zip from the development path only (no copilot/)."""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "dev_platform"
DEST = ROOT / "build" / "lambda.zip"


def _should_include(path: Path) -> bool:
    if not path.is_file():
        return False
    if path.suffix == ".pyc" or path.name == ".DS_Store":
        return False
    return "__pycache__" not in path.parts


def package(root: Path = ROOT) -> Path:
    src = root / "dev_platform"
    dest = root / "build" / "lambda.zip"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.unlink(missing_ok=True)
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(src.rglob("*")):
            if not _should_include(path):
                continue
            archive.write(path, path.relative_to(root).as_posix())
    return dest


def main() -> int:
    dest = package()
    print(f"wrote {dest}")
    print(f"size_bytes {dest.stat().st_size}")
    with zipfile.ZipFile(dest) as archive:
        for name in archive.namelist():
            print(name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
