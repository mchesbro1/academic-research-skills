"""Tests for scripts/adapters/obsidian.py."""
from pathlib import Path
import subprocess
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
ADAPTER = REPO_ROOT / "scripts/adapters/obsidian.py"
VAULT = REPO_ROOT / "scripts/adapters/examples/obsidian/input_fixture/vault"
EXPECTED_PASSPORT = REPO_ROOT / "scripts/adapters/examples/obsidian/expected_passport.yaml"
EXPECTED_REJECTION = REPO_ROOT / "scripts/adapters/examples/obsidian/expected_rejection_log.yaml"


def _run(*args):
    return subprocess.run(
        ["python", str(ADAPTER)] + list(args),
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )


def test_adapter_exists():
    assert ADAPTER.exists()


def test_happy_path(tmp_path, load_yaml, clean_timestamps):
    p = tmp_path / "p.yaml"
    r = tmp_path / "r.yaml"
    res = _run("--input", str(VAULT), "--passport", str(p), "--rejection-log", str(r))
    assert res.returncode == 0, res.stderr
    assert clean_timestamps(load_yaml(p)) == clean_timestamps(load_yaml(EXPECTED_PASSPORT))
    assert clean_timestamps(load_yaml(r)) == clean_timestamps(load_yaml(EXPECTED_REJECTION))


def test_missing_vault_fails_loud(tmp_path):
    p = tmp_path / "p.yaml"
    r = tmp_path / "r.yaml"
    res = _run("--input", str(tmp_path / "nope"), "--passport", str(p), "--rejection-log", str(r))
    assert res.returncode == 1


def test_templates_dir_skipped(tmp_path, load_yaml):
    vault = tmp_path / "v"
    (vault / "_templates").mkdir(parents=True)
    (vault / "_templates/tmpl.md").write_text(
        "---\ncitekey: tmpl2024\ntitle: T\nauthors:\n  - family: X\nyear: 2024\n---\n",
        encoding="utf-8",
    )
    (vault / "note.md").write_text(
        "---\ncitekey: note2024\ntitle: Real\nauthors:\n  - family: Y\nyear: 2024\n---\nbody\n",
        encoding="utf-8",
    )
    p = tmp_path / "p.yaml"
    r = tmp_path / "r.yaml"
    res = _run("--input", str(vault), "--passport", str(p), "--rejection-log", str(r))
    assert res.returncode == 0
    doc = load_yaml(p)
    keys = [e["citation_key"] for e in doc["literature_corpus"]]
    assert "tmpl2024" not in keys
    assert "note2024" in keys


def test_obsidian_dir_skipped(tmp_path, load_yaml):
    vault = tmp_path / "v"
    (vault / ".obsidian").mkdir(parents=True)
    (vault / ".obsidian/ignored.md").write_text(
        "---\ncitekey: skip2024\ntitle: T\nauthors:\n  - family: X\nyear: 2024\n---\n",
        encoding="utf-8",
    )
    (vault / "real.md").write_text(
        "---\ncitekey: real2024\ntitle: R\nauthors:\n  - family: Y\nyear: 2024\n---\n",
        encoding="utf-8",
    )
    p = tmp_path / "p.yaml"
    r = tmp_path / "r.yaml"
    _run("--input", str(vault), "--passport", str(p), "--rejection-log", str(r))
    doc = load_yaml(p)
    keys = [e["citation_key"] for e in doc["literature_corpus"]]
    assert "skip2024" not in keys
    assert "real2024" in keys


def test_convention_a_source_pointer_is_obsidian_uri(tmp_path, load_yaml):
    """source_pointer for Convention A must be an obsidian:// URI (deterministic, not file://)."""
    vault = tmp_path / "myvault"
    vault.mkdir()
    (vault / "paper.md").write_text(
        "---\ncitekey: smith2024\ntitle: A Study\nauthors:\n  - family: Smith\nyear: 2024\n---\n",
        encoding="utf-8",
    )
    p = tmp_path / "p.yaml"
    r = tmp_path / "r.yaml"
    res = _run("--input", str(vault), "--passport", str(p), "--rejection-log", str(r))
    assert res.returncode == 0, res.stderr
    doc = load_yaml(p)
    entry = doc["literature_corpus"][0]
    assert entry["source_pointer"].startswith("obsidian://open?vault=")
    assert "myvault" in entry["source_pointer"]
    assert "paper" in entry["source_pointer"]


def test_convention_b_source_pointer_is_obsidian_uri(tmp_path, load_yaml):
    """source_pointer for Convention B (Karpathy-style) must also be obsidian:// URI."""
    vault = tmp_path / "mybvault"
    vault.mkdir()
    (vault / "jones2022review.md").write_text(
        "---\nsource: https://doi.org/10.999/abc\n---\n\n# Review of methods\n\n**Authors**: Jones, A.\n**Year**: 2022\n\nContent.\n",
        encoding="utf-8",
    )
    p = tmp_path / "p.yaml"
    r = tmp_path / "r.yaml"
    res = _run("--input", str(vault), "--passport", str(p), "--rejection-log", str(r))
    assert res.returncode == 0, res.stderr
    doc = load_yaml(p)
    entry = doc["literature_corpus"][0]
    assert entry["source_pointer"].startswith("obsidian://open?vault=")
    assert "mybvault" in entry["source_pointer"]


def test_deterministic_output(tmp_path, load_yaml, clean_timestamps):
    p1 = tmp_path / "p1.yaml"
    r1 = tmp_path / "r1.yaml"
    p2 = tmp_path / "p2.yaml"
    r2 = tmp_path / "r2.yaml"
    _run("--input", str(VAULT), "--passport", str(p1), "--rejection-log", str(r1))
    _run("--input", str(VAULT), "--passport", str(p2), "--rejection-log", str(r2))
    assert clean_timestamps(load_yaml(p1)) == clean_timestamps(load_yaml(p2))
    assert clean_timestamps(load_yaml(r1)) == clean_timestamps(load_yaml(r2))
