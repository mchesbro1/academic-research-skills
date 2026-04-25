"""Tests for the CI lint that validates passport/rejection-log examples
against their schemas and enforces citation_key uniqueness."""
from pathlib import Path
import subprocess
import sys
import yaml
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts/check_literature_corpus_schema.py"


def _write_yaml(tmp_path, name, data):
    p = tmp_path / name
    with p.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=True)
    return p


def _run(args, cwd=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT)] + args,
        capture_output=True,
        text=True,
        cwd=cwd or REPO_ROOT,
    )


def test_script_exists():
    assert SCRIPT.exists()


def test_passes_on_valid_passport(tmp_path):
    passport = {
        "literature_corpus": [
            {
                "citation_key": "chen2024",
                "title": "T",
                "authors": [{"family": "Chen"}],
                "year": 2024,
                "source_pointer": "file:///x.pdf",
            }
        ]
    }
    _write_yaml(tmp_path, "passport.yaml", passport)
    r = _run(["--passport", str(tmp_path / "passport.yaml")])
    assert r.returncode == 0, r.stderr


def test_fails_on_schema_violation(tmp_path):
    passport = {
        "literature_corpus": [
            {
                "citation_key": "chen2024",
                "title": "T",
                "authors": [{}],  # invalid author
                "year": 2024,
                "source_pointer": "file:///x.pdf",
            }
        ]
    }
    _write_yaml(tmp_path, "passport.yaml", passport)
    r = _run(["--passport", str(tmp_path / "passport.yaml")])
    assert r.returncode != 0
    assert "schema" in r.stderr.lower() or "validation" in r.stderr.lower()


def test_fails_on_duplicate_citation_key(tmp_path):
    passport = {
        "literature_corpus": [
            {
                "citation_key": "dup",
                "title": "A",
                "authors": [{"family": "X"}],
                "year": 2024,
                "source_pointer": "file:///a.pdf",
            },
            {
                "citation_key": "dup",
                "title": "B",
                "authors": [{"family": "Y"}],
                "year": 2024,
                "source_pointer": "file:///b.pdf",
            },
        ]
    }
    _write_yaml(tmp_path, "passport.yaml", passport)
    r = _run(["--passport", str(tmp_path / "passport.yaml")])
    assert r.returncode != 0
    assert "duplicate" in r.stderr.lower() or "unique" in r.stderr.lower()


def test_passes_on_valid_rejection_log(tmp_path):
    log = {
        "adapter_name": "zotero.py",
        "adapter_version": "1.0.0",
        "generated_at": "2026-04-23T00:00:00Z",
        "rejected": [],
    }
    _write_yaml(tmp_path, "rejection_log.yaml", log)
    r = _run(["--rejection-log", str(tmp_path / "rejection_log.yaml")])
    assert r.returncode == 0, r.stderr


def test_default_mode_scans_repo_examples():
    """With no args, script scans scripts/adapters/examples/** for
    expected_passport.yaml and expected_rejection_log.yaml and validates
    each. This is the CI-invoked mode. At this point the examples don't
    exist yet (T7-T9 will populate them), so 0 (no files) is acceptable."""
    r = _run([])
    assert r.returncode in (0, 1)


# --- T4 reminder (codex T3-review P2): FORMAT_CHECKER must be wired ---
# Otherwise format=date-time is silently ignored on generated_at and obtained_at.

def test_passport_with_invalid_obtained_at_format_fails(tmp_path):
    passport = {
        "literature_corpus": [
            {
                "citation_key": "chen2024",
                "title": "T",
                "authors": [{"family": "Chen"}],
                "year": 2024,
                "source_pointer": "file:///x.pdf",
                "obtained_at": "definitely-not-a-date",
            }
        ]
    }
    _write_yaml(tmp_path, "passport.yaml", passport)
    r = _run(["--passport", str(tmp_path / "passport.yaml")])
    assert r.returncode != 0, (
        "format=date-time on obtained_at must be enforced. "
        "If this passes, validate_passport built Draft202012Validator "
        "without format_checker — see codex T3-review P2."
    )


def test_rejection_log_with_invalid_generated_at_format_fails(tmp_path):
    log = {
        "adapter_name": "x",
        "adapter_version": "1",
        "generated_at": "definitely-not-a-date",
        "rejected": [],
    }
    _write_yaml(tmp_path, "rejection_log.yaml", log)
    r = _run(["--rejection-log", str(tmp_path / "rejection_log.yaml")])
    assert r.returncode != 0, (
        "format=date-time on generated_at must be enforced. "
        "If this passes, validate_rejection_log built Draft202012Validator "
        "without format_checker — see codex T3-review P2."
    )


# --- additional integration coverage ---

def test_help_flag_runs_clean():
    r = _run(["--help"])
    assert r.returncode == 0
    assert "passport" in r.stdout.lower()


def test_passport_other_obtained_via_without_adapter_name_fails(tmp_path):
    """T2 patch contract: obtained_via='other' requires adapter_name.
    Lint must propagate the schema's allOf if/then conditional."""
    passport = {
        "literature_corpus": [
            {
                "citation_key": "chen2024",
                "title": "T",
                "authors": [{"family": "Chen"}],
                "year": 2024,
                "source_pointer": "file:///x.pdf",
                "obtained_via": "other",
                # adapter_name missing
            }
        ]
    }
    _write_yaml(tmp_path, "passport.yaml", passport)
    r = _run(["--passport", str(tmp_path / "passport.yaml")])
    assert r.returncode != 0


def test_rejection_log_other_reason_with_empty_detail_fails(tmp_path):
    """T3 patch contract: detail.minLength=1 must be enforced."""
    log = {
        "adapter_name": "x",
        "adapter_version": "1",
        "generated_at": "2026-04-23T00:00:00Z",
        "rejected": [{"source": "s", "reason": "other", "detail": ""}],
    }
    _write_yaml(tmp_path, "rejection_log.yaml", log)
    r = _run(["--rejection-log", str(tmp_path / "rejection_log.yaml")])
    assert r.returncode != 0
