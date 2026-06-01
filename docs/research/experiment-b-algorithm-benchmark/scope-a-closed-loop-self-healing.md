# Research Scope A: Closed-Loop Self-Healing Study

Status: future research scope. Deferred behind Experiment B.

## One-line scope

Study a closed loop:

```text
attack → judge → defend → replay → promotion evidence
```

The loop measures whether confirmed failures can be converted into safer behavior without breaking benign utility.

## Research question

Can RedThread turn JudgeAgent-confirmed failures into validated, replay-tested defense candidates while preserving utility and avoiding automatic overreach?

## Why this is promising

This is a strong paper and product angle because it studies the full repair loop, not just attack discovery.

Useful claim shape:

> RedThread studies an underexplored closed-loop safety workflow where attacks generate evidence, defenses are synthesized, and candidate defenses are replay-tested before promotion.

Avoid claiming this is definitively new.

## Minimal study design

1. Start with a fixed seed set.
2. Run selected attack strategies under fixed budgets.
3. Let JudgeAgent decide confirmed findings.
4. Generate candidate defenses only from confirmed findings.
5. Replay original and variant cases against the candidate defense.
6. Measure residual attack success, variant block rate, benign utility retention, and over-refusal.
7. Promote only when evidence meets explicit gates.

## Evidence ladder alignment

Use the existing defense ladder from `docs/DEFENSE_PIPELINE.md`:

```text
candidate_defense → validated_candidate → promotable_defense → active_guardrail
```

Rules:

- Runtime injection only uses `active_guardrail`.
- Promotion stays explicit.
- No auto-promotion.
- No extra hidden evidence states.
- External benchmark labels or detector scores are weak signals only.
- JudgeAgent owns confirmed findings.

## Metrics

Primary:

- confirmed attack success rate before defense
- residual confirmed attack success rate after defense
- cost per confirmed finding
- cost per promotable defense
- promotion yield from confirmed findings

Defense quality:

- original replay block rate
- variant replay block rate
- benign utility retention
- over-refusal rate
- regression count

Operator clarity:

- number of artifacts reviewed per promotion
- amount of manual labeling required
- reproducibility from ledger files

## Safety constraints

- Do not store raw jailbreak prompt bodies in public docs.
- Keep benchmark datasets behind license and safety review.
- Treat external labels as seed metadata, not product truth.
- Do not convert weak detector scores into findings.
- Keep the first study file-based: manifest + JSONL, not a database or dashboard.

## When to start Scope A

Start after Experiment B identifies which attack strategies are worth using in the loop. Scope A depends on knowing which methods create the best confirmed findings per cost.
