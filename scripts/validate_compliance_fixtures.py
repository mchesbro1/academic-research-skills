#!/usr/bin/env python3
"""Validate all compliance_report YAML fixtures against Schema 12.

Converts each examples/compliance/fixture_*.yaml to JSON in a temp file,
then invokes scripts/check_compliance_report.py. Exits 0 if every fixture
validates; exits 1 on first failure.

Usage:
  python scripts/validate_compliance_fixtures.py [fixture_dir]

Default fixture_dir: examples/compliance (relative to repo root).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DIR = REPO_ROOT / "examples" / "compliance"
VALIDATOR = REPO_ROOT / "scripts" / "check_compliance_report.py"


def validate_fixture(yaml_path: Path) -> tuple[bool, str]:
    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as tmp:
        json.dump(data, tmp)
        tmp_path = Path(tmp.name)
    try:
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), str(tmp_path)],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0, (result.stdout + result.stderr).strip()
    finally:
        tmp_path.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture_dir", type=Path, nargs="?", default=DEFAULT_DIR)
    args = parser.parse_args()

    fixtures = sorted(args.fixture_dir.glob("fixture_*.yaml"))
    if not fixtures:
        print(f"ERROR: no fixture_*.yaml files in {args.fixture_dir}", file=sys.stderr)
        return 1

    failed = 0
    for fx in fixtures:
        ok, output = validate_fixture(fx)
        status = "OK" if ok else "FAIL"
        print(f"[{status}] {fx.name}: {output}")
        if not ok:
            failed += 1
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
