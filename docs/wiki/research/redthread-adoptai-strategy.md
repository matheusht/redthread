---
title: RedThread x Adopt AI Strategy
type: research
status: active
summary: Research synthesis for keeping RedThread standalone while using Adopt AI as the builder plane in a separate integration repo.
source_of_truth:
  - README.md
  - docs/TECH_STACK.md
  - docs/PHASE_REGISTRY.md
  - docs/wiki/research/current-hardening-tracks.md
  - program.md
  - https://docs.adopt.ai/essentials/agent-builder
  - https://docs.adopt.ai/essentials/zero-shot-api-ingestion
  - https://docs.adopt.ai/essentials/zero-shot-action-generation
  - https://github.com/adoptai/zapi
  - https://github.com/adoptai/noui
  - https://github.com/adoptai/abcd
  - https://github.com/adoptai/AdoptXchange
updated_by: codex
updated_at: 2026-04-22
---

# RedThread x Adopt AI Strategy

## Research question

If RedThread should stay a strong standalone project, where should Adopt AI fit, what should go into a separate integration repo, and what should the ZAPI workflow look like at different levels of complexity?

## Current synthesis

Best move is simple:

- keep **RedThread standalone**
- create **a separate integration repo** for Adopt AI work
- let **Adopt AI own the builder plane**
- let **RedThread own the attack, replay, and hardening plane**

This keeps the portfolio story clean.

For recruiters, this gives two stories instead of one mixed story:

1. **RedThread** — standalone autonomous red-team and self-healing security system
2. **Adopt RedThread** — practical enterprise integration showing how RedThread can harden real agent toolchains

That is stronger than blending both into one repo too early.

---

## Why this split is best

### Why not merge Adopt work straight into RedThread now

If everything goes into RedThread right away, bad things happen:

- RedThread story gets blurry
- core repo gets shaped by one integration partner too early
- standalone security research becomes harder to explain
- recruiter pitch gets more confusing
- repo trust surface gets bigger and messier

RedThread already has its own identity:

- attack algorithms
- evaluation truth
- replay and promotion gates
- runtime truth hardening
- agentic-security controls

That is already a strong portfolio project.

### Why a separate integration repo is better

A second repo gives cleaner positioning:

- **RedThread** shows original system thinking and security architecture
- **Adopt RedThread** shows ecosystem fit and enterprise applicability
- each repo can move at its own speed
- the RedThread core can stay honest and reusable
- the integration repo can be more experimental

This also makes outreach easier.

For most recruiters:
- lead with **RedThread**

For targeted outreach:
- show **Adopt RedThread** as a tailored extension proving you can connect novel research to real product workflows

---

## Role split

## Adopt AI main role

Adopt AI should be treated as the **agent builder plane**.

Its main jobs are:

- discover application capabilities
- turn real app behavior into tools and actions
- manage action/workflow build loops
- test and publish agent assets
- provide the operator workspace for shipping agent behavior

Useful Adopt pieces:

- **ZAPI** — discover APIs from real browser traffic
- **ZACTION** — turn discovered tools into executable actions
- **ABCD** — disciplined CLI workflow for discover, build, test, draft, publish
- **NoUI** — website-to-API and MCP generation for hard browser-native targets
- **AdoptXchange** — useful eval and integration patterns

## RedThread main role

RedThread should be treated as the **security assurance plane**.

Its main jobs are:

- attack prompts, tools, and workflows
- test authorization boundaries
- catch confused-deputy chains
- replay known failures
- validate fixes
- gate promotion and publish decisions with evidence

Simple split:

- **Adopt builds**
- **RedThread breaks and proves**

---

## Recommended repo strategy

## Keep in `redthread/`

Keep these in the standalone repo:

- core attack algorithms
- evaluation and judge stack
- replay bundles and promotion logic
- runtime truth and execution truth work
- agentic-security controls
- generic tool-security scenarios
- generic MCP / action / workflow hardening abstractions
- docs and portfolio story for RedThread itself

