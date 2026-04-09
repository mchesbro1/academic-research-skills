# Experiment Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone Claude Code skill that executes/monitors experiments (code and human studies), interprets statistics, and verifies reproducibility — independently usable and optionally integrable with ARS pipeline.

**Architecture:** Single SKILL.md routes to 2 agents (code_runner_agent, study_manager_agent) via intent detection. 5 reference files provide detailed protocols. Output uses Markdown-based structured format compatible with ARS Material Passport (Schema 9). validate mode handles statistical interpretation inline in SKILL.md; reproducibility re-runs delegate to code_runner_agent.

**Tech Stack:** Claude Code skill (Markdown), no executable code. All files are `.md` instruction files for LLM consumption.

**Spec:** `docs/superpowers/specs/2026-04-09-experiment-agent-design.md`

**Working directory:** `/Users/imbad/Projects/HEEACT/academic-research-skills/experiment-agent/`

---

## File Map

| File | Responsibility | Created/Modified |
|------|---------------|-----------------|
| `SKILL.md` | Core skill: frontmatter, trigger keywords, 4 modes, routing, validate mode logic, plan mode logic, quality standards, safety rules | Create |
| `agents/code_runner_agent.md` | PARSE→EXECUTE→MONITOR→DECIDE→COLLECT loop for code experiments | Create |
| `agents/study_manager_agent.md` | PLAN→ETHICS→TRACK→COLLECT loop for human studies | Create |
| `references/stall_detection_protocol.md` | Monitoring thresholds and anomaly detection rules | Create |
| `references/irb_ethics_checklist.md` | IRB/ethics review checklist for human studies | Create |
| `references/statistical_interpretation_guide.md` | Statistical interpretation + 11-type fallacy scan | Create |
| `references/reproducibility_protocol.md` | Re-run comparison methodology | Create |
| `references/ars_integration_guide.md` | ARS handoff format + Material Passport + pipeline bridging | Create |
| `templates/code_experiment_plan.md` | Template for code experiment planning | Create |
| `templates/study_protocol.md` | Template for human study protocol | Create |
| `.claude/CLAUDE.md` | Repo-level skill description and routing rules | Create |
| `README.md` | English README | Create (overwrite default) |
| `README.zh-TW.md` | Traditional Chinese README | Create |
| `CHANGELOG.md` | Version history | Create |
| `LICENSE` | CC-BY-NC 4.0 | Create |

---

### Task 1: SKILL.md — Core Skill File

**Files:**
- Create: `SKILL.md`

This is the main file loaded into LLM context. Must be lean (~200 lines). Detailed protocols go to references/.

- [ ] **Step 1: Write SKILL.md with frontmatter, trigger, modes, routing, validate logic, plan logic, safety rules**

```markdown
---
name: experiment-agent
description: "Experiment executor and monitor for academic research. 2-agent system covering code experiments (ML training, statistical analysis, ETL, simulation) and human studies (surveys, field studies, interviews). 4 modes: run (execute + monitor code), manage (track human studies), validate (statistical interpretation + reproducibility verification), plan (Socratic experiment design). Triggers on: run experiment, execute code, train model, benchmark, manage study, track participants, field study, survey, validate results, check statistics, reproduce, plan experiment, design study, 跑實驗, 執行程式, 管理研究, 驗證結果, 規劃實驗."
metadata:
  version: "1.0"
  last_updated: "2026-04-09"
  author: "Cheng-I Wu"
  license: "CC-BY-NC 4.0"
  status: active
  related_skills:
    - academic-pipeline
    - deep-research
    - academic-paper
    - academic-paper-reviewer
---

# Experiment Agent v1.0 — Experiment Executor and Monitor

Execute, monitor, interpret, and verify experiments for academic research. Works independently or as an optional bridge between ARS Stage 1 (RESEARCH) and Stage 2 (WRITE).

**Role**: Executor + Monitor. This skill does NOT judge whether results are good for a paper (that is the reviewer's job). It ensures experiments complete successfully, interprets statistical output, and verifies reproducibility.

## Quick Start

**Run a code experiment:**
```
Run my training script: python train.py --epochs 50 --output results/
```

**Manage a human study:**
```
Help me manage my survey study — I need 200 responses by May 30
```

**Validate results:**
```
Validate these regression results: results/analysis_output.csv
```

**Plan an experiment:**
```
Help me design an experiment to test whether AI tools improve QA officer productivity
```

---

## Trigger Keywords

**English**: run experiment, execute code, train model, benchmark, analyze data, manage study, track participants, field study, survey, validate results, check statistics, reproduce, re-run, plan experiment, design study, what should I test

**Chinese**: 跑實驗, 執行程式, 訓練模型, 基準測試, 分析資料, 管理研究, 追蹤參與者, 田野研究, 問卷, 驗證結果, 檢查統計, 重現, 規劃實驗, 設計研究

---

## Modes

| Mode | Purpose | Agent | Spectrum |
|------|---------|-------|----------|
| `run` | Execute code experiments + real-time monitoring | code_runner_agent | Fidelity |
| `manage` | Manage human study workflow + progress tracking | study_manager_agent | Balanced |
| `validate` | Statistical interpretation + reproducibility verification | SKILL.md (stats) + code_runner_agent (re-run) | Fidelity |
| `plan` | Socratic dialogue to design experiments | SKILL.md direct | Originality |

## Mode Selection

| User Signal | Mode |
|-------------|------|
| Has a script/command to run | `run` |
| Running a survey, interview, field study, lab experiment | `manage` |
| Has results, wants to check numbers or reproduce | `validate` |
| Wants to figure out what experiment to do | `plan` |

---

## Routing Logic

1. Detect intent from user's first message using trigger keywords
2. If code execution keywords → dispatch `code_runner_agent` (run mode)
3. If human study keywords → dispatch `study_manager_agent` (manage mode)
4. If validation keywords → enter validate mode (handled inline, see below)
5. If design keywords → enter plan mode (handled inline, see below)
6. If ambiguous → ask user: "Are you running code or managing a human study?"

---

## validate Mode (Inline)

Two capabilities: **statistical interpretation** and **reproducibility verification**. Accepts results from any source (this agent's run/manage modes, external files, ARS pipeline output).

### Procedure

1. **DETECT** — Scan user-provided files for statistical content (p-values, CIs, effect sizes, coefficients, test statistics). Structured formats (CSV/JSON) auto-parsed; unstructured formats require user guidance.

2. **INTERPRET** — Item-by-item analysis. See `references/statistical_interpretation_guide.md` for full protocol covering: significance, effect size classification, CI assessment, assumption verification, multiple comparison correction.

3. **FALLACY SCAN** — Check 11 known statistical fallacy patterns across three categories. See `references/statistical_interpretation_guide.md` for the full checklist.

   | Category | Fallacies |
   |----------|-----------|
   | Structural (data) | Simpson's Paradox, Ecological Fallacy, Berkson's Paradox, Collider Bias |
   | Inferential (interpretation) | Base Rate Neglect, Regression to the Mean, Survivorship Bias, Look-Elsewhere Effect, Garden of Forking Paths |
   | Causal (claims) | Correlation != Causation, Reverse Causality |

   Severity: `RED_FLAG` (results may be invalid) / `CAUTION` (needs conditions) / `NOTE` (worth noting)

4. **REPRODUCE** (optional, code experiments only) — If user provides executable command + original results, delegate to code_runner_agent for re-run, then compare. See `references/reproducibility_protocol.md`. Not applicable to human studies.

5. **REPORT** — Produce validation report in Markdown structured format (see Output Formats below).

**Scope boundary**: validate mode describes what numbers say and flags potential fallacies. It does NOT make editorial recommendations about what to write in the paper — that is the ARS reviewer's job.

---

## plan Mode (Inline)

Socratic dialogue to help users design experiments before running them.

### Procedure

1. **Clarify RQ** — What are you trying to test? What is the hypothesis?
2. **Variables** — Identify IV, DV, control variables, potential confounds
3. **Design** — Experimental / quasi-experimental / observational / mixed methods?
4. **Method selection** — Based on RQ + design, suggest appropriate methods
5. **Sample** — Population, sampling strategy, power analysis for sample size
6. **Analysis strategy** — Which statistical tests? What are the assumptions?
7. **Produce plan** — Output a structured experiment plan using `templates/code_experiment_plan.md` or `templates/study_protocol.md`

One question at a time. Multiple choice preferred. If user brings ARS Stage 1 output (RQ Brief, Methodology Blueprint), parse section headings and pre-populate steps 1-4.

---

## Output Formats

All outputs use **Markdown-based structured format** with Material Passport for ARS compatibility.

### Experiment Result (from run mode)

```markdown
## Material Passport

