# Experiment Agent — Design Spec

**Date**: 2026-04-09
**Author**: Cheng-I Wu + Claude
**Status**: Approved — ready for implementation
**Repo**: `experiment-agent` (private, independent from ARS)
**License**: CC-BY-NC 4.0

---

## 1. Problem Statement

ARS (Academic Research Skills) covers research, writing, and review — but assumes the user runs experiments themselves and brings results back. Lu et al. (2026, Nature 651:914-919) demonstrated an Experiment Progress Manager that executes and monitors ML experiments autonomously. ARS needs a similar capability, but:

1. It must not break the existing ARS pipeline (zero-modification principle)
2. It must work independently of ARS (standalone experiment tool)
3. It must handle both code-driven experiments (ML training, statistical analysis, simulation) and human-driven studies (surveys, field studies, interviews)

## 2. Solution

A standalone Claude Code skill (`experiment-agent`) that serves as an **Executor + Monitor** for experiments. It does NOT review/judge result quality (that's ARS reviewer's job). It ensures experiments run to completion, monitors for problems, interprets statistical output, and verifies reproducibility.

### Relationship to ARS

```
Independent mode:
  User → experiment-agent → results

Pipeline mode:
  ARS Stage 1 (RQ Brief + Methodology) → User → experiment-agent → results → User → ARS Stage 2 (WRITE)
```

- **Single-direction dependency**: experiment-agent knows ARS handoff format; ARS does not know experiment-agent exists
- **ARS zero modification**: no new stages, no hard dependencies, no code changes to ARS
- **Glue is the user**: the user manually bridges between ARS and experiment-agent

## 3. Architecture

### Repo Structure

```
experiment-agent/
├── .claude/
│   └── CLAUDE.md
├── SKILL.md
├── agents/
│   ├── code_runner_agent.md
│   └── study_manager_agent.md
├── references/
│   ├── stall_detection_protocol.md
│   ├── irb_ethics_checklist.md
│   ├── statistical_interpretation_guide.md
│   ├── reproducibility_protocol.md
│   └── ars_integration_guide.md
├── templates/
│   ├── code_experiment_plan.md
│   └── study_protocol.md
├── README.md
├── README.zh-TW.md
├── CHANGELOG.md
└── LICENSE
```

### 4 Modes

| Mode | Purpose | Trigger Keywords | Agent | Spectrum |
|------|---------|-----------------|-------|----------|
| `run` | Execute code experiments + monitor | run experiment, execute, train, benchmark, analyze | code_runner_agent | Fidelity |
| `manage` | Manage human study workflow + track progress | manage study, track participants, field study, survey | study_manager_agent | Balanced |
| `validate` | Statistical interpretation + reproducibility verification | validate results, check statistics, reproduce, re-run | code_runner_agent (re-run) + SKILL.md (stats) | Fidelity |
| `plan` | Socratic dialogue to design experiments | plan experiment, design study, what should I test | SKILL.md direct | Originality |

### Routing Logic

```
User input → SKILL.md intent detection
  ├─ Code keywords ("run", "script", "train", "benchmark") → code_runner_agent (run mode)
  ├─ Study keywords ("study", "survey", "participants", "IRB") → study_manager_agent (manage mode)
  ├─ Validation keywords ("validate", "check results", "reproduce") → validate mode
  └─ Design keywords ("plan", "design", "what should I test") → plan mode (SKILL.md handles directly)
```

## 4. code_runner_agent

### Role

Execute any "has a script/command, needs to wait for results" experiment. Monitor in real-time. Detect anomalies. Collect results. Covers: ML training, statistical analysis, ETL, simulation, benchmarks, and anything else that runs as a process.

### Core Loop