Do **not** make RedThread depend on Adopt-specific runtime details for its identity.

## Put in `adopt-redthread/`

Put these in the integration repo:

- ZAPI ingestion adapters
- Adopt action and tool catalog importers
- NoUI target-generation experiments
- Adopt-specific replay packs
- pre-publish security gate wrappers for ABCD-style workflows
- mapping from Adopt actions to RedThread target fixtures
- demo architecture and case studies
- recruiter-friendly examples of real agent hardening against a practical stack

## Boundary rule

RedThread should expose reusable security patterns.

Adopt RedThread should consume those patterns for one real ecosystem.

That means:
- copy as little as possible
- wrap and integrate instead of forking RedThread logic blindly
- upstream generic security abstractions back into RedThread only when they are truly general

---

## Current bridge milestone

As of 2026-04-22, the bridge repo now has three meaningful intake/handoff lanes:

1. sample catalog-style ZAPI intake
2. real HAR-derived ZAPI intake
3. first NoUI MCP server intake (`manifest.json` + `tools.json`)

It also now has a bounded live-control ladder on top of those lanes:
- **one-command artifact pipeline**
- **one-command live ZAPI capture runner**
- **machine-readable live attack planning**
- **bounded live safe-read replay**
- **bounded reviewed auth-safe-read replay**
- **bounded reviewed staging-write replay**
- **bounded grouped workflow replay**
- **evidence-aware replay gate**

And it still reaches two real RedThread seams:
- **ReplayBundle export + promotion-gate evaluation**
- **dry-run campaign-case export + RedThread engine execution**

What this means now:
- `adopt-redthread` can ingest a HAR-shaped ZAPI capture
- it can ingest a NoUI MCP server output
- it can normalize those artifacts into the same RedThread-friendly fixture model
- it can generate `live_attack_plan.json` and `live_workflow_plan.json`
- it can execute bounded live lanes when policy and approval context allow them
- it can now carry **bounded workflow evidence** forward across grouped sequential steps
- it can emit structured workflow evidence like:
  - `final_state`
  - per-step `workflow_evidence.state_before`
  - per-step `workflow_evidence.state_after`
  - summary `reason_counts`
  - structured `failure_reason_code`
- it can feed that workflow/live evidence plus the RedThread replay verdict back into the bridge gate
- it can export fixtures into RedThread replay payloads and dry-run campaign seeds
- it can evaluate the replay payload with RedThread's real promotion-gate code
- it can run one generated case through RedThread's real dry-run engine path
- it can now chain those steps from one top-level command
- it can now launch a live ZAPI browser capture, select the downstream HAR, and feed that capture into the bridge automatically

What this still does **not** mean:
- RedThread has become a browser automation product
- RedThread core now depends on ZAPI, NoUI, or Tabby runtime code
- the bridge is now a full live production integration
- generated campaign prompts are production-truth target prompts
- workflow replay has become real browser/session-state orchestration
- later requests are dynamically rewritten from prior response bodies
- RedThread is already doing rich autonomous live attack execution immediately after discovery

This milestone keeps the original split intact:
- **Adopt tools improve discovery and app-specific surface generation**
- **Adopt RedThread adapts those artifacts into fixtures, live plans, workflow evidence, gate artifacts, and runtime handoff payloads**
- **RedThread remains the attack, replay, validation, and hardening engine**

The practical value is personalization without identity drift.
The target app can now shape the fixtures more realistically, the bridge can carry bounded workflow evidence forward instead of only single-request results, and the resulting live/runtime evidence can feed a more honest gate without turning RedThread into a browser runtime.

---

## Recommended architecture

```text
[real app / website]
        ↓
[ZAPI or NoUI discovery]
        ↓
[Adopt tools and actions]
        ↓
[agent under test]
        ↓
[RedThread attack + replay + validation]
        ↓
[publish / block / promote]
```

## Layer view

### Layer 1 — Discovery
Owner: Adopt AI

Use:
- ZAPI for API discovery
- NoUI for website-native or auth-heavy targets