- Origin Skill: experiment-agent
- Origin Mode: run
- Origin Date: [ISO 8601]
- Verification Status: UNVERIFIED
- Version Label: exp_result_v1

## Experiment Result

- **ID**: [unique id]
- **Type**: [training | analysis | etl | simulation | generic]
- **Status**: [completed | crashed | timeout | stopped_by_user]
- **Command**: [executed command]
- **Working Directory**: [path]
- **Duration**: [seconds]
- **Exit Code**: [int]

### Output Files

| File | Size |
|------|------|
| [path] | [size] |

### Output Summary

[Auto-generated summary of structured output, if available]

### Anomalies Detected

[List of anomalies detected during monitoring, or "None"]
```

### Study Status (from manage mode)

```markdown
## Material Passport

- Origin Skill: experiment-agent
- Origin Mode: manage
- Origin Date: [ISO 8601]
- Verification Status: UNVERIFIED
- Version Label: study_status_v1

## Study Status

- **ID**: [unique id]
- **Type**: [survey | experiment | field_study | interview | mixed]
- **Phase**: [planning | ethics_review | collecting | collected | paused]
- **Design**: [description]
- **Progress**: [current_n] / [target_n] ([completion_rate]%)
- **Timeline**: [start] to [expected_end] — [on_track | behind | ahead]

### Ethics Status

- **Status**: [READY | NEEDS_REVIEW | BLOCKED]
- **Blocked Items**: [list or "None"]

### Risks

[List of detected risks with suggestions, or "None"]

### Data Readiness

- **Samples**: [n]
- **Missing Rate**: [rate]
- **Format Consistent**: [yes/no]
- **Ready for Analysis**: [yes/no]
- **Blockers**: [list or "None"]
```

### Validation Report (from validate mode)

```markdown
## Material Passport

- Origin Skill: experiment-agent
- Origin Mode: validate
- Origin Date: [ISO 8601]
- Verification Status: VERIFIED
- Version Label: validation_v1

## Validation Report

- **Source**: [exp_id | external | manual_study]
- **Overall Confidence**: [SOLID | CAUTION | RED_FLAG]

### Statistical Findings

| Metric | Test | Value | Effect Size | Confidence |
|--------|------|-------|-------------|------------|
| [name] | [test] | [stat, p] | [size, class] | [SOLID/CAUTION/RED_FLAG] |

### Warnings

| Type | Detail | Affected |
|------|--------|----------|
| [type] | [detail] | [metrics] |

### Fallacy Scan

- **Coverage**: [N]/11 fallacy types checked

| Fallacy | Severity | Detail | Recommendation |
|---------|----------|--------|----------------|
| [type] | [RED_FLAG/CAUTION/NOTE] | [detail] | [suggestion] |

### Reproducibility (if applicable)

- **Method**: [re-run with same seed | re-run stochastic | N/A]
- **Verdict**: [REPRODUCIBLE | PARTIALLY_REPRODUCIBLE | NOT_REPRODUCIBLE | N/A — human study]

| Metric | Original | Re-run | Diff | Status |
|--------|----------|--------|------|--------|
| [name] | [value] | [value] | [diff] | [MATCH/WITHIN_TOLERANCE/MISMATCH] |
```

---

## Quality Standards

| Standard | Requirement |
|----------|-------------|
| Monitoring coverage | Every code experiment must have at least process-alive + timeout monitoring |
| Statistical rigor | All 11 fallacy types must be checked in validate mode; coverage reported |
| Reproducibility | Deterministic experiments: exact match required. Stochastic: < 5% relative diff default |
| ARS compatibility | All outputs include Material Passport with required fields per ARS Schema 9 |
| User sovereignty | All anomaly detections are ADVISORY; only hard timeout auto-kills |

---

## Safety Rules

| # | Rule |
|---|------|
| 1 | Only execute user-specified commands — never auto-generate or modify scripts |
| 2 | Never auto-retry crashed experiments — notify user, user decides |
| 3 | Never auto-kill except hard timeout — notify before kill |
| 4 | Monitor only user-specified output paths |
| 5 | Never upload data to external services |
| 6 | Never touch raw participant data — track metadata only (counts, rates) |
| 7 | Never send notifications to study participants |
| 8 | Power analysis uses conservative estimates |
| 9 | Statistical interpretation is descriptive — does not draw conclusions for user |
| 10 | RED_FLAG means "needs user attention", not "result is wrong" |

---

## Anti-Patterns

| # | Anti-Pattern | Why It's Wrong |
|---|-------------|---------------|
| 1 | Auto-modifying user's experiment code | Violates safety rule 1; user owns their code |
| 2 | Silently retrying a crashed run | Masks the real error; wastes compute |
| 3 | Reporting p < .05 as "the result is significant" without effect size | Statistical significance without practical significance is misleading |
| 4 | Skipping fallacy scan because "results look clean" | Fallacies are invisible without systematic checking |
| 5 | Making editorial recommendations in validate mode | That's the reviewer's job, not ours |

---

## Reference Files

| File | Purpose |
|------|---------|
| `references/stall_detection_protocol.md` | Monitoring thresholds, anomaly types, detection logic |
| `references/irb_ethics_checklist.md` | Human study ethics review checklist |
| `references/statistical_interpretation_guide.md` | Full statistical interpretation + 11-type fallacy scan protocol |
| `references/reproducibility_protocol.md` | Re-run methodology, comparison thresholds, verdict criteria |
| `references/ars_integration_guide.md` | ARS Material Passport, handoff format, pipeline bridging |

---

## ARS Integration (Optional)

This skill works independently. When used with ARS:

- **Consuming ARS output**: Recognizes ARS Stage 1 section headings (`## Research Question Brief`, `## Methodology Blueprint`) to pre-populate plan/manage modes
- **Producing ARS-compatible output**: All outputs carry Material Passport (Schema 9). Users bring results to ARS Stage 2 manually.
- **ARS requires zero modification**: No new pipeline stages, no dependencies. The user is the bridge.

See `references/ars_integration_guide.md` for details.

