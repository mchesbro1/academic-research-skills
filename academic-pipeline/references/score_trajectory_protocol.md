# Score Trajectory Protocol

**Status**: v3.3
**Used by**: `pipeline_orchestrator_agent`, `editorial_synthesizer_agent`
**Applies at**: Stage 3' (RE-REVIEW) and Stage 4' (RE-REVISE)

---

## Purpose

Tracks how rubric scores change across revision rounds. Detects score regressions — dimensions where the revised paper scores lower than the original — which indicate that a revision fix inadvertently damaged another aspect of the paper.

Inspired by PaperOrchestra's Content Refinement Agent (Song et al., 2026), which accepts revisions only when overall score increases and reverts when any sub-axis shows net negative gain.

---

## How it works

### At Stage 3 (REVIEW)

The `editorial_synthesizer_agent` produces dimension scores in the Review Report (Schema 6). These are the **baseline scores**.

### At Stage 3' (RE-REVIEW)

The `editorial_synthesizer_agent` produces new dimension scores. The `pipeline_orchestrator_agent` computes deltas:

```
For each dimension d in {originality, methodology, clarity, significance, overall}:
  delta[d] = score_re_review[d] - score_review[d]
```

### Decision rules

| Condition | Action |
|-----------|--------|
| All deltas >= 0 | Normal: revision improved or maintained all dimensions |
| Any delta < 0 but >= -3 | Warning: "Dimension X decreased slightly (delta = Y). Verify this is acceptable." Surface at checkpoint. |
| Any delta < -3 | **Regression detected**: "Dimension X regressed significantly (delta = Y). The revision may have damaged this aspect." Trigger MANDATORY checkpoint. |
| Overall delta < 3 AND no P0 issues | Early-stop eligible (existing v3.2 criterion). Suggest stopping revision loop. |

### Regression checkpoint

When regression is detected, the MANDATORY checkpoint presents:
1. The dimension(s) that regressed and by how much
2. The reviewer's comments on those dimensions (from the re-review report)
3. Three options:
   - **Proceed**: Accept the regression as a tradeoff (recorded in Stage 6 audit)
   - **Targeted fix**: Return to Stage 4' to fix only the regressed dimension(s)
   - **Revert**: Restore the pre-revision version for the regressed section(s)

---

## Integration with existing early-stopping

The v3.2 early-stopping criterion (delta < 3 + no P0) remains unchanged. Score trajectory extends it:
- Early-stopping checks the **overall** delta
- Trajectory tracking checks **per-dimension** deltas
- Both can fire at the same checkpoint: "Overall improvement is small (suggest stopping) AND dimension X regressed (suggest investigating)"

---

## Stage 6 reporting

The Process Summary includes a "Score Trajectory" subsection showing all rounds:

```markdown
### Score Trajectory

| Dimension | Review (Stage 3) | Re-Review (Stage 3') | Delta | Status |
|-----------|-------------------|----------------------|-------|--------|
| Originality | 65 | 68 | +3 | Improved |
| Methodology | 72 | 70 | -2 | Warning |
| Clarity | 58 | 71 | +13 | Improved |
| Significance | 60 | 62 | +2 | Improved |
| Overall | 64 | 68 | +4 | Improved |

Regressions detected: 1 (Methodology, -2, within tolerance)
Early-stop eligible: No (overall delta = 4 >= 3)
```

---

## References

- Song, Y. et al. (2026). PaperOrchestra. *arXiv:2604.05018*. — Section 4 Step 5 (Content Refinement Agent: score-driven accept/revert).
