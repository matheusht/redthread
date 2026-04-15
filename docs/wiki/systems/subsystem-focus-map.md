---
title: Subsystem Focus Map
type: system
status: active
summary: Current subsystem-by-subsystem focus map for RedThread, centered on trust, hardening, and bounded progress rather than new feature expansion.
source_of_truth:
  - README.md
  - docs/TECH_STACK.md
  - docs/PHASE_REGISTRY.md
  - docs/REDTHREAD_STATUS_AUDIT.md
  - docs/PROGRESS.md
  - program.md
updated_by: codex
updated_at: 2026-04-14
---

# Subsystem Focus Map

## Scope

This page answers a practical question:

**Where should work go right now, subsystem by subsystem?**

The current answer is not "build more features first."
The current answer is:
- make the truth layers trustworthy
- tighten governance boundaries
- prove runtime behavior more honestly
- deepen defense confidence

## Global priority

Current project-wide ordering:
1. verification and evaluation truth
2. governance and mutation boundaries
3. runtime truth and operator-safe execution
4. defense validation confidence
5. only then consider broader new features

## Subsystem map

### 1. Offense algorithms

**What it is**
- PAIR
- TAP
- Crescendo
- GS-MCTS

**Current state**
Strong feature coverage already exists.
The repo does not appear blocked by lack of attack families.

**What matters now**
- algorithm routing quality
- parameter tuning
- replay pressure against known weak spots
- measuring useful attack diversity instead of just adding breadth

**Do now**
- improve routing between existing algorithms
- calibrate search budgets and stopping heuristics
- use research lanes to improve objective-to-algorithm matching

**Do not do now**
- do not add another major attack algorithm before trust gaps are closed

### 2. Judge and evaluation

**What it is**
- JudgeAgent
- G-Eval / rubric scoring
- Golden Dataset regression
- evaluation pipeline and CI gates

**Current state**
This is the most important truth layer in the project.
It is also where current confidence is still weakest, because sealed regression and live behavior are not the same thing.

**What matters now**
- green regression suite
- correct handling of clear jailbreak classes such as system-prompt leakage
- explicit separation of sealed heuristic fallback vs live judge behavior

**Do now**
- fix failing golden regression cases
- tighten score calibration around sensitive disclosure and prompt exfiltration
- make evidence stronger for what CI proves vs what only live smoke proves

**Do not do now**
- do not widen mutation into judge logic from autoresearch lanes

### 3. Defense synthesis and validation

**What it is**
- isolate → classify → generate → validate → deploy pipeline
- defense architect prompts and assets
- replay validation and structured reports

**Current state**
This is RedThread's differentiator.
The main architecture is present, but confidence should keep moving from "good story" to "strong evidence."

**What matters now**
- replay depth
- benign utility preservation
- promotion evidence clarity
- exploit-scoped defensive behavior instead of broad refusal drift

**Do now**
- deepen replay fixtures
- strengthen benign checks
- keep deployment and promotion evidence operator-readable

**Do not do now**
- do not widen mutable defense scope beyond prompt/template assets yet

### 4. Telemetry and monitoring

**What it is**
- ARIMA
- ASI
- canary probes
- monitor daemon

**Current state**
Useful support layer.
Not the main blocker today.

**What matters now**
- use telemetry as a safety/control layer
- avoid overclaiming it as proof of deep runtime correctness
- keep control metrics protected from mutation

**Do now**
- preserve stability
- keep monitor useful for operator visibility
- make sure telemetry results are interpreted conservatively

**Do not do now**
- do not over-invest in more telemetry complexity before the judge/runtime truth gap is smaller

### 5. Orchestration and engine runtime

**What it is**
- engine facade
- LangGraph supervisor
- attack/judge/defense worker flow
- transcripts and campaign lifecycle

**Current state**
The main workflow exists end to end.
This is one of the stronger parts of the repo structurally.

**What matters now**
- honest runtime proof
- reliable dry-run semantics
- small live smoke validation path

**Do now**
- make dry-run truly offline
- add opt-in live smoke coverage for the real path
- keep worker boundaries simple and inspectable

**Do not do now**
- do not add orchestration complexity unless it directly reduces trust gaps

### 6. Research and bounded autoresearch

**What it is**
- Phase 3/4/5/6 research flows
- bounded source mutation
- bounded defense prompt mutation
- proposals, checkpoints, promotion preparation

**Current state**
Very strong and ambitious area.
Also highest governance risk area.

**What matters now**
- real boundedness
- explicit human gate
- protected surfaces that stay protected
- reproducible experiment evidence

**Do now**
- tighten mutation allowlists
- verify daemon behavior matches the claimed governance model
- keep supervisor acceptance separate from mutation generation

**Do not do now**
- do not let bounded autoresearch silently become broad self-editing

### 7. Knowledge system

**What it is**
- MemPalace retrieval layer
- wiki synthesis layer under `docs/wiki/`

**Current state**
Good system for durable recall and durable synthesis.
Useful for keeping architecture truth from drifting across sessions.

**What matters now**
- record real runtime truth, not marketing summary
- preserve contradictions and open questions honestly
- use the wiki to guide focus, not just describe features

**Do now**
- keep wiki aligned with status audits and phase registry
- use MemPalace before high-impact wiki edits
- document hardening decisions as they happen

### 8. Docs, governance, and operator trust

**What it is**
- source docs
- decision-tree navigation
- operator approval story
- claims about validation and promotion

**Current state**
This is a major trust surface.
Some docs are ahead of runtime truth.

**What matters now**
- doc/runtime alignment
- honest statements about manual gates, dry-run, and live validation
- reducing governance ambiguity

**Do now**
- fix stale navigation
- align docs with actual daemon and promotion behavior
- treat trust language as an engineering surface, not just copywriting

## Focus summary by urgency

### Highest urgency
- Judge and evaluation
- Docs, governance, and operator trust
- Research boundedness
- Dry-run and live runtime truth

### Medium urgency
- Defense validation depth
- Orchestration ergonomics for inspection

### Lower urgency for now
- new offense features
- more telemetry sophistication
- UI or enterprise packaging

## Bottom line

RedThread already has enough capability breadth.
The next wins should come from:
- stronger truth
- stronger gates
- stronger evidence
- stronger operator confidence

That is the current focus map.
