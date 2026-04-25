"""Tests for scripts/adapters/folder_scan.py."""
from pathlib import Path
import subprocess

REPO_ROOT = Path(__file__).resolve().parents[3]
ADAPTER = REPO_ROOT / "scripts/adapters/folder_scan.py"
FIXTURE_DIR = REPO_ROOT / "scripts/adapters/examples/folder_scan/input_fixture"
EXPECTED_PASSPORT = REPO_ROOT / "scripts/adapters/examples/folder_scan/expected_passport.yaml"
EXPECTED_REJECTION = REPO_ROOT / "scripts/adapters/examples/folder_scan/expected_rejection_log.yaml"


def _run(*args, cwd=None):
    return subprocess.run(
        ["python", str(ADAPTER)] + list(args),
        capture_output=True,
        text=True,
        cwd=cwd or REPO_ROOT,
    )


def test_adapter_exists():
    assert ADAPTER.exists()


def test_happy_path(tmp_path, load_yaml, clean_timestamps):
    passport_out = tmp_path / "passport.yaml"
    rejection_out = tmp_path / "rejection_log.yaml"
    r = _run(
        "--input", str(FIXTURE_DIR),
        "--passport", str(passport_out),
        "--rejection-log", str(rejection_out),
    )
    assert r.returncode == 0, r.stderr

    got = load_yaml(passport_out)
    expected = load_yaml(EXPECTED_PASSPORT)
    assert clean_timestamps(got) == clean_timestamps(expected)

    got_rej = load_yaml(rejection_out)
    expected_rej = load_yaml(EXPECTED_REJECTION)
    assert clean_timestamps(got_rej) == clean_timestamps(expected_rej)


def test_empty_folder_emits_empty_passport(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    passport_out = tmp_path / "p.yaml"
    rej_out = tmp_path / "r.yaml"
    r = _run(
        "--input", str(empty),
        "--passport", str(passport_out),
        "--rejection-log", str(rej_out),
    )
    assert r.returncode == 0
    import yaml
    with passport_out.open() as f:
        doc = yaml.safe_load(f)
    assert doc == {"literature_corpus": []}


def test_missing_input_dir_fails_loud(tmp_path):
    r = _run(
        "--input", str(tmp_path / "does-not-exist"),
        "--passport", str(tmp_path / "p.yaml"),
        "--rejection-log", str(tmp_path / "r.yaml"),
    )
    assert r.returncode == 1
    assert "not found" in r.stderr.lower() or "exist" in r.stderr.lower()


def test_deterministic_output(tmp_path, load_yaml, clean_timestamps):
    p1 = tmp_path / "p1.yaml"
    r1_log = tmp_path / "r1.yaml"
    p2 = tmp_path / "p2.yaml"
    r2_log = tmp_path / "r2.yaml"
    _run("--input", str(FIXTURE_DIR), "--passport", str(p1), "--rejection-log", str(r1_log))
    _run("--input", str(FIXTURE_DIR), "--passport", str(p2), "--rejection-log", str(r2_log))
    assert clean_timestamps(load_yaml(p1)) == clean_timestamps(load_yaml(p2))
    assert clean_timestamps(load_yaml(r1_log)) == clean_timestamps(load_yaml(r2_log))


def test_duplicate_collision_handled(tmp_path):
    # Two files that would produce the same base citation_key should each be
    # accepted with a disambiguating suffix.
    dup_dir = tmp_path / "dup"
    dup_dir.mkdir()
    (dup_dir / "Smith2024_alpha.pdf").touch()
    (dup_dir / "Smith2024_beta.pdf").touch()
    passport_out = tmp_path / "p.yaml"
    rej_out = tmp_path / "r.yaml"
    r = _run(
        "--input", str(dup_dir),
        "--passport", str(passport_out),
        "--rejection-log", str(rej_out),
    )
    assert r.returncode == 0
    import yaml
    with passport_out.open() as f:
        doc = yaml.safe_load(f)
    keys = {e["citation_key"] for e in doc["literature_corpus"]}
    assert len(keys) == 2  # no collisions