---

*Experiment Agent v1.0 | 2026-04-09 | CC-BY-NC 4.0 | Cheng-I Wu*
```

- [ ] **Step 2: Verify line count is under 250**

Run: `wc -l SKILL.md`
Expected: ~230 lines

- [ ] **Step 3: Commit**

```bash
git add SKILL.md
git commit -m "feat: add SKILL.md — core skill with 4 modes, routing, output formats, safety rules"
```

---

### Task 2: code_runner_agent.md

**Files:**
- Create: `agents/code_runner_agent.md`

- [ ] **Step 1: Write code_runner_agent.md**

```markdown
# Code Runner Agent — Experiment Executor and Monitor

## Role Definition

You execute and monitor code-based experiments. Your job is to run user-specified commands, watch for problems in real-time, and collect results when done. You cover any experiment that runs as a process: ML training, statistical analysis, data processing, simulation, benchmarks.

**You do not judge results.** You ensure experiments complete and report what happened. Quality assessment is the reviewer's job.

---

## Core Loop

### 1. PARSE — Understand the Experiment

Before executing anything, extract from the user's request:

| Field | Required | Description |
|-------|----------|-------------|
| `command` | Yes | Exact command to run (e.g., `python train.py --epochs 50`) |
| `working_dir` | Yes | Directory to run in (default: current directory) |
| `expected_outputs` | No | Files the experiment should produce |
| `success_criteria` | No | How to know it worked (e.g., "exit code 0", "output file > 0 bytes") |
| `timeout` | No | Max duration before kill (default: 30 minutes) |
| `monitor_files` | No | Files to watch for progress (e.g., log files) |
| `experiment_type` | No | Override auto-detection (see below) |

**Auto-detect experiment type** from command and file patterns:

| Type | Signals | Monitoring Strategy |
|------|---------|-------------------|
| `training` | pytorch, tensorflow, keras, epoch, --lr, --batch | Loss/metric plateau detection |
| `analysis` | Rscript, statsmodels, scipy, --output table/figure | Intermediate output count |
| `etl` | pandas, spark, dbt, clean, transform, --input --output | Row count progress |
| `simulation` | monte carlo, bootstrap, --iterations, --n-sims | Iteration count vs total |
| `generic` | None of the above | Conservative: process alive + output growth only |

If auto-detection is uncertain, ask the user. User can always override.

### 2. EXECUTE — Start the Process

1. Confirm the command with the user: "I'm about to run: `[command]` in `[dir]`. Proceed?"
2. Start via Bash tool in background mode
3. Record: start timestamp, PID, initial RSS memory
4. Set timeout timer

### 3. MONITOR — Watch for Problems

Run monitoring checks every 30 seconds (configurable). See `references/stall_detection_protocol.md` for full threshold definitions.

**Universal checks (all experiment types):**

| Check | Condition | Action |
|-------|-----------|--------|
| Process alive | PID no longer running + exit code != 0 | → CRASHED |
| Process alive | PID no longer running + exit code == 0 | → COMPLETED |
| Output stall | Monitored files unchanged for 3 consecutive checks (90s) | → STALL_SUSPECTED (ADVISORY) |
| Resource anomaly | RSS memory > 3x initial | → RESOURCE_ALERT (ADVISORY) |
| Hard timeout | Duration exceeds timeout | → Kill process, report |

**Type-specific checks (only if user provided log path/format):**

| Check | Applies To | Condition | Action |
|-------|-----------|-----------|--------|
| Metric plateau | training | Last K steps metric change < 0.1% | ADVISORY: suggest early stop |
| Slow progress | etl, simulation | Progress < 50% expected rate | ADVISORY: show ETA |

All detections except hard timeout are **ADVISORY** — notify user with options (continue / kill / adjust), never auto-act.

### 4. DECIDE — Handle Anomalies

When an anomaly is detected, present to user:

```
⚠️ [ANOMALY_TYPE] detected at check #[N] ([elapsed time])

Detail: [specific observation]

Options:
A. Continue monitoring (ignore this alert)
B. Kill the process
C. Adjust timeout / thresholds
D. [Type-specific suggestion, e.g., "Try early stopping"]
```

Wait for user response. If user doesn't respond within 2 checks, repeat the alert once. After that, continue silently (do not spam).

### 5. COLLECT — Gather Results

After the process ends (any reason):

1. Collect exit code and final stderr (last 50 lines)
2. List all files in expected output paths with sizes
3. If output is structured (CSV/JSON/parquet): produce summary stats (row count, column names, basic descriptives)
4. Compile `experiment_result` in Markdown format (see SKILL.md Output Formats)
5. Suggest: "Results collected. Run `validate` mode to check statistical integrity?"

---

## Safety Rules

1. **Never modify the user's command** — execute exactly as given
2. **Never auto-retry** — if it crashes, report and let user decide
3. **Never auto-kill** — only hard timeout kills. Always notify first.
4. **Never read files outside declared scope** — only monitor what user specified
5. **Confirm before execution** — always show the command and ask for go-ahead

---

## Integration Points

- **From plan mode**: receives structured experiment plan → auto-populates PARSE fields
- **From validate mode**: called for reproducibility re-runs → runs same command, returns new results for comparison
- **To validate mode**: after COLLECT, prompts user to validate

---

*Code Runner Agent v1.0 | experiment-agent*
```

- [ ] **Step 2: Commit**

```bash
git add agents/code_runner_agent.md
git commit -m "feat: add code_runner_agent — PARSE/EXECUTE/MONITOR/DECIDE/COLLECT loop"
```

---

### Task 3: study_manager_agent.md

**Files:**
- Create: `agents/study_manager_agent.md`

- [ ] **Step 1: Write study_manager_agent.md**

```markdown
# Study Manager Agent — Human Study Workflow Manager

## Role Definition

You manage experiments that humans execute — surveys, field studies, lab experiments, interviews, focus groups, observational studies. You do not run these experiments (people do). You: plan protocols, check ethics, track data collection progress, and confirm data readiness.

**You do not judge result quality.** You ensure the study process is complete and properly documented. Statistical interpretation is validate mode's job; paper quality is the reviewer's job.

---

## Core Loop

### 1. PLAN — Build Research Protocol

Help the user design their study protocol. One question at a time, multiple choice preferred.

**Step sequence:**

| Step | Question | Output |
|------|----------|--------|
| 1 | What are you trying to find out? (RQ + hypothesis) | Research question, directional/non-directional hypothesis |
| 2 | What is your research design? (A. Experimental / B. Quasi-experimental / C. Observational / D. Mixed methods) | Design type |
| 3 | What are your variables? | IV, DV, control variables, potential confounds |
| 4 | Who are your participants? (Population, sampling) | Target population, sampling strategy |
| 5 | How many participants? | Power analysis recommendation (conservative: err toward more) |
| 6 | What instruments will you use? | Questionnaire, scale, interview guide (existing or to-develop) |
| 7 | What is your data collection timeline? | Start date, phases, end date, milestones |
| 8 | How will you analyze the data? | Statistical tests, assumptions, fallback methods |

**If user brings ARS Stage 1 output**: detect `## Research Question Brief` and `## Methodology Blueprint` headings. Pre-populate steps 1-4, confirm with user, continue from step 5.

**Output**: Structured protocol using `templates/study_protocol.md`.

### 2. ETHICS — IRB/Ethics Review Checklist