```
1. PARSE — Parse experiment plan
   ├─ Identify: language/framework, entry command, expected outputs, success criteria, timeout
   ├─ Auto-detect experiment type (affects monitoring strategy):
   │   ├─ training — epoch/step loop, loss/metric log
   │   ├─ analysis — statistical script, expected tables/figures/report
   │   ├─ etl — data processing, expected cleaned dataset
   │   ├─ simulation — multi-iteration, expected distribution/summary
   │   └─ generic — unclassifiable, use most conservative monitoring
   └─ User can override auto-detection

2. EXECUTE — Run via Bash tool
   ├─ Start process (background mode)
   ├─ Set timeout guard (user-specified or default 30 min)
   └─ Record start timestamp + PID

3. MONITOR — Select strategy by experiment type
   Universal (all types):
   ├─ Process alive check
   ├─ Output file growth (new output = progress)
   ├─ Resource usage (RSS memory, disk)
   └─ Hard timeout guard

   Type-specific (optional, requires user-provided log path/format):
   ├─ training: loss/metric trend, plateau detection
   ├─ analysis: intermediate output count vs expected
   ├─ etl: row count progress (if logged)
   └─ simulation: iteration count vs total

4. DECIDE — On anomaly (all ADVISORY, user decides)
   ├─ STALL_SUSPECTED → notify user, suggest: continue / kill / adjust
   ├─ PLATEAU_DETECTED → notify + metric trend, suggest early stop
   ├─ CRASHED → collect stderr/log, diagnose, suggest fix
   ├─ RESOURCE_ANOMALY → notify, suggest investigation
   └─ TIMEOUT → kill process, report last state

5. COLLECT — After experiment ends (normal or abnormal)
   ├─ Collect all output files
   ├─ If structured output (CSV/JSON/parquet) → summary statistics
   ├─ Produce experiment_result object
   └─ Prompt user to enter validate mode
```

### Monitoring Strategy Table

| Detection Type | Applies To | Default Threshold | Action |
|---------------|-----------|-------------------|--------|
| `PROCESS_DEAD` | all | exit code != 0 | Collect stderr, diagnose, notify |
| `OUTPUT_STALL` | all | 3 consecutive checks (90s) no new output | ADVISORY |
| `RESOURCE_ANOMALY` | all | RSS > 3x initial | ADVISORY |
| `HARD_TIMEOUT` | all | user-set (default 30 min) | Kill, report |
| `METRIC_PLATEAU` | training | last K steps change < 0.1% | ADVISORY |
| `SLOW_PROGRESS` | etl, simulation | progress < 50% expected rate | ADVISORY |

### Output Format

```yaml
experiment_result:
  id: "exp_001"
  type: "training" | "analysis" | "etl" | "simulation" | "generic"
  status: "completed" | "crashed" | "timeout" | "stopped_by_user"
  command: "python train.py --epochs 50"
  working_dir: "/Users/user/project"
  duration_seconds: 342
  exit_code: 0
  output_files:
    - path: "results/model.pt"
      size_bytes: 48293012
    - path: "results/training_log.csv"
      size_bytes: 15234
  output_summary:
    type: "csv_stats"
    rows: 50000
    columns: ["epoch", "loss", "accuracy"]
    highlights: "final accuracy: 0.971, min loss: 0.023"
  anomalies_detected:
    - type: "METRIC_PLATEAU"
      at_check: 8
      detail: "accuracy unchanged for 10 epochs at 0.968"
      user_action: "continued"
  stderr_tail: "..."
```

## 5. study_manager_agent

### Role

Manage experiments not executed by code — surveys, field studies, lab experiments, interviews, focus groups. The agent does not run the experiment (humans do). It: plans protocols, tracks progress, manages data collection status, ensures process completeness.

### Core Loop

