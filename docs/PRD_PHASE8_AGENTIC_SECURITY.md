# PRD — Phase 8 Agentic Security Expansion

> **Status**: Implemented
> **Type**: Product Requirements Document
> **Scope**: Additive expansion on top of existing RedThread architecture
> **Last Updated**: 2026-04-16

---

## 1. One-line summary

Build a new **agentic security lane** for RedThread that tests and validates **tool hijacking, confused deputy chains, token/resource amplification, and deterministic pre-action controls** without replacing the current attack, judge, defense, telemetry, or bounded autoresearch systems.

---

## 2. Problem

RedThread is already strong at:
- adversarial prompt generation
- jailbreak evaluation
- defense synthesis
- replay validation
- telemetry and runtime truth

But modern agent systems fail in new ways that are not fully covered by classic jailbreak testing.

Main new risk areas:
- untrusted tool metadata and tool returns steer privileged actions
- one agent can launder malicious intent through another agent
- autonomous loops can burn tokens, time, and money without needing a classic jailbreak
- prompt-only defenses are too weak for execution-time risk

If RedThread stops at text-only jailbreak discovery, it will miss the new center of gravity in 2025-2026 agentic security.

---

## 3. Product vision

RedThread should become a **closed-loop agentic security validation system** that can answer all of these:

1. Can untrusted tool output steer a privileged action?
2. Can low-trust state or a low-privilege worker trigger a stronger worker indirectly?
3. Can an agent be pushed into expensive self-amplifying loops?
4. Can deterministic policy controls block the bad action before execution?
5. Can RedThread prove where contamination spread and where it was contained?

This must happen **without replacing**:
- PAIR
- TAP
- Crescendo
- GS-MCTS
- current LangGraph supervisor
- current Judge pipeline
- current Defense Synthesis pipeline
- current telemetry and bounded autoresearch lanes

This is an expansion layer, not a rewrite.

---

## 4. Goals

### 4.1 Core goals

#### G1 — Agentic attack coverage
Add first-class support for testing:
- MCP / tool poisoning
- ToolLeak-style argument exfiltration
- cross-tool contamination
- confused deputy / privilege laundering
- token and cost amplification

#### G2 — Deterministic control validation
Add first-class support for evaluating:
- pre-action authorization
- permission inheritance
- least-agency policy presets
- canary propagation and containment
- runtime budget stops

#### G3 — Honest evidence model
Extend RedThread’s evidence discipline so it can distinguish:
- sealed scenario evidence
- simulated runtime evidence
- live runtime evidence
- degraded / fallback evidence

#### G4 — Replay-first implementation
Build this expansion so it is testable with:
- sealed fixtures
- replay corpus
- promotion-grade validation

#### G5 — Additive architecture
Fit this work into the current repo structure without violating separation of concerns.

---

## 5. Non-goals

This phase does **not** do the following:
- replace current attack algorithms
- replace current supervisor orchestration flow
- build a full production MCP client stack first
- make live integrations the primary evidence source
- move authorization decisions into prompts or judges
- claim universal safety from a small benchmark
- collapse simulation evidence and live evidence into one class

---

## 6. Product principles

### P1 — Add, do not replace
New agentic security systems must layer on top of current RedThread features.

### P2 — Deterministic controls live outside the model
Authorization and execution gates must be rigid, inspectable, and fail-closed.

### P3 — Provenance first
Every risky request must carry origin and boundary-crossing metadata.

### P4 — Replay before live
Sealed fixtures and replay suites come before real tool integrations.

### P5 — Truth-conscious reporting
A blocked simulated attack is useful evidence, but it is not equal to a successful live runtime block. Keep evidence classes separate.

### P6 — Small modules
No giant files. New logic must follow current file-size and separation rules.

---

## 7. User and operator value

### 7.1 Primary users
- RedThread maintainers
- AI security engineers
- platform engineers building multi-agent systems
- operators who need promotion-grade evidence for runtime controls

