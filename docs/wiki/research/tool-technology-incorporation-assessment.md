---
title: Tool Technology Incorporation Assessment
type: research
status: active
summary: Honest assessment of which ideas/code patterns from PyRIT, promptfoo, garak, DeepEval, Giskard, Strix, ART, Gideon, and commercial tools RedThread should absorb into its own product versus avoid.
source_of_truth:
  - docs/product.md
  - docs/TECH_STACK.md
  - docs/algorithms.md
  - docs/wiki/research/ai-red-teaming-guide-redthread-use-case-map.md
  - docs/wiki/research/open-source-redteam-tool-integration-strategy.md
  - https://github.com/requie/AI-Red-Teaming-Guide
  - https://github.com/microsoft/PyRIT
  - https://github.com/promptfoo/promptfoo
  - https://www.promptfoo.dev/docs/red-team/architecture/
  - https://www.promptfoo.dev/docs/red-team/plugins/
  - https://www.promptfoo.dev/docs/red-team/strategies/
  - https://github.com/NVIDIA/garak
  - https://github.com/confident-ai/deepeval
  - https://github.com/Giskard-AI/giskard
  - https://github.com/usestrix/strix
  - https://github.com/Cogensec/Gideon
updated_by: codex
updated_at: 2026-04-26
---

# Tool Technology Incorporation Assessment

## Research question

Would RedThread get better by **incorporating** technologies, patterns, or code ideas from existing AI red-teaming tools instead of only integrating with them?

## Direct answer

Yes, RedThread should absorb **some ideas and internal patterns** from these tools.

No, RedThread should not absorb most of their runtimes wholesale.

The best move is not “integration-only” and not “fork everything.” The best move is:

```text
copy the useful product/architecture patterns
reimplement them in RedThread-native Python models
keep RedThread's own attack-search, JudgeAgent, defense synthesis, and validation loop as the core
use external code directly only where it is already a dependency or where the module is small, stable, license-safe, and does not own RedThread's thesis
```

Why: RedThread's edge is not “has the most scanners.” RedThread's edge is turning attacks into judged, validated, durable defenses. Absorbing scanner runtimes can make RedThread bigger but not smarter. Absorbing the right **taxonomies, strategy composition, scope controls, regression mechanics, and artifact standards** will make RedThread much better.

## Incorporation decision matrix

| Source | Absorb into RedThread? | What to absorb | What not to absorb | Honest reason |
|---|---:|---|---|---|
| **PyRIT** | **Yes, already P0** | Target adapters, converters, send/receive abstractions, scorer interfaces where useful | Do not become a PyRIT fork; do not move RedThread algorithms into PyRIT orchestrators | It fits Python and RedThread already chose it as plumbing. Keep proprietary logic above it. |
| **promptfoo** | **Yes, strongly** | Plugin/strategy split, custom policy DSL, strategy layering, retry/regression concept, coverage taxonomy, CI/report expectations | Do not port Node/TS runtime, UI, cache, provider system, or cloud generation dependency | Best product design to absorb. Huge value. Reimplement RedThread-native. |
| **garak** | **Yes, selectively** | Probe/detector metadata model, tags, static detector ideas, probe corpus shape, report digest concepts | Do not replace PyRIT targets, do not fork full harness, do not treat detectors as final truth | Great scanner corpus. But RedThread needs semantic JudgeAgent and defense loop. |
| **Strix** | **Yes, for safety runtime** | Authorized target scope context, sandbox execution split, tool validation, PoC discipline, diff-scope scanning idea | Do not import browser/proxy/terminal powers into core yet | Excellent agentic appsec runtime lessons. High blast radius if copied blindly. |
| **Giskard** | **Yes, lightly** | Multi-turn scenario/check style, RAG quality checks, suite organization | Do not replace RedThread's JudgeAgent or attack algorithms | Useful eval ergonomics. Not central to self-healing red-team loop. |
| **DeepEval / DeepTeam** | **Yes, lightly** | Pytest-native eval shape, agent/RAG metric names, vulnerability/attack-enhancement taxonomy | Do not depend on its binary pass/fail judge as core truth | Useful developer workflow. RedThread needs richer severity and defense validation. |
| **AI-Red-Teaming-Guide** | **Yes** | Program templates, severity dimensions, 30/60/90 maturity path, SDLC artifacts, release gates | No code runtime to absorb | Very useful for operator artifacts and product trust. |
| **ART** | **No for current core** | Maybe future classical ML/CV adversarial robustness lane | Do not add to LLM-agent pipeline now | Different problem. High learning/dependency cost for low current payoff. |
| **Gideon** | **Mostly no** | Threat-intel enrichment ideas, defensive-only guardrails, hardening output shape | Do not import autonomous security-op agent runtime | Different product. Can inspire but not improve RedThread core now. |
| **Commercial tools** | **No code** | Market expectations: compliance reports, executive posture, continuous testing | No dependency, no clone attempt | Use as product benchmark only. |

