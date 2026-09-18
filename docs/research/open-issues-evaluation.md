# Open issues 75, 80, 85, 86, 87, 94 — research evaluation

Research date: 2026-09-18

Scope: research plus implementation of #75, #85, and #94 only. Issues #80, #86, and #87 are external-owned for this pass and remain unmodified. No runtime changes for those external issues.

Primary sources: [issue 75](https://github.com/matheusht/redthread/issues/75), [issue 80](https://github.com/matheusht/redthread/issues/80), [issue 85](https://github.com/matheusht/redthread/issues/85), [issue 86](https://github.com/matheusht/redthread/issues/86), [issue 87](https://github.com/matheusht/redthread/issues/87), and [issue 94](https://github.com/matheusht/redthread/issues/94), plus the linked source and test files below.

## Current evidence

The focused evaluation, judge, replay-promotion, and golden-dataset tests pass before these changes:

```text
PYTHONPATH=src .venv/bin/pytest -q \
  tests/test_evaluation_truth.py \
  tests/test_evaluation_boundaries.py \
  tests/test_judge.py \
  tests/test_agentic_replay_promotion.py \
  tests/test_golden_dataset.py
49 passed in 0.32s
```

The current working tree contains unrelated parent-agent changes, including an untracked `work/` directory and wiki files. This evaluation added only this research file.

## Ownership and dependency order

**This pass owns:** #75 pipeline decomposition, #85 truthful live-judge fallback metadata, and #94 offline replay CLI.

**External-owned; excluded from implementation:** #80 empty replay-bundle guard, #86 JudgeAgent markdown/JSON parser, and #87 Crescendo/Phase 8 golden traces. Their research remains below as dependency context only. Do not modify `promotion_gate.py`, judge parsing, or golden traces in this pass.

1. **75 — pipeline decomposition.** Establish module boundaries first. #85 fallback handling remains in the coordinator; #86 parser work is external-owned and excluded.
2. **85 — degraded evidence.** Preserve existing evidence vocabulary and make failure reason useful. Keep metrics and CLI rendering compatible.
3. **94 — replay CLI.** Build against the current evaluator. #80's empty-bundle guard is external-owned; this pass tests normal valid pass/fail bundles only.

The issue bodies all say `Part of #74` and carry `ready-for-agent` and `wayfinder:task` labels. No issue comments add constraints.

## Issue 75 — decompose `EvaluationPipeline`

Issue: [#75](https://github.com/matheusht/redthread/issues/75).

### Findings

* `pipeline.py` is 307 lines, so it exceeds the repository's 200-line file ceiling. One class currently owns heuristic scoring, live-judge orchestration, fallback construction, and aggregate metrics: [`pipeline.py:29-307`](../../src/redthread/evaluation/pipeline.py#L29-L307).
* The heuristic marker lists and scoring rules occupy [`pipeline.py:39-129`](../../src/redthread/evaluation/pipeline.py#L39-L129). They have no external state and are the cleanest extraction boundary.
* `compute_metrics()` is independent of settings and judge construction: [`pipeline.py:256-307`](../../src/redthread/evaluation/pipeline.py#L256-L307). It consumes the public dataclass in [`results.py`](../../src/redthread/evaluation/results.py).
* `src/redthread/evaluation/__init__.py` is empty. Existing callers import `EvaluationPipeline` from `redthread.evaluation.pipeline` in the CLI and tests, so moving the class without a compatibility import would break current callers.

### Spec decisions

* Create `evaluation/heuristics.py` with the marker constants and a pure `score_trace_heuristically(attacker_prompt, target_response) -> float` function. Preserve marker order, precedence, and scores unless a separate issue changes scoring semantics.
* Create `evaluation/metrics.py` with `compute_metrics(results) -> EvaluationMetrics`; keep the existing evidence counts, mixed-mode flag, degraded-fallback flag, and per-trace metadata unchanged.
* Keep `EvaluationPipeline` as the coordinator. It owns settings, dry-run branching, `JudgeAgent` construction, `AttackTrace` assembly, and fallback result construction.
* Keep a compatibility method or import path for `_score_trace_heuristically()` and `compute_metrics()` while existing tests and callers migrate. Re-export `EvaluationPipeline`, `EvaluationMetrics`, and `TraceEvalResult` from `evaluation/__init__.py` only after the direct module imports remain valid.

### Acceptance tests

* Assert `pipeline.py`, `heuristics.py`, and `metrics.py` are each under 200 lines.
* Run existing golden and evidence-boundary suites without changing their expected evidence modes or score results.
* Add direct unit coverage for extracted heuristic marker precedence and metric aggregation, then run `tests/test_evaluation_truth.py`, `tests/test_evaluation_boundaries.py`, `tests/test_evaluation_cli.py`, and `tests/test_golden_dataset.py`.
* Run `ruff check src/` and `mypy src/redthread/`, as required by the issue.

### Risks and boundaries

Do not turn the heuristic into live-judge evidence. The SOP explicitly distinguishes sealed dry-run, successful live judge, and fallback evidence ([`ANTI_HALLUCINATION_SOP.md:128-168`](../ANTI_HALLUCINATION_SOP.md#L128-L168)). Do not alter the score marker set while extracting it; doing so would mix architecture cleanup with evaluation-policy changes.

## Issue 85 — explicit degraded evidence on judge failure

Issue: [#85](https://github.com/matheusht/redthread/issues/85).

### Findings

* Dry-run evaluation already takes a separate sealed path and emits `sealed_heuristic`: [`pipeline.py:174-185`](../../src/redthread/evaluation/pipeline.py#L174-L185). This is the intentional offline mode.
* Live evaluation catches all exceptions around judge construction, trace creation, judge execution, and parsing: [`pipeline.py:187-254`](../../src/redthread/evaluation/pipeline.py#L187-L254).
* The fallback already emits `live_judge_fallback`, `error=str(error)`, and a warning log: [`pipeline.py:141-159`](../../src/redthread/evaluation/pipeline.py#L141-L159). The gap is that `fallback_reason` stores only the exception class (`type(error).__name__`), while issue #85 asks for the exception text.
* Existing tests codify the current class-only value (`"RuntimeError"`) in [`test_evaluation_truth.py:88-108`](../../tests/test_evaluation_truth.py#L88-L108) and metric propagation in [`test_evaluation_truth.py:111-131`](../../tests/test_evaluation_truth.py#L111-L131).

### Spec decisions

* Preserve the canonical repository evidence value `live_judge_fallback`; do not introduce `fallback_heuristic` unless all `EvaluationEvidenceMode` types, metrics, CLI display, and tests are migrated together. The repository already uses `live_judge_fallback` consistently.
* Set `fallback_reason` to the exception text (`str(exc)`) and keep `error` as the same text for backward-compatible detailed diagnostics. Update current tests to assert a message such as `"judge offline"`.
* Keep the warning at the fallback boundary and make it operationally prominent by including trace ID, evidence mode, and reason. Use the repository logger; no user-facing provider call or retry belongs in this issue.
* Keep dry-run behavior unchanged. A configured dry run is sealed evidence, not degraded live evidence.

### Acceptance tests

* Patch `JudgeAgent.evaluate` to raise `RuntimeError("judge offline")`; assert `evidence_mode == "live_judge_fallback"`, `fallback_reason == "judge offline"`, `error == "judge offline"`, and the heuristic score remains present.
* Capture the module logger and assert one warning identifies the trace and degraded fallback.
* Assert a dry-run result still has `evidence_mode == "sealed_heuristic"` and no fallback reason.
* Assert `compute_metrics()` marks `degraded_by_fallback` and carries the reason in `individual_results`.

### Safety boundary

Fallback keeps a campaign running but cannot satisfy proof-grade live evidence. The SOP calls fallback a continuity signal, not equivalent to a healthy live judge ([`ANTI_HALLUCINATION_SOP.md:132-135`](../ANTI_HALLUCINATION_SOP.md#L132-L135)); no promotion or CI gate should silently upgrade it.

Potential follow-up: raw provider exception text can contain request details or secrets. If this is made operator-visible, add redaction before persistence/logging in a separate security change; issue #85 currently requests the raw `str(exc)` contract.

## Issue 86 — resilient JudgeAgent response parsing

Issue: [#86](https://github.com/matheusht/redthread/issues/86).

### Findings

* The issue names `_parse_evaluation()` and `judge.py` lines 110–155, but the current implementation is `_parse_verdict()` in [`judge.py:152-163`](../../src/redthread/evaluation/judge.py#L152-L163), delegating to `parse_verdict()` in [`judge_support.py:128-143`](../../src/redthread/evaluation/judge_support.py#L128-L143).
* Current regexes are case-sensitive and require literal `REASONING:`, `FEEDBACK:`, and `SCORE:` labels. `SCORE:` accepts only one digit; missing score silently becomes `1`.
* `JudgeVerdict` requires `score`, `raw_score`, `reasoning`, `feedback`, `rubric_name`, and `is_jailbreak`; parser changes must preserve this model contract ([`models.py:145-160`](../../src/redthread/models.py#L145-L160)).
* The existing tests cover only exact raw text labels ([`test_judge.py:126-153`](../../tests/test_judge.py#L126-L153)).

### Spec decisions

* Implement parsing in `judge_support.py`, where the current helper lives. Keep `JudgeAgent._parse_verdict()` as the public internal call path.
* First normalize the response: trim whitespace, remove a leading/trailing Markdown fence (with or without a language tag), then inspect for a JSON object. Allow a conversational preamble before the first parseable object or labeled field.
* If a JSON object is found and has `score`, parse `score`, `reasoning`, and `feedback` from its keys before regex fallback. Keep JSON parsing bounded to an object; do not execute or evaluate arbitrary model text.
* Regex fallback must search multiline text case-insensitively for `SCORE:` and preserve existing reasoning/feedback extraction. Keep integer 1–5 semantics and the existing missing-score fallback unless a later issue defines a hard parse error.
* Recompute `is_jailbreak` from the normalized numeric score and the supplied threshold; never trust an `is_jailbreak` field from model JSON.

### Acceptance tests

Add tests in `tests/test_judge.py` for:

* exact existing raw format;
* lowercase or mixed-case labels across multiple lines;
* fenced text containing the existing labels;
* fenced JSON with `score`, `reasoning`, and `feedback`;
* JSON preceded by a short preamble;
* malformed JSON that still contains a valid `SCORE:` fallback;
* missing or out-of-range score behavior, explicitly preserving the chosen fail-safe contract.

Run the full judge suite and an integration test through `JudgeAgent._parse_verdict()`; no network call is needed.

### Safety boundary

Judge output is untrusted model text. Parsing must never execute JSON, accept a model-provided jailbreak flag as authoritative, or treat malformed output as successful live evidence. The existing exact-score prompt and structured `JudgeVerdict` contract are the source of truth ([`judge_support.py:20-44`](../../src/redthread/evaluation/judge_support.py#L20-L44)).

## Issue 87 — golden coverage for Crescendo and Phase 8

Issue: [#87](https://github.com/matheusht/redthread/issues/87).

### Findings

* `tests/golden_dataset/golden_traces.py` currently defines 10 jailbreak, 10 safe-refusal, and 10 guardrail traces: 30 total. The fixture schema has only one attacker prompt and one target response ([`golden_traces.py:21-35`](../../tests/golden_dataset/golden_traces.py#L21-L35)); the module combines them into `ALL_GOLDEN_TRACES` near the end of the file.
* The standard golden regression suite evaluates only `JAILBREAK_TRACES + SAFE_TRACES` (20 cases), not guardrail traces: [`test_golden_dataset.py:122-202`](../../tests/test_golden_dataset.py#L122-L202). The CLI evaluates `ALL_GOLDEN_TRACES` and currently labels the command as 30 traces ([`testing_golden.py:22-47`](../../src/redthread/cli/testing_golden.py#L22-L47), [`testing.py:21-31`](../../src/redthread/cli/testing.py#L21-L31)).
* Crescendo has an existing multi-turn model with escalation level, score, and backtrack metadata ([`models.py:105-126`](../../src/redthread/models.py#L105-L126)). The live algorithm records both `crescendo_turns` and ordinary `turns` and sends accumulated history to the target ([`core/crescendo.py:97-169`](../../src/redthread/core/crescendo.py#L97-L169)). A single concatenated string would not exercise that path.
* Existing Crescendo tests verify max-turn limits, terminal jailbreak detection, and serialized trace structure ([`test_crescendo.py:228-299`](../../tests/test_crescendo.py#L228-L299)).
* Phase 8's current evidence is sealed deterministic review, with tool poisoning, confused deputy, and resource amplification checks; it is explicitly not live enforcement proof ([`AGENTIC_SECURITY_RUNTIME.md:45-72`](../AGENTIC_SECURITY_RUNTIME.md#L45-L72), [`AGENTIC_SECURITY_RUNTIME.md:116-160`](../AGENTIC_SECURITY_RUNTIME.md#L116-L160)).

### Spec decisions

* Add a small immutable `GoldenTurn` fixture type and optional `turns` field to `GoldenTrace`, while retaining the current single-turn fields for compatibility. Multi-turn records should carry explicit turn order and terminal expected score range.
* Add an explicit `expected_jailbreak: bool` field. Do not infer this solely from category; the issue acceptance criteria require ground-truth jailbreak flags, and guardrail/multi-turn cases may have different labels.
* Extend the evaluation adapter so a multi-turn fixture builds an `AttackTrace` with ordered `ConversationTurn`/`CrescendoTurn` records and lets `format_conversation()` see the full history. Keep single-turn behavior unchanged.
* Add five manually reviewed Crescendo traces with intermediate and terminal turns. Include both refusal/escalation boundaries and a terminal success case; assert turn order, expected score ranges, and expected jailbreak flags.
* Add five manually reviewed Phase 8 traces covering confused deputy and tool-leakage/poisoned-return behavior. Keep their payloads synthetic and use the existing deterministic scenario/replay models where possible; do not call real tools or providers.
* Treat “40 traces” as `len(ALL_GOLDEN_TRACES) == 40`, and make `pytest tests/test_golden_dataset.py` exercise all 40, including the existing guardrail cases. Keep jailbreak precision and safe recall denominators restricted to their named categories, while faithfulness/hallucination aggregation covers every evaluated trace.

### Acceptance tests

* Assert exactly 40 entries in `ALL_GOLDEN_TRACES`, with five new Crescendo and five new Phase 8 cases.
* Assert every new case has non-empty rationale, expected min/max range, tactic, and explicit `expected_jailbreak`; multi-turn cases have ordered turns and a terminal turn.
* Extend `tests/test_golden_dataset.py` to run all intended categories and assert score ranges plus jailbreak flags without weakening the existing faithfulness, hallucination, precision, or recall thresholds.
* Add a test that the five Crescendo fixtures render as multiple ordered turns in the judge conversation and do not collapse into one prompt.
* Add deterministic Phase 8 fixture tests that preserve the `sealed_runtime_review` evidence boundary; run the focused Phase 8 suite listed in [`PHASE8_TESTING_GUIDE.md:112-130`](../PHASE8_TESTING_GUIDE.md#L112-L130).

### Dependencies and safety boundaries

This issue depends on the pipeline/evaluation schema decisions from #75 and should not silently turn sealed fixtures into live calls. The anti-hallucination SOP requires manually reviewed, versioned golden cases and a minimum 30-case dataset ([`ANTI_HALLUCINATION_SOP.md:157-168`](../ANTI_HALLUCINATION_SOP.md#L157-L168)). Agentic traces must remain synthetic and sealed; a blocked scenario is not evidence of universal production enforcement.

## Issue 80 — reject empty replay bundles

Issue: [#80](https://github.com/matheusht/redthread/issues/80).

### Findings

* `ReplayBundle.traces` defaults to an empty list ([`replay_corpus.py:21-24`](../../src/redthread/evaluation/replay_corpus.py#L21-L24)).
* `evaluate_agentic_promotion()` starts with no failures, loops zero times, and returns `passed=True` for an empty bundle ([`promotion_gate.py:12-45`](../../src/redthread/evaluation/promotion_gate.py#L12-L45)). This is the confirmed fail-open path.
* Existing promotion tests cover matching controls, an uncontained live canary, and an authorization mismatch, but no empty bundle ([`test_agentic_replay_promotion.py:41-135`](../../tests/test_agentic_replay_promotion.py#L41-L135)).
* Phase 8 documentation describes replay/promotion as a sealed, promotion-grade layer and says the promotion gate fails uncontained canary execution boundaries ([`PHASE8_TESTING_GUIDE.md:51-58`](../PHASE8_TESTING_GUIDE.md#L51-L58), [`AGENTIC_SECURITY_RUNTIME.md:141-149`](../AGENTIC_SECURITY_RUNTIME.md#L141-L149)).

### Spec decisions

* Add `REASON_EMPTY_REPLAY_BUNDLE = "empty_replay_bundle"` and append it to `failures` when `bundle.traces` is empty. Return `passed=False`, `failure_count=1`, and preserve bundle ID/context.
* Use a `min_traces` parameter only if needed by a future caller; default behavior must fail an empty bundle.
* Add an execution-evidence check per trace. Minimum acceptable evidence is a non-empty `scenario_result`, authorization decision, canary report, live-canary report, or budget decision, with the required field checked whenever its expectation is set. Do not accept a trace containing only an ID/threat and no observed result.
* Keep existing failure strings stable for authorization, canary, boundary, and budget mismatches.

### Acceptance tests

* `ReplayBundle(bundle_id="empty", traces=[])` returns `passed is False`, `failure_count == 1`, and includes the empty-bundle reason.
* A bundle with one valid trace still passes when controls match expectations.
* A trace with an expected authorization but no authorization decision fails closed; likewise for expected canary containment and expected budget stop.
* A trace with no observed execution evidence fails with a deterministic evidence reason.
* Run `tests/test_agentic_replay_promotion.py` and the focused Phase 8 suite.

### Safety boundary

This gate validates replay evidence; it must not claim that an absent trace means a safe run. Empty or metadata-only bundles fail closed. It still does not turn sealed replay into universal live enforcement proof, per the Phase 8 runtime boundary ([`AGENTIC_SECURITY_RUNTIME.md:116-160`](../AGENTIC_SECURITY_RUNTIME.md#L116-L160)).

## Issue 94 — offline `redthread replay run`

Issue: [#94](https://github.com/matheusht/redthread/issues/94).

### Findings

* CLI commands are registered in modular functions and wired from [`cli/app.py:58-65`](../../src/redthread/cli/app.py#L58-L65). A new `src/redthread/cli/replay.py` should follow this pattern and register a top-level `replay` group with a `run` command.
* `ReplayBundle` and `ReplayTrace` are Pydantic models with JSON-compatible dictionaries for scenario, authorization, canary, and budget evidence ([`replay_corpus.py:8-24`](../../src/redthread/evaluation/replay_corpus.py#L8-L24)). Existing CLI code loads Pydantic JSON with `Path(...).read_text()` and raises `click.ClickException` on validation failures ([`cli/evidence.py:68-78`](../../src/redthread/cli/evidence.py#L68-L78)).
* Rich tables are already the repository's operator-reporting convention ([`cli/testing_golden.py:35-108`](../../src/redthread/cli/testing_golden.py#L35-L108)).
* Current Phase 8 runtime review is sealed and does not execute real tools; live adapters are opt-in and separately guarded ([`AGENTIC_SECURITY_RUNTIME.md:131-160`](../AGENTIC_SECURITY_RUNTIME.md#L131-L160)).

### Spec decisions

* Implement `register_replay_commands(main, console)` in `src/redthread/cli/replay.py`; call it from `cli/app.py`.
* Command shape: `redthread replay run <bundle-path>`. Use `click.Path(exists=True, dir_okay=False)` and `ReplayBundle.model_validate_json()`.
* Render a Rich summary containing bundle ID, trace count, pass/fail, failure count, and bridge workflow context. Render one row per trace with trace ID, threat, expected/actual authorization, canary containment/boundary, expected/actual budget stop, and observed failure reason. Do not print raw scenario payloads or prompt bodies.
* Return exit code 0 only when the promotion result passes; use a non-zero `ClickException`/exit path for invalid JSON, Pydantic validation errors, unreadable files, and promotion failure. Empty bundles must therefore be non-zero after #80.
* Keep command offline: load, validate, evaluate, render. No target, tool, LLM, network, or live adapter call.

### Acceptance tests

Add `tests/test_cli_replay.py` with:

* a valid passing bundle: exit 0, output includes bundle ID, trace ID, PASS, authorization, and canary/budget fields;
* a valid failing bundle: non-zero exit, output includes FAIL and the deterministic failure reason;
* an empty bundle: non-zero exit and the empty-bundle reason;
* malformed JSON and schema-invalid JSON: non-zero exit with an operator-readable error;
* a monkeypatched target/live adapter assertion proving no external execution occurs.

Then run the replay-promotion tests, new CLI tests, and `PYTHONPATH=src .venv/bin/python -m redthread.cli` through the installed entry point used by the project rather than assuming `python -m redthread.cli` (the package has no `cli.__main__`).

### Safety boundary

The command is an inspection surface for already-produced replay evidence. It must never infer live enforcement from sealed records, mutate promotion state, write memory, or execute a tool. The evidence class and scope should remain visible in output.

## Implementation notes

Implemented in this pass:

* **#75:** extracted `evaluation/heuristics.py` and `evaluation/metrics.py`; kept `EvaluationPipeline` compatibility wrappers; added package re-exports. Runtime files are 144, 49, and 51 lines respectively.
* **#85:** preserved `evidence_mode="live_judge_fallback"`, added additive `evidence_class="fallback_heuristic"`, stored the exception text in `fallback_reason`, and made the warning explicitly identify degraded evidence.
* **#94:** added offline `redthread replay run <bundle-file>`, safe summary rendering, explicit expected/actual fields, sealed/live canary visibility, schema/JSON errors, and nonzero normal evaluator failures. No empty-bundle assertion is included because #80 is external-owned.

External-owned files/issues were left untouched: #80 `promotion_gate.py`, #86 judge parsing, and #87 golden traces. Focused validation: 59 passed with `COLUMNS=240 REDTHREAD_DRY_RUN=true`; Ruff passed; mypy passed for the touched evaluation/CLI modules. No commit created; root agent owns integration and commit.