Run `references/irb_ethics_checklist.md` — a structured checklist covering:

| Category | Key Items |
|----------|-----------|
| Informed consent | Written consent? Age-appropriate? Language accessible? |
| Privacy & anonymity | Data anonymized? Storage location secure? Retention period defined? |
| Risk assessment | Physical/psychological/social risk to participants? Risk mitigation? |
| Vulnerable populations | Minors? Prisoners? Patients? Power differential? |
| Data handling | Who has access? How is data transmitted? Backup plan? |
| Institutional requirements | IRB/ethics committee approval needed? Status? |

**Output**: `ethics_status`
- `READY` — All items checked, no blockers
- `NEEDS_REVIEW` — Some items need institutional review (e.g., IRB submission pending)
- `BLOCKED` — Critical items unresolved (e.g., no consent form, vulnerable population without protocol)

`BLOCKED` items must be resolved before moving to TRACK. This is a hard gate.

### 3. TRACK — Monitor Data Collection

The user reports progress; the agent tracks and detects risks.

**What user reports:**
- Collection counts ("got 45 responses", "3 interviews done")
- Timeline updates ("delayed 1 week due to holidays")
- Quality issues ("20% missing on question 7")

**What agent does:**

| Input | Agent Response |
|-------|---------------|
| Count update | Update progress, calculate completion rate, estimate time remaining |
| Low response rate (< 50% of target at midpoint) | Flag risk, suggest: reminder, incentive, extend deadline, adjust target |
| Behind schedule | Recalculate timeline, suggest rescheduling |
| High missing rate (> 15% on any variable) | Flag risk, suggest: check instrument wording, add follow-up, plan imputation strategy |
| Quality concern | Document, suggest mitigation |

### 4. COLLECT — Confirm Data Readiness

When user reports collection is complete:

| Check | Criterion | Status |
|-------|-----------|--------|
| Sample size | current_n >= target_n | PASS / FAIL |
| Missing data | missing_rate <= 15% overall | PASS / WARN |
| Format | All data files in consistent format | PASS / FAIL |
| Timeline | Collection within planned window | PASS / LATE |

**Output**: `study_status` in Markdown format (see SKILL.md Output Formats) + `data_readiness` section.

If all checks PASS: "Data is ready for analysis. You can analyze manually or use `run` mode to execute your analysis script."

If any FAIL: list blockers, suggest actions.

---

## Safety Rules

1. **Never make ethics judgments** — present checklist, user answers, agent records. The agent is not an IRB.
2. **Never touch raw participant data** — only track metadata (counts, rates, completion percentages)
3. **Never contact participants** — no emails, no reminders, no recruitment messages
4. **Conservative power analysis** — when calculating sample size, use conservative effect size estimates. Better to suggest more participants than fewer.
5. **BLOCKED ethics status is a hard gate** — cannot proceed to TRACK until resolved

---

## Integration Points

- **From plan mode**: receives experiment design → auto-enters PLAN step with pre-populated fields
- **From ARS Stage 1**: recognizes RQ Brief + Methodology Blueprint headings → pre-populates PLAN steps 1-4
- **To validate mode**: after COLLECT, if user has analysis output, prompt to validate
- **To run mode**: if user needs to run analysis scripts on collected data, hand off to code_runner_agent

---

*Study Manager Agent v1.0 | experiment-agent*
```

- [ ] **Step 2: Commit**

```bash
git add agents/study_manager_agent.md
git commit -m "feat: add study_manager_agent — PLAN/ETHICS/TRACK/COLLECT for human studies"
```

---

### Task 4: Reference Files (all 5)

**Files:**
- Create: `references/stall_detection_protocol.md`
- Create: `references/irb_ethics_checklist.md`
- Create: `references/statistical_interpretation_guide.md`
- Create: `references/reproducibility_protocol.md`
- Create: `references/ars_integration_guide.md`

- [ ] **Step 1: Write stall_detection_protocol.md**

```markdown
# Stall Detection Protocol

Defines monitoring thresholds for code_runner_agent. All thresholds are user-overridable.

## Detection Types

### OUTPUT_STALL

- **What**: Monitored output files have not changed in size
- **Default threshold**: 3 consecutive checks (90 seconds at 30s interval)
- **Override**: User sets `stall_tolerance` (number of checks)
- **Exception**: Long-running single computations (e.g., large matrix operations) produce no intermediate output. If user warns "this takes a while", increase tolerance to 10 checks (5 min).
- **Action**: ADVISORY — notify user, suggest continue/kill/adjust

### METRIC_PLATEAU (training type only)

- **What**: Primary metric has stopped improving
- **Prerequisite**: User specifies `metric_file` (path to log) and `metric_key` (column/field name)
- **Default threshold**: Last 10 data points change < 0.1% relative
- **Override**: User sets `plateau_window` (data points) and `plateau_threshold` (relative change)
- **Action**: ADVISORY — show metric trend, suggest early stopping

### RESOURCE_ANOMALY

- **What**: Memory usage growing unexpectedly
- **Detection**: RSS memory via `ps aux` exceeds 3x the value recorded at process start
- **Override**: User sets `memory_multiplier_limit`
- **Action**: ADVISORY — possible memory leak, suggest investigation

### SLOW_PROGRESS (etl and simulation types)

- **What**: Experiment progressing slower than expected
- **Prerequisite**: User specifies expected total units (rows, iterations) and log format
- **Default threshold**: Actual rate < 50% of expected rate (calculated from first 10% of progress)
- **Override**: User sets `progress_rate_threshold`
- **Action**: ADVISORY — show current rate, revised ETA

### HARD_TIMEOUT

- **What**: Experiment has exceeded maximum allowed duration
- **Default**: 30 minutes
- **Override**: User sets `timeout` at PARSE step
- **Action**: MANDATORY — kill process (SIGTERM, then SIGKILL after 10s), collect stderr, report

## Check Interval

- Default: every 30 seconds
- Override: User sets `check_interval_seconds`
- Minimum: 10 seconds (to avoid excessive polling overhead)
- Maximum: 300 seconds (5 minutes — longer gaps risk missing transient failures)

## Alert Behavior

- First detection: full alert with options (continue / kill / adjust)
- Same anomaly persists after user chooses "continue": silent for 2 checks, then one reminder
- After reminder: silent until anomaly resolves or escalates
- Different anomaly: always full alert regardless of prior alerts
```

- [ ] **Step 2: Write irb_ethics_checklist.md**

```markdown
# IRB/Ethics Review Checklist

Structured checklist for study_manager_agent ETHICS phase. Agent presents each item, user answers, agent records status.

## Instructions

- Present one category at a time
- For each item, record: PASS / NEEDS_ACTION / NOT_APPLICABLE
- Any NEEDS_ACTION in categories 1-3 → ethics_status: BLOCKED
- Any NEEDS_ACTION in categories 4-6 → ethics_status: NEEDS_REVIEW
- All PASS or NOT_APPLICABLE → ethics_status: READY

---

## Category 1: Informed Consent (CRITICAL)

| # | Item | Check |
|---|------|-------|
| 1.1 | Written informed consent form prepared | Required for all studies involving human participants |
| 1.2 | Consent form in participant-accessible language | No jargon; translated if needed |
| 1.3 | Consent form describes: purpose, procedures, duration | Must be explicit |
| 1.4 | Consent form describes: risks and benefits | Even if minimal risk |
| 1.5 | Consent form states: voluntary participation, right to withdraw | Must be unconditional |
| 1.6 | Consent form states: data handling and confidentiality | How data will be stored, who has access |
| 1.7 | For online studies: digital consent mechanism | Click-through or e-signature |
| 1.8 | For minors (< 18): parental consent + child assent | Both required |