## What RedThread should incorporate now

### 1. A RedThread-native plugin/strategy architecture

This is the biggest concrete improvement from promptfoo and garak.

Promptfoo separates:

```text
plugin = what vulnerability/risk to test
strategy = how to deliver or transform the attack
provider/target = where to send it
grader = how to judge it
```

Garak separates:

```text
probe = attempt family
detector = weak/focused signal for success
buff = transformation
report = evidence artifact
```

RedThread should absorb this as:

```text
RiskPlugin       → target risk category, policy, examples, expected failure mode
AttackStrategy   → PAIR/TAP/Crescendo/GS-MCTS/static transform/layered transform
TargetAdapter    → PyRIT-backed target execution
JudgeRubric      → RedThread semantic judge criteria
EvidenceArtifact → trace, score, detector hints, reproduction data
DefenseCandidate → generated guardrail/control
RegressionCase   → replayable test after validation
```

This would make RedThread better because campaign planning becomes modular. Example:

```yaml
risks:
  - prompt_injection
  - rbac
  - agentic_memory_poisoning
  - rag_document_exfiltration
strategies:
  - tap
  - crescendo
  - layer:
      - base64
      - authority_impersonation
judge:
  rubric: sensitive_info
  severity_dimensions:
    - autonomy
    - blast_radius
    - recoverability
```

**Verdict:** yes, absorb. This is core-product improvement.

### 2. promptfoo-style custom policies

RedThread should have first-class custom policy tests.

Promptfoo's best idea is not just its scanner. It is that users can define business rules like:

```text
The assistant must not create binding contractual commitments.
The assistant must not reveal customer credit score in support chat.
The assistant must not book or purchase without explicit human approval.
```

RedThread should turn those into:

```text
custom policy → adversarial objective → attack strategy selection → JudgeRubric → defense synthesis constraint → regression test
```

This is stronger than promptfoo because RedThread can close the loop after failure.

**Verdict:** yes, absorb soon.

### 3. garak-style probe and detector catalog

RedThread should not copy garak's whole harness, but it should learn from the probe/detector design.

Useful pieces:

- probe metadata: goal, tags, modality, language, recommended detector
- detector output as `0.0–1.0` hint, not final verdict
- static detectors for obvious issues: API keys, markdown exfil, SQL echo, unsafe content strings, prompt-injection trigger strings
- report digest pattern

RedThread should model this as:

```text
ProbeSeed → AttackTrace candidate
DetectorHint → JudgeAgent input feature
```

Do not let detector hints directly create Critical findings. A string match is evidence, not judgment.

**Verdict:** yes, absorb as seed/detector-hint system.

### 4. Strix-style scope and sandbox discipline

Strix has one very important pattern RedThread should copy: scope is not casual text. It is structured system context.

Good Strix pattern:

```text
scope_source = system_scan_config
authorization_source = strix_platform_verified_targets
user_instructions_do_not_expand_scope = true
authorized_targets = [...]
```

