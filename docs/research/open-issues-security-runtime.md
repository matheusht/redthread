# Open security/runtime issues: research and implementation specification

Date: 2026-09-18
Status: research and implementation complete; integrated review pending
Scope: issues #78, #79, and #82 from [map issue #74](https://github.com/matheusht/redthread/issues/74)

This note follows the repository's Research → Plan → Implement workflow. It records current code facts, decisions for the next implementation pass, acceptance tests, dependencies, and safety boundaries. Initial research made no runtime changes. Subsequent implementation and focused verification are recorded in the linked wiki verification page.

## Sources and baseline

Primary sources used:

- GitHub issue bodies: [#78](https://github.com/matheusht/redthread/issues/78), [#79](https://github.com/matheusht/redthread/issues/79), and [#82](https://github.com/matheusht/redthread/issues/82).
- Repository decision tree: [`docs/AGENT_DECISION_TREE.md`](../AGENT_DECISION_TREE.md), which routes this work to [`docs/AGENTIC_SECURITY_RUNTIME.md`](../AGENTIC_SECURITY_RUNTIME.md).
- Runtime contract: [`docs/AGENTIC_SECURITY_RUNTIME.md`](../AGENTIC_SECURITY_RUNTIME.md), especially its sealed-versus-live evidence boundary and shared-send containment notes.
- Current implementation and tests cited below by path and line anchor.

Focused baseline passed before this note was written:

```text
PYTHONPATH=src .venv/bin/pytest -q \
  tests/test_authorization_engine.py \
  tests/test_agents.py \
  tests/test_supervisor.py
25 passed
```

## Current execution map

| Issue | Current path | Research finding |
| --- | --- | --- |
| #78 | `ActionEnvelope` → `AuthorizationEngine.authorize()` → live authorization seams | Envelope arguments are scalar-typed but semantically unchecked; policy matching only checks actor role and capability. |
| #79 | `ActionEnvelope.target_sensitivity` → authorization policy checks | Sensitivity is caller-asserted; there is no authoritative resource catalog or resource identifier. |
| #82 | CLI/settings → supervisor fan-out → attack worker → attack registry | Specialized Recon → Social → Exploit code exists and has unit coverage, but no supervisor or CLI branch invokes it. |

## Issue #78 — strict `ActionEnvelope` argument validation

### Observed code

`ActionEnvelope.arguments` accepts a dictionary of scalar values and has no path, domain, size, or per-capability schema (`src/redthread/orchestration/models/agentic_security.py:L106-L114`). `AuthorizationEngine._matches_allowed_policy()` returns true when only `actor_role` and `capability` match (`src/redthread/tools/authorization/engine.py:L145-L146`); `_matches_denied_policy()` has the same role/capability shape plus a trust-level condition (`engine.py:L137-L143`). The issue's proposed `PolicyRule` type does not exist. The actual policy model is `AuthorizationPolicy` with role/capability lists (`src/redthread/tools/authorization/models.py:L10-L20`).

The current decision model carries a human-readable `reason` but no stable reason-code field (`src/redthread/orchestration/models/agentic_security.py:L94-L103`). Current tests cover lineage, capability, sensitivity, and fallback decisions, but no argument tampering (`tests/test_authorization_engine.py:L1-L180`).

### Spec decisions

1. Extend `AuthorizationPolicy`, not a new `PolicyRule` name, with optional argument constraints. Keep the constraints policy-owned and capability-specific. A policy grant without a schema for a capability that needs resource validation must not silently become an unrestricted grant.
2. Add stable machine-readable reason codes, including `REASON_INVALID_ARGUMENTS`, while retaining the existing human-readable `reason`. Do not encode a code by replacing all existing explanatory strings.
3. Validate semantic arguments before policy matching. A malformed request returns `DENY` with `REASON_INVALID_ARGUMENTS`; valid requests preserve the existing precedence documented in [`docs/AGENTIC_SECURITY_RUNTIME.md`](../AGENTIC_SECURITY_RUNTIME.md): permission inheritance, deny, escalate, allow, then safe fallback.
4. Canonicalize paths before checking roots. Reject `..` traversal, NUL/control characters, and absolute paths unless the policy explicitly allows that root. Reject unknown argument keys, missing required keys, wrong scalar types, and configured size limits.
5. Do not apply a global shell-metacharacter blacklist to every string. Query text, tenant names, and report labels may contain punctuation legitimately. For shell execution, require an explicit argument schema and an argv-style representation; the eventual executor must still avoid shell interpolation. Authorization is a gate, not a safe shell implementation.
6. Preserve fail-closed behavior for high-risk capabilities. A known high-risk capability with no applicable argument schema must not be allowed by a generic role/capability rule.

### Acceptance tests for implementation

- A read policy with a declared `path` root denies `../../etc/shadow` and equivalent normalized traversal with `decision=DENY` and `reason_code=REASON_INVALID_ARGUMENTS`.
- A restricted path policy denies an unapproved absolute path and allows a normalized path inside its configured root.
- A policy rejects an unknown argument key, a missing required key, a wrong scalar type, and an over-limit value.
- A configured command policy rejects shell metacharacters or shell-string input while allowing an explicit safe argv shape.
- A valid `tenant=acme-prod` lookup still matches the current read-only policy and remains allowed.
- Existing lineage and capability tests continue to pass; malformed input does not reach a provider or tool execution seam.

Suggested coverage location: extend `tests/test_authorization_engine.py`; add a dedicated argument-constraint fixture only if the test file approaches the 200-line repository limit.

## Issue #79 — authoritative target sensitivity

### Observed code

`ActionEnvelope.target_sensitivity` is a free string supplied by the caller (`src/redthread/orchestration/models/agentic_security.py:L106-L114`). The engine compares that value directly against policy thresholds in both allow and escalate paths (`src/redthread/tools/authorization/engine.py:L78-L135`). Unknown sensitivity strings map to the highest numeric level through `SENSITIVITY_ORDER.get(..., 2)` (`engine.py:L148-L149`), but a caller can assert `low` for a genuinely sensitive target and thereby pass a medium threshold. No resource ID exists in the envelope; the only stable identity fields are `capability` and `tool_name`.

### Spec decisions

1. Add an engine-owned sensitivity catalog, injected when constructing `AuthorizationEngine`. The first slice keys entries by canonical capability/tool name because the current envelope has no resource field. The catalog may later add resource selectors after #78 supplies safe argument matching.
2. For catalogued capabilities, policy evaluation uses authoritative sensitivity, never the caller's lower assertion. If the assertion is lower than the catalog value, return `DENY` or `ESCALATE` according to the policy's safe behavior, with `REASON_SENSITIVITY_SPOOFED`; do not allow the lower value to influence threshold checks.
3. A higher caller assertion is conservative. It may escalate, but it can never lower the catalog value. This preserves safety while retaining useful operator visibility that the caller over-classified an action.
4. Do not change the existing unknown trusted low-risk fallback for unclassified read-only capabilities in this slice; current compatibility coverage expects `docs.search` to default to allow. Unknown high-risk capabilities remain subject to the existing trusted escalation path. Known sensitive capabilities must be catalogued before a policy can allow them.
5. Keep sensitivity evidence in authorization decisions. A spoof event is an authorization finding, not proof that a target resource was actually accessed.

### Acceptance tests for implementation

- A catalog entry marking `secrets.read` or a critical resource as high causes an envelope asserting `low` to return `DENY` or `ESCALATE` with `REASON_SENSITIVITY_SPOOFED`.
- A high caller assertion cannot cause a catalogued high resource to be evaluated as low or medium.
- A catalogued medium action at a medium policy threshold remains eligible for the policy's normal decision.
- An unknown trusted low-risk read retains the current default-allow compatibility behavior; an unknown trusted high-risk capability still escalates.
- The test proves the catalog, not the caller's envelope field, controls the threshold comparison.

Suggested coverage location: `tests/test_authorization_engine.py`, beside the current sensitivity and fallback tests (`L100-L180`).

## Issue #82 — specialized agent chain in supervisor/CLI

### Observed code

The specialized graph is complete in isolation: `build_specialized_agent_graph()` links `recon → social → exploit` (`src/redthread/orchestration/agents/agent_chain.py:L18-L30`), and `run_specialized_pipeline()` executes the three injected/default agents sequentially (`agent_chain.py:L33-L56`). Its tests cover each node, the pipeline, and graph construction (`tests/test_agents.py:L1-L140`).

The production supervisor graph registers only `generate_personas`, generic `attack_worker`, collection, judge, agentic review, defense, and finalize (`src/redthread/orchestration/supervisor_graph.py:L18-L48`). Fan-out always sends to `attack_worker` (`src/redthread/orchestration/supervisor_routing.py:L12-L35`). `AlgorithmType` has only PAIR, TAP, Crescendo, and MCTS (`src/redthread/config/types.py:L8-L14`); the default attack registry registers only those four (`src/redthread/core/attack_runner.py:L56-L80`); and the CLI's `--algorithm` choice omits `agent_chain` (`src/redthread/cli/run.py:L63-L74`).

The specialized nodes send directly through their target objects and produce an `AgentPhaseState`, whose `turns` entries are plain dictionaries (`src/redthread/orchestration/agents/models.py:L10-L22`). They also use a heuristic `is_jailbreak` result inside `ExploitAgent`; that is not equivalent to the existing JudgeAgent confirmation boundary.

### Spec decisions

1. Add `AlgorithmType.AGENT_CHAIN` and the CLI choice. Keep existing algorithms and defaults unchanged.
2. Add a dedicated supervisor branch/worker for this algorithm. Do not force the phase-state object into the generic attack-runner registry without an adapter. The branch should pass persona, target system prompt, and settings metadata into the specialized pipeline, then convert the phase output into the existing `AttackTrace`/`AttackResult` contract.
3. Preserve the existing judge stage after conversion. The specialized heuristic is diagnostic only; it must not route directly to defense or become confirmed jailbreak evidence.
4. Convert each phase turn into a `ConversationTurn` with explicit phase metadata. Record pipeline errors as an `AttackOutcome.ERROR` result with a non-success verdict and an error marker, so the supervisor can report degraded runtime truth consistently.
5. Route all production target sends through the existing shared execution/canary metadata seam where possible. The specialized path must not create an authorization or canary bypass while being wired into the supervisor.
6. Share the worker timeout contract from #83 with this branch. Recon probes and social/exploit sends are part of one bounded worker operation.

### Acceptance tests for implementation

- `RedThreadSettings(algorithm="agent_chain")` validates and `redthread run --algorithm agent_chain` reaches the specialized branch.
- Fan-out routes `agent_chain` sends to the specialized worker and leaves PAIR/TAP/Crescendo/MCTS routing unchanged.
- A supervisor test with injected fake Recon, Social, and Exploit agents proves phase order, `AttackResult` conversion, and post-chain JudgeAgent routing.
- A heuristic exploit response cannot skip JudgeAgent confirmation or create a defense record by itself.
- A specialized worker error is represented in the normal worker/error counters and does not crash graph finalization.
- A slow specialized phase is bounded by the #83 worker timeout.

Suggested coverage location: extend `tests/test_agents.py` for the adapter and `tests/test_supervisor.py` for graph/CLI routing; add `tests/test_attack_graph_agent_chain.py` only if the adapter deserves an isolated contract test.

## Overlap, dependencies, and implementation order

Recommended dependency graph:

```text
#78 argument contract ──> #82 specialized branch must use safe action/result seams
#79 sensitivity catalog ─> #82 specialized actions must not bypass authorization
```

Implementation order:

1. #78: establish argument constraints and reason-code shape.
2. #79: add authoritative sensitivity lookup and spoof handling using the #78 matching seam.
3. #82: wire the specialized branch and preserve the shared worker/result seams.

#81, #83, #84, and #93 are external-owned tickets for this pass. #82 must consume their eventual public contracts where relevant: scoped authorization from #81, timeout/cancellation behavior from #83, metadata/report shape from #84, and redaction guarantees from #93. This note does not specify or modify those tickets.

## Safety boundaries to preserve

- Authorization decisions remain deterministic and fail closed for malformed, spoofed, unscoped, or high-risk actions.
- Authorization is a pre-execution gate; it does not make shell interpolation, filesystem APIs, or network clients safe by itself.
- Caller-provided sensitivity never downgrades an authoritative catalog value.
- Specialized-agent heuristics never replace JudgeAgent confirmation and never directly create promotion evidence.
- All touched implementation files must retain the repository's 200-line ceiling; split adapters/helpers before crossing it.