```
1. PLAN — Build research protocol
   ├─ From user's RQ/hypothesis (or from ARS Stage 1 output)
   ├─ Produce structured protocol:
   │   ├─ Research design (experimental / quasi-experimental / observational / mixed)
   │   ├─ Participants: population, sampling strategy, sample size (power analysis)
   │   ├─ Variables: IV / DV / control / confound
   │   ├─ Instruments: questionnaire/scale/interview guide
   │   ├─ Data collection procedure: timeline, steps, responsible persons
   │   └─ Analysis strategy: planned statistical methods + fallback
   └─ Output: study_protocol (using templates/study_protocol.md)

2. ETHICS — IRB / ethics review checklist
   ├─ Run references/irb_ethics_checklist.md
   ├─ Check each item: informed consent, anonymity, data storage, vulnerable populations
   ├─ Produce ethics_status: READY / NEEDS_REVIEW / BLOCKED
   └─ BLOCKED items must be resolved before TRACK

3. TRACK — Track data collection progress
   ├─ User reports collection status ("collected 45/100", "second round interviews done")
   ├─ Agent updates progress, calculates completion rate, estimates remaining time
   ├─ Detect risks:
   │   ├─ Low response rate → suggest follow-up strategies or sample adjustment
   │   ├─ Behind schedule → rescheduling suggestions
   │   └─ Data quality issues (user reports excessive missing values) → suggest handling
   └─ Produce progress_report

4. COLLECT — Data collection complete
   ├─ Confirm all planned data has arrived
   ├─ Checklist: sample size met? missing rate? format consistency?
   ├─ Produce data_readiness_report
   └─ Prompt user: ready for analysis (manual or use run mode for scripts)
```

### Output Format

```yaml
study_status:
  id: "study_001"
  type: "survey" | "experiment" | "field_study" | "interview" | "mixed"
  phase: "planning" | "ethics_review" | "collecting" | "collected" | "paused"
  protocol:
    design: "quasi-experimental pre-post with control group"
    target_n: 100
    current_n: 45
    completion_rate: 0.45
    instruments: ["SERVQUAL adapted", "semi-structured interview guide"]
    timeline:
      start: "2026-04-15"
      expected_end: "2026-05-30"
      actual_progress: "on track" | "behind" | "ahead"
  ethics:
    status: "READY" | "NEEDS_REVIEW" | "BLOCKED"
    blocked_items: []
  risks:
    - type: "LOW_RESPONSE_RATE"
      detail: "45/100 after 3 weeks, need 100 by May 30"
      suggestion: "Send reminder + extend deadline 1 week"
  data_readiness:
    samples_collected: 45
    missing_rate: 0.03
    format_consistent: true
    ready_for_analysis: false
    blockers: ["target_n not reached"]
```

## 6. validate mode

### Role

Two jobs: **statistical interpretation** and **reproducibility verification**. Does not judge whether results are good for the paper (that's ARS reviewer's job). Only answers: "are these numbers trustworthy?"

### Input Sources

- experiment_result from run mode
- data_readiness_report from manage mode + user's analysis output
- Any external result files (CSV, JSON, log, images) brought by the user
- Data produced mid-ARS-pipeline (user manually feeds in)

### 6A. Statistical Interpretation

```
1. DETECT — Identify statistical content in results
   ├─ Scan output files for: p-value, CI, effect size, coefficients, F/t/chi2
   ├─ Structured format (CSV/JSON) → auto parse
   └─ Unstructured (log/text/image) → ask user to point out key numbers

2. INTERPRET — Item-by-item interpretation
   ├─ p-value:
   │   ├─ Report significance level (p < .05 / .01 / .001)
   │   ├─ Warn p-hacking indicators (many comparisons uncorrected, p just below .05)
   │   └─ Suggest: Bonferroni / FDR correction needed?
   ├─ Effect size:
   │   ├─ Classify magnitude (Cohen's d: small/medium/large; eta-squared likewise)
   │   └─ Warn "statistically significant but trivial effect size"
   ├─ Confidence interval:
   │   ├─ Width reasonableness (CI crosses 0? too wide for practical significance?)
   │   └─ Consistency check with p-value
   ├─ Assumption checks:
   │   ├─ Normality (t-test with n < 30 and no normality check?)
   │   ├─ Homogeneity of variance (Levene's test done?)
   │   └─ Independence (repeated measures analyzed with independent test?)
   └─ Multiple comparisons:
       ├─ Count: how many tests were run?
       └─ If > 3 and uncorrected → warn

3. FALLACY SCAN — Check for known statistical fallacy patterns

   Structural fallacies (data level):
   ├─ Simpson's Paradox
   │   Detection: overall trend opposite to subgroup trends
   │   Method: if grouping variables exist, compare aggregated vs per-group direction
   ├─ Ecological Fallacy
   │   Detection: group-level data used to infer individual behavior
   │   Method: unit of analysis = unit of inference?
   ├─ Berkson's Paradox
   │   Detection: selection bias creates spurious negative correlation
   │   Method: was sample filtered/truncated?
   └─ Collider Bias
       Detection: controlling for a collider creates spurious association
       Method: could any control variable be a joint effect of IV and DV?

   Inferential fallacies (interpretation level):
   ├─ Base Rate Neglect
   │   Detection: conditional probability reported without base rate
   ├─ Regression to the Mean
   │   Detection: extreme group "improves" in pre-post design
   ├─ Survivorship Bias
   │   Detection: only "surviving" samples analyzed; dropout > 15%?
   ├─ Look-Elsewhere Effect
   │   Detection: cherry-picking significant results from many variables
   └─ Garden of Forking Paths
       Detection: multiple researcher degrees of freedom, only one path reported

   Causal fallacies (claim level):
   ├─ Correlation != Causation
   │   Detection: observational study using causal language
   └─ Reverse Causality
       Detection: cross-sectional data with directional claims

   Severity levels:
   - RED_FLAG: results may be entirely invalid
   - CAUTION: results need additional conditions to hold
   - NOTE: worth noting but not necessarily problematic

4. REPORT — Produce statistical interpretation summary
   Format: item-by-item findings + confidence level (SOLID / CAUTION / RED_FLAG)
   Include fallacy scan results with severity
```

