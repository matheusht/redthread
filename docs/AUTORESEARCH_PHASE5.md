# Autoresearch Phase 5

Phase 5 formalizes bounded source-code mutation as the next safe autoresearch step.

## Goal

Move from prompt/runtime mutation into **bounded source patches** over offense modules, while keeping the existing safety gates intact:
- dedicated autoresearch branch
- explicit Phase 3 accept/reject boundary
- reverse patch artifacts and fingerprint validation
- promotion only after explicit research-plane acceptance

## Scope

This phase uses the existing bounded source mutation worker as the execution core.

Allowed mutation surface:
- `src/redthread/personas/generator.py`
- `src/redthread/core/pair.py`
- `src/redthread/core/tap.py`
- `src/redthread/core/crescendo.py`
- `src/redthread/core/mcts.py`
- `src/redthread/research/`

Protected surface:
- evaluation and judge logic
- defense synthesis
- telemetry
- golden dataset
- production promotion logic

## CLI

Run one bounded source-patch cycle:

```bash
./.venv/bin/python -m redthread.cli research phase5 cycle --baseline-first
```

Inspect the latest patch candidate:

```bash
./.venv/bin/python -m redthread.cli research phase5 inspect
```

Revert the latest patch candidate:

```bash
./.venv/bin/python -m redthread.cli research phase5 revert
```

## Proposal Contract

Every Phase 5 proposal must capture:
- mutation family
- touched files
- selected tests
- forward patch artifact
- reverse patch artifact
- supervisor decision
- research-plane acceptance state
- promotion eligibility status

## Success Criteria

RedThread can safely:
1. generate one bounded source mutation
2. apply it on the research branch
3. evaluate it through the Phase 3 supervisor
4. revert it safely if rejected
5. promote it only after explicit research-plane acceptance
