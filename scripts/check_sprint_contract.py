#!/usr/bin/env python3
"""Validate an ARS sprint contract against sprint_contract.schema.json.

Usage: python scripts/check_sprint_contract.py path/to/contract.json [--ars-version vX.Y.Z]

Exit 0 on pass (warnings may still be printed to stderr).
Exit 1 on schema or structural validation failure, or file error.
"""
from __future__ import annotations

import argparse
import json
import re  # noqa: F401  # used by SC-1 (Task 5) and SC-4 (Task 7)
import sys
from pathlib import Path

import jsonschema

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "shared" / "sprint_contract.schema.json"


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def validate(contract: dict) -> list[str]:
    """Return list of schema violation messages. Empty list means pass."""
    schema = load_schema()
    validator = jsonschema.Draft202012Validator(
        schema,
        format_checker=jsonschema.Draft202012Validator.FORMAT_CHECKER,
    )
    return [f"{list(e.absolute_path)}: {e.message}" for e in validator.iter_errors(contract)]


def check_structural_invariants(contract: dict) -> list[str]:
    """Return list of hard structural-invariant errors. Empty means pass.
    Only meaningful if validate() already returned [].

    Stub. Filled by Task 4 (uniqueness checks for dimension id, dimension
    name, condition_id; spec §4.1 item 2).
    """
    return []


def warn_suspicious(contract: dict, ars_current_version: str | None) -> list[str]:
    """Return list of soft warnings. Non-blocking.

    Stub. Filled incrementally by Tasks 5-13 (SC-1 baseline lag through
    SC-11 panel_size sanity; spec §4.3).
    """
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract", type=Path, help="Path to the sprint contract JSON")
    parser.add_argument("--ars-version", type=str, default=None,
                        help="Current ARS version (e.g. v3.6.2) for SC-1 baseline lag check")
    args = parser.parse_args()

    try:
        contract = json.loads(args.contract.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"ERROR: failed to load {args.contract}: {exc}")
        return 1

    errors = validate(contract)
    if errors:
        for e in errors:
            print(f"ERROR: {e}")
        print(
            f"\n{len(errors)} schema violation(s). "
            "See shared/sprint_contract.schema.json for field definitions.",
            file=sys.stderr,
        )
        return 1

    struct_errors = check_structural_invariants(contract)
    if struct_errors:
        for e in struct_errors:
            print(f"ERROR: {e}")
        print(
            f"\n{len(struct_errors)} structural invariant violation(s).",
            file=sys.stderr,
        )
        return 1

    for w in warn_suspicious(contract, args.ars_version):
        print(w, file=sys.stderr)

    print(f"OK: {args.contract} is a valid sprint_contract (Schema 13)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
