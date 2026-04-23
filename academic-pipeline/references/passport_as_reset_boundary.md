# Passport as Reset Boundary (v3.6.3)

## Purpose

Defines how `pipeline_orchestrator_agent` converts FULL checkpoints into reset boundaries when `ARS_PASSPORT_RESET=1` is set. This is the authoritative protocol; any divergent behavior in agent prompts is a bug.

## When this protocol applies

| Flag state | Mode | Behavior at FULL checkpoint |
|------------|------|-----------------------------|
| `ARS_PASSPORT_RESET` unset / `=0` | any | Continuation (pre-v3.6.3 default). No reset tag emitted. |
| `ARS_PASSPORT_RESET=1` | `systematic-review` | **Mandatory reset** at every FULL checkpoint. |
| `ARS_PASSPORT_RESET=1` | any other mode | **Strong-default reset** at every FULL checkpoint. User `continue` response overrides back to continuation for the next stage only. |

MANDATORY checkpoints (integrity Stage 2.5 / 4.5, review decisions, Stage 5 finalization) are orthogonal: reset can co-occur with MANDATORY. SLIM checkpoints never trigger reset.

## The reset boundary protocol

When the orchestrator reaches a FULL checkpoint with the flag ON:

1. **Freeze state.** `state_tracker` snapshots the current stage's deliverables and updates the Material Passport with a new ledger entry (append-only; never mutate prior entries).
2. **Compute hash.** Content hash is SHA-256 of the concatenated passport ledger entries through this checkpoint, lowercase hex, first 12 characters used as the short-form handoff ID (`hash=<short>`).
3. **Emit reset tag.** In the checkpoint notification block, append a machine-stable line:
   ```
   [PASSPORT-RESET: hash=<short>, stage=<stage_number>, next=<next_stage_number_or_name>]
   ```
4. **Emit human instruction.** In the same checkpoint notification, include a `### Resume Instruction` subsection with:
   - Passport file path (absolute or repo-relative)
   - The exact resume command the user pastes into a fresh session:
     ```
     resume_from_passport=<short-hash>
     ```
   - A one-line note that the next stage should be invoked in a fresh Claude Code session to realize the token-savings intent.
5. **Halt after emission.** The orchestrator stops after emitting the reset boundary and awaits resume in a fresh session.
6. **In-session override (non-SR modes).** If the user pastes `continue` in the same session, the orchestrator acknowledges but treats the passport as the only input to the next stage. Working-memory content from prior turns is non-authoritative and must not be replayed.
7. **Systematic-review hard stop.** In `systematic-review` mode, in-session continuation is refused outright. The orchestrator repeats the Resume Instruction and asks the user to start a fresh session.

## `resume_from_passport` mode contract

Invocation shape (prompt-layer, user-pasted or auto-dispatched in a new session):

```
resume_from_passport=<short-hash> [stage=<stage_number_or_name>] [mode=<downstream_mode>]
```

Required:
- `resume_from_passport=<short-hash>` — must match the short-hash from a `[PASSPORT-RESET: ...]` tag emitted in a prior session. Orchestrator verifies hash against the passport ledger on disk; mismatch is a hard error.

Optional:
- `stage=<stage_number_or_name>` — override the `next=` recorded in the reset tag. Useful when the user wants to re-run a stage rather than proceed. If omitted, the orchestrator uses `next=` from the reset tag.
- `mode=<downstream_mode>` — override the mode of the next stage (e.g., swap `full` for `quick`). Orchestrator validates the override against Mode Advisor rules.

Orchestrator obligations on resume:
- Read the passport ledger entry matching the hash. Load artifacts by reference (paths or IDs recorded in the entry).
- Do NOT ask the user to re-summarize prior stages; the passport is authoritative.
- Honor the `verification_status` field. If `STALE`, display a warning and prompt the user to re-verify before continuing.
- Emit a `### Resume Acknowledged` section at the start of the new session with: hash, source session ISO-8601 timestamp, recovered stage number, and next-stage plan.

## Append-only ledger semantics

Material Passport ledger (`compliance_history[]` + new `reset_boundary` entries) is append-only:
- Every checkpoint with the flag ON appends one `reset_boundary` entry under Schema 9's `reset_boundary` field.
- Re-running a stage (e.g., after a review rejection) appends a new entry with `version_label` bumped (`v1.0 → v1.1-revised`).
- Prior entries are never deleted, reordered, or mutated.
- Stage-re-run cases produce adjacent entries for the same `stage`; both are preserved.

## Iron rules

1. Flag OFF is pre-v3.6.3 behavior, bit-for-bit.
2. Ledger is append-only. No exception, no "clean up" operation.
3. Reset tag is the sole machine-stable handoff. Human-readable `### Resume Instruction` is for user ergonomics; consumers parse the tag.
4. `systematic-review` with flag ON refuses in-session continuation across FULL checkpoints.
5. Hash mismatch on resume is a hard error; orchestrator never proceeds on a guessed or coerced hash.
6. MANDATORY checkpoints are not downgraded by reset; they co-occur.

## Interaction with existing features

- **Collaboration Depth Observer (v3.5.0):** fires on FULL/SLIM as before. Observer output is included in the checkpoint notification regardless of reset state. Observer state does NOT carry across resets; each fresh session observes only its own stage.
- **Compliance agent (v3.4.0):** `compliance_history[]` remains append-only and is consumed from the passport on resume. No change to Schema 12.
- **Sprint contract (v3.6.2):** reviewer sprint contracts load from the passport on resume (Phase 1 paper-content-blind stage remains valid across the reset boundary because the contract + paper metadata are carried in the passport).
- **Socratic reading probe (v3.5.1):** reading probe fires at most once per session. Across a reset boundary, the probe counter resets — the next session may fire its own probe. This is by design: each session is its own Socratic unit.

## What this protocol does NOT do

- Does not define Zotero / Obsidian / folder-scan adapter shapes (deferred to v3.6.4, PR-B).
- Does not define `literature_corpus` entry shape (deferred to v3.6.4, PR-B).
- Does not add runtime CLI tooling. Passport resolution is the user's responsibility — the orchestrator loads from the path the user provides.
- Does not claim specific token savings numbers. Empirical measurement goes in `docs/PERFORMANCE.md` only after real runs.

## Related references

- [`shared/handoff_schemas.md`](../../shared/handoff_schemas.md) — Schema 9 definition
- [`academic-pipeline/agents/pipeline_orchestrator_agent.md`](../agents/pipeline_orchestrator_agent.md) — orchestrator integration
- [`academic-pipeline/references/pipeline_state_machine.md`](pipeline_state_machine.md) — state transitions
- [`docs/PERFORMANCE.md`](../../docs/PERFORMANCE.md) — long-running session guidance
