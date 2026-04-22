"""Lint tests for the v3.5.1 opt-in Socratic reading-check probe.

Target spec: docs/design/2026-04-22-ars-v3.7.3-reading-check-probe-design.md §5.1.

These are file-content lints (grep / regex / structure assertions) against:
- deep-research/agents/socratic_mentor_agent.md §"Optional Reading Probe Layer"
- deep-research/references/socratic_mode_protocol.md §"Reading Probe"
- deep-research/SKILL.md §"Opt-in Reading Probe (v3.5.1)"
- academic-pipeline/references/process_summary_protocol.md §"Reading Probe Outcomes"

Pattern matches test_check_compliance_report.py — no LLM runtime, no subprocess fork,
just read file bytes and assert structural invariants.

Run standalone:
    python -m unittest scripts/test_reading_probe_lint.py -v

Run via suite:
    python -m unittest discover scripts/ -v
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

MENTOR_AGENT = REPO_ROOT / "deep-research" / "agents" / "socratic_mentor_agent.md"
SOCRATIC_PROTOCOL = REPO_ROOT / "deep-research" / "references" / "socratic_mode_protocol.md"
DEEP_RESEARCH_SKILL = REPO_ROOT / "deep-research" / "SKILL.md"
README_EN = REPO_ROOT / "README.md"
README_ZH = REPO_ROOT / "README.zh-TW.md"
PIPELINE_PROCESS_SUMMARY = REPO_ROOT / "academic-pipeline" / "references" / "process_summary_protocol.md"
COLLABORATION_RUBRIC = REPO_ROOT / "shared" / "collaboration_depth_rubric.md"
COMPLIANCE_SCHEMA = REPO_ROOT / "shared" / "schemas" / "compliance_report.schema.json"


class ReadingProbeLintTests(unittest.TestCase):
    """Spec §5.1 — 7 file-content lints for the reading-check probe."""

    # Test 1 — spec §5.1 item 1
    def test_mentor_file_has_probe_section(self):
        """Mentor file contains §'Optional Reading Probe Layer' with 6 subsections."""
        text = MENTOR_AGENT.read_text(encoding="utf-8")
        self.assertIn("## Optional Reading Probe Layer", text,
                      f"{MENTOR_AGENT} missing §'Optional Reading Probe Layer' heading")
        # Required subsections — match spec §3.1-3.7 ordering
        required_subheadings = [
            "### Activation",
            "### Candidate Paper Tracking",
            "### Probe Wording",
            "### Response Handling",
            "### Banned Phrases",
            "### Research Plan Summary Subsection",
        ]
        for sub in required_subheadings:
            self.assertIn(sub, text,
                          f"{MENTOR_AGENT} missing subsection {sub!r}")

    # Test 2 — spec §5.1 item 2
    def test_env_var_name_consistent_across_repo(self):
        """ARS_SOCRATIC_READING_PROBE appears verbatim in all 4 canonical files.

        No case drift, no typos, no aliases.
        """
        expected = "ARS_SOCRATIC_READING_PROBE"
        # Spec §5.1 item 2: "agent, protocol, SKILL, README".
        # process_summary_protocol is excluded — it carries the [READING-PROBE:]
        # pickup rule (tested separately by test_probe_tag_format), not the env var.
        files = [MENTOR_AGENT, SOCRATIC_PROTOCOL, DEEP_RESEARCH_SKILL, README_EN, README_ZH]
        for f in files:
            text = f.read_text(encoding="utf-8")
            self.assertIn(expected, text,
                          f"{f.relative_to(REPO_ROOT)} missing env var {expected!r}")
        # Defense: no case-drifted siblings should exist anywhere in the repo
        for f in files:
            text = f.read_text(encoding="utf-8")
            # Matches e.g. ARS_SOCRATIC_READING_PROBE_FOO or typos like ARS_SOCRATIC_READINGPROBE
            wrong_cases = re.findall(
                r"\bARS_SOCRATIC[_A-Z]*\b", text
            )
            for hit in wrong_cases:
                self.assertEqual(hit, expected,
                                 f"{f.relative_to(REPO_ROOT)} has case-drifted "
                                 f"env var {hit!r}, expected {expected!r}")

    # Test 3 — spec §5.1 item 3
    def test_probe_gated_by_goal_oriented(self):
        """Mentor probe section states goal-oriented-only activation.

        Also verifies no instruction activates the probe in exploratory mode.
        """
        text = MENTOR_AGENT.read_text(encoding="utf-8")
        # Locate the probe section
        start = text.find("## Optional Reading Probe Layer")
        self.assertGreater(start, -1, "probe section not found")
        # Boundary — next top-level heading
        end = text.find("\n## ", start + 1)
        probe_section = text[start:end if end > -1 else len(text)]
        # Required phrasing (spec §3.2 activation clause line 3)
        self.assertRegex(probe_section,
                         r"goal[- ]oriented",
                         "probe section must state goal-oriented gating")
        # Negative — no "exploratory" activation directive
        self.assertNotRegex(probe_section,
                            r"(activate|fire|trigger)s?.*exploratory",
                            "probe section must NOT activate in exploratory mode")

    # Test 4 — spec §5.1 item 4
    def test_decline_is_zero_penalty(self):
        """Decline outcome is explicitly excluded from all 5 scoring channels."""
        text = MENTOR_AGENT.read_text(encoding="utf-8")
        start = text.find("## Optional Reading Probe Layer")
        end = text.find("\n## ", start + 1)
        probe_section = text[start:end if end > -1 else len(text)]
        # The 5 channels decline must not touch (spec §3.5 OUTCOME=decline)
        exclusions = [
            "Persistent-Agreement",
            "Conflict-Avoidance",
            "Premature-Convergence",
            "convergence signal",
            "intent classification",
        ]
        for chan in exclusions:
            self.assertIn(chan, probe_section,
                          f"probe section must mention {chan!r} in decline-zero-penalty clause")
        # Positive: must contain "no penalty" or "not penalised"/"not penalized"
        self.assertRegex(probe_section,
                         r"(no penalty|not penali[sz]ed)",
                         "probe section must state decline is not penalised")

    # Test 5 — spec §5.1 item 5
    def test_probe_tag_format(self):
        """Mentor's [READING-PROBE: ...] tag format is defined and referenced identically in process_summary_protocol."""
        mentor_text = MENTOR_AGENT.read_text(encoding="utf-8")
        process_text = PIPELINE_PROCESS_SUMMARY.read_text(encoding="utf-8")
        # The literal tag prefix
        tag_prefix = "[READING-PROBE:"
        self.assertIn(tag_prefix, mentor_text,
                      f"{MENTOR_AGENT.name} must define {tag_prefix!r} tag format")
        self.assertIn(tag_prefix, process_text,
                      f"{PIPELINE_PROCESS_SUMMARY.name} must reference {tag_prefix!r} for Stage 6 pickup")
        # Consistency of the fields mentioned in both files
        for field in ["paper=", "outcome=", "turn="]:
            self.assertIn(field, mentor_text,
                          f"{MENTOR_AGENT.name} tag spec missing field {field!r}")
            self.assertIn(field, process_text,
                          f"{PIPELINE_PROCESS_SUMMARY.name} pickup rule missing field {field!r}")

    # Test 6 — spec §5.1 item 6
    def test_no_probe_in_scoring_files(self):
        """Probe identifiers must not leak into scoring / rubric / convergence files.

        Prevents regression where the probe becomes a de-facto gate.
        """
        # Candidate files where a regression could land
        scoring_files = []
        if COLLABORATION_RUBRIC.exists():
            scoring_files.append(COLLABORATION_RUBRIC)
        if COMPLIANCE_SCHEMA.exists():
            scoring_files.append(COMPLIANCE_SCHEMA)
        # Mentor convergence-signal subsection — scan outside the probe section
        mentor_text = MENTOR_AGENT.read_text(encoding="utf-8")
        probe_start = mentor_text.find("## Optional Reading Probe Layer")
        probe_end = mentor_text.find("\n## ", probe_start + 1) if probe_start > -1 else -1
        if probe_start > -1:
            mentor_without_probe = (
                mentor_text[:probe_start]
                + (mentor_text[probe_end:] if probe_end > -1 else "")
            )
        else:
            mentor_without_probe = mentor_text

        banned_identifiers = ["reading_probe", "READING-PROBE", "reading-probe"]
        # Check mentor file sections OUTSIDE the probe section
        for ident in banned_identifiers:
            self.assertNotIn(
                ident, mentor_without_probe,
                f"{MENTOR_AGENT.name} has {ident!r} leaking OUTSIDE §'Optional Reading Probe Layer'"
            )
        # Check all scoring / rubric files
        for f in scoring_files:
            text = f.read_text(encoding="utf-8")
            for ident in banned_identifiers:
                self.assertNotIn(
                    ident, text,
                    f"{f.relative_to(REPO_ROOT)} contains {ident!r} — "
                    f"probe must not appear in scoring/rubric files"
                )

    # Test 7 — spec §5.1 item 7
    def test_banned_praise_phrases(self):
        """Probe section's banned-phrases list contains the 8 exact strings from spec §3.6."""
        text = MENTOR_AGENT.read_text(encoding="utf-8")
        start = text.find("### Banned Phrases")
        self.assertGreater(start, -1, "missing '### Banned Phrases' subheading")
        end = text.find("\n### ", start + 1)
        if end == -1:
            end = text.find("\n## ", start + 1)
        banned_section = text[start:end if end > -1 else len(text)]
        # Exact strings, quoted as in spec §3.6
        expected_banned = [
            '"correct"',
            '"right"',
            '"wrong"',
            '"good answer"',
            '"well said"',
            '"make sure"',
            '"verify"',
            '"prove"',
        ]
        for phrase in expected_banned:
            self.assertIn(phrase, banned_section,
                          f"banned-phrases list missing {phrase!r}")
        # Negative: "check" must NOT be in the banned list
        # (per spec §3.6 note — "check" has non-evaluative uses elsewhere in the section)
        self.assertNotRegex(
            banned_section,
            r'["\'`]check["\'`]',
            "'check' must NOT be in banned list (per spec §3.6 explicit carve-out)"
        )


if __name__ == "__main__":
    unittest.main()