Output:
- documented APIs
- auth hints
- tool candidates
- workflow groups

RedThread entry:
- risk classification
- read vs write tagging
- sensitive-path detection
- approval-needed tagging

### Layer 2 — Action generation
Owner: Adopt AI

Use:
- ZACTION
- Agent Builder
- ABCD workflow

Output:
- actions
- workflows
- prompts
- publishable drafts

RedThread entry:
- attack fixtures
- negative tests
- route-confusion probes
- action misuse probes

### Layer 3 — Runtime execution
Owner: Adopt AI runtime

RedThread entry:
- prompt abuse testing
- wrong-tool-choice testing
- multi-step escalation testing
- provenance and authorization validation
- tool-output poisoning tests

### Layer 4 — Promotion gate
Shared seam, but RedThread should own trust evidence.

Adopt handles:
- draft
- publish
- environment workflow

RedThread handles:
- attack evidence
- replay verdicts
- benign utility checks
- recommendation to block or approve

---

## Repo-by-repo recommendation

## `adoptai/zapi`

### Role
Discovery intake plane.

### Best use
- capture real browser traffic
- build endpoint inventory
- generate documented API set
- feed RedThread target modeling

### Recommendation
Use directly through wrappers in `adopt-redthread/`.
Do not merge it into RedThread core.

### What to build around it
- importer from documented APIs into RedThread target fixtures
- endpoint risk classifier
- safe replay planner

## `adoptai/noui`

### Role
Target factory for browser-native and auth-heavy systems.

### Best use
- turn websites into callable APIs or MCP servers
- preserve authenticated context
- generate realistic tool surfaces for security testing

### Recommendation
Use in `adopt-redthread/` when the target is too browser-dependent for plain API discovery.
Higher value, higher operational complexity.

## `adoptai/abcd`

### Role
Builder workflow and operator discipline.

### Best use
- discover → build → test → draft → publish flow
- workspace separation
- environment discipline

### Recommendation
Borrow process patterns.
Integrate RedThread as a pre-publish gate.
Do not make RedThread itself an ABCD plugin-first project.

## `adoptai/AdoptXchange`

### Role
Evaluation and integration pattern donor.

### Best use
- grouped multi-turn conversation evals
- schema and tracing checks
- bulk evaluation structure

### Recommendation
Reference and reuse ideas, especially for multi-turn replay packs.

## `adoptai/agent-orchestrator`

### Role
Reference for route ambiguity and action-matching scenarios.

### Recommendation
Use as reference only.

---

## ZAPI workflow

## Wrong simple framing

Too simple:

- capture HAR
- send POST requests
- call that bot testing

That misses the real layers.

Real layers are:

1. discovery
2. cataloging
3. auth/session truth
4. action generation
5. routing behavior
6. multi-turn workflow behavior
7. live replay safety
8. release gating

So the ZAPI workflow should grow by levels.

## Level 0 — Discovery only

Goal:
- learn what the app can do

Flow:
- run ZAPI discovery
- capture HAR
- upload and document APIs
- build endpoint inventory

RedThread job:
- classify risk
- tag sensitive endpoints
- separate safe reads from risky writes

Good for:
- first contact with a target
- low-risk research

## Level 1 — Safe endpoint replay

Goal:
- test raw capability surface safely

Flow:
- use documented APIs from ZAPI
- filter to read-only or low-risk endpoints first
- replay structured requests
- fuzz parameters and leakage cases

RedThread job:
- detect secret leakage
- detect schema confusion
- detect overbroad retrieval
- create first replay fixtures

Good for:
- low blast radius validation

## Level 2 — Action-level testing

Goal:
- test the built agent actions, not just raw HTTP

Flow:
- ZAPI discovers APIs
- Adopt turns them into actions
- RedThread attacks those actions through natural language prompts

RedThread job:
- wrong action choice
- hidden write activation
- bad param extraction
- approval bypass attempts

Good for:
- first real “test the bot” stage

## Level 3 — Multi-turn workflow testing

