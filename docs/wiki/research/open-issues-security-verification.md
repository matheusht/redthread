---
title: Open Issues Security Verification
type: research
status: implemented
summary: Focused verification record for strict authorization arguments, authoritative sensitivity, and specialized agent-chain routing in issues 78, 79, and 82.
source_of_truth:
  - src/redthread/tools/authorization/engine.py
  - src/redthread/tools/authorization/validation.py
  - src/redthread/tools/authorization/sensitivity.py
  - src/redthread/orchestration/supervisor_graph.py
  - src/redthread/orchestration/agents/specialized_adapter.py
  - src/redthread/orchestration/agents/transport.py
  - tests/test_authorization_runtime_security.py
  - tests/test_specialized_agent_supervisor.py
updated_by: codex
updated_at: 2026-09-18
---

# Open Issues Security Verification

## Scope

This page records implementation evidence for [#78](https://github.com/matheusht/redthread/issues/78), [#79](https://github.com/matheusht/redthread/issues/79), and [#82](https://github.com/matheusht/redthread/issues/82). It complements the [security/runtime research and specification](../../research/open-issues-security-runtime.md) and the [open-issues specification](../../research/open-issues-spec.md).

Issues #81, #83, #84, and #93 remain externally owned and are excluded from this verification. In particular, this page makes no worker-timeout or cancellation claim for #83.

## Verified behavior

### #78: scalar argument policy validation

`AuthorizationPolicy.argument_schema` declares a scalar `ArgumentRule` for each accepted key. Rules specify scalar type, maximum string length, and whether a string is a path or command. Validation runs before authorization policy evaluation. It rejects control characters, unknown keys, missing required keys, wrong scalar types, over-limit values, unsafe path traversal or absolute paths, and shell metacharacters in command values. Every supplied key must have a typed rule; an untyped key allowlist cannot bypass this contract. [`ArgumentRule`](../../../src/redthread/tools/authorization/models.py#L12-L18) and [`validate_arguments`](../../../src/redthread/tools/authorization/validation.py#L26-L94) define this contract.

Empty argument dictionaries retain the existing low-risk fallback behavior. Nonempty calls without a policy schema or the small default schema for an established safe capability are denied with `reason_code=invalid_arguments`. Valid scalar calls such as the existing tenant lookup remain compatible through the declared safe schemas in [`validation.py`](../../../src/redthread/tools/authorization/validation.py#L13-L19) and the read-only presets in [`presets.py`](../../../src/redthread/tools/authorization/presets.py).

The focused regression tests prove traversal-shaped input is denied before a read grant, an unrecognized argument key is denied even when listed as an untyped allowed key, and the existing authorization, lineage, live-intercept, and scenario seams continue to pass. See [`test_authorization_runtime_security.py`](../../../tests/test_authorization_runtime_security.py#L19-L55).

### #79: authoritative sensitivity

`AuthorizationEngine` starts with an engine-owned catalog and merges an explicitly supplied operator catalog. It considers the maximum sensitivity found for the capability, tool name, and resource selector values (`resource`, `resource_id`, `target`, `path`, `table`, `url`, or `domain`). The effective sensitivity is never lower than the authoritative catalog value. A caller assertion below that value receives `reason_code=sensitivity_spoofed`; an existing escalation policy remains an escalation decision and carries the reason code. [`AuthorizationEngine`](../../../src/redthread/tools/authorization/engine.py#L44-L90) and [`authoritative_sensitivity`](../../../src/redthread/tools/authorization/sensitivity.py#L8-L36) define the behavior.

The default catalog treats sensitive capabilities such as `db.write`, `secrets.read`, `shell.exec`, and `system.update` as high sensitivity. Catalog entries are operator-owned configuration passed to the engine; caller-provided `target_sensitivity` cannot downgrade them. This slice does not claim that the catalog proves resource access or replaces provider-side controls.

The focused test marks `secrets.read` high, submits a low caller assertion, and verifies escalation plus the stable spoof reason code. Existing precedence and trusted-secret compatibility tests pass alongside it.

### #82: specialized agent-chain routing

`AlgorithmType.AGENT_CHAIN` is accepted by settings and the CLI choice in [`run.py`](../../../src/redthread/cli/run.py#L71-L80). Supervisor fan-out sends this algorithm to `specialized_attack_worker`; other algorithms continue to use `attack_worker`. [`fan_out_attack_workers`](../../../src/redthread/orchestration/supervisor_routing.py#L15-L35) and [`build_supervisor_graph`](../../../src/redthread/orchestration/supervisor_graph.py#L37-L65) show the branch.

The specialized worker runs Recon → Social → Exploit through [`run_specialized_attack`](../../../src/redthread/orchestration/agents/specialized_adapter.py#L54-L104), then converts phase turns to the existing `AttackTrace`/`AttackResult` contract. Production phase sends use the shared execution/canary helper with an agent-chain trace identifier; recon probes remain isolated while social and exploit target turns share one target conversation so target history is preserved ([`send_agent_message`](../../../src/redthread/orchestration/agents/transport.py#L12-L38)). Phase failures are retained in trace metadata and the worker error field, incrementing collection failure counters; a failed exploit is marked failed rather than completed. The judge passes an error trace through without upgrading it.

The specialized heuristic is diagnostic metadata only. The adapter emits a non-jailbreak verdict, and the normal supervisor Judge stage remains responsible for independent confirmation before defense routing. The adapter contains no timeout implementation; timeout ownership remains with #83.

## Verification evidence

Focused verification ran with fixed terminal width and dry-run environment:

```text
PYTHONPATH=src COLUMNS=240 REDTHREAD_DRY_RUN=true .venv/bin/pytest -q \
  tests/test_authorization_runtime_security.py \
  tests/test_authorization_engine.py \
  tests/test_authorization_precedence.py \
  tests/test_agentic_security_scenarios.py \
  tests/test_live_authorization_smoke.py \
  tests/test_live_execution_interceptor.py \
  tests/test_agents.py \
  tests/test_specialized_agent_supervisor.py \
  tests/test_supervisor.py \
  tests/test_attack_runner_registry.py
56 passed
```

Ruff passed for the changed security/runtime modules and focused tests. Mypy passed for the same source set. The focused run covers authorization engine and policy precedence, agentic-security scenarios, live authorization/interception, the isolated specialized agents, supervisor routing, result conversion, and the existing attack-runner registry.

## Operator notes and boundaries

Use `redthread run --algorithm agent_chain` to select the specialized branch. The chain still uses the normal campaign result and Judge stages. Authorization policy authors must declare a typed `argument_schema` for every supplied argument; a bare capability grant does not authorize arbitrary parameters.

The catalog and schemas are deterministic pre-execution controls. They do not make shell interpolation, filesystem APIs, or network clients safe by themselves. Specialized phase heuristics do not establish confirmed jailbreak evidence or promotion evidence.

## Sources

- [Agentic security runtime contract](../../AGENTIC_SECURITY_RUNTIME.md)
- [Security/runtime research and specification](../../research/open-issues-security-runtime.md)
- [Open-issue implementation specification](../../research/open-issues-spec.md)
- [Issue #78](https://github.com/matheusht/redthread/issues/78), [issue #79](https://github.com/matheusht/redthread/issues/79), [issue #82](https://github.com/matheusht/redthread/issues/82)
