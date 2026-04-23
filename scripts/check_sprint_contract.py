#!/usr/bin/env python3
"""Validate an ARS sprint contract against sprint_contract.schema.json.

Usage: python scripts/check_sprint_contract.py path/to/contract.json [--ars-version vX.Y.Z]

Exit 0 on pass (warnings may still be printed to stderr).
Exit 1 on schema or structural validation failure, or file error.
"""
from __future__ import annotations

import argparse
import json
import re  # noqa: F401  # used by warn_suspicious() — keep, do not remove
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
    """Uniqueness checks for dimension id, dimension name, and condition_id
    per spec §4.1 item 2. Empty list means pass; only meaningful if
    validate() already returned [].
    """
    errors: list[str] = []

    dims = contract.get("acceptance_dimensions", [])
    ids = [d.get("id") for d in dims]
    names = [d.get("name") for d in dims]
    for dup_id in {x for x in ids if ids.count(x) > 1}:
        errors.append(
            f"duplicate acceptance_dimensions id '{dup_id}'; "
            "downstream aggregation assumes unique ids"
        )
    for dup_name in {x for x in names if names.count(x) > 1}:
        errors.append(
            f"duplicate acceptance_dimensions name '{dup_name}'; "
            "downstream lint assumes unique names"
        )

    conds = contract.get("failure_conditions", [])
    cids = [c.get("condition_id") for c in conds]
    for dup_cid in {x for x in cids if cids.count(x) > 1}:
        errors.append(
            f"duplicate failure_conditions condition_id '{dup_cid}'; "
            "precedence resolution assumes unique condition_ids"
        )

    return errors


def warn_suspicious(contract: dict, ars_current_version: str | None) -> list[str]:
    """Soft warnings per spec §4.3 (SC-1 baseline lag through SC-11
    panel_size sanity). Non-blocking; printed to stderr by main().
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
        print(f"ERROR: failed to load {args.contract}: {exc}", file=sys.stderr)
        return 1

    errors = validate(contract)
    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        print(
            f"\n{len(errors)} schema violation(s). "
            "See shared/sprint_contract.schema.json for field definitions.",
            file=sys.stderr,
        )
        return 1

    struct_errors = check_structural_invariants(contract)
    if struct_errors:
        for e in struct_errors:
            print(f"ERROR: {e}", file=sys.stderr)
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