## Category 2: Privacy and Data Protection (CRITICAL)

| # | Item | Check |
|---|------|-------|
| 2.1 | Data anonymized or pseudonymized | Direct identifiers removed or coded |
| 2.2 | Secure storage location defined | Encrypted drive, institutional server, not personal cloud |
| 2.3 | Data retention period defined | How long kept, when destroyed |
| 2.4 | Access control specified | Who can access raw data, under what conditions |
| 2.5 | Data transfer method secure | Encrypted transmission if sent electronically |
| 2.6 | Compliance with local data protection laws | GDPR, PDPA, or local equivalent |

## Category 3: Risk Assessment (CRITICAL)

| # | Item | Check |
|---|------|-------|
| 3.1 | Physical risks assessed | Any physical procedure or environmental exposure |
| 3.2 | Psychological risks assessed | Sensitive topics, stress, discomfort |
| 3.3 | Social risks assessed | Stigma, discrimination, professional consequences |
| 3.4 | Risk mitigation plan documented | For each identified risk |
| 3.5 | Debriefing protocol (if deception used) | Must explain deception and provide support |
| 3.6 | Support resources available | Counseling, hotline, or referral for distressed participants |

## Category 4: Vulnerable Populations

| # | Item | Check |
|---|------|-------|
| 4.1 | Minors: additional protections in place | Age-appropriate materials, parental consent |
| 4.2 | Prisoners/detainees: no coercion | Voluntary participation genuinely free |
| 4.3 | Patients: therapeutic misconception addressed | Clear that research ≠ treatment |
| 4.4 | Students/employees: power differential mitigated | Cannot affect grades/employment |
| 4.5 | Cognitively impaired: capacity assessment | Legally authorized representative if needed |

## Category 5: Institutional Requirements

| # | Item | Check |
|---|------|-------|
| 5.1 | IRB/ethics committee approval status | Approved / Submitted / Not yet submitted / Exempt |
| 5.2 | Protocol registration (if required) | ClinicalTrials.gov, OSF, or other registry |
| 5.3 | Funding agency requirements met | Some funders have additional ethics requirements |

## Category 6: Data Management Plan

| # | Item | Check |
|---|------|-------|
| 6.1 | Data collection instruments validated | Reliability/validity evidence for scales |
| 6.2 | Data cleaning plan documented | How missing data, outliers will be handled |
| 6.3 | Analysis plan pre-specified | Prevent post-hoc fishing |
| 6.4 | Data sharing plan | Will anonymized data be shared? Under what terms? |
```

- [ ] **Step 3: Write statistical_interpretation_guide.md**

```markdown
# Statistical Interpretation Guide

Full protocol for validate mode's statistical interpretation and fallacy scan.

## Part 1: Statistical Interpretation

### Step 1: Detect Statistical Content

Scan user-provided output for these patterns:
- p-values: `p = 0.023`, `p < .001`, `p > .05`
- Confidence intervals: `95% CI [0.12, 0.45]`, `CI: 0.12-0.45`
- Effect sizes: `d = 0.47`, `eta-squared = .036`, `r = .31`, `OR = 2.4`
- Test statistics: `t(98) = 2.34`, `F(2, 97) = 1.82`, `chi2(4) = 12.3`
- Coefficients: `beta = 0.23`, `B = 1.45`, `SE = 0.12`

If structured format (CSV/JSON): auto-extract column names matching these patterns.
If unstructured: ask user to highlight key numbers.

### Step 2: Interpret Each Finding

For each statistical result, assess:

**Significance:**
- Report exact p-value (not just "significant" or "not significant")
- Flag if p is borderline (.04-.05): "marginal significance — interpret with caution"
- Flag if many tests run without correction: "N tests without multiple comparison correction"

**Effect Size:**
| Measure | Small | Medium | Large |
|---------|-------|--------|-------|
| Cohen's d | 0.2 | 0.5 | 0.8 |
| eta-squared | .01 | .06 | .14 |
| r (correlation) | .10 | .30 | .50 |
| Odds Ratio | 1.5 | 2.5 | 4.3 |

- Always report: "statistically significant with [small/medium/large] effect"
- Warn if significant but small effect: "statistically significant but practically small — consider whether this difference matters in context"

**Confidence Interval:**
- Does CI include 0 (or 1 for OR)? → result is not significant regardless of p-value
- Width: narrow CI = precise estimate; wide CI = uncertain estimate
- Asymmetric CI around point estimate → possible skewness

**Assumption Checks:**
| Test | Assumption | Red Flag |
|------|-----------|----------|
| t-test | Normality | n < 30 per group and no normality test reported |
| t-test | Equal variance | No Levene's test and group sizes differ > 2:1 |
| ANOVA | Normality + homogeneity | Same as t-test; additionally check sphericity for RM |
| Chi-squared | Expected frequencies >= 5 | Any cell < 5 → use Fisher's exact |
| Regression | Linearity, normality of residuals, homoscedasticity | No diagnostic plots reported |
| Correlation | Both variables continuous, linearity | Pearson used on ordinal data |

**Multiple Comparisons:**
- Count total number of statistical tests in the analysis
- If > 3 tests and no correction reported:
  - Suggest Bonferroni (conservative): adjusted alpha = .05 / N
  - Suggest Benjamini-Hochberg FDR (less conservative): for exploratory analyses
  - Report: which results survive correction, which don't

### Step 3: Assign Confidence Level

| Level | Criteria |
|-------|---------|
| `SOLID` | Significant with medium+ effect size, assumptions met, no fallacies detected |
| `CAUTION` | One or more: borderline p, small effect, unchecked assumptions, uncorrected comparisons |
| `RED_FLAG` | Multiple issues: non-significant reframed as trend, violated assumptions, detected fallacy |

---

## Part 2: Fallacy Scan (11 Types)

Check ALL 11 types for every validation. Report coverage in output ("11/11 checked").

### Structural Fallacies (Data Level)

**1. Simpson's Paradox**
- **What**: Overall trend reverses when data is split by a grouping variable
- **Detection**: If analysis has grouping variables (gender, department, site), compare aggregated result direction vs per-group direction
- **When to suspect**: Aggregate shows negative relationship but subgroups are all positive (or vice versa)
- **Severity if found**: RED_FLAG
- **Reporting note**: describe what numbers say (overall vs per-group), do NOT recommend which to report — that is an editorial decision for the reviewer

**2. Ecological Fallacy**
- **What**: Inferring individual-level relationships from group-level data
- **Detection**: Unit of analysis (e.g., schools, countries) differs from unit of inference (e.g., students, citizens)
- **When to suspect**: Regression on aggregated data used to make claims about individuals
- **Severity if found**: RED_FLAG

**3. Berkson's Paradox**
- **What**: Selection/sampling bias creates spurious negative correlation
- **Detection**: Sample drawn from a filtered population (only hospitalized patients, only admitted students, only published papers)
- **When to suspect**: Two seemingly unrelated variables show unexpected negative correlation in a selected sample
- **Severity if found**: CAUTION

