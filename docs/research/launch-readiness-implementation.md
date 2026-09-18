# Launch-readiness implementation (#19)

Status: first version implemented. Scope covers the named `launch-readiness` preset and its evidence gate. It does not certify production safety or promote a defense.

## Delivered

- `LaunchReadinessConfig` defines the required `pair`, `tap`, and `crescendo` campaigns, live JudgeAgent evidence, live exploit replay, live benign replay, diagnostic-only fallback handling, and a zero unresolved-high-finding limit (`src/redthread/launch_readiness/models.py`, `LaunchReadinessConfig`).
- `run_launch_campaigns` invokes every required strategy through an injected normal campaign runner and captures failures as blocked evidence (`src/redthread/launch_readiness/coordinator.py`, `run_launch_campaigns`). The CLI adapter wires that runner to `RedThreadEngine.run()` once per strategy (`src/redthread/launch_readiness/cli.py`, `execute_launch_readiness`). Canonical CLI invocation is `redthread run --preset launch-readiness`; `agent_chain` is also accepted by the existing `--algorithm` choice for the security-runtime handoff (`src/redthread/cli/run.py`).
- The evaluator requires per-trace live JudgeAgent status and rejects error/skipped traces. Clean traces require matching scoped `live_baseline_replay` evidence; confirmed jailbreak traces require matching defense records whose validation is explicit `live_replay` with nonempty passing exploit and benign cases (`evaluate_launch_readiness`, `replay_status`). Sealed replay, score-only inference, campaign runtime mode, and arbitrary metadata booleans cannot satisfy those gates.
- Decisions are `ready`, `conditional`, or `blocked`; missing strategy/evidence or unresolved high findings block. Fallback remains diagnostic-only and defense `promotable` stays false because this surface does not perform defense promotion (`build_launch_gate`).
- Executive Markdown prints decision and gates before findings. The JSON packet contains bounded counts/statuses plus an explicit reproduction-details placeholder; prompts and responses are omitted (`src/redthread/launch_readiness/packet.py`, `render_executive_markdown`, `build_sanitized_packet`; `src/redthread/launch_readiness/outputs.py`, `write_launch_reports`). Human review remains required before release. Each successful strategy also receives the existing standard report bundle under `reports/launch-readiness/strategies/<strategy>/` (or the supplied report directory), with direct Markdown/JSON/SARIF exports suffixed by strategy and internal sidecars preserved. Aggregate launch Markdown/JSON default to `reports/launch-readiness/`.

## Focused verification

`COLUMNS=240 REDTHREAD_DRY_RUN=true PYTHONPATH=src .venv/bin/pytest -q tests/test_launch_readiness.py` → **16 passed**.

`ruff check` passed for launch modules, `cli/run.py`, replay-baseline seams, and the focused test. `mypy` passed for 15 touched source modules.

Tests cover clean required evidence, missing strategy, mixed missing judge/sealed replay evidence, fallback non-promotion, unresolved high findings, sanitized packet output, executive ordering, coordinator failure capture, report persistence, invalid preset strategies, baseline replay seam behavior, baseline scope matching, mixed-trace provenance, and CLI execution across all three strategies with both ready and blocked baseline replay outcomes (`tests/test_launch_readiness.py`). Full suite remains parent-owned.

## Limits and handoff

The preset reports evidence for observed campaign scope. Scope uplift and capability uplift remain unknown; no universal safety claim is inferred from scores or detector output. In live mode, clean traces invoke the existing replay runner baseline seam (`DefenseReplayRunner.run_live_baseline`) with the target system prompt and retain only case outcomes, trace IDs, and a scope hash. The baseline uses the final available attacker turn as one bounded single-turn probe; it does not claim full multi-turn replay coverage. Campaigns with findings additionally require matching live candidate validation records. Dry-run/sealed evidence remains blocked. Missing evidence remains blocked. Launch mode supports `--report-md`, `--report-json`, `--report-sarif`, `--report-dir`, and internal sidecars; per-strategy standard reports use the same existing persistence path.
