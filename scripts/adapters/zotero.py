#!/usr/bin/env python3
"""zotero: produce a literature_corpus passport from a Better BibTeX
Extension JSON export. Reads only local files; does not call the Zotero
Web API.

See design doc §5.3. Users who want a live-sync API-based variant are
expected to write their own adapter using this file as a starting point
(see overview.md extension-point guidance).

Usage:
  python scripts/adapters/zotero.py \
      --input <bbt_export.json> --passport <out.yaml> --rejection-log <out.yaml>
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

# Allow running as a script: ensure repo root is importable for
# `from scripts.adapters._common import ...`
_THIS = Path(__file__).resolve()
_REPO_ROOT = _THIS.parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.adapters._common import (  # noqa: E402
    write_passport,
    write_rejection_log,
    now_iso,
)

ADAPTER_NAME = "zotero.py"
ADAPTER_VERSION = "1.0.0"

RE_YEAR = re.compile(r"\b((?:19|20)\d{2})\b")


def extract_authors(creators: list[dict]) -> list[dict] | None:
    """Pull only author-type creators. Return CSL-name list or None when no authors."""
    out: list[dict] = []
    for c in creators or []:
        if c.get("creatorType") != "author":
            continue
        if "name" in c:  # institution / corporate author
            out.append({"literal": c["name"].strip()})
            continue
        family = (c.get("lastName") or "").strip()
        given = (c.get("firstName") or "").strip()
        if not family:
            continue
        entry: dict[str, str] = {"family": family}
        if given:
            entry["given"] = given
        out.append(entry)
    return out if out else None


def extract_year(date_str: str) -> int | None:
    if not date_str:
        return None
    m = RE_YEAR.search(date_str)
    if m:
        return int(m.group(1))
    return None


def strip_doi(doi: str | None) -> str | None:
    if not doi:
        return None
    doi = doi.strip()
    for prefix in ("doi:", "DOI:", "https://doi.org/", "http://doi.org/"):
        if doi.lower().startswith(prefix.lower()):
            doi = doi[len(prefix):]
            break
    return doi.strip() or None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, required=True, help="BBT JSON export file")
    ap.add_argument("--passport", type=Path, required=True)
    ap.add_argument("--rejection-log", dest="rejection_log", type=Path, required=True)
    args = ap.parse_args()

    try:
        raw = args.input.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"ERROR: input not found: {args.input}", file=sys.stderr)
        return 1
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"ERROR: input is not valid JSON: {e}", file=sys.stderr)
        return 1
    if not isinstance(data, list):
        print(f"ERROR: expected top-level JSON array, got {type(data).__name__}", file=sys.stderr)
        return 1

    entries: list[dict] = []
    rejected: list[dict] = []

    for item in data:
        citekey = item.get("citationKey") or ""
        item_id = item.get("itemID") or ""
        source_key = item_id or citekey or "<unknown>"

        authors = extract_authors(item.get("creators", []))
        year = extract_year(item.get("date", ""))

        missing: list[str] = []
        if not authors:
            missing.append("authors")
        if not year:
            missing.append("year")

        if missing:
            reason = "authors_unparseable" if "authors" in missing else "year_unparseable"
            rejected.append({
                "source": source_key,
                "reason": reason,
                "raw": item,
                "missing_fields": missing,
            })
            continue

        venue = (
            item.get("publicationTitle")
            or item.get("proceedingsTitle")
            or item.get("bookTitle")
            or None
        )

        source_pointer = (
            f"zotero://select/items/0_{item_id}"
            if item_id
            else f"zotero://select/items/@{citekey}"
        )

        entry: dict = {
            "citation_key": citekey,
            "title": item.get("title", "").strip(),
            "authors": authors,
            "year": year,
            "source_pointer": source_pointer,
            "obtained_via": "zotero-bbt-export",
            "obtained_at": now_iso(),
            "adapter_name": ADAPTER_NAME,
            "adapter_version": ADAPTER_VERSION,
        }
        if venue:
            entry["venue"] = venue
        doi = strip_doi(item.get("DOI"))
        if doi:
            entry["doi"] = doi
        tags = [t.get("tag") for t in item.get("tags", []) if t.get("tag")]
        if tags:
            entry["tags"] = tags
        abstract = item.get("abstractNote")
        if abstract:
            entry["abstract"] = abstract
        notes = item.get("notes") or []
        if notes:
            plain = "\n\n".join(
                re.sub(r"<[^>]+>", "", n.get("note", ""))
                for n in notes
                if n.get("note")
            )
            if plain.strip():
                entry["user_notes"] = plain

        entries.append(entry)

    write_passport(args.passport, entries)
    # input_source is intentionally omitted: it is a machine-dependent absolute
    # path that would make the golden fixture non-portable. The rejection log
    # schema marks input_source as optional precisely for this use case.
    write_rejection_log(
        args.rejection_log,
        adapter_name=ADAPTER_NAME,
        adapter_version=ADAPTER_VERSION,
        rejected=rejected,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
