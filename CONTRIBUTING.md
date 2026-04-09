# Contributing to Academic Research Skills

Thank you for your interest in contributing. This document explains what kinds of contributions we accept and how to submit them.

---

## How to submit a contribution

ARS uses the standard **fork-and-PR** workflow:

```bash
# 1. Fork the repo on GitHub (click "Fork" button on the repo page)

# 2. Clone your fork
git clone https://github.com/YOUR-USERNAME/academic-research-skills.git
cd academic-research-skills

# 3. Create a branch
git checkout -b feat/your-feature-name

# 4. Make your changes and commit
git add .
git commit -m "feat: description of your change"

# 5. Push to your fork
git push origin feat/your-feature-name

# 6. Open a PR on GitHub
# Go to https://github.com/Imbad0202/academic-research-skills
# Click "Compare & pull request"
```

**Important**: You cannot push directly to this repo — you must fork it first and submit a PR from your fork. This is standard GitHub practice for open collaboration.

---

## What we accept

### Community-maintained (fast merge)

These contributions can be merged quickly with minimal review:

- **Typo and formatting fixes** — spelling, broken links, markdown rendering issues
- **New examples** — pipeline output showcases, worked examples for specific disciplines
- **Translation improvements** — better zh-TW or EN phrasing in READMEs or agent definitions

### Requires maintainer review

These need careful review because they affect system behavior:

- **Journal and field reference lists** — additions to `top_journals_by_field.md`, new discipline glossaries
- **Evaluation sets** — gold-standard papers for calibration mode, benchmark data
- **New reference files** — methodology guides, citation format references, domain-specific protocols
- **Bug and drift fixes** — version inconsistencies, broken cross-references, incorrect metadata
- **Mode changes** — new modes, trigger keyword changes, oversight level adjustments

### Requires maintainer approval + discussion

Open an issue first before submitting a PR for these:

- **Agent definition changes** — modifications to any file in `*/agents/*.md`
- **IRON RULE modifications** — any change to rules marked with the IRON RULE marker
- **Ethics and integrity rules** — changes to the failure mode checklist, integrity protocols, or ethics review
- **Handoff schema changes** — modifications to `shared/handoff_schemas.md`
- **New skills or modes** — additions to the pipeline

---

## PR guidelines

- **One concern per PR** — don't mix unrelated changes
- **Describe what and why** — explain the motivation, not just the change
- **Reference issues** — if your PR addresses an open issue, link it
- **Test your changes** — if you're modifying agent definitions, try running the skill to confirm it works as expected
- **Keep READMEs in sync** — if your change affects user-facing documentation, update both `README.md` and `README.zh-TW.md`

---

## Governance

### Maintainer

The repo is maintained by [Cheng-I Wu](https://github.com/Imbad0202) (HEEACT). The maintainer has final say on all merges.

### Decision principles

1. **Accuracy over completeness** — we'd rather have fewer, verified journal entries than a long unvetted list
2. **Human-in-the-loop always** — contributions that reduce human oversight or enable fully autonomous paper generation will be declined
3. **No detection evasion** — features designed to make AI-generated text harder to detect (as opposed to higher quality) are out of scope. See [Issue #3](https://github.com/Imbad0202/academic-research-skills/issues/3) for context.
4. **Discipline diversity welcome** — ARS defaults to higher education research but aims to be domain-agnostic. Discipline-specific modules are encouraged.

---

## Academic integrity policy

This repo is designed to be **assistive, not deceptive**.

- ARS helps researchers write better papers, not hide that they used AI
- Contributors must not add features designed to evade AI detection tools
- All pipeline outputs include AI disclosure by design
- The Disclosure Mode generates venue-specific AI usage statements because transparency is the standard, not the exception

If you're unsure whether a contribution aligns with this policy, open an issue to discuss before submitting a PR.

---

## Credit

Contributors are credited in commit messages, CHANGELOG entries, and the Contributors section of the README. For significant contributions (new features, major reference files), we also add a mention in the relevant release notes.

## License

By contributing, you agree that your contributions will be licensed under [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/), the same license as the rest of the project.