**4. Collider Bias**
- **What**: Controlling for a variable that is a common effect of both IV and DV creates spurious association
- **Detection**: Check if any control variable could be caused by both IV and DV
- **When to suspect**: Adding a control variable changes the sign or significance of the main effect
- **Severity if found**: CAUTION

### Inferential Fallacies (Interpretation Level)

**5. Base Rate Neglect**
- **What**: Reporting sensitivity/specificity without considering prevalence
- **Detection**: Results present conditional probabilities (PPV, NPV, sensitivity, specificity) without base rate
- **When to suspect**: Screening or diagnostic accuracy studies
- **Severity if found**: CAUTION

**6. Regression to the Mean**
- **What**: Extreme values naturally move toward the mean on re-measurement
- **Detection**: Pre-post design where groups were selected based on extreme scores (lowest performers, highest risk)
- **When to suspect**: "Improvement" in the worst-performing group without a control group
- **Severity if found**: RED_FLAG if no control group; CAUTION if control group exists but not compared

**7. Survivorship Bias**
- **What**: Analyzing only "survivors" (those who completed, stayed, succeeded)
- **Detection**: Dropout/attrition rate > 15%; no intention-to-treat analysis; no dropout comparison
- **When to suspect**: Longitudinal studies, intervention studies, cohort studies
- **Severity if found**: CAUTION if dropout documented; RED_FLAG if dropout not reported

**8. Look-Elsewhere Effect**
- **What**: Testing many variables and reporting only the significant ones
- **Detection**: Ratio of (reported significant results) to (total tests run) is suspiciously high
- **When to suspect**: Exploratory analysis with many DVs; "we also found..." language
- **Severity if found**: CAUTION

**9. Garden of Forking Paths**
- **What**: Many researcher degrees of freedom (outlier removal criteria, variable transformations, model specifications) but only one path reported
- **Detection**: No pre-registration; analysis described only in final form; no robustness checks
- **When to suspect**: Complex analyses with many decision points
- **Severity if found**: NOTE if exploratory; CAUTION if presented as confirmatory

### Causal Fallacies (Claim Level)

**10. Correlation != Causation**
- **What**: Observational study uses causal language
- **Detection**: Study design is cross-sectional, correlational, or observational, but language includes "caused", "led to", "resulted in", "improved", "reduced"
- **When to suspect**: Always check in non-experimental designs
- **Severity if found**: CAUTION
- **Reporting note**: flag the specific causal language; suggest associational alternatives ("was associated with", "correlated with")

**11. Reverse Causality**
- **What**: The assumed direction of causation may be backwards
- **Detection**: Cross-sectional data with directional claims; no temporal precedence established
- **When to suspect**: "X predicts Y" in cross-sectional design (maybe Y causes X)
- **Severity if found**: CAUTION

---

## Output Template

See SKILL.md "Validation Report" output format for the Markdown template.
```

- [ ] **Step 4: Write reproducibility_protocol.md**

```markdown
# Reproducibility Protocol

Defines how validate mode verifies reproducibility of code experiments by re-running and comparing.

## Applicability

- **Applicable**: Any experiment with an executable command and recorded original results
- **Not applicable**: Human studies, external API calls with non-deterministic responses, hardware-dependent benchmarks
- If not applicable, skip reproducibility verification and report: "Reproducibility: N/A — [reason]"

## Procedure

### Step 1: Classify Experiment Determinism

| Type | Criteria | Expected Outcome |
|------|----------|-----------------|
| **Deterministic** | Same seed, same data, same code, same environment | Exact match required |
| **Stochastic** | Random elements (different seed, dropout, data augmentation) | Statistical equivalence |
| **Environment-sensitive** | Results depend on hardware, OS, or library version | Document environment, allow wider tolerance |

Ask user: "Is this experiment deterministic (same seed/data → same result) or stochastic (involves randomness)?"

### Step 2: Re-Run

1. Delegate to code_runner_agent with the same command and working directory
2. code_runner_agent runs full EXECUTE → MONITOR → COLLECT cycle
3. Collect new experiment_result

### Step 3: Compare

**Deterministic comparison:**
- For each numeric metric: `abs(original - rerun)` must be exactly 0
- For output files: byte-for-byte comparison (`diff` or hash)
- Any difference = `MISMATCH`

**Stochastic comparison:**
- For each numeric metric: `abs(original - rerun) / original` must be < threshold
- Default threshold: 5% relative difference
- User can override with `reproducibility_threshold`
- For distributions: compare summary statistics (mean, std, min, max)

**File comparison:**
- Size within 10% tolerance (stochastic outputs may vary)
- Structure match (same columns, same row count for CSV)
- Content: spot-check first/last 5 rows

### Step 4: Verdict

| Verdict | Criteria |
|---------|---------|
| `REPRODUCIBLE` | All metrics within tolerance; all output files match |
| `PARTIALLY_REPRODUCIBLE` | Some metrics match, some don't; or files differ in non-critical ways |
| `NOT_REPRODUCIBLE` | Significant differences in primary metrics |

## Tolerance Defaults

| Comparison | Deterministic | Stochastic |
|-----------|--------------|------------|
| Numeric metrics | Exact (0 diff) | < 5% relative |
| Output file size | Exact | < 10% |
| Output file content | Byte-for-byte | Structure + spot check |
| Timing metrics | Not compared (always varies) | Not compared |

## Edge Cases

- **Missing original results**: Cannot compare → report "Reproducibility: CANNOT_VERIFY — original results not provided"
- **Environment changed**: Warn "environment may differ from original run — results may not match even if code is correct"
- **Partial output**: If original has 5 output files but re-run produces 4 → `PARTIALLY_REPRODUCIBLE` + flag missing file
```

- [ ] **Step 5: Write ars_integration_guide.md**

```markdown
# ARS Integration Guide

How experiment-agent works with ARS (Academic Research Skills) pipeline. This file lives in experiment-agent repo. ARS requires zero modification.

## Principle

```
experiment-agent ──knows──> ARS handoff format
ARS ──does not know──> experiment-agent
User ──bridges──> between the two
```

## Reading ARS Stage 1 Output

When a user brings ARS Stage 1 (RESEARCH) output to experiment-agent, detect these section headings:

| Heading | Maps To |
|---------|---------|
| `## Research Question Brief` | plan mode step 1 (RQ + hypothesis), manage mode PLAN step 1 |
| `## Methodology Blueprint` | plan mode steps 2-4 (variables, design, methods), manage mode PLAN steps 2-4 |
| `## Annotated Bibliography` | Reference context (do not depend on; experiment-agent does not do lit review) |
| `## Synthesis Report` | Background context for experiment design |

**Detection method**: Loose heading matching. Do not depend on ARS schema version numbers. If headings are present, parse. If not, ask user for context.

## Producing ARS-Compatible Output

All experiment-agent outputs include a **Material Passport** header (ARS Schema 9):

```markdown
## Material Passport

- Origin Skill: experiment-agent
- Origin Mode: [run | manage | validate | plan]
- Origin Date: [ISO 8601 timestamp]
- Verification Status: [UNVERIFIED | VERIFIED]
- Version Label: [exp_result_v1 | study_status_v1 | validation_v1]
```

**Verification Status rules:**
- `run` mode output → `UNVERIFIED` (results not yet validated)
- `manage` mode output → `UNVERIFIED` (data collected but not analyzed)
- `validate` mode output → `VERIFIED` (has been through statistical interpretation + optional reproducibility check)
- After validate mode processes a run/manage output, the original output's passport can be updated to `VERIFIED`

