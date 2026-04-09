# ARS v3.2 Roadmap

**Status**: Draft — 2026-04-09
**Previous plan**: v3.1 optimization (aspi6246 adoption, anti-context-rot anchors, what/how separation)
**New input**: Lu et al. (2026), *Towards end-to-end automation of AI research*, Nature 651, 914-919. [doi:10.1038/s41586-026-10265-5](https://doi.org/10.1038/s41586-026-10265-5)

This roadmap extends the v3.1 plan with evidence and mechanisms from the first published end-to-end autonomous AI research system (The AI Scientist). Where v3.1 was driven by comparisons to sibling Claude Code skill suites, v3.2 is driven by the symmetric question: *what has a fully-automated AI research pipeline learned that a human-in-the-loop pipeline like ARS should steal?*

---

## Why this paper matters for ARS

The AI Scientist and ARS occupy opposite ends of the same design space.

| Dimension | The AI Scientist (Lu 2026) | ARS |
|---|---|---|
| Actor | Fully autonomous LLM agents | Human researcher + LLM skills |
| Goal | Generate and publish papers end-to-end | Help a human produce a better paper |
| Evaluation | ICLR workshop blind peer review (one paper accepted, 6.33/10) | Internal quality rubrics (0-100) |
| Published limits | Implementation bugs, hallucinated citations, shortcut reliance, frame-lock at hyperparameter stage | Context rot, sycophancy, premature convergence |

ARS's *raison d'être* is that the human-in-the-loop path is currently better. Lu et al.'s own limitations section is the strongest external argument for ARS's position. But The AI Scientist also made engineering choices that ARS has not — and those choices are free to borrow.

---

## v3.2 additions (ordered by implementation cost, cheapest first)

### 1. Reviewer self-calibration mode (HIGH priority, LOW cost)

**Source**: Lu 2026 Table 1, Automated Reviewer validation methodology.

**Finding**: The AI Scientist's Automated Reviewer achieves balanced accuracy of 0.65 on 500 ICLR 2022 papers, within 0.05 of human reviewers (0.67-0.73), **with a much lower false negative rate (0.17 vs human 0.52)** at the cost of higher false positive rate (0.50 vs human 0.17-0.34). Human reviewers miss half of papers that should be rejected; Automated Reviewer misses very few.

**Implication for ARS**: `academic-paper-reviewer` currently produces 0-100 rubric scores with no calibration against ground truth. A single LLM reviewer's absolute score is weakly interpretable. Users would benefit from knowing the reviewer's error profile.

**Change**: Add a new mode to `academic-paper-reviewer`:

- **`calibration` mode** — User supplies a small set of papers with known outcomes (accepted / rejected / borderline, ideally from their own domain). The reviewer runs `full` mode on each, produces a confusion matrix (FNR / FPR / balanced accuracy / AUC), and reports its own error profile. The calibration report is then attached as a confidence disclosure to subsequent reviews in the same session.
- Reuse bootstrapping methodology from Lu 2026 Methods A.1.1 (agent pool + ensemble voting) to reduce single-pass variance. Recommend ensembling ≥5 reviewer runs by default for calibration; current default is 1.
- Cross-model verification (`ARS_CROSS_MODEL`) should be promoted from optional to **default-on** for calibration mode, based on Lu 2026's use of multiple reviewer forms.

**File locations**:
- New mode spec: `academic-paper-reviewer/references/calibration_mode_protocol.md`
- SKILL.md: add `calibration` to the mode table (currently lists `full`, `re-review`, `quick`, `methodology-focus`, `guided`)
- Quality rubrics update: `academic-paper-reviewer/references/quality_rubrics.md` — add "known error profile" subsection pointing to calibration mode output

### 2. AI Research Failure Mode Checklist (HIGH priority, LOW cost)

**Source**: Lu 2026 "Limitations" section, Supplementary Information A.2.9 (debugging traces), Figure 2 (concrete review excerpts flagging issues in The AI Scientist's own accepted paper).

**Finding**: Lu et al. enumerate specific, operationalizable failure modes of automated AI research:
1. Implementation bugs that pass AI self-review
2. Hallucinated citations (matches ARS's existing 5-type taxonomy)
3. Hallucinated experimental results (e.g. loss curves that look reasonable but come from crashed runs)
4. Shortcut reliance (models exploiting spurious features, e.g. the MNIST colour-bias case in Fig 2b)
5. "Implementation bug as insight" — buggy behaviour reframed as a novel finding
6. Methodology fabrication — methods section describes experiments that were not actually run as stated
7. Frame-lock at hyperparameter tuning stage (Stage 2 in Fig 3a) — agent commits to wrong direction early and fails to backtrack

**Implication for ARS**: The current integrity verification catches (2) but is weak on (1), (3), (4), (5), and (7). These are precisely the failure modes a human researcher using ARS is most likely to miss, because they *look* like competent work.

**Change**: Create `academic-pipeline/references/ai_research_failure_modes.md` containing the full taxonomy with:
- Description of each failure mode
- Concrete example from Lu 2026 (with page reference)
- Detection question(s) the user should ask at the relevant pipeline stage
- Which agent in which skill is responsible for catching it

Then wire the checklist into the pipeline's integrity verification stages, where the paper is still editable:

- **Stage 2.5 INTEGRITY** (first integrity gate, after initial draft): full 7-mode rule-out. Suspected failures **block** the pipeline — it halts and surfaces the specific suspicion to the user, who must explicitly acknowledge (confirm / override / revise) before Stage 3 REVIEW begins.
- **Stage 4.5 FINAL INTEGRITY** (after revisions, before finalization): re-run the 7-mode rule-out. Any previously-flagged issue that is not resolved re-blocks.
- **Stage 6 PROCESS SUMMARY** (AI Self-Reflection Report): report the 7-mode history as an honest account of what was flagged and resolved during the pipeline. No blocking here — Stage 6 is post-finalization reflection, too late to change the paper.

Rationale for not putting the block at Stage 6: Stage 6 happens after the paper is finalized and PDFed. Blocking then cannot actually change the paper. Blocking at 2.5 and 4.5 catches problems while they can still be fixed.

Block behaviour at 2.5 and 4.5 is mandatory; there is no `--no-block` escape hatch in v3.2. Rationale: the user would rather be interrupted than catch a bug-as-insight paper after the fact. If this proves too noisy in practice, revisit in v3.3.

**Correction from initial draft**: The first draft of this roadmap placed the blocking checkpoint at Stage 6. That was wrong — Stage 6 is post-finalization and cannot change the paper. Corrected to Stage 2.5 and 4.5 after inspecting the actual pipeline state machine in `academic-pipeline/SKILL.md`.

This also extends the existing **"5-type citation hallucination taxonomy"** into a broader **"N-type AI research hallucination taxonomy"** — citation hallucinations are a subset.

### 3. Template-based vs template-free mode separation (MEDIUM priority, MEDIUM cost)

**Source**: Lu 2026 Figure 1c (bar chart: template-based score ≈ 3.8, template-free ≈ 3.4, human ceiling ≈ 4.5; template-free has higher variance).

**Finding**: The AI Scientist runs in two modes. Template-based (given a reference codebase skeleton) produces higher-quality, lower-variance papers. Template-free produces more diverse outputs but fewer successful papers. Lu et al. frame this as a **fidelity-vs-originality trade-off**, not a strict ordering.

**Implication for ARS**: This directly validates Phase 3 of the v3.1 plan (separate what/how: templates → sub-files). It also refines the plan: ARS modes should be explicitly labelled on the fidelity-vs-originality spectrum, and the right mode depends on the user's goal.

**Change**: Reclassify existing modes on the spectrum and document in each SKILL.md:

| Skill | Mode | Template load | Spectrum position |
|---|---|---|---|
| deep-research | `systematic-review` | Heavy | Fidelity |
| deep-research | `lit-review` | Heavy | Fidelity |
| deep-research | `full` | Medium | Balanced |
| deep-research | `socratic` | Light | Originality |
| deep-research | `quick` | Heavy | Fidelity |
| academic-paper | `full-auto` | Heavy | Fidelity |
| academic-paper | `plan` | Light | Originality |
| academic-paper-reviewer | `full` | Medium | Balanced |
| academic-paper-reviewer | `guided` | Light | Originality |

Users should see this table in the README and get mode recommendations based on whether they want a predictable output or a creative one. The template-heavy modes can safely move long examples into sub-files (v3.1 Phase 3); the template-light modes should keep inline guidance because they rely on context priming.

### 4. Early-stopping criterion for the pipeline (MEDIUM priority, MEDIUM cost)

**Source**: Lu 2026 Figure 3c — "Paper scores given by the Automated Reviewer" vs "Number of experimental nodes". Scores rise from ~3.3 at 5 nodes to ~3.9 at 30 nodes, then plateau. Each additional node costs compute linearly.

**Finding**: Quality improvements from agentic search saturate around 30 experimental nodes. More compute stops paying off.

**Implication for ARS**: `academic-pipeline` currently runs 10 fixed stages and burns 200K+ input tokens. The existing `project_ars_optimization.md` flags this as a known cost limitation. Lu's scaling curve suggests ARS should similarly stop iterating when marginal quality gain is below threshold.

**Change**: Add to `academic-pipeline/SKILL.md`:

- **Convergence check** at end of each revision loop: compute delta in reviewer score vs previous iteration. If delta < 3 points on 0-100 rubric AND no P0 issues remain, terminate with "converged" status instead of running another loop.
- **Hard cap**: maximum 3 revision loops (current cap implied but not enforced). Lu 2026 used tree search with up to 30 nodes; ARS is doing linear revision, so 3 full passes is the analogous budget.
- **Budget transparency**: at pipeline start, reviewer estimates expected token cost based on paper length and selected mode. User confirms before proceeding.

### 5. Experiment Progress Manager — roadmap placeholder (LOW priority, HIGH cost)

**Source**: Lu 2026 Methods A.2.4 — "Experiment Progress Manager" agent that tracks long-running experiments, detects stalls, and decides whether to kill runs.

**Finding**: The AI Scientist has a dedicated agent for experiment execution oversight that ARS has no analogue for. ARS currently assumes all work is writing/reading/reviewing, not running experiments.

**Implication for ARS**: If ARS ever wants to become a full research pipeline (not just a writing pipeline), this is the missing module. Currently the user runs experiments themselves and brings results to ARS; The AI Scientist closes that loop.

**Change**: **Not v3.2.** Record as a known gap in the roadmap. Revisit after v3.2 ships.

**Correction (2026-04-09)**: The initial draft proposed this as a new standalone skill (`experiment-manager`). That was wrong. This is an **agent** (`experiment_monitor_agent`), not a skill. Rationale:
- It is **dispatched** by the pipeline orchestrator (or invoked by another agent), not triggered directly by the user via keywords.
- It runs in the **background** (polling run status, detecting stalls), not in interactive dialogue.
- It does not need its own SKILL.md, trigger keywords, or mode table — those are skill-level constructs.
- It naturally lives at `academic-pipeline/agents/experiment_monitor_agent.md`, alongside the existing pipeline agents (state_tracker, integrity_verification, etc.).

The pipeline orchestrator would dispatch it between Stage 1 RESEARCH and Stage 2 WRITE, when the user says "I need to run experiments first". The agent monitors runs, reports status, and returns verified results to the orchestrator, which then proceeds to Stage 2 with confidence that the experimental data is sound.

### 6. Disclosure mode for `academic-paper` (LOW priority, LOW cost)

**Source**: Lu 2026 Methods, "Ethics statement" — full disclosure to participating workshop organizers and reviewers. Nature required this.

**Finding**: Journals and conferences increasingly require explicit AI-usage disclosure. The AI Scientist ran a formally-approved human subjects protocol for reviewer participation. Different venues have different requirements (Nature, ICLR, ACL, COPE, COPE-aligned journals).

**Implication for ARS**: ARS currently enforces "AI disclosure in all reports" at the internal-rubric level but does not produce a venue-appropriate disclosure paragraph as an output artefact.

**Change**: Add `disclosure` sub-mode to `academic-paper`:
- **Input**: target venue (journal name or conference)
- **Built-in venues for v1**: ICLR, NeurIPS, Nature, Science, ACL, EMNLP. Each entry in the venue database stores:
  - Current AI-usage policy text (verbatim or summarized)
  - Source URL + access date
  - Preferred disclosure location (Methods / Acknowledgements / cover letter / separate statement)
  - Required phrasing elements, if any
- **Unknown venues**: trigger a "policy unknown" prompt asking the user to paste the venue's current policy before proceeding. Do not guess or fabricate a policy.
- **Output**: a disclosure paragraph written in the venue's preferred voice and placed in the preferred section, disclosing ARS's role in research, writing, and review
- **Education/QA journals** (HEEACT target venues): deferred to v2 of this mode. v1 focuses on the ML/NLP heavy set because (a) they have the most well-defined AI policies, (b) they are the venues Lu 2026's own paper was tested against, making comparability cleaner.

### 7. Positioning update in README (LOW priority, LOW cost)

**Source**: Lu 2026 conclusion + Limitations.

**Finding**: Lu et al. explicitly state that even with a Nature-published end-to-end system in 2026, autonomous AI research has not reached top-tier human quality and remains bottlenecked by hallucination, shortcut reliance, and methodology gaps. The accepted paper scored 6.33/10 at a workshop; orals typically require 7-8.

**Implication for ARS**: This is direct external evidence for ARS's human-in-the-loop thesis, from the strongest possible source.

**Change**: Update `README.md` and `README.zh-TW.md` positioning section:

> ARS is built on the premise that human researchers augmented by AI produce better scholarship than either alone. This premise is reinforced by Lu et al. (2026, *Nature*), whose end-to-end autonomous AI research system — the first to publish an AI-authored paper through blind peer review — remains bounded by implementation-bug blindness, hallucination, shortcut reliance, and frame-lock at early-stage decisions. ARS is designed to give human researchers the leverage of autonomous agents without inheriting these failure modes.

Also fixes the known issue that zh-TW README lags EN (v2.9.1 vs v3.0) — this update lands in both at once.

---

## Items NOT adopted from Lu 2026

For completeness, these were considered and rejected:

- **Tree search over research agendas** (Lu 2026 Fig 3a): ARS does linear revision, not exploration over a research-idea space. Adding tree search would fundamentally change the interaction model. Not a fit.
- **Agentic code execution**: The AI Scientist literally runs ML experiments. ARS assumes the user runs experiments. Staying out of execution keeps ARS framework-agnostic and avoids a whole class of reproducibility problems.
- **LLM-as-judge for final paper acceptance**: Lu 2026's Automated Reviewer makes accept/reject recommendations. ARS's reviewer skill deliberately stops short of this — it produces rubrics and editorial letters, and the user decides. Lu's own FPR of 0.50 is a good reason to keep this separation.

---

## Relationship to v3.1 plan

v3.1 items remain in scope. v3.2 refines and extends:

| v3.1 item | v3.2 impact |
|---|---|
| TheEditor 7-audit checklist fusion into reviewer | Compatible. Complements the new failure-mode checklist. |
| Data Profiler mode in deep-research | Compatible. Unchanged. |
| Hostile Referee 2 persona for devil's advocate | Compatible. Unchanged. |
| IRON RULE markers + checkpoint self-checks | **Extended** — checkpoints now include the 7-item AI research failure mode rule-out. |
| Mid-conversation reinforcement | Compatible. Unchanged. |
| Quality degradation detection | **Reinforced** — the early-stopping criterion (v3.2 item 4) is a quantitative instantiation of this. |
| Templates to sub-files | **Reinforced and refined** — now tied to the fidelity/originality spectrum. |

Net effect: v3.1 was about *tightening existing quality*; v3.2 adds *external calibration* (reviewer self-calibration), *failure-mode coverage* (7-type taxonomy), and *cost control* (early stopping).

---

## Implementation order

1. Update CLAUDE.md version strings to reality (v1.7 reviewer, v3.1.1 overall). Memory-identified debt, trivial.
2. v3.2 item 2 — AI Research Failure Mode Checklist. Pure documentation, unblocks everything else.
3. v3.2 item 1 — Reviewer calibration mode. Depends on (2).
4. v3.2 item 7 — README positioning update.
5. v3.2 item 6 — Disclosure mode.
6. v3.2 item 4 — Pipeline early stopping. Depends on (1) for accurate version tracking.
7. v3.2 item 3 — Mode spectrum reclassification + v3.1 Phase 3 (templates to sub-files) together.
8. v3.2 item 5 — Experiment Progress Manager: parked. Will be an agent (`experiment_monitor_agent`) in `academic-pipeline/agents/`, not a standalone skill.

---

## Design decisions (resolved 2026-04-09)

- **Calibration mode trigger**: **Opt-in**. User invokes `calibration` mode explicitly. No auto-run, no implicit caching across sessions. Rationale: the user wants to keep the calibration decision in their hands rather than have ARS silently spend tokens on calibration runs.
- **Stage 6 failure-mode checkpoint behaviour**: **Block**. When the AI Research Failure Mode Checklist flags one or more of the 7 failure modes, the pipeline halts and surfaces the specific suspicion to the user. User must explicitly acknowledge (confirm / override / revise) before the pipeline continues. Rationale: the cost of letting a bug-as-insight or hallucinated-result paper through is worse than the cost of occasional false alarms, and the user would rather be interrupted than have to catch it after the fact.
- **Disclosure mode venue coverage (v1)**: Start with **ICLR, NeurIPS, Nature, Science, ACL, EMNLP** — ML/NLP-heavy set. Each venue needs: (a) current AI-usage policy text with source URL and access date, (b) preferred disclosure location (Methods / Acknowledgements / cover letter / separate statement), (c) required phrasing elements if any. Venues outside this set trigger a "policy unknown" prompt asking the user to paste the policy before proceeding. Education/QA journals (HEEACT target venues) are deferred to v2 of this mode.
