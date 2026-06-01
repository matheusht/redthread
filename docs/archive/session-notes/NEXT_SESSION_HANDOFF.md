# Next Session Handoff — RedThread

Date: 2026-05-21  
Branch at handoff: `feat/cop-strategy-composition`  
Goal for next session: decide whether to continue, revert, or park the current CoP experiment. Do not add new features by default.

## Current repo state

The simplicity PR was merged before this handoff. Current branch is now past that work.

Recent commits on this branch:

```text
4526907 Fix CI: resolve 13 mypy type errors and 3 pre-existing test failures
38546e6 docs: readme change
bcdb3a3 Simplify RedThread operator evidence spine
```

Current working tree is dirty.

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
docs/COP_IMPLEMENTATION.md
src/outreach-extension/
src/redthread/core/cop.py
```

Open GitHub PR observed:

```text
#12 feat: add redthread ECC bundle
https://github.com/matheusht/redthread/pull/12
head: ecc-tools/redthread-1778636220764
base: main
```

## Important product direction

CEO/CTO review after simplicity merge agreed:

- No Phase 14 yet.
- No enshitification.
- No feature adding by default.
- Move from implementation mode to proof/release-confidence mode.
- Next useful work should be live reliability checks, full proof-loop testing, trust contract, and a canonical demo.

Strong reject list:

- auto-promotion
- dashboard
- more agents
- more evidence states
- more profiles
- more CLI flags unless explicitly approved
- scanner wrappers
- compliance subsystem around audit logs
- more hidden state machines

## Simplicity PR state

Merged simplicity work established the spine:

```text
attack → judge → defend → replay → promotion evidence
```

Important current behavior from that merge:

- Runtime guardrail injection reads only `active_guardrail` records.
- `validated_candidate` is not injected.
- `promotable_defense` is not injected.
- `logs/guardrail_audit.jsonl` records non-secret injection proof.
- Reports lead with executive proof sections.
- Promotion remains explicit.
- Compatibility aliases remain for later breaking cleanup:
  - `defense_deployed`
  - `defense_deployments`
  - `DeploymentRecord`

The missing `src/redthread/memory/formatting.py` issue was fixed before merge by force-adding the ignored file into the PR commit.

## Current experimental work: CoP strategy composition

There is an uncommitted CoP experiment on `feat/cop-strategy-composition`.

Intent:

- Add optional Composition of Principles strategy generation.
- Keep atomic strategy generation as default.
- Enable CoP only with `--cop`.

Current changed behavior:

- `src/redthread/config/settings_groups.py`
  - Adds `use_cop: bool = False`.
- `src/redthread/cli/run.py`
  - Adds `--cop` flag.
  - Sets `settings.use_cop = True` when used.
- `src/redthread/core/mcts_helpers.py`
  - Changes `derive_strategies(persona)` to `derive_strategies(persona, use_cop=False)`.
  - Delegates to `redthread.core.cop.generate_cop_strategies()` when enabled.
- `src/redthread/core/mcts.py`
  - Passes `self.settings.use_cop` into `derive_strategies()`.
- `src/redthread/core/crescendo.py`
  - Passes `self.settings.use_cop` into `derive_strategies()`.
- `src/redthread/personas/generator.py`
  - Passes `self.settings.use_cop` when setting `candidate.allowed_strategies`.
- `src/redthread/core/cop.py`
  - New untracked module with principle definitions and composition templates.
- `docs/COP_IMPLEMENTATION.md`
  - New untracked note describing the experiment and A/B plan.

Risk note:

This CoP work conflicts with the current strategic direction if treated as product work. It is feature adding. It should either be parked, reverted, or treated as an explicitly approved research experiment. Do not merge by default.

## Unrelated/unreviewed local files

`src/outreach-extension/` is untracked and unrelated to the current RedThread simplicity/proof work unless the user says otherwise.

Do not delete it without approval.

## Recommended next-session plan

### Step 1 — Confirm branch and dirty state

```bash
git status --short
git branch --show-current
git log -3 --oneline
```

### Step 2 — Decide what to do with CoP

Choose one:

1. Park it in a separate branch/commit as research-only.
2. Revert/drop it from the working tree.
3. Continue only if user explicitly approves a research experiment.

Default recommendation: park or revert. Do not merge into main yet.

### Step 3 — Run release-confidence checks on main/simplicity baseline

After stashing or isolating CoP, run:

```bash
.venv/bin/python -m pytest -q
.venv/bin/ruff check src tests
python3 scripts/wiki_lint.py
```

### Step 4 — Run live smoke checks

Use real provider setup if available:

```bash
.venv/bin/python -m redthread.cli.app run \
  --objective "live smoke test" \
  --personas 1 \
  --report-dir /tmp/redthread-live-smoke
```

Inspect:

```bash
find /tmp/redthread-live-smoke -name operator-report.md -print
tail -n 5 logs/guardrail_audit.jsonl
```

Expected:

- campaign starts normally
- report writes under `/tmp/redthread-live-smoke/<campaign_id>/`
- audit event has `INJECT` or `SKIP`
- audit event does not include raw guardrail clause text

### Step 5 — Write trust contract doc

If doing docs next, keep it small:

```text
# What RedThread Means By Evidence
```

Define only:

- weak signal
- confirmed finding
- sealed dry-run
- live replay
- validated candidate
- promotable defense
- active guardrail

Do not add new states.

## Commands to inspect current CoP diff

```bash
git diff --stat
git diff -- src/redthread/cli/run.py src/redthread/config/settings_groups.py src/redthread/core/mcts_helpers.py src/redthread/core/mcts.py src/redthread/core/crescendo.py src/redthread/personas/generator.py
sed -n '1,220p' src/redthread/core/cop.py
sed -n '1,220p' docs/COP_IMPLEMENTATION.md
```

## Known validation status

Not validated in this handoff turn.

Previous simplicity validation before merge was:

```text
636 passed, 1 skipped
ruff passed
wiki lint passed
```

Run validation again before any commit or PR.
