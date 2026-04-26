---
title: AI Red Teaming Guide Use-Case Map for RedThread
type: research
status: active
summary: Deep research synthesis of AI-Red-Teaming-Guide and related tools, mapped to exact RedThread use cases, infrastructure changes, workflow entrypoints, and expected outcomes without overbuilding.
source_of_truth:
  - https://github.com/requie/AI-Red-Teaming-Guide
  - docs/product.md
  - docs/TECH_STACK.md
  - docs/algorithms.md
  - docs/wiki/research/open-source-redteam-tool-integration-strategy.md
  - docs/wiki/concepts/ai-red-teaming-tooling-landscape.md
  - https://github.com/microsoft/PyRIT
  - https://github.com/confident-ai/deepeval
  - https://github.com/NVIDIA/garak
  - https://github.com/promptfoo/promptfoo
  - https://github.com/Trusted-AI/adversarial-robustness-toolbox
  - https://github.com/Giskard-AI/giskard
  - https://github.com/Cogensec/Gideon
  - https://github.com/usestrix/strix
updated_by: codex
updated_at: 2026-04-26
---

# AI Red Teaming Guide Use-Case Map for RedThread

## Research question

What does [AI-Red-Teaming-Guide](https://github.com/requie/AI-Red-Teaming-Guide) teach RedThread, which tools should RedThread integrate with, and where exactly should each tool enter the RedThread workflow without overkill?

## Bottom line

RedThread should **not** try to absorb the whole AI red-teaming ecosystem.

The right posture is:

```text
AI-Red-Teaming-Guide = operating program and templates
PyRIT = already-chosen target/converter/orchestration plumbing
promptfoo = CI/report/export-import bridge
Garak = baseline scanner and probe corpus
DeepEval / Giskard = optional eval interoperability, not core attack engine
Strix = future appsec-to-agent objective source and sandbox/scope reference
ART = only for classical ML/CV lanes, not current LLM-agent core
Gideon = threat-intel/hardening inspiration, not runtime dependency
Commercial tools = external benchmarks or customer ecosystem, not dependencies
RedThread = closed-loop attack → judge → defend → validate → regress brain
```

The exact RedThread value statement should remain:

```text
Tool X found or framed a failure.
RedThread reproduced or imported it.
RedThread scored it.
RedThread generated a defense.
RedThread validated the defense.
RedThread turned it into a regression test.
```

## What the guide adds that RedThread should adopt

The guide is most useful as a **program design reference**, not as code to import.

| Guide asset | What it says | Exact RedThread use | Build now? |
|---|---|---|---|
| Four-phase methodology | Plan/threat model → execute → score → report/remediate | Align RedThread campaign lifecycle and operator docs to this shape | Yes, docs + artifacts |
| 30/60/90 rollout | Foundation, operationalization, scale | Use as product onboarding and roadmap framing | Yes, docs only |
| Evaluation harness | Prompts, policies, scorers, reports, trend data | Maps to RedThread regression corpus + JudgeAgent + result store | Yes, partially |
| Release gates | Block criticals, ASR thresholds, regression deltas | Add configurable CI gates after import/export exists | Yes, after promptfoo bridge |
| Agentic attack trees | Tool misuse, memory poisoning, inter-agent privilege escalation | Map directly to RedThread Phase 8 agentic-security runtime tests | Yes, taxonomy first |
| Harm severity model | Exploitability, user impact, autonomy, blast radius, recoverability | Extend RedThread severity scoring beyond raw Judge score | Yes, model/schema |
| SDLC artifacts | PR checklist, system card, rules of engagement, vuln report | Export campaign artifacts for teams adopting RedThread | Yes, low-cost |
| Multilingual playbook | Translation-loop, mixed-language, code-switching, local harm | Add attack seeds and ASR-by-language report lanes | Later |
| Data governance | retention, PII handling, access controls | Add to finding storage and evidence redaction policy | Yes before enterprise use |
| Purple-team cadence | detection/runbook/replay | Long-term output mode after defense validation matures | Later |

## Comparison matrix

This matrix combines the guide's tool list, repo checks, and RedThread-specific integration value.

| Tool | Type | Cost | Automation | Learning curve | Best use case | RedThread exact use case | Priority | Integration stance |
|---|---:|---:|---:|---:|---|---|---:|---|
| **PyRIT** | Open | Free | High | Medium | Comprehensive generative-AI testing | Keep as adapter/plumbing for targets, converters, attack execution loops | P0 | Already foundational; do not replace |
| **promptfoo** | Open | Free / paid cloud optional | High | Low-Medium | CI evals, red-team configs, policy tests, reports | Export RedThread findings/defenses to CI regression suites; import promptfoo failures | P1 | Build import/export bridge |
| **Garak** | Open | Free | High | Low | Quick LLM vulnerability scans | Import JSONL reports; use probes as baseline coverage and attack seeds | P1 | Build import first, runner later |
| **DeepTeam / DeepEval** | Open | Free / paid platform optional | High | Low | RAG, chatbot, agent, pytest-style evals | Optional eval-result import and CI compatibility for teams already using DeepEval | P2 | Interop only, no core dependency |
| **Giskard** | Open / commercial | Free OSS + paid platform | High | Medium | Multi-turn agent/RAG testing and test generation | Optional testset import/export; compare Giskard checks against RedThread JudgeAgent | P2 | Interop only |
| **Strix** | Open | Free | High | Medium-High | Agentic appsec, source-aware scans, PoC validation | Ingest appsec findings as attack objectives; borrow scope/sandbox patterns | P2/P3 | Ingest reports, not runtime tools |
| **IBM ART** | Open | Free | Medium | High | Classical ML, CV, adversarial robustness | Only use when RedThread tests non-LLM model lanes, image/classifier robustness, or model extraction | P3 | Do not integrate now |
| **Gideon** | Open | Free | High | Medium | Defensive threat intel, CVE research, hardening policy generation | Optional threat-intel enrichment for scenarios and hardening context | P3 | Inspiration or offline enrichment only |
| **BrokenHill** | Open | Free | Medium-High | Medium | Automatic jailbreak generation | Mine jailbreak-generation ideas if RedThread lacks attack diversity | P3 | Do not integrate unless specific gap appears |
| **Counterfit** | Open | Free | Medium | Medium | Educational adversarial ML testing | Training/reference only | P4 | No integration |
| **Mindgard** | Commercial | $$$ | Very high | Low | Enterprise AI risk and continuous red teaming | Benchmark against enterprise expectations; possible customer import/export later | P4 | No dependency |
| **Lakera Guard / Lakera Red** | Commercial | $$$ | High | Low | Production protection, prompt-injection defense, expert red teaming | Compare guardrail/detection output; maybe export RedThread tests to customers using Lakera | P4 | No dependency |
| **Pillar Security** | Service/platform | $$$$ | Custom | N/A | Full-service AI security testing and posture management | Market/compliance benchmark only | P4 | No dependency |
| **NeuralTrust** | Service/platform | $$$ | Custom | N/A | GenAI firewall, red-team services, compliance alignment | Market/compliance benchmark only | P4 | No dependency |
| **Pallma AI** | Service/platform | $$$ | Very high | Low | Automated red/purple teaming, agent/voice security | Market benchmark; possible future result-import if customer asks | P4 | No dependency |
| **Splx AI / Adversa AI** | Commercial | $$$ | High | Low | Enterprise AI app security testing | Track market; not central to current RedThread architecture | P4 | No dependency |

## Exact RedThread use cases

### Use case 1 — Baseline external scan intake

**Goal:** get broad coverage fast without spending RedThread attack budget.

**Tools:** garak first, promptfoo second.

**Workflow entrypoint:** before RedThread deep attack generation.

```text
External scan report
→ ExternalFinding parser
→ taxonomy mapper
→ JudgeAgent re-score
→ promote confirmed high-severity findings
→ defense synthesis / validation if applicable
```

**Infrastructure needed:**

- `ExternalFinding` model with source/category/severity/prompt/response/evidence/raw_path/metadata.
- Importer registry: `garak`, `promptfoo`, later `giskard`, `deepeval`, `strix`.
- Taxonomy map from external labels to RedThread rubrics and OWASP/MITRE categories.
- Raw artifact retention with redaction rules.

**Expected result:** more initial findings and better coverage map. Not better defenses by itself; JudgeAgent and validation still make it useful.

**Overkill to avoid:** running every external scanner on every campaign.

### Use case 2 — CI regression export

**Goal:** make RedThread findings useful to normal engineering workflows.

**Tool:** promptfoo first.

**Workflow entrypoint:** after RedThread validates a finding or defense.

```text
Successful attack trace / validated defense
→ normalize into regression intent
→ export promptfooconfig.yaml
→ run in CI
→ CI blocks if critical/high regression appears
```

**Infrastructure needed:**

- `redthread export promptfoo --campaign <id>`.
- RedThread-to-promptfoo provider target mapping.
- Policy/test exporter for successful attack prompts and defense regression cases.
- CI gate thresholds: critical open, ASR by high-risk category, ASR delta.

**Expected result:** RedThread findings stop being one-off reports and become repeatable engineering controls.

**Overkill to avoid:** rebuilding promptfoo's UI, cache, provider system, or YAML DSL.

### Use case 3 — Tool taxonomy and coverage gap map

**Goal:** know what RedThread does and does not test.

**Tools:** all tools as taxonomy sources; no runtime integration required.

**Workflow entrypoint:** campaign planning and final reporting.

```text
Target profile
→ required risk categories
→ RedThread algorithm/rubric coverage
→ external tool categories
→ coverage gap report
```

**Infrastructure needed:**

- Static mapping file: external categories → RedThread rubrics → OWASP/MITRE/NIST.
- Report field: `covered`, `partially_covered`, `not_covered`, `external_only`.
- Operator warning when high-risk target categories lack tests.

**Expected result:** better honesty. RedThread can say “we tested X, did not test Y.”

**Overkill to avoid:** importing full external taxonomies as hard dependencies.

### Use case 4 — Agentic appsec objective generation

**Goal:** convert real app vulnerabilities into LLM-agent abuse tests.

**Tool:** Strix later.

**Workflow entrypoint:** before agentic workflow replay / Phase 8 testing.

```text
Strix appsec finding
→ RedThread objective generator
→ agent/tool misuse attack tree
→ workflow replay attack
→ JudgeAgent score
→ defense / authorization gate recommendation
```

**Example:** Strix finds IDOR in an order endpoint. RedThread tests whether a support agent can be socially engineered into calling that endpoint for another user's order.

**Infrastructure needed:**

- Strix report importer.
- `AppSecFinding → AgentAbuseObjective` converter.
- Scope/authorization model so imported vulnerabilities cannot expand testing beyond allowed targets.
- Sandbox-only execution for PoC replay.

**Expected result:** RedThread tests realistic agent harm paths tied to actual app weaknesses.

**Overkill to avoid:** bundling browser/proxy/terminal exploitation tools into RedThread core.

### Use case 5 — Evaluation compatibility lane

**Goal:** let teams using DeepEval/Giskard compare or import results without changing RedThread's JudgeAgent.

**Tools:** DeepEval, Giskard.

**Workflow entrypoint:** after target execution or during CI.

```text
DeepEval/Giskard results
→ ExternalFinding/Event import
→ optional RedThread JudgeAgent re-score
→ dashboard/report comparison
```

**Infrastructure needed:**

- Optional importers.
- Score normalization model.
- Report section: external score vs RedThread score.

**Expected result:** easier adoption in teams that already use eval frameworks.

**Overkill to avoid:** replacing G-Eval/Prometheus 2 JudgeAgent or copying all metrics.

### Use case 6 — Security program artifacts

**Goal:** make RedThread useful to teams, auditors, and executives.

**Tool/source:** AI-Red-Teaming-Guide templates.

**Workflow entrypoint:** campaign setup and campaign close.

```text
Campaign config
→ rules of engagement + scope
→ run campaign
→ finding report + model/system security card update
→ stakeholder readout
```

**Infrastructure needed:**

- Artifact exporters:
  - rules of engagement
  - vulnerability report
  - model/system security card
  - stakeholder readout
  - PR checklist snippet
- Evidence-quality tags: evidence-backed, judge-inferred, operator-reviewed.
- Risk dimensions: exploitability, impact, autonomy, blast radius, recoverability.

**Expected result:** RedThread outputs become decision-ready, not just raw attack traces.

**Overkill to avoid:** building a full GRC platform.

## Desired end-state workflow

### 1. Campaign planning

```text
redthread plan --target target.yaml --profile agentic-rag
```

RedThread should:

- load scope and rules of engagement
- identify crown-jewel assets
- choose risk categories
- create baseline attack library slice
- flag coverage gaps
- optionally suggest external scanner lanes

### 2. Baseline scan lane

```text
redthread import garak ./garak-report.jsonl
redthread import promptfoo ./promptfoo-results.json
```

RedThread should:

- parse external findings
- preserve raw evidence
- map categories to rubrics
- re-score with JudgeAgent
- avoid defense synthesis until evidence is confirmed

### 3. Native RedThread attack lane

```text
redthread run --campaign campaign.yaml
```

RedThread should:

- generate personas
- run PAIR/TAP/Crescendo/GS-MCTS as appropriate
- fan out attack runners
- evaluate with JudgeAgent
- produce severity and confidence

### 4. Defense lane

```text
redthread defend --finding rt-find-123 --sandbox staging
```

RedThread should:

- synthesize grounded defense
- validate in sandbox
- re-run original attack and nearby variants
- mark defense as validated, partial, or failed

### 5. Regression/export lane

```text
redthread export promptfoo --campaign campaign-id --out security-evals/
```

RedThread should:

- export attack prompts and expected outcomes
- export defense regression tests
- emit CI thresholds
- preserve links back to RedThread findings

### 6. Reporting lane

```text
redthread report --campaign campaign-id --format markdown,json
```

RedThread should emit:

- executive summary
- ASR by category
- critical/high/medium/low findings
- top exploit chains
- defense validation status
- residual risk
- coverage gaps
- model/system security card delta

## Infrastructure changes needed

### P0 — data model and adapters

Add these concepts before any heavy integration:

```text
ExternalFinding
ExternalFindingSource
ExternalFindingImporter
ExternalTaxonomyMapping
ExternalScoreNormalization
EvidenceQuality
RiskTriageDimensions
```

Likely locations:

- `src/redthread/models.py` or a small `src/redthread/external_findings/models.py`
- `src/redthread/integrations/` for import/export adapters
- `src/redthread/evaluation/` for score normalization and re-scoring
- `src/redthread/reporting/` for artifacts

### P1 — import/export command surface

Add commands gradually:

```text
redthread import garak <path>
redthread import promptfoo <path>
redthread export promptfoo --campaign <id>
redthread coverage map --target <profile>
```

Do not add many commands at once. Start with one importer and one exporter.

### P1 — taxonomy map

Create a versioned mapping file:

```text
garak probe/detector → RedThread rubric → OWASP LLM Top 10 → MITRE ATLAS tactic
promptfoo plugin → RedThread rubric → OWASP/NIST category
DeepEval/Giskard check → RedThread rubric
Strix finding class → Agentic attack tree objective
```

This is more important than more scanners. It prevents fake coverage claims.

### P2 — artifact exporters

Generate guide-compatible artifacts:

- vulnerability report
- stakeholder readout
- rules of engagement
- model/system security card
- PR checklist

These should be templates populated from RedThread campaign evidence.

### P3 — optional external runners

Only after import/export works:

```text
redthread scan external garak --probes promptinject,encoding,dan
```

Do not run external scanners inside the core campaign loop by default. Keep them as explicit lanes.

## What RedThread should not do

| Temptation | Why not | Better move |
|---|---|---|
| Integrate every tool | Bloats dependencies and confuses ownership | Import/export + taxonomy map |
| Replace RedThread algorithms with promptfoo/PyRIT/Giskard attacks | Loses the proprietary closed-loop thesis | Use external attacks as seeds or regressions |
| Treat scanner results as final truth | Detectors can be noisy and context-blind | Re-score with JudgeAgent and preserve confidence |
| Build a commercial-platform clone | Not RedThread's current product shape | Export artifacts that satisfy platform/report needs |
| Add Strix runtime tools now | Expands blast radius | Ingest reports and copy scope/sandbox lessons |
| Make ART part of LLM pipeline | ART is strongest for classical ML/CV | Keep for future non-LLM lanes |
| Track only aggregate ASR | Hides high-risk categories | ASR by category, severity, autonomy, blast radius |

## Expected results if implemented correctly

### Near-term

- faster baseline coverage from garak/promptfoo imports
- cleaner CI adoption through promptfoo export
- better evidence normalization
- clearer reports and risk triage
- less repeated manual work

### Mid-term

- RedThread campaigns become comparable across targets and time
- validated defenses become persistent regression tests
- external scanner failures become higher-quality RedThread findings after re-scoring
- coverage gaps are explicit instead of hidden

### Long-term

- RedThread becomes a hub for AI security evidence:
  - imports scanner results
  - runs deeper native attacks
  - validates defenses
  - exports regressions
  - produces audit-ready artifacts

## Gap check

### Security / red-teaming coverage

No single-turn-only plan is acceptable. Any imported finding should be eligible for:

- single-turn replay when simple
- TAP branching when bypass depends on strategy variation
- Crescendo/GS-MCTS when the failure is multi-turn, agentic, or context-dependent

### Evaluation metrics

Every imported failure must be re-scored or at least confidence-tagged. Required metrics:

- external severity
- RedThread JudgeAgent score
- confidence
- ASR by category
- recurrence after mitigation
- time-to-verify

### Defense pipeline

The loop is broken if RedThread only imports and reports. High-confidence findings must be promotable to:

```text
defense synthesis → sandbox validation → regression export
```

### Open questions

- What external result schemas are stable enough to support first?
- Should promptfoo export target RedThread's internal target schema or user-provided provider config?
- How much raw prompt/response evidence can be retained before privacy controls are mandatory?
- Should severity be RedThread-owned or mapped directly from OWASP/NIST/CVSS-like categories?

## Recommended build order

1. **ExternalFinding schema + taxonomy map**
2. **garak import**
3. **promptfoo export**
4. **promptfoo import**
5. **coverage gap report**
6. **guide-style report/artifact exporters**
7. **DeepEval/Giskard optional importers**
8. **Strix report ingest and appsec-to-agent objective converter**
9. **external scanner runners only where they save real user time**

## Final stance

RedThread should use the guide to become more operationally complete, not more bloated.

The guide's best contribution is its **program shape**: scope, threat model, execute, score, report, remediate, regress. The tools' best contribution is **coverage and interoperability**. RedThread's best contribution remains **closing the loop** from exploit to validated defense.
