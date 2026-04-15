#!/usr/bin/env python3
"""Lint: every top-level SKILL.md must declare metadata.data_access_level.

Legal values: raw | redacted | verified_only.

Exit 0 on success, 1 on any violation.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

LEGAL_VALUES = {"raw", "redacted", "verified_only"}
SKIP_DIRS = {"shared", "scripts", "docs", ".git", ".github", "examples", ".local-plans"}


def _iter_skill_files(root: Path) -> list[Path]:
    results: list[Path] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir() or child.name in SKIP_DIRS:
            continue
        skill_md = child / "SKILL.md"
        if skill_md.is_file():
            results.append(skill_md)
    return results


def _parse_frontmatter(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    _, _, rest = text.partition("---\n")
    fm, _, _ = rest.partition("\n---")
    try:
        return yaml.safe_load(fm) or {}
    except yaml.YAMLError as exc:
        print(f"ERROR: {path}: malformed YAML frontmatter: {exc}", file=sys.stderr)
        return None


def check(root: Path) -> list[str]:
    violations: list[str] = []
    skills = _iter_skill_files(root)
    if not skills:
        violations.append(f"no SKILL.md files found under {root}")
        return violations
    for path in skills:
        fm = _parse_frontmatter(path)
        if fm is None:
            violations.append(f"{path}: could not parse frontmatter")
            continue
        metadata = fm.get("metadata") or {}
        if "data_access_level" not in metadata:
            violations.append(
                f"{path}: metadata.data_access_level is missing"
            )
            continue
        value = metadata["data_access_level"]
        if value not in LEGAL_VALUES:
            violations.append(
                f"{path}: metadata.data_access_level = {value!r}, "
                f"must be one of {sorted(LEGAL_VALUES)}"
            )
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--path",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Repo root (default: script's parent)",
    )
    args = parser.parse_args()

    violations = check(args.path)
    if violations:
        for v in violations:
            print(f"ERROR: {v}")
        print(f"\n{len(violations)} violation(s) found.", file=sys.stderr)
        return 1
    print("OK: all SKILL.md files declare a valid data_access_level.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
