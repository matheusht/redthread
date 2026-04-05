# Autoresearch Phase 3

This document describes the Phase 3 layer added on top of the existing Phase 1 and Phase 2 harnesses.

## Goal

Phase 3 adds the missing control-loop pieces needed before full autonomous experimentation:
- history-aware objective scheduling
- dedicated git research sessions on `autoresearch/<tag>` branches
- explicit proposal output after each supervised cycle
- accept/reject commands that map supervisor decisions to git actions

Phase 3 still does **not** mutate code by itself.
It provides the machinery needed to evaluate and promote or reject code changes safely.

## What Changed

### History-aware scheduling
- [history.py](/Users/matheusvsky/Documents/personal/redthread/src/redthread/research/history.py)
- reads `autoresearch/results.tsv`
- ranks objective slugs by historical jailbreaks, near misses, ASR, and score

### Safe git session control
- [git_ops.py](/Users/matheusvsky/Documents/personal/redthread/src/redthread/research/git_ops.py)
- refuses to start if the worktree is dirty outside `autoresearch/` and `logs/`
- creates a dedicated `autoresearch/<tag>` branch
- supports commit or hard reset only when the operator explicitly invokes accept or reject

### Phase 3 harness
- [phase3.py](/Users/matheusvsky/Documents/personal/redthread/src/redthread/research/phase3.py)
- stores session metadata in `autoresearch/session.json`
- writes proposals to `autoresearch/proposals/`
- updates lane assignment dynamically from prior results before running the Phase 2 supervisor

## CLI

Start a session:

```bash
./.venv/bin/python -m redthread.cli research phase3 start --tag apr5a
```

Run one history-aware cycle:

```bash
./.venv/bin/python -m redthread.cli research phase3 cycle --baseline-first
```

Accept the latest accepted proposal and commit current changes:

```bash
./.venv/bin/python -m redthread.cli research phase3 accept
```

Reject the latest proposal and reset back to the session base commit:

```bash
./.venv/bin/python -m redthread.cli research phase3 reject
```

## Workflow

1. Start from a clean git tree.
2. Create a Phase 3 session on a dedicated branch.
3. Make a bounded code change manually or via a future autonomous worker.
4. Run `research phase3 cycle`.
5. Inspect the proposal in `autoresearch/proposals/`.
6. If the proposal is accepted, run `research phase3 accept`.
7. If the proposal is rejected, run `research phase3 reject`.

## Why This Order

Phase 2 gave RedThread a supervisor and control lane.
Phase 3 makes that decision meaningful by tying it to:
- a specific branch
- a specific base commit
- a specific proposal artifact

Without those three pieces, git-backed autonomous evaluation would be too brittle.

## Safety Model

Phase 3 is intentionally conservative.

It will not:
- start on a dirty tree
- auto-commit without an accepted proposal
- silently reset the worktree during ordinary operation

The destructive action is isolated to `research phase3 reject`, which is explicit operator intent.

## What Comes Next

The next step after Phase 3 is true code-mutation automation:
- bounded change proposals
- automatic patch generation
- per-lane code ownership
- automatic commit/revert loop over real candidate edits

That is the first point where RedThread becomes genuinely Karpathy-style autoresearch over its own codebase rather than a supervised research harness.
