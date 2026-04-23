#!/usr/bin/env python3
"""Validate an ARS sprint contract against sprint_contract.schema.json.

Usage: python scripts/check_sprint_contract.py path/to/contract.json [--ars-version vX.Y.Z]

Exit 0 on pass (warnings may still be printed to stderr).
Exit 1 on schema or structural validation failure, or file error.
"""
from __future__ import annotations

import argparse
import json
import re
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
    ids = [d.get("id") for d in dims if d.get("id") is not None]
    names = [d.get("name") for d in dims if d.get("name") is not None]
    for dup_id in sorted({x for x in ids if ids.count(x) > 1}):
        errors.append(
            f"duplicate acceptance_dimensions id '{dup_id}'; "
            "downstream aggregation assumes unique ids"
        )
    for dup_name in sorted({x for x in names if names.count(x) > 1}):
        errors.append(
            f"duplicate acceptance_dimensions name '{dup_name}'; "
            "downstream lint assumes unique names"
        )

    conds = contract.get("failure_conditions", [])
    cids = [c.get("condition_id") for c in conds if c.get("condition_id") is not None]
    for dup_cid in sorted({x for x in cids if cids.count(x) > 1}):
        errors.append(
            f"duplicate failure_conditions condition_id '{dup_cid}'; "
            "precedence resolution assumes unique condition_ids"
        )

    return errors


# v? accepts both 'v3.6.2' and '3.6.2' on --ars-version CLI input;
# baseline_version is schema-bound to require the v prefix.
_VERSION_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")


def _parse_version(v: str | None) -> tuple[int, int, int] | None:
    if not v:
        return None
    m = _VERSION_RE.match(v)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def warn_suspicious(contract: dict, ars_current_version: str | None) -> list[str]:
    """Soft warnings per spec §4.3 (SC-1 baseline lag through SC-11
    panel_size sanity). Non-blocking; printed to stderr by main().
    """
    warnings: list[str] = []

    # SC-1 baseline lag: contract.baseline_version lags current ARS by > 2 minor
    bv = _parse_version(contract.get("baseline_version"))
    cv = _parse_version(ars_current_version)
    if bv and cv:
        bv_major, bv_minor, _ = bv
        cv_major, cv_minor, _ = cv
        if bv_major == cv_major and (cv_minor - bv_minor) > 2:
            warnings.append(
                f"SC-1 WARNING: contract baseline v{bv_major}.{bv_minor}.* lags "
                f"current ARS v{cv_major}.{cv_minor}.* by {cv_minor - bv_minor} minor; "
                "retirement candidate"
            )
        elif bv_major != cv_major:
            warnings.append(
                f"SC-1 WARNING: contract baseline major v{bv_major} differs from "
                f"current ARS v{cv_major}; retirement candidate"
            )

    # SC-2 single dimension
    dims = contract.get("acceptance_dimensions", [])
    if len(dims) == 1:
        warnings.append(
            "SC-2 WARNING: contract has only 1 acceptance dimension; "
            "consider whether this mode needs sprint contract at all"
        )

    # SC-3 no mandatory dimension. Empty dims handled by schema validation
    # (minItems: 1); SC-3 only fires when dims exist but lack mandatory.
    if dims and not any(d.get("priority") == "mandatory" for d in dims):
        warnings.append(
            f"SC-3 WARNING: 0 of {len(dims)} acceptance dimensions are mandatory; "
            "failure_conditions referencing 'mandatory' will be vacuous"
        )

    return warnings


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
