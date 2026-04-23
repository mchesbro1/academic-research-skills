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

1. **Freeze state.** `state_tracker` stages the current stage's deliverables and prepares a new `kind: boundary` ledger entry — but does NOT yet write `hash` (append happens in Step 2 after hash is known).
2. **Compute hash.** Canonical byte serialization is normative; two implementations must produce the same bytes from the same ledger:
   - Each entry is serialized as **JSON Canonical Form (RFC 8785 / JCS)**: UTF-8, no insignificant whitespace, keys sorted ASCII-ascending at every object level, numbers in JCS canonical form.
   - Entries are separated by a single `\x0a` (LF) byte. The first entry has no leading separator; the last entry has a trailing LF.
   - The new entry is serialized with `hash` set to the canonical placeholder `"000000000000"` and all other fields populated; concatenated AFTER every prior entry (each already carrying its own finalized `hash`).
   - SHA-256 the byte stream. Take the lowercase hex digest. Take the first 12 characters. That IS the new entry's `hash`. Overwrite the placeholder before appending to the ledger.
   - **Iron rule (see §Iron rules 2 + 7):** never hash an entry that already contains a non-placeholder `hash` for itself; never reorder prior entries; never include `kind: resume` entries in a boundary hash computation.
3. **Emit reset tag.** In the checkpoint notification block, append a machine-stable line:
   ```
   [PASSPORT-RESET: hash=<hash>, stage=<completed>, next=<next>]
   ```
4. **Emit human instruction.** In the same checkpoint notification, include a `### Resume Instruction` subsection with:
   - Passport file path (absolute or repo-relative)
   - The exact resume command the user pastes into a fresh session:
     ```
     resume_from_passport=<hash>
     ```
   - A one-line note that the next stage should be invoked in a fresh Claude Code session to realize the token-savings intent.
5. **Halt after emission.** The orchestrator stops after emitting the reset boundary and awaits resume in a fresh session.
6. **In-session override (non-SR modes).** If the user pastes `continue` in the same session, the orchestrator acknowledges but treats the passport as the only input to the next stage. Working-memory content from prior turns is non-authoritative and must not be replayed.
7. **Systematic-review hard stop.** In `systematic-review` mode, in-session continuation is refused outright. The orchestrator repeats the Resume Instruction and asks the user to start a fresh session.
8. **Pending MANDATORY decision.** If the reset co-occurs with a MANDATORY checkpoint that requires a user decision with multiple valid branches (e.g., Stage 3 review outcome: `revise` / `restructure` / `abort`; Stage 5 finalization format choice), the orchestrator sets `pending_decision` on the ledger entry with the decision-space enumerated. On resume, the orchestrator re-prompts the user to choose before invoking any downstream stage. `next` is populated as a best-guess default only; it must NOT be used to auto-advance when `pending_decision` is present.

## `resume_from_passport` mode contract

Invocation shape (prompt-layer, user-pasted or auto-dispatched in a new session):

```
resume_from_passport=<hash> [stage=<stage_number_or_name>] [mode=<downstream_mode>]
```

Required:
- `resume_from_passport=<hash>` — must match the 12-hex `hash` from a `[PASSPORT-RESET: ...]` tag emitted in a prior session. Orchestrator verifies the hash against the passport ledger on disk; mismatch is a hard error.

Optional:
- `stage=<stage_number_or_name>` — override the `next=` recorded in the reset tag. Useful when the user wants to re-run a stage rather than proceed. If omitted, the orchestrator uses `next=` from the reset tag.
- `mode=<downstream_mode>` — override the mode of the next stage (e.g., swap `full` for `quick`). Orchestrator validates the override against Mode Advisor rules.

Orchestrator obligations on resume:
- Locate the target `kind: boundary` entry by matching `hash`. Hard error if no match, or if a later `kind: resume` entry already carries `consumes_hash == <hash>` (double-resume is forbidden).
- Do NOT ask the user to re-summarize prior stages; the passport is authoritative. Load artifacts by reference (paths or IDs recorded in the entry).
- Honor the `verification_status` field. If `STALE` or `UNVERIFIED`, display a warning and prompt the user to re-verify before continuing. If `VERIFIED`, proceed without prompting.
- If `pending_decision` is set on the ledger entry, re-prompt the user for that decision BEFORE invoking any downstream stage. `next` is advisory in this case. The user's chosen option is recorded on the new `resume` entry's `chosen_branch` field. Note: a user-supplied `stage=<n>` override on the resume command does NOT satisfy `pending_decision` — the decision prompt always fires when `pending_decision` is present.
- Emit a `### Resume Acknowledged` section at the start of the new session with: hash, source session `session_marker` + `generated_at`, recovered stage, and next-stage plan.
- Append a new `kind: resume` entry to `reset_boundary[]` with `consumes_hash = <hash>`, fresh `generated_at` and `session_marker`, and (if applicable) `chosen_branch` + `user_override`. This is how resume leaves an append-only trace and lets downstream readers compute `awaiting_resume` from the ledger alone.

## Append-only ledger semantics

Material Passport ledger (`compliance_history[]` + new `reset_boundary` entries) is append-only:
- Every checkpoint with the flag ON appends one `reset_boundary` entry of kind `boundary` under Schema 9's `reset_boundary` field.
- Re-running a stage (e.g., after a review rejection) appends a new entry with `version_label` bumped (`v1.0 → v1.1-revised`).
- `resume_from_passport` consumption appends one entry of kind `resume` to the same ledger, carrying the `consumes_hash` pointer to the `boundary` entry it resolves. This is how resume leaves a trace — no mutation of prior entries.
- Prior entries are never deleted, reordered, or mutated.
- Stage-re-run cases produce adjacent entries for the same `stage`; both are preserved.

### Computing `awaiting_resume` from the ledger

A `boundary` entry with hash `H` is considered **awaiting resume** iff no `resume` entry exists later in the ledger with `consumes_hash == H`. Downstream readers (state machine, observers, external audit tools) compute this by a single pass over `reset_boundary[]` — no out-of-band state required.

## Iron rules

1. Flag OFF is pre-v3.6.3 behavior, bit-for-bit.
2. Ledger is append-only. No exception, no "clean up" operation.
3. Reset tag is the sole machine-stable handoff. Human-readable `### Resume Instruction` is for user ergonomics; consumers parse the tag.
4. `systematic-review` with flag ON refuses in-session continuation across FULL checkpoints.
5. Hash mismatch on resume is a hard error; orchestrator never proceeds on a guessed or coerced hash.
6. MANDATORY checkpoints are not downgraded by reset; they co-occur.
7. Hash is computed over the entry with the canonical placeholder `"000000000000"` in the `hash` field, serialized per the byte rules in §"The reset boundary protocol" step 2. `kind: resume` entries are never included in a `boundary` hash computation — the hash covers only prior `boundary` entries plus the new boundary entry itself. Any other convention (exclude-field, variable-length placeholder, post-hoc mutation, including resume entries) breaks cross-implementation interoperability and is forbidden.
8. A `boundary` entry is "consumed" only by appending a `resume` entry with matching `consumes_hash`. If a `boundary` entry has `pending_decision` set, the orchestrator MUST re-prompt the user on resume and MUST NOT auto-advance using `next`.

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