**Optional fields** (include when available):
- `Integrity Pass Date`: timestamp when validate mode completed
- `Upstream Dependencies`: version labels of artifacts this one depends on (e.g., if experiment used ARS Stage 1 RQ Brief)

## User Workflow: ARS → experiment-agent → ARS

```
1. User runs ARS Stage 1 (deep-research) → gets RQ Brief + Methodology Blueprint
2. User copies relevant sections to experiment-agent
3. experiment-agent: plan mode → run/manage mode → validate mode → produces results
4. User copies experiment_result / validation_report back to ARS
5. User starts ARS Stage 2 (academic-paper) with experiment results as input
6. ARS Stage 2 writer sees Material Passport → knows origin and verification status
```

The user is the bridge. No API calls, no automated handoff, no shared state.

## Future ARS Integration (Not v1)

If ARS ever wants to auto-detect experiment-agent output:

```
At Stage 2 start:
  if user input contains "## Material Passport" with "Origin Skill: experiment-agent":
    → auto-load experiment results as Stage 2 source material
    → skip "do you have experiment data?" question
  else:
    → normal flow
```

This requires a one-line detection in ARS pipeline_orchestrator_agent. Not implemented in v1 — documented here for future reference.
```

- [ ] **Step 6: Commit all 5 reference files**

```bash
git add references/
git commit -m "feat: add 5 reference files — stall detection, IRB checklist, stats guide, reproducibility, ARS integration"
```

---

### Task 5: Templates

**Files:**
- Create: `templates/code_experiment_plan.md`
- Create: `templates/study_protocol.md`

- [ ] **Step 1: Write code_experiment_plan.md**

```markdown
# Code Experiment Plan

## Experiment Overview

- **Title**: [descriptive name]
- **Objective**: [what this experiment tests]
- **Hypothesis**: [expected outcome, if any]
- **Type**: [training | analysis | etl | simulation | generic]

## Setup

- **Language/Framework**: [e.g., Python 3.11, PyTorch 2.x]
- **Entry Command**: `[exact command to run]`
- **Working Directory**: `[path]`
- **Dependencies**: [list or "see requirements.txt"]
- **Environment**: [OS, GPU, memory requirements if relevant]

## Inputs

| Input | Path | Description |
|-------|------|-------------|
| [name] | [path] | [what it is] |

## Expected Outputs

| Output | Path | Format | Success Criterion |
|--------|------|--------|------------------|
| [name] | [path] | [CSV/JSON/model/figure] | [e.g., "file exists and > 0 bytes"] |

## Monitoring Configuration

- **Timeout**: [duration, default 30 min]
- **Monitor files**: [paths to watch for progress]
- **Experiment type override**: [if auto-detection should be overridden]
- **Metric file**: [path to loss/metric log, if applicable]
- **Metric key**: [column/field name, if applicable]

## Analysis Plan

- **Primary metric**: [what to look at first]
- **Success threshold**: [e.g., "accuracy > 0.90", "p < .05"]
- **Comparison**: [baseline, previous run, theoretical expectation]
```

- [ ] **Step 2: Write study_protocol.md**

```markdown
# Study Protocol

## Study Overview

- **Title**: [descriptive name]
- **Research Question**: [primary RQ]
- **Hypothesis**: [directional or non-directional]
- **Design**: [experimental | quasi-experimental | observational | mixed]
- **Type**: [survey | experiment | field_study | interview | mixed]

## Participants

- **Target Population**: [who]
- **Sampling Strategy**: [random | stratified | convenience | purposive | snowball]
- **Target Sample Size**: [N] (based on power analysis: [parameters used])
- **Inclusion Criteria**: [list]
- **Exclusion Criteria**: [list]

## Variables

| Role | Variable | Measurement | Scale |
|------|----------|-------------|-------|
| IV | [name] | [how measured] | [nominal/ordinal/interval/ratio] |
| DV | [name] | [how measured] | [nominal/ordinal/interval/ratio] |
| Control | [name] | [how measured] | [nominal/ordinal/interval/ratio] |
| Confound | [name] | [how addressed] | — |

## Instruments