Goal:
- test chained actions and conversation memory

Flow:
- use grouped conversation suites
- run follow-up prompts that try to escalate or redirect prior safe flows

RedThread job:
- confused deputy detection
- cross-turn escalation
- approval fatigue pressure
- provenance loss detection

Good for:
- real business agent workflows

Current bridge truth:
- the bridge now has a **bounded version** of this layer
- grouped workflow replay exists
- it carries bounded workflow evidence forward in output artifacts
- it emits structured failure reasons for gate mapping
- but it is still not full browser/session-state orchestration

## Level 4 — Auth/session-aware live replay

Goal:
- test with realistic authenticated context

Flow:
- use staging or sandbox
- run with controlled sessions
- intercept every risky action before send

RedThread job:
- session misuse detection
- tenant boundary checks
- action authorization proof
- deny-before-send behavior

Good for:
- enterprise-grade confidence

Constraint:
- only do this with strong interception and low-risk environments

## Level 5 — Pre-publish certification

Goal:
- make security proof part of shipping

Flow:
- on new or changed actions, run selected replay packs automatically
- collect attack and benign evidence
- block publish when needed

RedThread job:
- final trust verdict
- operator-readable evidence

Good for:
- repeatable product discipline

---

## Complexity cases

## Case A — Read-heavy analytics apps

Best starting path:
- ZAPI discovery
- read-only replay
- leakage tests
- action retrieval tests

Main risk:
- sensitive overexposure

## Case B — CRUD business apps

Best starting path:
- ZAPI discovery
- write-path tagging
- read-only replay first
- sandboxed write-path tests later

Main risk:
- unauthorized mutation

## Case C — Workflow-heavy enterprise agents

Best starting path:
- action-level testing
- multi-turn replay suites
- approval and provenance checks

Main risk:
- safe individual actions becoming unsafe when chained

## Case D — Auth-heavy browser apps

Best starting path:
- human-guided discovery or NoUI
- session-aware staging replay
- minimal live mutation

Main risk:
- role confusion and session leakage

---

## Portfolio positioning

## RedThread pitch

Use RedThread as the main portfolio story:

- standalone
- opinionated
- security-focused
- architecture-heavy
- proves original thinking

## Adopt RedThread pitch

Use the integration repo for tailored outreach:

- shows you can map deep security work onto real product stacks
- shows practical agent hardening, not just theory
- makes your outreach feel customized and high-signal

This pairing is strong:

- RedThread shows depth
- Adopt RedThread shows relevance

---

## Current recommendation

Best path now:

1. keep `redthread/` standalone
2. use `adopt-redthread/` as the integration repo
3. write one strong strategy page in the RedThread wiki
4. build the smallest working ZAPI → RedThread intake path first
5. only then add action-level and pre-publish gate experiments

## Next questions

1. what should the first `adopt-redthread/` MVP ingest from ZAPI exactly?
2. what should the RedThread fixture schema be for Adopt tools and actions?
3. what should the first pre-publish gate command look like?
4. how should recruiter-facing demos differ between RedThread and Adopt RedThread?

## Sources

Internal:
- [README.md](../../README.md)
- [docs/TECH_STACK.md](../../TECH_STACK.md)
- [docs/PHASE_REGISTRY.md](../../PHASE_REGISTRY.md)
- [research/current-hardening-tracks.md](current-hardening-tracks.md)
- [../../program.md](../../program.md)

External:
- [Adopt AI Agent Builder docs](https://docs.adopt.ai/essentials/agent-builder)
- [Adopt AI ZAPI docs](https://docs.adopt.ai/essentials/zero-shot-api-ingestion)
- [Adopt AI ZACTION docs](https://docs.adopt.ai/essentials/zero-shot-action-generation)
- [adoptai/zapi](https://github.com/adoptai/zapi)
- [adoptai/noui](https://github.com/adoptai/noui)
- [adoptai/abcd](https://github.com/adoptai/abcd)
- [adoptai/AdoptXchange](https://github.com/adoptai/AdoptXchange)
