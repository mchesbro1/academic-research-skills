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

    def test_missing_top_level_required_fails(self):
        from scripts.check_sprint_contract import validate
        c = _valid_reviewer_full_contract()
        del c["acceptance_dimensions"]
        errors = validate(c)
        self.assertTrue(any("acceptance_dimensions" in e for e in errors))

    def test_bad_contract_id_pattern_fails(self):
        from scripts.check_sprint_contract import validate
        c = _valid_reviewer_full_contract()
        c["contract_id"] = "BAD"
        errors = validate(c)
        self.assertTrue(any("contract_id" in e.lower() or "pattern" in e for e in errors))

    def test_mode_enum_rejects_quick(self):
        from scripts.check_sprint_contract import validate
        c = _valid_reviewer_full_contract()
        c["mode"] = "reviewer_quick"
        errors = validate(c)
        self.assertTrue(any("mode" in e for e in errors))

    def test_additional_top_level_property_fails(self):
        from scripts.check_sprint_contract import validate
        c = _valid_reviewer_full_contract()
        c["foo"] = "bar"
        errors = validate(c)
        self.assertTrue(any("foo" in e or "additional" in e.lower() for e in errors))

    def test_agent_amendments_extra_key_fails(self):
        from scripts.check_sprint_contract import validate
        c = _valid_reviewer_full_contract()
        c["agent_amendments"] = {"extra_field": "x"}
        errors = validate(c)
        self.assertTrue(any("extra_field" in e or "additional" in e.lower() for e in errors))

    def test_override_ladder_when_present_must_be_exactly_3(self):
        from scripts.check_sprint_contract import validate
        c = _valid_reviewer_full_contract()
        c["override_ladder"] = [
            {"round": 1, "trigger": "x", "required": ["rationale"]},
            {"round": 2, "trigger": "x", "required": ["rationale"]},
        ]  # only 2 items
        errors = validate(c)
        self.assertTrue(any("override_ladder" in e or "minItems" in e.lower() for e in errors))

    def test_override_ladder_optional_absence_passes(self):
        from scripts.check_sprint_contract import validate
        c = _valid_reviewer_full_contract()
        if "override_ladder" in c:
            del c["override_ladder"]
        self.assertEqual(validate(c), [])

    def test_override_ladder_positional_order_enforced(self):
        from scripts.check_sprint_contract import validate
        c = _valid_reviewer_full_contract()
        c["override_ladder"] = [
            {"round": 1, "trigger": "x", "required": ["rationale"]},
            {"round": 1, "trigger": "x", "required": ["rationale"]},  # should be 2
            {"round": 3, "trigger": "x", "required": ["rationale"]},
        ]
        errors = validate(c)
        self.assertTrue(any("round" in e or "const" in e.lower() for e in errors))

    def test_priority_enum(self):
        from scripts.check_sprint_contract import validate
        c = _valid_reviewer_full_contract()
        c["acceptance_dimensions"][0]["priority"] = "critical"
        errors = validate(c)
        self.assertTrue(any("priority" in e for e in errors))

    def test_dimension_no_scoring_scale_field(self):
        from scripts.check_sprint_contract import validate
        c = _valid_reviewer_full_contract()
        c["acceptance_dimensions"][0]["scoring_scale"] = "block|warn|pass"
        errors = validate(c)
        self.assertTrue(any("scoring_scale" in e or "additional" in e.lower() for e in errors))

    def test_acceptance_dimension_id_pattern(self):
        from scripts.check_sprint_contract import validate
        c = _valid_reviewer_full_contract()
        c["acceptance_dimensions"][0]["id"] = "d1"
        errors = validate(c)
        self.assertTrue(any("id" in e.lower() or "pattern" in e for e in errors))

    def test_failure_condition_id_pattern(self):
        from scripts.check_sprint_contract import validate
        c = _valid_reviewer_full_contract()
        c["failure_conditions"][0]["condition_id"] = "Fail1"
        errors = validate(c)
        self.assertTrue(any("condition_id" in e.lower() or "pattern" in e for e in errors))

    def test_failure_condition_id_pattern_rejects_leading_zero(self):
        """Audit-induced (Task 2 quality review I-1): leading-zero forms F00,
        F01, F02... must be rejected to keep ordinal tie-break (§3.2 severity
        precedence) unambiguous. Schema pattern is ^F(0|[1-9][0-9]?)$."""
        from scripts.check_sprint_contract import validate
        c = _valid_reviewer_full_contract()
        c["failure_conditions"][0]["condition_id"] = "F01"
        errors = validate(c)
        self.assertTrue(any("condition_id" in e.lower() or "pattern" in e for e in errors))
        c["failure_conditions"][0]["condition_id"] = "F00"
        errors = validate(c)
        self.assertTrue(any("condition_id" in e.lower() or "pattern" in e for e in errors))

    def test_failure_condition_requires_severity(self):
        from scripts.check_sprint_contract import validate
        c = _valid_reviewer_full_contract()
        del c["failure_conditions"][0]["severity"]
        errors = validate(c)
        self.assertTrue(any("severity" in e for e in errors))

    def test_reviewer_mode_failure_condition_requires_quantifier(self):
        from scripts.check_sprint_contract import validate
        c = _valid_reviewer_full_contract()
        del c["failure_conditions"][0]["cross_reviewer_quantifier"]
        errors = validate(c)
        self.assertTrue(any("cross_reviewer_quantifier" in e for e in errors))

    def test_severity_range(self):
        from scripts.check_sprint_contract import validate
        c = _valid_reviewer_full_contract()
        c["failure_conditions"][0]["severity"] = -1
        errors = validate(c)
        self.assertTrue(any("severity" in e or "minimum" in e.lower() for e in errors))
        c["failure_conditions"][0]["severity"] = 101
        errors = validate(c)
        self.assertTrue(any("severity" in e or "maximum" in e.lower() for e in errors))

    def test_cross_reviewer_quantifier_enum(self):
        from scripts.check_sprint_contract import validate
        c = _valid_reviewer_full_contract()
        c["failure_conditions"][0]["cross_reviewer_quantifier"] = "plurality"
        errors = validate(c)
        self.assertTrue(any("quantifier" in e or "enum" in e.lower() for e in errors))

    def test_panel_size_required(self):
        from scripts.check_sprint_contract import validate
        c = _valid_reviewer_full_contract()
        del c["panel_size"]
        errors = validate(c)
        self.assertTrue(any("panel_size" in e for e in errors))

    def test_panel_size_minimum_1(self):
        from scripts.check_sprint_contract import validate
        c = _valid_reviewer_full_contract()
        c["panel_size"] = 0
        errors = validate(c)
        self.assertTrue(any("panel_size" in e or "minimum" in e.lower() for e in errors))

    def test_paraphrase_minimum_dimensions_accepts_all_and_integer(self):
        from scripts.check_sprint_contract import validate
        c = _valid_reviewer_full_contract()
        c["measurement_procedure"]["paraphrase_minimum_dimensions"] = "all"
        self.assertEqual(validate(c), [])
        c["measurement_procedure"]["paraphrase_minimum_dimensions"] = 3
        self.assertEqual(validate(c), [])
        c["measurement_procedure"]["paraphrase_minimum_dimensions"] = 0
        self.assertNotEqual(validate(c), [])
        c["measurement_procedure"]["paraphrase_minimum_dimensions"] = "most"
        self.assertNotEqual(validate(c), [])

    def test_conditional_quantifier_not_required_for_non_reviewer_mode(self):
        """spec §7.1 + spec §3.3: when mode does NOT start with 'reviewer_', the
        allOf branch must NOT require cross_reviewer_quantifier on
        failure_conditions[]. Guards the P2 #12 future-proofing intent so
        v3.6.4 writer/evaluator enum additions stay backward-compatible.

        v3.6.2 schema enum only contains reviewer_* values, so we patch the
        loaded schema in-test to add a hypothetical non-reviewer mode and
        re-validate. We DO NOT modify the on-disk schema."""
        import copy
        from scripts.check_sprint_contract import load_schema
        import jsonschema
        schema = copy.deepcopy(load_schema())
        # Add a non-reviewer-prefixed mode to the enum.
        schema["properties"]["mode"]["enum"].append("writer_full")
        c = _valid_reviewer_full_contract()
        c["mode"] = "writer_full"
        c["contract_id"] = "writer/writer_full/v1"
        c["stage"] = "writer_full_draft"
        # Strip cross_reviewer_quantifier from every failure_condition.
        for fc in c["failure_conditions"]:
            fc.pop("cross_reviewer_quantifier", None)
        validator = jsonschema.Draft202012Validator(
            schema,
            format_checker=jsonschema.Draft202012Validator.FORMAT_CHECKER,
        )
        errors = [str(e.message) for e in validator.iter_errors(c)]
        # No error should mention cross_reviewer_quantifier — the conditional
        # branch in §3.3 only fires when mode starts with 'reviewer_'.
        self.assertFalse(
            any("cross_reviewer_quantifier" in e for e in errors),
            f"Unexpected quantifier error on non-reviewer mode: {errors}",
        )


