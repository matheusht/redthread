---
title: Defense Synthesis and Validation
type: system
status: active
summary: How RedThread turns confirmed jailbreaks into validated defensive proposals rather than raw findings alone.
source_of_truth:
  - docs/DEFENSE_PIPELINE.md
  - docs/PHASE_REGISTRY.md
updated_by: codex
updated_at: 2026-04-18
---

# Defense Synthesis and Validation

## Scope

This page summarizes the self-healing path from confirmed jailbreak to validated defensive evidence.

## Workflow

The documented pipeline follows a clear pattern:
1. isolate the relevant exploit slice
2. classify the attack pattern
3. generate a defensive proposal
4. validate it through replay / sealed checks
5. preserve evidence for later promotion decisions

## Why it matters

This is the core difference between a tool that only reports failures and one that helps close the loop on remediation.

## Guardrails

- proposals are not treated as production-ready by default
- validation evidence matters as much as the proposal text
- promotion stays separate from generation

## Defense evidence modes

Defense validation should now be read in three classes:
- `sealed_dry_run_replay` — sealed offline replay evidence for consistency checks
- `live_replay` — successful live replay evidence with exploit and benign cases recorded
- `live_validation_error` — live validation infrastructure failed before replay evidence completed

This matters because these are not equally strong.
A sealed dry-run replay is useful, but it is not promotable proof.
A live validation error is a warning about missing evidence, not proof that a defense passed or failed the real replay path cleanly.

As of 2026-04-18, the live execution truth pass also labels two real defense-generation seams at the shared provider boundary:
- `defense.architect` for live guardrail generation
- `defense.replay` for live exploit and benign replay sends

That means defense evidence is now better tied to actual send boundaries instead of only higher-level replay outcomes.

## Replay breadth notes

Current default replay suite is `default-defense-replay-v4`.
It now includes:
- the isolated exploit replay
- an `exploit_override_probe` to catch narrow fixes that only block the exact original wording
- an `exploit_roleplay_probe` to catch narrow fixes that still yield during training or roleplay framing
- the starter benign pack
- extra benign utility checks for formatting, translation, scheduling, short policy explanation tasks, and simple YAML output

This still does not prove broad production utility.
It means the replay suite is better at catching three specific trust failures:
- a defense that blocks the exact exploit text but still complies with a close override variant
- a defense that blocks the override phrasing but still yields when the exploit is framed as training or roleplay
- a defense that over-refuses harmless formatting, explanation, or structured-output prompts

## Related pages

- [promotion-and-revalidation.md](promotion-and-revalidation.md)
- [evaluation-and-anti-hallucination.md](evaluation-and-anti-hallucination.md)
- [../entities/defense-architect.md](../entities/defense-architect.md)

## Sources

- [../../DEFENSE_PIPELINE.md](../../DEFENSE_PIPELINE.md)
- [../../PHASE_REGISTRY.md](../../PHASE_REGISTRY.md)