### 6B. Reproducibility Verification

```
1. Prerequisite: user provides executable command + original results
   (If human study or non-rerunnable → skip, do statistical interpretation only)

2. RE-RUN
   ├─ Use code_runner_agent to re-execute same command
   └─ Collect new results

3. COMPARE
   ├─ Deterministic algorithm (same seed) → expect exact match, any diff = RED_FLAG
   ├─ Stochastic algorithm (different seed) → compare distributions, allow statistical variance
   ├─ Threshold: user-configurable, default relative diff < 5%
   ├─ File comparison: size, structure
   └─ List all non-reproducible items

4. VERDICT
   ├─ REPRODUCIBLE — re-run within tolerance
   ├─ PARTIALLY_REPRODUCIBLE — some results match, some don't
   └─ NOT_REPRODUCIBLE — significant differences, investigation needed
```

### validate mode Output Format

```yaml
validation_report:
  id: "val_001"
  source: "exp_001" | "external" | "manual_study"
  
  statistical_interpretation:
    findings:
      - metric: "treatment effect on satisfaction score"
        test: "independent t-test"
        value: "t(98) = 2.34, p = .021, d = 0.47"
        significance: "p < .05"
        effect_size: "medium (Cohen's d = 0.47)"
        confidence: "SOLID"
        notes: null
      - metric: "interaction effect"
        test: "two-way ANOVA"
        value: "F(2, 97) = 1.82, p = .048"
        significance: "p < .05 (marginal)"
        effect_size: "small (eta-sq = .036)"
        confidence: "CAUTION"
        notes: "p near .05 with small effect; 6 comparisons uncorrected"
    warnings:
      - type: "MULTIPLE_COMPARISONS"
        detail: "6 tests without correction; Bonferroni threshold = .008"
        affected: ["interaction effect"]
      - type: "ASSUMPTION_UNCHECKED"
        detail: "normality not verified for group with n=23"
    fallacy_scan:
      detected:
        - type: "SIMPSONS_PARADOX"
          severity: "RED_FLAG"
          detail: "Overall satisfaction down (r=-.12) but all 4 departments up (r=.08~.21)"
          grouping_variable: "department"
          recommendation: "Report per-group results; flag Simpson's Paradox in overall"
        - type: "CORRELATION_NOT_CAUSATION"
          severity: "CAUTION"
          detail: "Cross-sectional survey uses 'AI adoption improved teaching quality'"
          recommendation: "Change to 'was associated with'"
      not_applicable:
        - "BERKSONS_PARADOX: no apparent selection truncation"
        - "BASE_RATE_NEGLECT: no conditional probabilities involved"
      scan_coverage: "11/11 fallacy types checked"
    overall_confidence: "CAUTION"

  reproducibility:
    method: "re-run with same seed"
    original_run: "exp_001"
    rerun_run: "exp_002"
    comparison:
      - metric: "final_accuracy"
        original: 0.971
        rerun: 0.971
        diff: 0.0
        status: "MATCH"
      - metric: "training_time_seconds"
        original: 342
        rerun: 338
        diff_pct: 1.2
        status: "WITHIN_TOLERANCE"
    verdict: "REPRODUCIBLE"
```

