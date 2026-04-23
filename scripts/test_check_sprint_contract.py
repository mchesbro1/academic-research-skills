"""Unit tests for check_sprint_contract.py (Schema 13 validator)."""
from __future__ import annotations

import json  # noqa: F401  # used by Group C CLI tests (Task 14)
import subprocess  # noqa: F401  # used by Group C CLI tests (Task 14)
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory  # noqa: F401  # used by Group C CLI tests (Task 14)

from scripts._test_helpers import run_script  # noqa: F401  # used by Group C CLI tests (Task 14)

SCRIPT = Path(__file__).resolve().parent / "check_sprint_contract.py"
# SCHEMA / TEMPLATE_FULL / TEMPLATE_METHOD reserved for Tasks 14-17
# (CLI tests + shipped-template assertions); kept module-level so later tasks
# don't have to reshuffle imports.
SCHEMA = Path(__file__).resolve().parent.parent / "shared" / "sprint_contract.schema.json"
TEMPLATE_FULL = (
    Path(__file__).resolve().parent.parent / "shared" / "contracts" / "reviewer" / "full.json"
)
TEMPLATE_METHOD = (
    Path(__file__).resolve().parent.parent / "shared" / "contracts" / "reviewer" / "methodology_focus.json"
)


def _valid_reviewer_full_contract() -> dict:
    """Returns a fresh fully-valid reviewer_full contract. Callers may mutate freely."""
    return {
        "contract_id": "reviewer/reviewer_full/v1",
        "mode": "reviewer_full",
        "stage": "reviewer_full_review",
        "baseline_version": "v3.6.2",
        "panel_size": 5,
        "acceptance_dimensions": [
            {"id": "D1", "name": "methodology_rigor", "description": "x", "priority": "mandatory"},
            {"id": "D2", "name": "domain_accuracy", "description": "x", "priority": "mandatory"},
            {"id": "D3", "name": "argumentative_coherence", "description": "x", "priority": "mandatory"},
            {"id": "D4", "name": "cross_disciplinary_relevance", "description": "x", "priority": "high"},
            {"id": "D5", "name": "writing_and_structure", "description": "x", "priority": "normal"},
        ],
        "measurement_procedure": {
            "reviewer_must_output_before_paper": ["contract_paraphrase", "scoring_plan"],
            "scoring_plan_schema": {
                "required": [
                    "dimension_id",
                    "what_to_look_for",
                    "what_triggers_block",
                    "what_triggers_warn",
                ]
            },
            "paraphrase_minimum_dimensions": "all",
        },
        "failure_conditions": [
            {
                "condition_id": "F1",
                "severity": 90,
                "cross_reviewer_quantifier": "any",
                "expression": "any mandatory dimension scores 'block'",
                "action": "editorial_decision=reject_or_major_revision",
            },
            {
                "condition_id": "F2",
                "severity": 70,
                "cross_reviewer_quantifier": "majority",
                "expression": "two or more mandatory dimensions score 'warn' or worse",
                "action": "editorial_decision=major_revision",
            },
            {
                "condition_id": "F3",
                "severity": 60,
                "cross_reviewer_quantifier": "any",
                "expression": "any high-priority dimension scores 'block'",
                "action": "editorial_decision=major_revision",
            },
            {
                "condition_id": "F0",
                "severity": 10,
                "cross_reviewer_quantifier": "all",
                "expression": "every mandatory dimension scores 'pass'",
                "action": "editorial_decision=accept",
            },
        ],
    }


class TestSchemaValidation(unittest.TestCase):
    def test_valid_reviewer_full_passes(self):
        from scripts.check_sprint_contract import validate

        errors = validate(_valid_reviewer_full_contract())
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
