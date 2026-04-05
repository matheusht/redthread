# Autoresearch Phase 4

Phase 4 adds the first real mutation layer on top of the research harness.

## Scope

This phase does **not** perform arbitrary source-code rewriting.
It performs bounded mutations over:
- attacker prompt profiles
- runtime search parameters

Those mutations are stored under `autoresearch/` and then evaluated through the Phase 3 git-backed supervisor workflow.

## Why This Design

Free-form self-editing over the whole codebase is too risky this early.
The safer path is:
1. externalize attacker-side prompt behavior into profiles
2. allow bounded runtime mutations over those profiles
3. evaluate them with the existing baseline / supervisor / proposal machinery
4. only later move to arbitrary patch generation

## Files

- [prompt_profiles.py](/Users/matheusvsky/Documents/personal/redthread/src/redthread/research/prompt_profiles.py)
- [runtime.py](/Users/matheusvsky/Documents/personal/redthread/src/redthread/research/runtime.py)
- [mutations.py](/Users/matheusvsky/Documents/personal/redthread/src/redthread/research/mutations.py)
- [phase4.py](/Users/matheusvsky/Documents/personal/redthread/src/redthread/research/phase4.py)

Runtime artifacts:
- `autoresearch/prompt_profiles.json`
- `autoresearch/mutation_state.json`
- `autoresearch/mutations/*.json`

## CLI

Run one bounded mutation cycle:

```bash
./.venv/bin/python -m redthread.cli research phase4 cycle --baseline-first
```

That command:
1. ranks objectives from the ledger
2. chooses the next mutation candidate
3. writes prompt/runtime mutation artifacts
4. runs the Phase 3 evaluation cycle
5. emits a proposal recommendation

## What Mutates

Current mutation families:
- authority escalation wording
- prompt-injection pressure wording
- Crescendo persistence/escalation tuning
- bounded runtime parameters such as attacker temperature, tree depth, tree width, and Crescendo thresholds

## What Does Not Mutate

- judge logic
- golden dataset
- defense synthesis
- production telemetry thresholds
- arbitrary source files

## Next Step

The next phase after this would be real patch generation:
- propose code changes to attack/prompt/persona modules
- apply them on the dedicated research branch
- evaluate them through the existing Phase 3 accept/reject workflow