### 7.2 User outcomes
After Phase 8, a user should be able to:
- run a sealed tool-hijack scenario
- run a sealed confused-deputy scenario
- run a sealed resource-amplification scenario
- test a deterministic policy against those scenarios
- inspect whether contamination crossed trust boundaries
- compare blocked vs unblocked traces
- promote only those deterministic controls that survive replay validation

---

## 8. Scope

## 8.1 In scope

### Attack-side additions
- simulated malicious tool fixtures
- simulated tool registries and tool-return poisoning
- confused deputy scenario packs
- resource amplification scenario packs

### Control-side additions
- action envelope model
- provenance model
- deterministic authorization engine
- permission inheritance checks
- least-agency policy presets
- canary injection and propagation tracking
- runtime budget controls for amplification tests

### Evaluation-side additions
- new evidence modes
- new rubrics
- replay corpus
- policy-validation report sections
- transcript/runtime-summary enrichment

## 8.2 Out of scope for first delivery
- full live enterprise tool adapters
- automatic policy synthesis by LLM
- uncontrolled self-modifying authorization rules
- broad live deployment enforcement in arbitrary user environments
- full real-time interception of every external framework on day one

---

## 9. Phase structure

Recommend a new additive roadmap tranche:

- **Phase 8A — Agentic Security Schema**
- **Phase 8B — Attack Simulation Lane**
- **Phase 8C — Deterministic Control Plane**
- **Phase 8D — Canary & Runtime Containment**
- **Phase 8E — Replay, Promotion, and Controlled Live Adapters**

Each phase is described below.

---

## 10. Phase 8A — Agentic Security Schema

## Objective
Add the shared data contracts needed for all later work.

## Deliverables

### D8A.1 Threat taxonomy
Standard names for:
- tool poisoning
- tool leak
- cross-tool contamination
- confused deputy
- privilege laundering
- resource amplification
- canary propagation
- deterministic policy containment

### D8A.2 Provenance model
Track:
- source kind
- trust level
- origin chain
- parent event IDs
- boundary crossings
- canary tags

### D8A.3 Action envelope model
Represent any risky action as one common object.

Required fields:
- action ID
- actor ID
- actor role
- capability
- tool name
- normalized args
- provenance
- target sensitivity
- requested side effects
- approval state
- authorization result
- canary info

### D8A.4 Amplification metrics model
Track:
- tool call count
- retry count
- repeated call count
- loop depth
- token growth slope
- fallback escalation count
- budget breach flags

## Suggested file areas
- `src/redthread/models.py` or small extracted models folder
- `src/redthread/orchestration/provenance.py`
- `src/redthread/orchestration/models/`
- `src/redthread/telemetry/models.py`
- `docs/AGENTIC_SECURITY_THREAT_MODEL.md`

## Acceptance criteria
- provenance serializes cleanly in transcripts and tests
- action envelope can represent file read, shell exec, db write, HTTP post, and delegation
- new threat taxonomy is used consistently in tests and reports
- no file exceeds repo size limits

---

## 11. Phase 8B — Attack Simulation Lane

## Objective
Let RedThread run reproducible agentic-security scenarios without needing live infrastructure first.

## Deliverables

### D8B.1 Tool hijack fixture pack
Fixtures for:
- poisoned tool descriptions
- ToolLeak-style argument schemas
- poisoned tool returns
- nested tool chain contamination
- benign control fixtures

### D8B.2 Simulated tool registry
A deterministic simulation harness that can:
- expose tools
- serve benign or malicious metadata
- return structured or free-text outputs
- record downstream action attempts

### D8B.3 Confused deputy scenario pack
Scenarios where:
- a low-trust worker reads poisoned content
- task state is laundered into internal workflow metadata
- a stronger worker receives derived action requests
- permission inheritance succeeds or fails

