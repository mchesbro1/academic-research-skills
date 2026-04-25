"""Tests for scripts/adapters/zotero.py."""
from pathlib import Path
import subprocess
import json

REPO_ROOT = Path(__file__).resolve().parents[3]
ADAPTER = REPO_ROOT / "scripts/adapters/zotero.py"
FIXTURE_INPUT = REPO_ROOT / "scripts/adapters/examples/zotero/input_fixture/export.json"
EXPECTED_PASSPORT = REPO_ROOT / "scripts/adapters/examples/zotero/expected_passport.yaml"
EXPECTED_REJECTION = REPO_ROOT / "scripts/adapters/examples/zotero/expected_rejection_log.yaml"


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
    res = _run("--input", str(FIXTURE_INPUT), "--passport", str(p), "--rejection-log", str(r))
    assert res.returncode == 0, res.stderr
    assert clean_timestamps(load_yaml(p)) == clean_timestamps(load_yaml(EXPECTED_PASSPORT))
    assert clean_timestamps(load_yaml(r)) == clean_timestamps(load_yaml(EXPECTED_REJECTION))


def test_malformed_json_fails_loud(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    p = tmp_path / "p.yaml"
    r = tmp_path / "r.yaml"
    res = _run("--input", str(bad), "--passport", str(p), "--rejection-log", str(r))
    assert res.returncode == 1
    assert "json" in res.stderr.lower() or "parse" in res.stderr.lower()


def test_empty_array_emits_empty_passport(tmp_path, load_yaml):
    empty = tmp_path / "empty.json"
    empty.write_text("[]", encoding="utf-8")
    p = tmp_path / "p.yaml"
    r = tmp_path / "r.yaml"
    res = _run("--input", str(empty), "--passport", str(p), "--rejection-log", str(r))
    assert res.returncode == 0
    doc = load_yaml(p)
    assert doc == {"literature_corpus": []}


def test_institution_author_preserved(tmp_path, load_yaml):
    data = [
        {
            "citationKey": "who2024",
            "itemType": "report",
            "title": "World report",
            "creators": [{"creatorType": "author", "name": "World Health Organization"}],
            "date": "2024",
            "itemID": "AAAA1111",
        }
    ]
    infile = tmp_path / "i.json"
    infile.write_text(json.dumps(data), encoding="utf-8")
    p = tmp_path / "p.yaml"
    r = tmp_path / "r.yaml"
    res = _run("--input", str(infile), "--passport", str(p), "--rejection-log", str(r))
    assert res.returncode == 0
    doc = load_yaml(p)
    assert doc["literature_corpus"][0]["authors"] == [{"literal": "World Health Organization"}]


def test_no_authors_rejected(tmp_path, load_yaml):
    data = [
        {
            "citationKey": "anon2024",
            "itemType": "journalArticle",
            "title": "Untitled",
            "creators": [{"creatorType": "editor", "firstName": "A", "lastName": "B"}],
            "date": "2024",
            "itemID": "BBBB1111",
        }
    ]
    infile = tmp_path / "i.json"
    infile.write_text(json.dumps(data), encoding="utf-8")
    p = tmp_path / "p.yaml"
    r = tmp_path / "r.yaml"
    res = _run("--input", str(infile), "--passport", str(p), "--rejection-log", str(r))
    assert res.returncode == 0
    pp = load_yaml(p)
    rr = load_yaml(r)
    assert pp["literature_corpus"] == []
    assert len(rr["rejected"]) == 1
    assert rr["rejected"][0]["reason"] == "authors_unparseable"


def test_unparseable_date_rejected(tmp_path, load_yaml):
    data = [
        {
            "citationKey": "fwd2024",
            "itemType": "journalArticle",
            "title": "Forthcoming",
            "creators": [{"creatorType": "author", "firstName": "A", "lastName": "B"}],
            "date": "forthcoming",
            "itemID": "CCCC1111",
        }
    ]
    infile = tmp_path / "i.json"
    infile.write_text(json.dumps(data), encoding="utf-8")
    p = tmp_path / "p.yaml"
    r = tmp_path / "r.yaml"
    res = _run("--input", str(infile), "--passport", str(p), "--rejection-log", str(r))
    assert res.returncode == 0
    rr = load_yaml(r)
    assert rr["rejected"][0]["reason"] == "year_unparseable"