| Instrument | Purpose | Source | Reliability |
|-----------|---------|--------|-------------|
| [name] | [what it measures] | [original author / self-developed] | [Cronbach's alpha, if known] |

## Data Collection

| Phase | Timeline | Activity | Responsible |
|-------|----------|----------|-------------|
| 1 | [dates] | [what happens] | [who] |
| 2 | [dates] | [what happens] | [who] |

## Analysis Strategy

| RQ/Hypothesis | Statistical Test | Assumptions | Fallback |
|--------------|-----------------|-------------|----------|
| [RQ1] | [e.g., independent t-test] | [normality, equal variance] | [Mann-Whitney U if assumptions violated] |

## Ethics

- **IRB Status**: [approved | submitted | pending | exempt]
- **Consent Method**: [written | digital | verbal]
- **Data Anonymization**: [method]
- **Data Storage**: [location, encryption, access control]
- **Retention Period**: [duration]
```

- [ ] **Step 3: Commit**

```bash
git add templates/
git commit -m "feat: add experiment plan and study protocol templates"
```

---

### Task 6: Supporting Files

**Files:**
- Create: `.claude/CLAUDE.md`
- Overwrite: `README.md`
- Create: `README.zh-TW.md`
- Create: `CHANGELOG.md`
- Create: `LICENSE`

- [ ] **Step 1: Write .claude/CLAUDE.md**

```markdown
# Experiment Agent

A Claude Code skill for experiment execution, monitoring, statistical interpretation, and reproducibility verification.

## Skill Overview

| Skill | Purpose | Key Modes |
|-------|---------|-----------|
| `experiment-agent` v1.0 | Execute + monitor experiments | run, manage, validate, plan |

## Routing Rules

1. **run vs manage**: run = code experiments (scripts, training, analysis). manage = human studies (surveys, interviews, field work). If unclear, ask user.
2. **validate**: Works on results from any source — this agent's outputs, external files, or ARS pipeline data. Does statistical interpretation + optional reproducibility re-run.
3. **plan**: Socratic dialogue to design experiments before running them. If user brings ARS Stage 1 output, pre-populates from RQ Brief and Methodology Blueprint.

## ARS Integration

- This skill works independently. No ARS dependency.
- When used with ARS: all outputs include Material Passport (Schema 9) for compatibility.
- ARS requires zero modification. The user bridges manually.

## Key Rules

- All anomaly detections are ADVISORY (user decides)
- Only execute user-specified commands
- Never auto-retry, never auto-kill (except hard timeout)
- Statistical interpretation is descriptive, not editorial
- Ethics checklist items are hard gates for human studies

## Version Info
- **Version**: 1.0
- **Last Updated**: 2026-04-09
- **Author**: Cheng-I Wu
- **License**: CC-BY-NC 4.0
```

- [ ] **Step 2: Write README.md**

```markdown
# Experiment Agent

![Version](https://img.shields.io/badge/version-1.0-blue)
![License](https://img.shields.io/badge/license-CC--BY--NC--4.0-green)

A Claude Code skill for executing, monitoring, interpreting, and verifying experiments in academic research.

## What It Does

- **Runs code experiments** — executes scripts (Python, R, etc.), monitors for stalls/crashes in real-time, collects results
- **Manages human studies** — plans protocols, checks IRB ethics, tracks data collection progress
- **Interprets statistics** — reads p-values, effect sizes, CIs; checks 11 types of statistical fallacies (Simpson's Paradox, survivorship bias, etc.)
- **Verifies reproducibility** — re-runs experiments and compares results

## Why It Exists

Lu et al. (2026, *Nature*) demonstrated an Experiment Progress Manager for autonomous AI research. This skill brings the same execute-and-monitor capability to human-in-the-loop academic workflows — without the risks of full automation.

## Modes

| Mode | What It Does |
|------|-------------|
| `run` | Execute code + monitor process |
| `manage` | Plan + track human studies |
| `validate` | Statistical interpretation + reproducibility check |
| `plan` | Socratic dialogue to design experiments |

## Quick Start

1. Clone this repo into your project or `.claude/skills/`
2. Start a Claude Code session
3. Try: "Run my analysis: `Rscript analysis.R`"

## ARS Compatibility

This skill works independently. It also integrates optionally with [Academic Research Skills (ARS)](https://github.com/Imbad0202/academic-research-skills):

- Reads ARS Stage 1 output (RQ Brief, Methodology Blueprint) to pre-populate experiment design
- Produces Material Passport-compatible output for ARS Stage 2 consumption
- ARS requires zero modification — the user bridges manually

## Safety

- Only executes commands you specify — never auto-generates or modifies your code
- Never auto-retries crashed experiments
- Never touches raw participant data
- Statistical interpretation describes, never concludes
- Full list: see SKILL.md Safety Rules

## License

CC-BY-NC 4.0

## Author

Cheng-I Wu

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md)
```

- [ ] **Step 3: Write README.zh-TW.md**

```markdown
# 實驗代理人 (Experiment Agent)

![Version](https://img.shields.io/badge/version-1.0-blue)
![License](https://img.shields.io/badge/license-CC--BY--NC--4.0-green)

Claude Code 技能：執行、監控、解讀、驗證學術研究實驗。

## 功能

- **執行程式碼實驗** — 執行腳本（Python、R 等），即時監控 stall/crash，收集結果
- **管理人工研究** — 規劃 protocol、檢查 IRB 倫理、追蹤資料收集進度
- **統計解讀** — 解讀 p-value、效果量、信賴區間；檢查 11 種統計謬誤（Simpson's Paradox、存活者偏誤等）
- **驗證重現性** — 重新執行實驗並比對結果

## 為什麼需要

Lu et al.（2026, *Nature*）展示了自主 AI 研究的實驗進度管理器。本技能將同樣的執行與監控能力帶入人類參與的學術工作流程——不承擔全自動化的風險。

## 模式

| 模式 | 功能 |
|------|------|
| `run` | 執行程式碼 + 監控 process |
| `manage` | 規劃 + 追蹤人工研究 |
| `validate` | 統計解讀 + 重現性驗證 |
| `plan` | Socratic 對話設計實驗 |

## 快速開始

1. Clone 本 repo 到你的專案或 `.claude/skills/`
2. 啟動 Claude Code session
3. 試試：「跑我的分析：`Rscript analysis.R`」

## ARS 相容性

本技能可獨立使用，也可選擇性整合 [Academic Research Skills (ARS)](https://github.com/Imbad0202/academic-research-skills)：

- 讀取 ARS Stage 1 輸出（RQ Brief、Methodology Blueprint）預填實驗設計
- 產出符合 Material Passport 的輸出供 ARS Stage 2 使用
- ARS 不需要任何修改——使用者手動銜接

## 安全機制

- 只執行你指定的命令——從不自動生成或修改你的程式碼
- 從不自動重試 crash 的實驗
- 從不接觸原始參與者資料
- 統計解讀是描述性的，不代替你下結論
- 完整清單見 SKILL.md 安全規則

## 授權

CC-BY-NC 4.0

## 作者

吳承翊 (Cheng-I Wu)

---

## 變更紀錄

見 [CHANGELOG.md](CHANGELOG.md)
```

- [ ] **Step 4: Write CHANGELOG.md**

```markdown
# Changelog

## v1.0 (2026-04-09)

### Initial Release

**New Skill: experiment-agent**

- 4 modes: `run` (code experiments), `manage` (human studies), `validate` (statistical interpretation + reproducibility), `plan` (Socratic experiment design)
- 2 agents: `code_runner_agent` (execute + monitor), `study_manager_agent` (plan + track)
- 5 reference protocols: stall detection, IRB ethics checklist, statistical interpretation (11-type fallacy scan), reproducibility verification, ARS integration guide
- 2 templates: code experiment plan, study protocol
- ARS-compatible Material Passport output (Schema 9)
- Independent operation + optional ARS pipeline integration (zero ARS modification)
- Source: Lu et al. (2026, *Nature* 651:914-919) Experiment Progress Manager concept

**Design decisions:**
- Executor + Monitor role only (no quality review — that's ARS reviewer's job)
- All anomaly detections are ADVISORY (user decides, except hard timeout)
- Statistical interpretation is descriptive (flags issues, does not make editorial recommendations)
- validate mode scope boundary: describes what numbers say, does not judge paper quality
- Single-direction ARS dependency: experiment-agent knows ARS format, ARS does not know experiment-agent
```

- [ ] **Step 5: Write LICENSE**

```
Creative Commons Attribution-NonCommercial 4.0 International

Copyright (c) 2026 Cheng-I Wu

This work is licensed under the Creative Commons Attribution-NonCommercial 4.0
International License. To view a copy of this license, visit
http://creativecommons.org/licenses/by-nc/4.0/ or send a letter to Creative
Commons, PO Box 1866, Mountain View, CA 94042, USA.
```

- [ ] **Step 6: Commit all supporting files**

```bash
git add .claude/CLAUDE.md README.md README.zh-TW.md CHANGELOG.md LICENSE
git commit -m "feat: add CLAUDE.md, README (EN/zh-TW), CHANGELOG, LICENSE"
```

---

### Task 7: Final Review and Push

- [ ] **Step 1: Verify repo structure**

```bash
find . -not -path './.git/*' -type f | sort
```

Expected:
```
./.claude/CLAUDE.md
./agents/code_runner_agent.md
./agents/study_manager_agent.md
./CHANGELOG.md
./LICENSE
./README.md
./README.zh-TW.md
./references/ars_integration_guide.md
./references/irb_ethics_checklist.md
./references/reproducibility_protocol.md
./references/stall_detection_protocol.md
./references/statistical_interpretation_guide.md
./SKILL.md
./templates/code_experiment_plan.md
./templates/study_protocol.md
```

Total: 14 files (excluding .git)

- [ ] **Step 2: Verify SKILL.md line count**

```bash
wc -l SKILL.md
```

Expected: ~230 lines (under 250 target)

- [ ] **Step 3: Cross-check all internal references**

Verify every file referenced in SKILL.md exists:
```bash
grep -oP 'references/\S+\.md|templates/\S+\.md' SKILL.md | sort -u | while read f; do [ -f "$f" ] && echo "OK: $f" || echo "MISSING: $f"; done
```

- [ ] **Step 4: Push to GitHub**

```bash
git push origin main
```

- [ ] **Step 5: Verify on GitHub**

```bash
gh repo view imbad0202/experiment-agent --web
```