class TestStructuralInvariants(unittest.TestCase):
    def test_structural_invariant_duplicate_dimension_id(self):
        from scripts.check_sprint_contract import check_structural_invariants
        c = _valid_reviewer_full_contract()
        # force duplicate id
        c["acceptance_dimensions"][1] = dict(c["acceptance_dimensions"][1], id="D1")
        errors = check_structural_invariants(c)
        self.assertTrue(any("duplicate" in e.lower() and "id" in e.lower() for e in errors))

    def test_structural_invariant_duplicate_dimension_name(self):
        from scripts.check_sprint_contract import check_structural_invariants
        c = _valid_reviewer_full_contract()
        c["acceptance_dimensions"][1] = dict(c["acceptance_dimensions"][1], name="methodology_rigor")
        errors = check_structural_invariants(c)
        self.assertTrue(any("duplicate" in e.lower() and "name" in e.lower() for e in errors))

    def test_structural_invariant_duplicate_condition_id(self):
        from scripts.check_sprint_contract import check_structural_invariants
        c = _valid_reviewer_full_contract()
        c["failure_conditions"][1] = dict(c["failure_conditions"][1], condition_id="F1")
        errors = check_structural_invariants(c)
        self.assertTrue(any("duplicate" in e.lower() and "condition_id" in e.lower() for e in errors))

    def test_structural_invariant_clean_contract_passes(self):
        from scripts.check_sprint_contract import check_structural_invariants
        self.assertEqual(check_structural_invariants(_valid_reviewer_full_contract()), [])


if __name__ == "__main__":
    unittest.main()
