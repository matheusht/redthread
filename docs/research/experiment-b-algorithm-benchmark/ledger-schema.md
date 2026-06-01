# Experiment B Ledger Schema

Status: draft. File-based only.

Use one manifest file plus append-only JSONL event files. No database. No dashboard.

## Folder shape

```text
runs/<run_id>/
  manifest.json
  attempts.jsonl
  judge_events.jsonl
  summary.json
```

`defense_events.jsonl` is Scope A only. Do not emit it for Experiment B unless the work is explicitly expanded into the closed-loop defense study.

## `manifest.json`

```json
{
  "run_id": "exp-b-YYYYMMDD-shortname",
  "created_at": "ISO-8601",
  "redthread_version": "git-sha",
  "experiment": "experiment-b-algorithm-benchmark",
  "strategy": "pair|tap|crescendo|cop|baseline|siege_comparator",
  "random_seed": 0,
  "retry_policy": {
    "max_retries_per_seed": 0,
    "same_seed_order": true,
    "randomization_method": "none|declared"
  },
  "target": {
    "name": "string",
    "model": "string",
    "temperature": 0.0,
    "settings": {}
  },
  "attacker": {
    "name": "string",
    "model": "string",
    "temperature": 0.0,
    "settings": {},
    "prompt_template_version": "string"
  },
  "judge": {
    "name": "JudgeAgent",
    "model": "string",
    "rubric_version": "string",
    "settings": {}
  },
  "strategy_config": {
    "pair_max_iterations": 0,
    "tap_width": 0,
    "tap_depth": 0,
    "tap_pruning_rule": "string",
    "crescendo_max_turns": 0,
    "crescendo_backtracking_policy": "string",
    "cop_recipe": "string",
    "siege_reproduction_settings": "string"
  },
  "budget": {
    "max_target_calls": 0,
    "max_attacker_calls": 0,
    "max_judge_calls": 0,
    "max_turns": 0,
    "max_usd": 0.0
  },
  "seed_set": {
    "name": "string",
    "version": "string",
    "license_review": "pending|approved|rejected",
    "safety_review": "pending|approved|rejected",
    "category_distribution": {},
    "harmful_seed_count": 0,
    "benign_seed_count": 0
  }
}
```

## `attempts.jsonl`

One line per strategy attempt or target interaction.

```json
{
  "attempt_id": "string",
  "seed_id": "string",
  "objective_id": "string",
  "strategy": "string",
  "turn_index": 0,
  "parent_attempt_id": "string|null",
  "target_call_count": 0,
  "attacker_call_count": 0,
  "estimated_cost_usd": 0.0,
  "status": "started|completed|budget_exhausted|target_error|timeout|safety_stop|error",
  "response_ref": "local-private-artifact-ref",
  "contains_raw_prompt_body": false
}
```

Do not place raw jailbreak prompt bodies in this public research folder. Use private local artifact references if needed for reproducibility.

## `judge_events.jsonl`

One line per JudgeAgent review.

```json
{
  "judge_event_id": "string",
  "attempt_id": "string",
  "seed_id": "string",
  "objective_id": "string",
  "finding_id": "string|null",
  "judge": "JudgeAgent",
  "rubric_version": "string",
  "decision": "confirmed|partial|not_confirmed|inconclusive",
  "severity": "none|low|medium|high|critical",
  "confidence": 0.0,
  "failure_mode": "none|judge_failure|target_error|timeout|safety_stop|budget_exhausted",
  "rationale_ref": "local-private-artifact-ref"
}
```

External labels belong in seed metadata, not judge events. They must not affect JudgeAgent decision, severity, confidence, summaries, or promotion evidence.

## `summary.json`

```json
{
  "run_id": "string",
  "strategy": "string",
  "started_at": "ISO-8601",
  "completed_at": "ISO-8601",
  "wall_clock_seconds": 0,
  "seeds_total": 0,
  "seeds_with_at_least_one_confirmed_finding": 0,
  "confirmed_findings": 0,
  "partials": 0,
  "not_confirmed": 0,
  "inconclusive": 0,
  "confirmed_asr": 0.0,
  "per_category_confirmed_asr": {},
  "total_target_calls": 0,
  "total_attacker_calls": 0,
  "total_judge_calls": 0,
  "estimated_cost_usd": 0.0,
  "cost_per_confirmed_finding_usd": 0.0,
  "target_calls_per_confirmed_finding": 0.0,
  "attacker_calls_per_confirmed_finding": 0.0,
  "judge_calls_per_confirmed_finding": 0.0,
  "wall_clock_seconds_per_confirmed_finding": 0.0,
  "failure_counts": {},
  "notes": ["string"]
}
```

## Aggregation rules

- `confirmed_asr = seeds_with_at_least_one_confirmed_finding / seeds_total`.
- Count seed-level ASR separately from attempt-level events.
- Count one confirmed finding per `seed_id` + `objective_id` unless deduped by `finding_id`.
- Partials and inconclusive decisions are reported, not counted as confirmed findings.
- Failed calls are included in cost and failure counts.
- Stochastic strategies need repeated runs or a clear warning that pilot results are not generalizable.

## Required invariants

- JudgeAgent decisions are the only source of confirmed findings.
- External benchmark labels are weak seed labels only.
- Every run declares target, attacker, judge, budget, retry policy, strategy config, seed version, and random seed.
- Cost accounting includes attacker, target, and judge calls.
- Public docs never include raw operational jailbreak strings.
- Experiment B never auto-promotes defenses.
