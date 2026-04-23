"""Unit tests for check_passport_reset_contract.py (ARS v3.6.3 lint).

Enforces the contract: every text file that mentions the env-flag token
`ARS_PASSPORT_RESET` must co-locate a reference to the protocol-doc stem
`passport_as_reset_boundary` so readers can follow the flag to the spec.

The protocol doc itself (`academic-pipeline/references/passport_as_reset_boundary.md`)
is exempt from needing a self-reference.
"""
from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts._test_helpers import run_script

SCRIPT = Path(__file__).resolve().parent / "check_passport_reset_contract.py"


def _write(root: Path, rel_path: str, content: str) -> Path:
    """Create a text file at root/rel_path with UTF-8 content, parents auto-made."""
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


class TestPassportResetContractLint(unittest.TestCase):
    def test_empty_repo_passes(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            result = run_script(SCRIPT, "--root", str(root))
            self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_mention_without_protocol_ref_fails(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            _write(root, "some_doc.md", "Set ARS_PASSPORT_RESET=1 to enable the flag.\n")
            result = run_script(SCRIPT, "--root", str(root))
            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            # Diagnostic should name the required protocol-doc stem.
            combined = result.stdout + result.stderr
            self.assertIn("passport_as_reset_boundary", combined)

    def test_mention_with_protocol_ref_passes(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            _write(
                root,
                "some_doc.md",
                "Set ARS_PASSPORT_RESET=1 to enable.\n"
                "See academic-pipeline/references/passport_as_reset_boundary.md for details.\n",
            )
            result = run_script(SCRIPT, "--root", str(root))
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    def test_protocol_doc_itself_passes_without_self_reference(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            # The protocol doc IS the reference — it does not need to link to itself.
            _write(
                root,
                "academic-pipeline/references/passport_as_reset_boundary.md",
                "# Passport as Reset Boundary\n\n"
                "This protocol is activated by the ARS_PASSPORT_RESET env flag.\n",
            )
            result = run_script(SCRIPT, "--root", str(root))
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    def test_json_description_satisfies_reference(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            _write(
                root,
                "shared/contracts/passport/reset_ledger_entry.schema.json",
                '{"description": "Set ARS_PASSPORT_RESET=1; see '
                'academic-pipeline/references/passport_as_reset_boundary.md for protocol."}\n',
            )
            result = run_script(SCRIPT, "--root", str(root))
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    def test_code_comment_still_requires_reference(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            _write(root, "scripts/foo.py", "# ARS_PASSPORT_RESET handling\n")
            result = run_script(SCRIPT, "--root", str(root))
            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)

    def test_binary_file_skipped(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            blob = root / "blob.bin"
            blob.write_bytes(b"\x00\x01\x02ARS_PASSPORT_RESET\x03\x04\xff\xfe")
            result = run_script(SCRIPT, "--root", str(root))
            # Binary file either skipped (exit 0) or treated as text (exit 1);
            # both acceptable — the contract is "no crash".
            self.assertIn(result.returncode, (0, 1), msg=result.stdout + result.stderr)
            self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
