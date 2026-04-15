# ARS Pipeline Architecture (v3.3.5)

Full pipeline view across stages × skills × artifacts × gates. Use the matrix for detail; use the diagrams for structure.

## 1. Pipeline Flow

```mermaid
flowchart TD
    Start([User input])
    S1[1. RESEARCH<br/>deep-research]
    S2[2. WRITE<br/>academic-paper]
    G25{2.5 INTEGRITY<br/>7-mode gate}
    S3[3. REVIEW<br/>academic-paper-reviewer]
    D3{Decision}
    S4[4. REVISE<br/>academic-paper]
    S3p[3'. RE-REVIEW]
    D3p{Decision}
    S4p[4'. RE-REVISE]
    G45{4.5 FINAL<br/>INTEGRITY gate}
    S5[5. FINALIZE<br/>MD → DOCX/PDF]
    S6[6. PROCESS<br/>SUMMARY]
    End([Done])

    Start --> S1 --> S2 --> G25
    G25 -- PASS --> S3
    G25 -- FAIL, max 3 retries --> S2
    S3 --> D3
    D3 -- Accept --> G45
    D3 -- Minor / Major --> S4
    D3 -- Reject --> End
    S4 --> S3p --> D3p
    D3p -- Accept / Minor --> G45
    D3p -- Major --> S4p
    S4p --> G45
    G45 -- PASS, zero tolerance --> S5
    G45 -- FAIL --> S4p
    S5 --> S6 --> End

    classDef gate fill:#fff4e6,stroke:#d48806,stroke-width:2px
    classDef skill fill:#e6f4ff,stroke:#1677ff
    classDef decision fill:#f9f0ff,stroke:#9254de
    class G25,G45 gate
    class S1,S2,S3,S4,S3p,S4p,S5,S6 skill
    class D3,D3p decision
```

## 2. Stage × Dimension Matrix

