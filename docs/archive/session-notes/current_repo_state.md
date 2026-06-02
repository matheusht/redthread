# Current Repo State — RedThread

Date: 2026-05-21  
Current branch: `feat/cop-strategy-composition`

## High-level state

The simplicity PR was merged. RedThread’s intended product spine is now:

```text
attack → judge → defend → replay → promotion evidence
```

The merged simplicity work should be treated as the current stable direction. The next recommended work is not new feature development. It is release-confidence work: live smoke testing, proof-loop testing, report inspection, and evidence/trust documentation.

CEO/CTO review guidance after the merge:

- Do not start Phase 14 by default.
- Do not add features by default.
- Do not add dashboards, auto-promotion, more agents, new evidence states, more profiles, or more hidden state machines.
- Focus on trust, live reliability, evidence honesty, and operator clarity.

## Recent commit context

Recent commits visible on the current branch:

```text
4526907 Fix CI: resolve 13 mypy type errors and 3 pre-existing test failures
38546e6 docs: readme change
bcdb3a3 Simplify RedThread operator evidence spine
```

The simplicity PR merge established:

- reports lead with executive proof sections
- promotion remains explicit
- runtime injection only uses `active_guardrail`
- runtime audit events are written to `logs/guardrail_audit.jsonl`
- audit events use trace IDs and clause hashes, not raw guardrail clause text
- compatibility aliases remain for later explicit breaking cleanup

Known compatibility debt intentionally left in place:

- `DeploymentRecord`
- `defense_deployed`
- `defense_deployments`

Do not remove or rename these without an explicit API-breaking cleanup decision.

## Current working tree

Current branch has uncommitted changes.

Tracked modified files:

```text
src/redthread/cli/run.py
src/redthread/config/settings_groups.py
src/redthread/core/crescendo.py
src/redthread/core/mcts.py
src/redthread/core/mcts_helpers.py
src/redthread/personas/generator.py
```

Untracked files/directories:

```text
NEXT_SESSION_HANDOFF.md
current_repo_state.md
docs/COP_IMPLEMENTATION.md
src/outreach-extension/
src/redthread/core/cop.py
```

Note: `NEXT_SESSION_HANDOFF.md` was created before this file, but the requested state-tracking file is now `current_repo_state.md`. It has not been deleted.

## Current uncommitted experiment: CoP strategy composition

The current dirty changes appear to implement an optional CoP, or Composition of Principles, strategy-generation experiment.

This is feature work. It conflicts with the current “no enshitification / no feature adding by default” direction unless explicitly approved as a research experiment.

### Intended behavior

- Default behavior remains atomic strategy generation.
- CoP is enabled only with a new `--cop` CLI flag.
- When enabled, attack strategy generation composes persuasion principles instead of returning only atomic persona-trigger strategies.

### Files changed for CoP

#### `src/redthread/cli/run.py`

Adds a new CLI flag:

```text
--cop
```

Wires the flag into `_apply_run_overrides()` and sets:

```python
settings.use_cop = True
```

when the flag is present.

Risk:

- This adds new CLI surface.
- CTO/CEO guidance says no new flags by default.
- Should not merge unless explicitly approved.

#### `src/redthread/config/settings_groups.py`

Adds:

```python
use_cop: bool = Field(default=False)
```

Risk:

- Adds another setting/profile surface.
- Probably acceptable only if CoP becomes an approved research option.

#### `src/redthread/core/mcts_helpers.py`

Changes:

```python
derive_strategies(persona)
```

to:

```python
derive_strategies(persona, use_cop=False)
```

When `use_cop=True`, it imports and calls:

```python
redthread.core.cop.generate_cop_strategies(persona)
```

Risk:

- Introduces a new import path to an untracked module.
- If `src/redthread/core/cop.py` is not committed with the other changes, CoP calls will fail.
- Default path should still work if `use_cop=False`.

#### `src/redthread/core/mcts.py`

Passes:

```python
self.settings.use_cop
```

into `derive_strategies()`.

#### `src/redthread/core/crescendo.py`

Passes:

```python
self.settings.use_cop
```

into `derive_strategies()`.

#### `src/redthread/personas/generator.py`

Passes:

```python
self.settings.use_cop
```

when setting `candidate.allowed_strategies`.

#### `src/redthread/core/cop.py`

New untracked module.

Contains:

- `PRINCIPLES`
- `COMBINATION_MAP`
- `_COP_TEMPLATES`
- `generate_cop_strategies(persona)`

It maps persona psychological triggers to composed persuasion-principle strategies.

Risk:

