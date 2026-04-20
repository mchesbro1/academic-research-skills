"""Unit tests for check_compliance_report.py (Schema 10 validator)."""
import json
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts._test_helpers import run_script

SCRIPT = Path(__file__).resolve().parent / "check_compliance_report.py"
SCHEMA = Path(__file__).resolve().parent.parent / "shared" / "compliance_report.schema.json"


def _valid_sr_report() -> dict:
    return {
        "mode": "systematic_review",
        "stage": "2.5",
        "generated_at": "2026-04-20T10:00:00Z",
        "prisma_trAIce": {
            "items_total": 17,
            "by_tier": {
                "mandatory": {"total": 9, "pass": 9, "fail": []},
                "highly_recommended": {"total": 1, "pass": 1, "fail": []},
                "recommended": {"total": 4, "pass": 4, "fail": []},
                "optional": {"total": 3, "pass": 3, "fail": []},
            },
            "block_decision": "pass",
        },
        "raise": {
            "mode": "full",
            "principles": {
                "human_oversight": "pass",
                "transparency": "pass",
                "reproducibility": "pass",
                "fit_for_purpose": "pass",
            },
            "principle_evidence": {
                "human_oversight": ["Stage 2: bibliography.yaml L12"],
                "transparency": ["manuscript §Methods L40"],
                "reproducibility": ["passport.repro_lock"],
                "fit_for_purpose": ["Stage 1: scoping.md L5"],
            },
            "roles": {
                "evidence_synthesists": ["manuscript §Acknowledgements"],
                "ai_development_teams": ["CHANGELOG"],
                "methodologists": [],
                "publishers": [],
                "users": [],
                "trainers": [],
                "organisations": [],
                "funders": [],
            },
            "block_decision": "pass",
        },
        "overall_decision": "pass",
        "user_action_required": False,
        "evidence": ["manuscript §Methods"],
    }


def _valid_primary_report() -> dict:
    return {
        "mode": "primary_research",
        "stage": "4.5",
        "generated_at": "2026-04-20T11:00:00Z",
        "prisma_trAIce": None,
        "raise": {
            "mode": "principles_only",
            "principles": {
                "human_oversight": "pass",
                "transparency": "warn",
                "reproducibility": "pass",
                "fit_for_purpose": "pass",
            },
            "principle_evidence": {
                "human_oversight": ["manuscript §Limitations"],
                "transparency": [],
                "reproducibility": ["manuscript §Methods"],
                "fit_for_purpose": ["manuscript §Introduction"],
            },
            "block_decision": "warn",
        },
        "overall_decision": "warn",
        "user_action_required": True,
        "evidence": [],
    }


def _run(path: Path) -> subprocess.CompletedProcess:
    return run_script(SCRIPT, str(path))


def _write(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data), encoding="utf-8")


class TestComplianceReportValidator(unittest.TestCase):
    def test_valid_sr_report_passes(self) -> None:
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "r.json"
            _write(p, _valid_sr_report())
            result = _run(p)
            self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_valid_primary_report_passes(self) -> None:
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "r.json"
            _write(p, _valid_primary_report())
            result = _run(p)
            self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_missing_required_field_fails(self) -> None:
        report = _valid_sr_report()
        del report["overall_decision"]
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "r.json"
            _write(p, report)
            result = _run(p)
            self.assertEqual(result.returncode, 1)
            self.assertIn("overall_decision", result.stdout + result.stderr)

    def test_invalid_mode_enum_fails(self) -> None:
        report = _valid_sr_report()
        report["mode"] = "random_mode"
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "r.json"
            _write(p, report)
            result = _run(p)
            self.assertEqual(result.returncode, 1)

    def test_invalid_stage_enum_fails(self) -> None:
        report = _valid_sr_report()
        report["stage"] = "3.5"
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "r.json"
            _write(p, report)
            result = _run(p)
            self.assertEqual(result.returncode, 1)

    def test_primary_with_populated_prisma_trAIce_fails(self) -> None:
        # Schema enforces: mode=primary_research implies prisma_trAIce is null.
        # This cross-field rule was added when hardening the schema per code review.
        report = _valid_primary_report()
        report["prisma_trAIce"] = _valid_sr_report()["prisma_trAIce"]
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "r.json"
            _write(p, report)
            result = _run(p)
            self.assertEqual(result.returncode, 1)

    def test_sr_with_null_prisma_trAIce_fails(self) -> None:
        # Cross-field rule: systematic_review requires prisma_trAIce object.
        report = _valid_sr_report()
        report["prisma_trAIce"] = None
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "r.json"
            _write(p, report)
            result = _run(p)
            self.assertEqual(result.returncode, 1)

    def test_raise_full_without_roles_fails(self) -> None:
        # Cross-field rule: raise.mode=full requires roles.
        report = _valid_sr_report()
        del report["raise"]["roles"]
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "r.json"
            _write(p, report)
            result = _run(p)
            self.assertEqual(result.returncode, 1)

    def test_invalid_scope_pattern_fails(self) -> None:
        # user_override.scope must match PRISMA-trAIce IDs or RAISE principles.
        report = _valid_sr_report()
        report["user_override"] = {
            "decision": True,
            "timestamp": "2026-04-20T12:00:00Z",
            "rationale": "Test invalid scope",
            "scope": ["NOT_AN_ITEM"],
        }
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "r.json"
            _write(p, report)
            result = _run(p)
            self.assertEqual(result.returncode, 1)

    def test_extra_top_level_property_fails(self) -> None:
        # additionalProperties: false on top-level rejects typos.
        report = _valid_sr_report()
        report["bogus_extra"] = "x"
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "r.json"
            _write(p, report)
            result = _run(p)
            self.assertEqual(result.returncode, 1)

    def test_user_override_missing_rationale_fails(self) -> None:
        report = _valid_sr_report()
        report["user_override"] = {
            "decision": True,
            "timestamp": "2026-04-20T12:00:00Z",
            "rationale": "",
            "scope": ["M4"],
        }
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "r.json"
            _write(p, report)
            result = _run(p)
            self.assertEqual(result.returncode, 1)

    def test_user_override_empty_scope_fails(self) -> None:
        report = _valid_sr_report()
        report["user_override"] = {
            "decision": True,
            "timestamp": "2026-04-20T12:00:00Z",
            "rationale": "Insufficient time to backfill M4 details before submission deadline.",
            "scope": [],
        }
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "r.json"
            _write(p, report)
            result = _run(p)
            self.assertEqual(result.returncode, 1)

    def test_valid_override_with_real_ids_passes(self) -> None:
        # Positive: scope containing real PRISMA-trAIce IDs and RAISE principle names.
        report = _valid_sr_report()
        report["user_override"] = {
            "decision": True,
            "timestamp": "2026-04-20T12:00:00Z",
            "rationale": "Material unavailable to backfill M4 before venue deadline.",
            "scope": ["M4", "transparency"],
        }
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "r.json"
            _write(p, report)
            result = _run(p)
            self.assertEqual(result.returncode, 0, msg=result.stderr)


if __name__ == "__main__":
    unittest.main()
