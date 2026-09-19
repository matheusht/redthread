---
title: Open Issues Evaluation and Replay Verification
type: research
status: active
summary: Verification record for evaluation pipeline decomposition, truthful judge fallback evidence, and offline replay inspection.
source_of_truth:
  - docs/research/open-issues-evaluation.md
  - src/redthread/evaluation/pipeline.py
  - src/redthread/evaluation/heuristics.py
  - src/redthread/evaluation/metrics.py
  - src/redthread/evaluation/results.py
  - src/redthread/cli/replay.py
  - src/redthread/cli/app.py
  - tests/test_evaluation_decomposition.py
  - tests/test_cli_replay.py
  - docs/PHASE8_TESTING_GUIDE.md
updated_by: codex
updated_at: 2026-09-18
---

# Open Issues Evaluation and Replay Verification

## Research question

What did the scoped implementation of issues [#75](https://github.com/matheusht/redthread/issues/75), [#85](https://github.com/matheusht/redthread/issues/85), and [#94](https://github.com/matheusht/redthread/issues/94) change, and what does the current verification prove?

## Current synthesis

The evaluation path now has small, testable boundaries while preserving existing callers and evidence modes. `EvaluationPipeline` coordinates settings, dry-run scoring, live judge execution, and fallback construction. Heuristic scoring lives in [`heuristics.py`](../../../src/redthread/evaluation/heuristics.py), aggregate calculations live in [`metrics.py`](../../../src/redthread/evaluation/metrics.py), and the coordinator is 144 lines ([`pipeline.py:16-144`](../../../src/redthread/evaluation/pipeline.py#L16-L144)).

Live judge failure now remains visibly degraded: `evidence_mode` keeps the compatible value `live_judge_fallback`, while the additive `evidence_class` is `fallback_heuristic`, `fallback_reason` carries the exception text, and the logger emits an explicit degraded-evidence warning ([`pipeline.py:26-56`](../../../src/redthread/evaluation/pipeline.py#L26-L56); [`results.py:40-55`](../../../src/redthread/evaluation/results.py#L40-L55)). Intentional dry-run scoring remains `sealed_heuristic`; successful provider-backed scoring remains `live_judge` ([`pipeline.py:58-83`](../../../src/redthread/evaluation/pipeline.py#L58-L83), [`pipeline.py:118-130`](../../../src/redthread/evaluation/pipeline.py#L118-L130)).

Operators can inspect an existing replay bundle with `redthread replay run <bundle-file>`. The command validates Pydantic JSON, evaluates the current promotion evaluator, renders expected/actual authorization and budget values plus sealed/live canary visibility, and returns nonzero for ordinary evaluator failures or invalid input ([`replay.py:17-101`](../../../src/redthread/cli/replay.py#L17-L101); [`app.py:58-66`](../../../src/redthread/cli/app.py#L58-L66)). It performs no target, tool, LLM, network, or live-adapter execution.

## Verification evidence

Focused checks ran with `COLUMNS=240 REDTHREAD_DRY_RUN=true`:

```text
59 passed in 5.03s
```

The set covered decomposition exports and file ceilings, evaluation truth/boundary behavior, CLI rendering and input errors, judge regressions, replay-promotion behavior, and the golden dataset:

```text
tests/test_evaluation_decomposition.py
tests/test_cli_replay.py
tests/test_evaluation_truth.py
tests/test_evaluation_boundaries.py
tests/test_evaluation_cli.py
tests/test_judge.py
tests/test_agentic_replay_promotion.py
tests/test_golden_dataset.py
```

Ruff passed for the touched evaluation, replay CLI, and focused tests. Mypy passed for the touched evaluation and replay CLI modules. The decomposition leaves `pipeline.py`, `heuristics.py`, and `metrics.py` at 144, 49, and 51 lines respectively ([`test_evaluation_decomposition.py:27-30`](../../../tests/test_evaluation_decomposition.py#L27-L30)).

The replay CLI has focused tests for a passing bundle, an authorization failure, a canary mismatch, malformed JSON, and schema-invalid JSON ([`test_cli_replay.py:34-90`](../../../tests/test_cli_replay.py#L34-L90)). The operator guide can use:

```bash
PYTHONPATH=src .venv/bin/redthread replay run ./replay-bundle.json
```

The command is an inspection surface for already-produced evidence. It does not create promotion state or claim live enforcement.

## Evidence boundaries

The evaluation evidence vocabulary remains:

| Mode | Meaning |
| --- | --- |
| `sealed_heuristic` | Intentional offline deterministic scoring. Useful for regression consistency. |
| `live_judge` | Judge provider path completed successfully. |
| `live_judge_fallback` | Live path failed and heuristic scoring continued; weaker than successful live evidence. |

`evidence_class="fallback_heuristic"` adds the issue-requested explicit degraded class without breaking consumers of `evidence_mode`. Metrics preserve mode counts and carry `evidence_class` in individual rows ([`metrics.py:21-50`](../../../src/redthread/evaluation/metrics.py#L21-L50)). The anti-hallucination SOP remains authoritative for the distinction between sealed, live, and fallback evidence ([`ANTI_HALLUCINATION_SOP.md:128-168`](../../../docs/ANTI_HALLUCINATION_SOP.md#L128-L168)).

The replay command shows sealed and live canary reports separately because the evaluator checks both execution boundaries. This improves inspection, but the underlying promotion semantics remain owned by the current evaluator.

## Explicit exclusions and remaining dependency

Issues [#80](https://github.com/matheusht/redthread/issues/80), [#86](https://github.com/matheusht/redthread/issues/86), and [#87](https://github.com/matheusht/redthread/issues/87) are external-owned and were not modified in this pass.

* **#80 — empty replay bundles:** `ReplayBundle.traces` still defaults to an empty list, and the current evaluator can treat an empty bundle as passed until the external fail-closed guard lands ([`replay_corpus.py:21-24`](../../../src/redthread/evaluation/replay_corpus.py#L21-L24); [`promotion_gate.py:12-45`](../../../src/redthread/evaluation/promotion_gate.py#L12-L45)). The CLI intentionally tests normal valid pass/fail bundles only; do not read a successful empty-bundle result as promotion proof.
* **#86 — JudgeAgent parsing:** markdown-fence and JSON parsing remains external-owned. This verification does not claim that parser resilience was added.
* **#87 — golden traces:** Crescendo and Phase 8 fixture expansion remains external-owned. Current verification does not claim the dataset reached 40 traces.

These exclusions are recorded in the implementation research handoff ([`open-issues-evaluation.md`](../../research/open-issues-evaluation.md)).

## Contradictions and uncertainty

The focused 59-test result is implementation evidence for this slice, not a full-suite result. Parent integration still needs the repository-wide checks and must account for concurrent changes in other issue groups. Raw exception text is now operator-visible as requested by #85; provider errors can contain sensitive request detail, so redaction would be a separate follow-up if that risk appears in real logs.

The replay CLI deliberately does not duplicate #80's empty-bundle guard. After the external guard lands, add a CLI regression proving empty bundles return nonzero and expose the canonical reason.

## Next questions

1. After parent integration, does the full suite preserve existing `live_judge_fallback` consumers?
2. Does external #80 define the final empty-bundle failure string and trace-evidence contract consumed by the CLI?
3. Do external #86 and #87 changes require updates to this page's verification references?

## Sources

- [Issue evaluation research and implementation handoff](../../research/open-issues-evaluation.md)
- [Anti-Hallucination SOP](../../../docs/ANTI_HALLUCINATION_SOP.md)
- [Phase 8 testing guide](../../../docs/PHASE8_TESTING_GUIDE.md)
- [Agentic Security Runtime](../../../docs/AGENTIC_SECURITY_RUNTIME.md)
