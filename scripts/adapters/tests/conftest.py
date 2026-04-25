"""pytest configuration + shared fixtures for adapter tests.

Provides:
- `repo_root` : Path to the ARS repo root
- `adapters_dir` : Path to scripts/adapters/
- `examples_dir` : Path to scripts/adapters/examples/
- `clean_timestamps(doc)` : helper that blanks `generated_at`,
   `obtained_at`, `source_pointer`, and `input_source` fields so
   byte-identical comparisons are possible across machines (absolute
   paths differ).
- `load_yaml(path)` : convenience YAML loader.
"""
from __future__ import annotations
from pathlib import Path
import copy
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def adapters_dir() -> Path:
    return REPO_ROOT / "scripts/adapters"


@pytest.fixture(scope="session")
def examples_dir() -> Path:
    return REPO_ROOT / "scripts/adapters/examples"


def _strip_keys(obj, keys_to_blank: set[str]):
    if isinstance(obj, dict):
        return {
            k: ("<TIMESTAMP>" if k in keys_to_blank else _strip_keys(v, keys_to_blank))
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_strip_keys(v, keys_to_blank) for v in obj]
    return obj


@pytest.fixture
def clean_timestamps():
    """Return a function that returns a copy of a dict/list with all
    `generated_at`, `obtained_at`, `source_pointer`, and `input_source`
    values blanked to '<TIMESTAMP>'. Used to compare adapter output against
    expected fixtures without flakiness across machines (absolute paths
    differ; timestamps drift)."""
    def _clean(doc):
        return _strip_keys(
            copy.deepcopy(doc),
            {"generated_at", "obtained_at", "source_pointer", "input_source"},
        )
    return _clean


@pytest.fixture
def load_yaml():
    """Return a function that loads a YAML file into a Python dict."""
    def _load(path: Path):
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return _load