### D8B.4 Resource amplification scenario pack
Scenarios where:
- fake verification flows trigger retries
- `REPAIR` / `RETRY` / fallback loops grow cost
- oversized skill/tool content bloats context
- repeated calls cross budget thresholds

## Suggested file areas
- `src/redthread/tools/fixtures/`
- `src/redthread/tools/simulated_registry.py`
- `src/redthread/tools/simulated_servers.py`
- `src/redthread/orchestration/scenarios/confused_deputy.py`
- `src/redthread/orchestration/scenarios/resource_amplification.py`
- `src/redthread/orchestration/graphs/tool_attack_graph.py`
- `tests/fixtures/agentic_security/`

## Acceptance criteria
- RedThread can run at least one sealed case each for tool poisoning, confused deputy, and resource amplification
- results record requested downstream actions even without live tool execution
- scenarios are deterministic in dry-run / sealed mode

---

## 12. Phase 8C — Deterministic Control Plane

## Objective
Add rigid, testable execution-time defenses outside the model.

## Deliverables

### D8C.1 Authorization engine
Single interface:
- `authorize(action_envelope) -> ALLOW | DENY | ESCALATE`

### D8C.2 Policy schema
Policies must support:
- actor role constraints
- capability constraints
- tool allow/deny lists
- parameter constraints
- sensitivity labels
- provenance requirements
- explicit escalation rules

### D8C.3 Permission inheritance checks
A derived request cannot exceed the effective authority of its lineage.

### D8C.4 Least-agency presets
Preset policy bundles for roles like:
- retriever
- summarizer
- analyst
- executor
- db reader
- db writer
- shell-limited worker

## Suggested file areas
- `src/redthread/tools/authorization/engine.py`
- `src/redthread/tools/authorization/models.py`
- `src/redthread/tools/authorization/presets.py`
- `src/redthread/orchestration/permission_inheritance.py`
- `tests/test_authorization_engine.py`

## Acceptance criteria
- at least one tool-poisoning case is blocked by deterministic policy
- at least one confused-deputy case is blocked by permission inheritance
- allow/deny/escalate decisions are logged in structured reports
- authorization path is non-LLM and deterministic

---

## 13. Phase 8D — Canary & Runtime Containment

## Objective
Show how contamination spreads, and stop amplification before cost explodes.

## Deliverables

### D8D.1 Canary injection and propagation
Inject canaries into:
- tool returns
- task envelopes
- summaries
- memory writes
- outbound requests

### D8D.2 Canary report
Show:
- injection point
- boundaries crossed
- first blocked point
- if execution boundary was reached

### D8D.3 Runtime amplification controls
Add budget and stop conditions for:
- repeated identical calls
- repeated retry loops
- excessive reflection loops
- repeated fallback escalation
- token growth beyond threshold

## Suggested file areas
- `src/redthread/telemetry/canaries.py`
- `src/redthread/orchestration/canary_flow.py`
- `src/redthread/telemetry/models.py`
- `src/redthread/orchestration/runtime_summary.py`
- `tests/test_canary_propagation.py`
- `tests/test_runtime_budgets.py`

## Acceptance criteria
- canary can be traced across at least two trust boundaries in sealed tests
- report can identify where containment succeeded or failed
- amplification controls can stop a replayed loop scenario deterministically

---

## 14. Phase 8E — Replay, Promotion, and Controlled Live Adapters

## Objective
Make Phase 8 durable, promotable, and eventually portable to live environments.

## Deliverables

### D8E.1 New evidence modes
Attack evidence examples:
- `sealed_tool_fixture`
- `sealed_multi_agent_fixture`
- `simulated_runtime`
- `live_runtime`

Defense evidence examples:
- `sealed_authorization_block`
- `sealed_canary_contained`
- `live_policy_block`
- `live_budget_stop`

### D8E.2 New rubrics
Need rubrics for:
- tool misuse success
- privilege laundering success
- unauthorized action severity
- canary propagation severity
- resource amplification severity
- deterministic containment quality

