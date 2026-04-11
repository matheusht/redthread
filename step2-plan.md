# Step 2 Plan: Restore the Human Review Gate

## Summary

Step 1 is done: the repo is green and the validation/docs story is more truthful. The next step is to make runtime behavior match that truth by removing automatic Phase 3 accept/reject inside the research daemon.

After this step, the daemon will emit a proposal, persist a paused review state, and wait for a human to run `research phase3 accept` or `research phase3 reject`. Promotion behavior stays unchanged in this step. The remaining sequence after this step is: tighten mutation boundaries, add a real live smoke-validation lane, then deepen Phase 6 replay and benign-utility guarantees.

## Key Changes

1. Change daemon behavior at the proposal boundary.
   - Remove automatic `finalize_proposal(...)` calls from the normal daemon cycle and resume path.
   - When a proposal is emitted, persist daemon state as `awaiting_review` instead of auto-accepting or auto-rejecting.
   - Keep candidate-application recovery logic intact for partially applied mutations, but stop at the review boundary once the proposal exists.

2. Add an explicit daemon review state model.
   - Extend daemon status/state types to represent `awaiting_review`.
   - Add a review-oriented step label such as `review_pending` or reuse `proposal_emitted` as the step while status becomes `awaiting_review`.
   - Store enough information in daemon state to show the latest proposal id and candidate id in status output without re-deriving intent.

3. Define resume semantics precisely.
   - `research daemon start` and `research resume` should not advance a pending proposal automatically.
   - If the latest proposal is still pending review, the daemon should return or remain in `awaiting_review` without mutating the worktree.
   - Once the operator manually accepts or rejects through the existing Phase 3 CLI, the next daemon run may continue with the next cycle as normal.
   - Promotion checkpoint auto-resume remains unchanged in this step; only the research-plane accept/reject boundary becomes manual.

4. Update daemon/CLI messaging.
   - `research daemon status` should clearly show `awaiting_review`.
   - `research daemon start` / `research resume` output should explain that a proposal is waiting for manual review when applicable.
   - High-level docs should align with this runtime behavior again, but keep wording minimal and specific to the daemon review boundary.

## Public Interfaces / Types

- Extend `ResearchDaemonState.status` / `ResearchDaemonStatus.status` to include `awaiting_review`.
- Keep existing `research phase3 accept` and `research phase3 reject` commands unchanged.
- No new config flags in this step.
- No change to promotion CLI or promotion rules in this step.

## Test Plan

- Add daemon tests for:
  - proposal emission leaves daemon in `awaiting_review`
  - daemon does not auto-accept accepted proposals
  - daemon does not auto-reject rejected proposals
  - resume/start with a pending proposal stays in review state without mutating the branch
  - promotion checkpoint resume still works as before
- Update CLI tests for:
  - `research daemon status` renders `awaiting_review`
  - `research daemon start` or `research resume` reports review-pending state correctly
- Run:
  - `pytest tests/test_research_daemon.py -v`
  - `pytest tests/test_research_daemon_cli.py -v`
  - `pytest tests/test_research_phase3.py -v`
  - `make test`
  - `make lint`
  - `make typecheck`

## Assumptions and Defaults

- Chosen behavior: the daemon pauses in a persisted `awaiting_review` state rather than stopping immediately or timing out into auto-application.
- Manual review is required only for the Phase 3 research-plane accept/reject boundary in this step.
- Promotion resumability remains as-is for already-started promotion checkpoints.
- This step does not narrow Phase 5 mutation scope, change dry-run semantics, or introduce live smoke tests.