## 7. ARS Integration

### Principles

1. **ARS zero modification** — experiment-agent's absence does not affect ARS pipeline
2. **Single-direction dependency** — experiment-agent knows ARS handoff schema; ARS does not know experiment-agent
3. **Glue point is data format, not code import**

### Independent vs Pipeline Mode

```
Independent mode:
  Trigger: user starts in experiment-agent repo
  Input: user's own experiment needs
  Output: experiment_result / study_status / validation_report
  No ARS needed

Pipeline mode:
  Trigger: user in ARS pipeline says "I need to run experiments first"
  Input: ARS Stage 1 output (RQ Brief + Methodology Blueprint)
  Output: experiment_result in ARS handoff-compatible format
  Handoff: user brings results back to ARS; orchestrator recognizes format, continues Stage 2
```

### experiment-agent → ARS Handoff Format

```yaml
experiment_handoff:
  version: "1.0"
  source: "experiment-agent"
  
  upstream:
    rq_brief: "..." | null
    methodology_blueprint: "..." | null
  
  experiments:
    - id: "exp_001"
      type: "code"
      description: "Logistic regression on SERVQUAL data (n=450)"
      command: "Rscript analysis/main.R"
      status: "completed"
      key_findings:
        - "Treatment group satisfaction significantly higher (t(448)=3.21, p=.001, d=0.48)"
      output_files:
        - path: "results/regression_table.csv"
        - path: "results/figure1.png"
      validation:
        statistical_confidence: "SOLID"
        reproducibility: "REPRODUCIBLE"
        fallacies_detected: []

  writing_notes:
    methods_section: "Experiment design, sample, instruments, analysis in protocol — transfer to Methods"
    results_section: "key_findings are summaries; full data in output_files"
    limitations: "Cross-sectional design; single institution sample"
```

### ARS Stage 1 → experiment-agent

```
experiment-agent recognizes ARS output by section headings:
├─ "## Research Question Brief" → extract RQ, hypotheses → feed plan/manage mode
├─ "## Methodology Blueprint" → extract methods, variables → feed experiment design
└─ "## Annotated Bibliography" → reference but no hard dependency
Detection: loose heading matching, no ARS schema version dependency
```

## 8. Safety Rules (All Modes)

```
IRON RULES:
1. Only execute user-specified commands — never auto-generate or modify scripts
2. Never auto-retry crashed experiments — notify user, user decides
3. Never auto-kill — only hard timeout kills, and notify before kill
4. Only monitor files user specified — monitoring scope limited to declared output paths
5. Never upload data to external services
6. Never touch raw participant data — only track metadata (counts, rates)
7. Never send notifications to study participants
8. Power analysis uses conservative estimates — suggest more rather than fewer
9. Statistical interpretation is descriptive — report what numbers say, don't draw conclusions for user
10. RED_FLAG != "wrong" — it means "needs user attention"
```

## 9. Non-Goals (v1)

- MCP server interface (possible v2)
- Auto-modify user code based on experiment results
- Cross-session state persistence
- Integration with specific experiment platforms (W&B, MLflow, etc.)
- Automated literature search for methodology justification (that's deep-research's job)

## 10. Success Criteria

1. User can run `plan` → `run` → `validate` for a code experiment end-to-end
2. User can run `plan` → `manage` → (manual collection) → `validate` for a human study
3. Results from either path can be fed into ARS Stage 2 via experiment_handoff format
4. ARS pipeline works identically with or without experiment-agent