### D8E.3 Replay corpus
Pinned replay suites for:
- tool poisoning
- ToolLeak
- confused deputy
- budget amplification
- permission inheritance edge cases

### D8E.4 Promotion gate additions
Policy/canary controls must prove:
- attack blocked
- false positive rate acceptable
- containment path visible
- replay coverage exists
- evidence class is honest

### D8E.5 Controlled live adapters
Only after sealed and replay evidence are stable, add:
- controlled MCP-like replay adapter
- controlled tool-interception hooks
- optional live policy interception path

## Suggested file areas
- `src/redthread/evaluation/results.py`
- `src/redthread/evaluation/rubrics/`
- `src/redthread/evaluation/reporting/`
- `tests/replay/agentic_security/`
- `tests/test_agentic_security_replay.py`

## Acceptance criteria
- replay corpus catches regressions in policy and containment logic
- promotion reports include deterministic-control sections
- at least one controlled live adapter proves the abstractions hold outside sealed mode

---

## 15. Detailed functional requirements

## FR1 — Provenance must be first-class
Every scenario and every risky action must include provenance metadata that survives serialization and reporting.

## FR2 — Sensitive actions must use a common envelope
All sensitive action attempts must be represented through the action envelope model.

## FR3 — Sealed scenarios must exist before live integrations
No live tool adapter work should begin until sealed fixture suites exist for the same threat families.

## FR4 — Authorization must be deterministic
Authorization results must not depend on LLM judgment.

## FR5 — Permission inheritance must be enforceable
If a low-privilege source triggers a high-privilege request indirectly, the lineage rule must be able to deny it.

## FR6 — Canaries must support spread-path reporting
Canaries must support stage-by-stage reporting of contamination spread.

## FR7 — Resource amplification must be measurable
Reports must expose whether a scenario caused abnormal loop, retry, or budget behavior.

## FR8 — Evidence classes must remain separate
Sealed, simulated, live, and degraded evidence cannot be merged into one label.

## FR9 — Reports must be operator-readable
JSONL artifacts and summaries must show both machine-readable and human-readable explanations.

## FR10 — Existing RedThread phases must keep working
Phase 8 must not break:
- current campaign flow
- existing evaluation pipeline
- existing defense synthesis validation
- existing telemetry truth model
- existing bounded autoresearch controls

---

## 16. Data contracts

## 16.1 ProvenanceRecord
Minimum contract:
- `source_kind`
- `trust_level`
- `origin_id`
- `parent_ids`
- `boundary_crossings`
- `canary_tags`
- `derived_from_untrusted: bool`

## 16.2 ActionEnvelope
Minimum contract:
- `action_id`
- `actor_id`
- `actor_role`
- `capability`
- `tool_name`
- `arguments`
- `target_sensitivity`
- `provenance`
- `requested_effect`
- `authorization_status`
- `authorization_reason`
- `requires_human_approval`

## 16.3 AuthorizationDecision
Minimum contract:
- `decision`
- `policy_id`
- `reason`
- `matched_rules`
- `required_escalation`

## 16.4 AmplificationMetrics
Minimum contract:
- `tool_call_count`
- `retry_count`
- `duplicate_call_count`
- `loop_depth`
- `fallback_count`
- `token_growth_ratio`
- `budget_breached`

---

## 17. Architecture fit

## 17.1 Orchestration
Use `src/redthread/orchestration/` for:
- provenance handling
- action lineage
- confused deputy scenarios
- canary movement through workflow state

## 17.2 Tools
Use `src/redthread/tools/` for:
- simulated tool registry
- simulated malicious tool servers
- authorization engine
- policy presets

## 17.3 Evaluation
Use `src/redthread/evaluation/` for:
- new evidence modes
- new rubrics
- deterministic containment reporting

## 17.4 Telemetry
Use `src/redthread/telemetry/` for:
- canary instrumentation
- amplification metrics
- cost and runtime anomaly summaries