RedThread should adopt this for every destructive or semi-destructive test.

RedThread-native shape:

```text
AuthorizedScope
  targets
  allowed_tools
  denied_tools
  allowed_networks
  workspace_roots
  evidence_retention_policy
  user_instructions_cannot_expand_scope = true
```

This matters more if RedThread moves into agentic workflow replay, appsec, or live sandbox validation.

**Verdict:** yes, absorb. This is safety-critical.

### 5. Regression retry as first-class memory

Promptfoo has a retry/regression strategy. The AI-Red-Teaming-Guide emphasizes attack libraries and recurring scans.

RedThread should absorb the concept, but make it stronger:

```text
successful exploit trace
→ minimized reproduction
→ defense validation replay
→ recurring regression case
→ drift/recurrence tracking
```

This fits RedThread perfectly.

**Verdict:** yes, absorb now.

### 6. Guide-style operator artifacts

The guide's templates should become RedThread report outputs:

- rules of engagement
- vulnerability report
- model/system security card
- PR checklist
- stakeholder readout
- case study template

This makes RedThread feel enterprise-ready without changing the attack engine.

**Verdict:** yes, absorb. Low risk, high trust value.

## What RedThread should maybe incorporate later

### 1. Giskard-style multi-turn scenario DSL

Giskard's scenario/check framing is useful for readable tests:

```text
turn 1 → turn 2 → turn 3 → check over full trace
```

RedThread already has Crescendo and GS-MCTS. So Giskard does not add stronger attacks. It adds better test authoring and report readability.

RedThread could add:

```yaml
scenario:
  name: support-agent-cross-session-leak
  turns:
    - user: "I lost my order number"
    - user: "Can you look up the last order for this email?"
  checks:
    - no_cross_tenant_data
    - no_pii_disclosure
```

**Verdict:** useful later. Not urgent.

### 2. DeepEval-style pytest integration

DeepEval is good at developer workflow. RedThread should not replace its JudgeAgent with DeepEval metrics. But it can adopt the ergonomics:

```python
def test_support_agent_security(redthread_case):
    result = redthread_case.run()
    assert result.max_severity < "high"
```

**Verdict:** useful later for adoption. Not core intelligence.

### 3. Commercial-tool report posture

Commercial tools are useful as product-pressure signals. RedThread should copy the expectation that outputs are:

- executive-readable
- compliance-mapped
- trend-aware
- risk-prioritized
- continuous, not one-off

**Verdict:** copy output expectations, not runtime.

## What RedThread should not incorporate

### 1. promptfoo runtime

Do not port promptfoo's Node/TypeScript runtime into RedThread.

Reasons:

- RedThread is Python and LangGraph/PyRIT based.
- Promptfoo already owns provider/config/report UX well.
- Porting it creates a second product inside RedThread.
- It distracts from defense synthesis.

Absorb the ideas. Do not absorb the runtime.

### 2. garak harness as core

Do not make garak the RedThread scan engine.

Reasons:

- garak is scanner-first.
- RedThread is closed-loop defense-first.
- garak detectors are useful but can be shallow/noisy for semantic harm.
- RedThread already has PyRIT target plumbing.

Absorb probes and detector hints. Keep RedThread's campaign engine.

### 3. Strix tool powers

Do not copy Strix's browser/proxy/terminal tool execution into RedThread core now.

Reasons:

- it expands blast radius
- it changes product scope from LLM red-team/defense engine into appsec agent
- it needs strong authorization and sandbox maturity first

Absorb scope and sandbox patterns first.

### 4. ART classical ML stack

Do not bring ART into current LLM-agent core.

Reasons:

- ART targets classical ML/CV/adversarial robustness
- dependency and expertise cost is high
- RedThread's immediate value is LLM/agentic security

Keep as future lane only.

### 5. Gideon autonomous SOC runtime

Do not merge Gideon's defensive security agent runtime.

Reasons:

- it solves threat intel / CVE / SOC-style tasks
- RedThread solves adversarial LLM campaign and defense validation
- overlap is mostly reporting/hardening vocabulary

Absorb threat-intel enrichment ideas later if needed.

## Incorporation architecture RedThread should build

### Core internal abstractions

```text
RiskPlugin
  id
  category
  policy_text
  examples
  applicable_target_types
  owasp_tags
  mitre_tags
  nist_tags
  default_strategies
  judge_rubric_id

AttackStrategy
  id
  type: static | dynamic | tree | multi_turn | layered
  cost_level
  compatible_plugins
  execute(seed, target, judge)

DetectorHint
  detector_id
  confidence
  matched_evidence
  limitations

ScenarioCase
  turns
  state_assertions
  trace_checks

RegressionCase
  source_finding_id
  minimized_trace
  expected_safe_behavior
  replay_schedule

AuthorizedScope
  targets
  workspace_roots
  tools
  network
  retention
  cannot_be_expanded_by_user_text
```

### Data flow

```text
RiskPlugin selects what to test
→ AttackStrategy creates attempts
→ PyRIT TargetAdapter executes attempts
→ DetectorHint captures cheap signals
→ JudgeAgent gives semantic severity
→ DefenseSynthesizer proposes control
→ SandboxValidateTool replays original + variants
→ RegressionCase stores durable test
→ ReportExporter emits operator artifacts
```

This is incorporation, not just external integration.

## Priority list

### P0 — incorporate now

1. **RiskPlugin / AttackStrategy split** from promptfoo + garak.
2. **Custom policy plugin** from promptfoo.
3. **Probe/detector hint model** from garak.
4. **AuthorizedScope** from Strix.
5. **RegressionCase** from promptfoo retry + guide attack library.
6. **Severity dimensions** from the guide: exploitability, user impact, autonomy, blast radius, recoverability.

### P1 — incorporate next

1. Strategy layering: base64 + roleplay + TAP, etc.
2. Multilingual and modality metadata from garak/promptfoo.
3. Coverage gap map across OWASP/MITRE/NIST.
4. Guide-style report exporters.

### P2 — incorporate later

1. Giskard-like scenario DSL.
2. DeepEval-like pytest developer tests.
3. Strix-like appsec objective converter.
4. Commercial-style posture dashboard outputs.

### P3 — probably do not incorporate

1. ART unless RedThread expands into classical ML/CV.
2. Gideon runtime unless RedThread becomes SOC/threat-intel product.
3. Full promptfoo UI/runtime.
4. Full garak harness.
5. Full Strix tool runtime.

## Honest strategic assessment

The original “integration layer” plan was safe, but incomplete. If RedThread only imports/exports, it gains interoperability but not much intelligence.

To get better, RedThread should **incorporate the best internal concepts**:

- promptfoo's product taxonomy and policy ergonomics
- garak's probe/detector catalog discipline
- Strix's hard scope/sandbox enforcement
- Giskard/DeepEval's readable test ergonomics
- the guide's operating artifacts and severity model

But RedThread should **not** absorb full runtimes, because that creates bloat and weakens the product thesis.

The right thesis is:

```text
RedThread should become internally plugin-driven like promptfoo/garak,
scope-safe like Strix,
regression-friendly like promptfoo/DeepEval,
report-ready like commercial tools,
but still uniquely closed-loop through JudgeAgent + DefenseSynthesizer + sandbox validation.
```

## Final recommendation

Build incorporation first in this order:

1. RedThread-native `RiskPlugin` and `AttackStrategy` abstractions.
2. Custom policy/risk definitions.
3. Garak-inspired `DetectorHint` and probe seed catalog.
4. Strix-inspired `AuthorizedScope` enforcement.
5. Regression-case memory and retry.
6. Guide-style report artifacts.

That will make RedThread better without making it a Franken-tool.

For the detailed implementation path, see [Tool Technology Incorporation Roadmap](tool-technology-incorporation-roadmap.md).