| Stage | Skill / Mode | Data level | Artifact produced | Core agents | Gate / Checkpoint |
|---|---|---|---|---|---|
| **1. RESEARCH** | `deep-research` (full / socratic / lit-review / systematic-review / fact-check / review / quick) | RAW | RQ Brief; Methodology Blueprint; Annotated Bibliography (S2-verified); Synthesis Report; INSIGHT Collection | research_question_agent; research_architect_agent; bibliography_agent; source_verification_agent; synthesis_agent; meta_analysis_agent; editor_in_chief_agent; devils_advocate_agent; risk_of_bias_agent; ethics_review_agent; socratic_mentor_agent; report_compiler_agent; monitoring_agent | FULL checkpoint: user confirms RQ brief + methodology. S2 API Tier-0 verification (Levenshtein ≥ 0.70). Evidence hierarchy graded. Anti-sycophancy on DA (score 1-5, concede only ≥ 4) |
| **2. WRITE** | `academic-paper` (full / plan / outline-only / lit-review / revision-coach / abstract-only / citation-check / disclosure / format-convert / revision) | REDACTED | Paper Configuration Record; Outline; Argument Map; Draft Text; Bilingual Abstract; Figures + Captions; Citation List | intake_agent; structure_architect_agent; argument_builder_agent; draft_writer_agent; abstract_bilingual_agent; visualization_agent; literature_strategist_agent; socratic_mentor_agent (plan mode); style_calibration_agent; writing_quality_agent; formatter_agent; revision_coach_agent | FULL checkpoint: outline approved. Anti-leakage protocol: any unsupported fill → `[MATERIAL GAP]`. VLM figure verification (10-pt APA checklist, max 2 refinements). Style calibration vs user voice. Parallelization: Phase 1 + visualization run after outline. |
| **2.5 INTEGRITY** | `academic-pipeline` (gate) | VERIFIED_ONLY | Material Passport (Schema 9, required) + `repro_lock` (v3.3.5, declared — populated or `null`); Claim ↔ Reference Map (100% verified); Data Provenance Audit | integrity_verification_agent; state_tracker_agent; pipeline_orchestrator_agent | **MANDATORY gate.** 7-mode AI failure checklist (Lu 2026): Mode 1 impl bugs, Mode 2 hallucinated results, Mode 3 shortcut reliance, Mode 4 reframed bugs, Mode 5 methodology fabrication, Mode 6 frame-lock, Mode 7 citation hallucination. FAIL → fix + re-verify (max 3 rounds) |
| **3. REVIEW** | `academic-paper-reviewer` (full / guided / quick / methodology-focus / calibration) | VERIFIED_ONLY | Editor-in-Chief Decision (Accept / Minor / Major / Reject); 3× Reviewer Reports (R1, R2, R3); Devil's Advocate Critique; Revision Roadmap; R&R Traceability Matrix | editor_in_chief_agent; field_analyst_agent (auto-detects domain, configures 3 field-adaptive reviewers); 3 peer reviewer agents (methodology, domain, cross-disciplinary); devils_advocate_agent; reviewer_calibration_agent (calibration mode) | **MANDATORY checkpoint** (user sees decision). Concession threshold protocol: DA rebuttal scored 1-5, no concede below 4. Attack intensity preserved through revisions. Cross-model DA critique (optional, `ARS_CROSS_MODEL` env). Read-only constraint (no new claims). |
| **4. REVISE** | `academic-paper` (revision / revision-coach) | REDACTED | Point-by-Point Response; Revised Draft; Delta Report (what changed + why) | revision_coach_agent (v3.3 Socratic mode); draft_writer_agent (re-entry); style_calibration_agent (continuous); argument_builder_agent (if structural) | FULL checkpoint: user confirms changes. Score trajectory tracked per rubric dimension (v3.3) — revisions that regress a dimension are flagged. |
| **3'. RE-REVIEW** | `academic-paper-reviewer` (re-review) | VERIFIED_ONLY | Verification Review (did revisions address roadmap?); Decision (Accept / Minor / Major) | editor_in_chief_agent (continuity); same 3 peer reviewers (v1.8 continuity); devils_advocate_agent | **MANDATORY checkpoint.** Max 2 review ⇄ revise loops total. Major outcome → Stage 4' (no further review loop). R&R Traceability Matrix updated. |
| **4'. RE-REVISE** | `academic-paper` (revision) | REDACTED | Final Revised Draft (terminal; advances to 4.5) | draft_writer_agent; revision_coach_agent | FULL checkpoint: content frozen. No further review loop permitted. |
| **4.5 FINAL INTEGRITY** | `academic-pipeline` (gate) | VERIFIED_ONLY | Updated Material Passport (`verification_status: VERIFIED`) + `repro_lock` populated | integrity_verification_agent (Mode 2 — deeper than 2.5); state_tracker_agent | **MANDATORY gate. Zero-tolerance; no skip permitted** (unlike 2.5). Mode 2 is deeper than Mode 1. ANY issue → fix + re-verify. `repro_lock.stochasticity_declaration` required verbatim if populated. |
| **5. FINALIZE** | `academic-paper` (format-convert) | VERIFIED_ONLY | Publication-ready MD; DOCX (Pandoc, if available); LaTeX (user confirms); PDF (tectonic); AI Disclosure Statement (venue-specific) | formatter_agent; disclosure_agent | **MANDATORY checkpoint:** user selects format before render. Disclosure statement must match venue (ICLR / NeurIPS / Nature / Science / ACL / EMNLP). |
| **6. PROCESS SUMMARY** | `academic-pipeline` | VERIFIED_ONLY | Paper Creation Process Record (MD + PDF); AI Self-Reflection Report (concession rate, sycophancy risk, health alerts); Score trajectory visualization | state_tracker_agent; pipeline_orchestrator_agent | Language confirmed with user. Collaboration quality evaluated. Post-publication audit report (if peer-review published). |

## 3. Data Access Level Flow (v3.3.2+)

```mermaid
flowchart LR
    User[User input<br/>web / PDFs / queries]
    Raw[deep-research<br/>data_access_level: raw]
    Red[academic-paper<br/>data_access_level: redacted]
    Ver1[academic-paper-reviewer<br/>data_access_level: verified_only]
    Ver2[academic-pipeline<br/>data_access_level: verified_only]

    User --> Raw
    Raw -- source_verification elevates --> Red
    Red -- Gate 2.5: 7-mode integrity --> Ver1
    Red -- Gate 2.5 --> Ver2
    Ver2 -. orchestrates .-> Raw
    Ver2 -. orchestrates .-> Red
    Ver2 -. orchestrates .-> Ver1

    classDef raw fill:#fff1f0,stroke:#cf1322
    classDef red fill:#fffbe6,stroke:#d48806
    classDef ver fill:#f6ffed,stroke:#389e0d
    class Raw raw
    class Red red
    class Ver1,Ver2 ver
```

Rules (from `shared/ground_truth_isolation_pattern.md`):
- `raw` skills consume layer-1 data (arbitrary, possibly adversarial)
- `redacted` skills operate on sanitized material, no new raw ingestion
- `verified_only` skills run only after upstream integrity gates
- No skill ever reads ground-truth / rubrics / gold labels within the same process as producing a response

## 4. Skill Dependency Graph