- This is a new attack-strategy-generation feature.
- It may be valuable for research, but it should not be merged into the simplified product path by default.

#### `docs/COP_IMPLEMENTATION.md`

New untracked implementation note.

Documents:

- paper reference
- design decisions
- changed files
- A/B plan
- verification claim

Risk:

- Documentation describes feature work and an A/B path.
- Should be kept only if CoP is approved as a research experiment.

## Unrelated/unreviewed untracked directory

```text
src/outreach-extension/
```

This appears unrelated to the current RedThread simplicity/proof work.

Do not delete it without explicit approval.
Do not include it in a RedThread core PR unless the user explicitly asks.

## Open GitHub PR observed

An open PR exists:

```text
#12 feat: add redthread ECC bundle
https://github.com/matheusht/redthread/pull/12
head: ecc-tools/redthread-1778636220764
base: main
```

This is separate from the current dirty CoP working tree unless explicitly connected later.

## Known good baseline from simplicity work

Before the simplicity PR was merged, validation passed with:

```text
.venv/bin/python -m pytest -q      → 636 passed, 1 skipped
.venv/bin/ruff check src tests     → passed
python3 scripts/wiki_lint.py       → passed
```

After the merge and current CoP changes, validation has not been rerun in this state.

## Recommended immediate next actions

### Option A — Preserve “no feature adding” direction

Recommended default.

1. Stash or park the CoP experiment.
2. Return to a clean baseline.
3. Run release-confidence validation.
4. Run live smoke tests.
5. Write evidence/trust contract docs if desired.

Useful commands:

```bash
git status --short
git stash push -u -m "park cop strategy composition experiment"
.venv/bin/python -m pytest -q
.venv/bin/ruff check src tests
python3 scripts/wiki_lint.py
```

### Option B — Keep CoP as research-only experiment

Only if explicitly approved.

1. Keep it on a separate research branch.
2. Add tests for default behavior and `--cop` behavior.
3. Confirm default operator path is unchanged.
4. Make docs clear that CoP is experimental and not default.
5. Do not merge into main until it passes product review.

Suggested tests before any CoP commit:

```bash
.venv/bin/python -m pytest tests/test_tap.py tests/test_attack_runner_registry.py tests/test_supervisor.py -q
.venv/bin/ruff check src tests
```

Also test CLI help to confirm new flag visibility is intentional:

```bash
.venv/bin/python -m redthread.cli.app run --help | grep -i cop
```

### Option C — Drop CoP changes

If the goal is strict no-feature mode, revert tracked edits and remove untracked CoP docs/module only after approval.

Do not remove files without explicit permission.

## Live-run confidence checklist

After returning to a clean baseline, test live runs with the real provider setup:

```bash
.venv/bin/python -m redthread.cli.app run \
  --objective "live smoke test" \
  --personas 1 \
  --report-dir /tmp/redthread-live-smoke
```

Inspect outputs:

```bash
find /tmp/redthread-live-smoke -name operator-report.md -print
tail -n 5 logs/guardrail_audit.jsonl
```

Expected:

- campaign starts normally
- provider calls happen
- report writes under `/tmp/redthread-live-smoke/<campaign_id>/`
- audit event has `INJECT` or `SKIP`
- audit event contains no raw guardrail clause text

## Full proof-loop checklist

The most important next product proof is one complete loop:

```text
confirmed finding
→ defense candidate
→ replay validation
→ explicit promotion
→ active_guardrail
→ later live run injects only active_guardrail
→ audit log proves injection/skip decision
```

This is more important than adding new attack methods.

## Trust contract doc idea

If doing documentation next, write a small doc named something like:

```text
docs/WHAT_REDTHREAD_MEANS_BY_EVIDENCE.md
```

Define only existing terms:

- weak signal
- confirmed finding
- sealed dry-run
- live replay
- validated candidate
- promotable defense
- active guardrail

Do not add new evidence states.

## Commands to re-check current state

```bash
git status --short
git branch --show-current
git log -3 --oneline
git diff --stat
git diff -- src/redthread/cli/run.py src/redthread/config/settings_groups.py src/redthread/core/mcts_helpers.py src/redthread/core/mcts.py src/redthread/core/crescendo.py src/redthread/personas/generator.py
sed -n '1,220p' src/redthread/core/cop.py
sed -n '1,220p' docs/COP_IMPLEMENTATION.md
```

## Bottom line

RedThread is in a good post-simplicity state, but the current dirty tree contains a new CoP feature experiment.

Default recommendation:

```text
park CoP → return to clean baseline → run live/proof-loop checks → document trust contract
```

Do not merge the CoP work by default.
