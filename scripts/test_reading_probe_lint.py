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
PIPELINE_PROCESS_SUMMARY = REPO_ROOT / "academic-pipeline" / "references" / "process_summary_protocol.md"
COLLABORATION_RUBRIC = REPO_ROOT / "shared" / "collaboration_depth_rubric.md"
COMPLIANCE_SCHEMA = REPO_ROOT / "shared" / "schemas" / "compliance_report.schema.json"


# Tests will be added in subsequent tasks.