```mermaid
graph TD
    Pipeline[academic-pipeline<br/>orchestrator<br/>v3.2.2]
    DR[deep-research<br/>13 agents<br/>v2.8.2]
    AP[academic-paper<br/>12 agents<br/>v3.0.2]
    APR[academic-paper-reviewer<br/>5 reviewers + DA<br/>v1.8.2]
    Shared[shared/<br/>handoff_schemas.md<br/>ground_truth_isolation<br/>benchmark_report<br/>artifact_reproducibility<br/>cross_model_verification<br/>mode_spectrum<br/>style_calibration]

    Pipeline --> DR
    Pipeline --> AP
    Pipeline --> APR
    DR -. "RQ Brief + Bibliography + Synthesis" .-> AP
    AP -. "Complete manuscript" .-> APR
    APR -. "Revision Roadmap" .-> AP
    DR --- Shared
    AP --- Shared
    APR --- Shared
    Pipeline --- Shared

    classDef orch fill:#f0f5ff,stroke:#2f54eb,stroke-width:2px
    classDef skill fill:#e6f4ff,stroke:#1677ff
    classDef shared fill:#f5f5f5,stroke:#595959,stroke-dasharray:5 5
    class Pipeline orch
    class DR,AP,APR skill
    class Shared shared
```

## 5. Quality Gates

| Gate | Stage | What blocks advancement | Failure handling |
|---|---|---|---|
| S2 API verification | 1 | Citation not in Semantic Scholar; title Levenshtein < 0.70 | Flag; user decides to drop or re-cite |
| Anti-leakage (v3.3) | 2 | Draft contains parametric fill not grounded in session materials | `[MATERIAL GAP]` tag; user provides material or accepts gap |
| VLM figure verify (v3.3) | 2 | Rendered figure fails 10-pt APA 7.0 checklist | Max 2 refinement iterations |
| Stage 2.5 integrity | 2.5 | Any of 7-mode AI failure checklist | Fix + re-verify; max 3 rounds |
| Concession threshold | 3 | DA rebuttal scored < 4/5 by responder | No concession; frame-lock detector runs |
| Stage 4.5 final integrity | 4.5 | ANY issue on Mode 2 deep check | ZERO-tolerance; no skip; fix + re-verify |
| Disclosure check | 5 | Venue-specific AI disclosure absent or wrong form | Block render until fixed |
| `repro_lock` (v3.3.5) | 4.5 | Missing key, missing `stochasticity_declaration`, or invalid `hash_timing` | Lint fails; CI errors |
| `benchmark_report` (v3.3.5, external) | — | Publishing a benchmark without honest disclosure | Users run `check_benchmark_report.py` before publishing |

## 6. v3.3.x Evolution Timeline

```mermaid
timeline
    title ARS v3.3.x incremental additions
    v3.3 : Semantic Scholar API verification
         : Anti-leakage protocol
         : VLM figure verification
         : Score trajectory tracking
         : Stage 2 parallelization
    v3.3.1 : Public contract drift fixes
           : check_spec_consistency.py
    v3.3.2 : data_access_level frontmatter
           : task_type frontmatter
           : shared/ground_truth_isolation_pattern.md
    v3.3.3 : Lint hardening (missing closing fence, non-mapping frontmatter)
           : Broken link fixes
    v3.3.4 : README changelog summaries sync
           : CI validation of embedded changelog
    v3.3.5 : benchmark_report.schema.json
           : repro_lock on Material Passport
           : requirements-dev.txt (pyyaml + jsonschema≥4.17)
```

## 7. Skill Modes

| Skill | Modes |
|---|---|
| `deep-research` | full, quick, socratic, review, lit-review, fact-check, systematic-review (7) |
| `academic-paper` | full, plan, outline-only, revision, revision-coach, abstract-only, lit-review, format-convert, citation-check, disclosure (10) |
| `academic-paper-reviewer` | full, re-review, quick, methodology-focus, guided, calibration (6) |
| `academic-pipeline` | (orchestrator — delegates to sub-skill modes; no standalone modes) |

## How to read

- **Flow diagram** (§1): macro view — which stage follows which, where loops exist, where gates block.
- **Matrix** (§2): the only place where (stage × skill × mode × data_level × artifacts × agents × gate) all co-exist. Use this when asking "what happens at Stage X?"
- **Data access flow** (§3) and **skill graph** (§4): orthogonal views answering "who sees what" and "who depends on what" respectively.
- **Quality gates** (§5): zoom on the blocking checks. Crucial for understanding failure modes.
- **Timeline** (§6): why the architecture looks the way it does — each v3.3.x release added one honesty primitive.
- **Modes** (§7): reference when composing a pipeline invocation.

The matrix alone is insufficient: it hides data-access hierarchy and skill dependency. The diagrams alone are insufficient: they hide artifact flow and per-stage agent detail. Together they are the full architecture.