## 17.5 Core algorithms
Keep `src/redthread/core/` focused on existing attack and defense algorithms. Do not mix deterministic authorization logic into core algorithm modules.

---

## 18. Testing strategy

## 18.1 Sealed unit tests
Add narrow tests for:
- provenance serialization
- action envelope validation
- authorization rule matching
- permission inheritance deny/allow cases
- canary injection and detection
- budget stop logic

## 18.2 Sealed scenario tests
Add end-to-end tests for:
- tool poisoning fixture
- ToolLeak-style schema case
- confused deputy case
- resource amplification case

## 18.3 Replay tests
Add replay suites for:
- deterministic policy regressions
- containment regressions
- false positive checks on benign scenarios

## 18.4 Controlled live tests
Only after sealed and replay layers are green:
- run limited live adapter checks
- keep evidence class separate from sealed results

---

## 19. Success metrics

### Functional success
- RedThread can simulate and score at least 3 new agentic attack families
- RedThread can block those attacks with deterministic controls in replayable form
- reports show provenance, policy decision, canary path, and amplification metrics

### Reliability success
- sealed fixtures are deterministic
- replay corpus is stable in CI
- no regression to current evaluation truth boundary

### Product success
- operators can understand whether failure happened in prompt layer, tool layer, agent handoff layer, or budget layer
- maintainers can add new policies and scenarios without changing core algorithms

---

## 20. Risks and mitigations

### Risk R1 — Scope explosion
**Mitigation**: phase rollout, replay-first, no broad live adapters early.

### Risk R2 — Architecture sprawl
**Mitigation**: keep strict module boundaries; use shared data contracts early.

### Risk R3 — Weak truth claims
**Mitigation**: keep evidence classes separate and explicit.

### Risk R4 — Supervisor bloat
**Mitigation**: add scenario modules and sidecar engines outside the supervisor core.

### Risk R5 — False positives from rigid policy
**Mitigation**: include benign control fixtures and promotion checks for over-blocking.

### Risk R6 — Context-contamination tracing becomes hand-wavy
**Mitigation**: make canary propagation and provenance explicit, structured, and serialized.

---

## 21. Recommended build order

### Wave 1
- threat taxonomy
- provenance model
- action envelope
- sealed tool poisoning fixtures
- sealed confused deputy fixtures
- sealed amplification fixtures

### Wave 2
- authorization engine
- policy schema
- permission inheritance
- least-agency presets

### Wave 3
- canary propagation
- runtime budget controls
- transcript/runtime-summary enrichment

### Wave 4
- evidence extensions
- rubrics
- replay corpus
- promotion gate integration

### Wave 5
- controlled live adapters
- optional live interception validation

---

## 22. First implementation slice

If the team wants the smallest high-value first cut, implement this exact slice:

1. provenance model
2. action envelope model
3. one sealed tool poisoning fixture
4. one sealed confused deputy fixture
5. one authorization engine with `ALLOW | DENY | ESCALATE`
6. one policy denying `external_untrusted -> shell.exec`
7. one permission inheritance rule denying privilege laundering
8. one transcript section showing provenance and authorization result

This slice gives immediate product value with low blast radius.

---

## 23. Open questions

These do not block Phase 8A, but should be tracked:
- Which current transcript schema changes are safest for backward compatibility?
- Should action envelopes live in `models.py` or a new local models package?
- How much of permission inheritance belongs in orchestration vs authorization modules?
- What is the minimal controlled live adapter that proves portability without creating noise?
- When, if ever, should bounded autoresearch be allowed to mutate policy assets?

---

## 24. Final statement

Phase 8 should make RedThread better at the real modern question:

**Not only “can the model be tricked into unsafe text?”**

But also:

**“Can the agent system be pushed into unsafe action, unsafe delegation, unsafe spend, or unsafe execution — and can deterministic controls stop it?”**

That is the purpose of this expansion.
