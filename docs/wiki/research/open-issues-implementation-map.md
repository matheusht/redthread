---
title: Open Issues Implementation Map
type: research
status: active
summary: Research, specifications, implementation, and verification for the complete open-issue snapshot.
source_of_truth:
  - docs/research/sources/open-issues-2026-09-18.json
  - AGENTS.md
updated_by: codex
updated_at: 2026-09-18
---

# Open Issues Implementation Map

## Destination

Implement the remaining intake issues: 19, 75, 76, 78, 79, 82, 85, 88, 91, 92, 94. User excluded 80, 89, 83, 86, 90, 93, 84, 77, 81, 87 because another contributor is implementing them. Preserve human promotion gates. Prove requirements with current code, focused tests, full suite, lint, type checks, and independent review.

## Source and workflow

- Baseline commit: `4242ab8`. Working branch: `feat/open-issues-production-readiness`.
- [Immutable issue snapshot](../../research/sources/open-issues-2026-09-18.json).
- [Existing map](https://github.com/matheusht/redthread/issues/74) supplies Wave 2 scope; launch-readiness issue adds separate product scope.
- Workflow: wayfinder → research → to-spec → implement → standards/spec review.
- Matt Pocock workflow skills installed from `mattpocock/skills`, `skills/engineering/`, on 2026-09-18.
- User authorizes autonomous decisions and Luna high subagents. Routine interview/approval pauses waived; actual gates remain.
- [LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f): immutable evidence, curated synthesis, navigation/log maintenance. Existing repo schema retained.

## Current evidence and constraints

- Three research agents inspect evaluation/replay, security/runtime, and product/storage separately.
- Repo references absent `.agent/skills/plan`, `.agent/skills/implement`, and `.agent/rules`; installed workflow skills plus authoritative docs supply procedures.
- MemPalace local command supports `--room`, not documented `--wing`. Keyword search for redthread production readiness returned no results.
- GitHub viewer permission is READ; assignment rejected. Local ledger records ownership; no issue claimed or closed remotely.
- Fresh Python 3.12 virtualenv installed with project dev dependencies.
- Baseline Ruff passed. Baseline mypy passed across 301 source files. Baseline pytest: 714 passed, 3 skipped, 2 terminal-wrap assertion failures. Both failing tests pass with `COLUMNS=240 REDTHREAD_DRY_RUN=true`; full final suite will use that reproducible environment.

## Requirements ledger

Each row remains pending until implementation and validation evidence is linked.

| Issue | Work | State |
| --- | --- | --- |
| [19](https://github.com/matheusht/redthread/issues/19) | If only Fable had a RedThread report: launch-readiness preset | Implementation |
| [74](https://github.com/matheusht/redthread/issues/74) | [Map] RedThread System Evolution & Production Readiness (Wave 2) | Tracking only |
| [75](https://github.com/matheusht/redthread/issues/75) | Architecture: Decompose monolithic evaluation pipeline (pipeline.py) into orchestrator, heuristics, and metrics | Implemented; focused checks passed; integration review pending |
| [76](https://github.com/matheusht/redthread/issues/76) | Architecture: Decompose core data models (models.py) to enforce separation of concerns | Implemented; focused checks passed; integration review pending |
| [77](https://github.com/matheusht/redthread/issues/77) | Architecture: Modularize benchmark exports and regression handoff serialization | External owner — excluded |
| [78](https://github.com/matheusht/redthread/issues/78) | Security: Enforce strict parameter validation in ActionEnvelope authorization engine | Implementation |
| [79](https://github.com/matheusht/redthread/issues/79) | Security: Prevent authorization bypass via spoofed target sensitivity in ActionEnvelope | Implementation |
| [80](https://github.com/matheusht/redthread/issues/80) | Security: Guard promotion gate against empty replay bundles | External owner — excluded |
| [81](https://github.com/matheusht/redthread/issues/81) | Security: Add deterministic least-agency policy presets for filesystem and network egress | External owner — excluded |
| [82](https://github.com/matheusht/redthread/issues/82) | Architecture: Wire specialized agent pipeline (ReconAgent -> SocialAgent -> ExploitAgent) into SupervisorGraph | Implementation |
| [83](https://github.com/matheusht/redthread/issues/83) | Resilience: Implement worker-level execution timeouts and cancellation tripwires in AttackGraph | External owner — excluded |
| [84](https://github.com/matheusht/redthread/issues/84) | Observability: Propagate agentic security summaries and canary events into campaign metadata | External owner — excluded |
| [85](https://github.com/matheusht/redthread/issues/85) | Robustness: Add explicit degraded evidence warnings when Judge LLM fails in EvaluationPipeline | Implemented; focused checks passed; integration review pending |
| [86](https://github.com/matheusht/redthread/issues/86) | Robustness: Resilient markdown fence and JSON parsing in JudgeAgent evaluation responses | External owner — excluded |
| [87](https://github.com/matheusht/redthread/issues/87) | Feature: Expand Golden Dataset coverage for multi-turn Crescendo and confused deputy traces | External owner — excluded |
| [88](https://github.com/matheusht/redthread/issues/88) | Performance: Enable SQLite WAL mode and busy timeout in TelemetryStorage | Implemented; focused checks passed; integration review pending |
| [89](https://github.com/matheusht/redthread/issues/89) | Robustness: Handle zero-variance and stationary series in ARIMA drift detector | External owner — excluded |
| [90](https://github.com/matheusht/redthread/issues/90) | Robustness: Guard AgentStabilityIndex (ASI) calculation against zero or insufficient records | External owner — excluded |
| [91](https://github.com/matheusht/redthread/issues/91) | Concurrency: Atomic cross-process file locking for MEMORY.md and deployments.jsonl | Implemented; focused checks passed; integration review pending |
| [92](https://github.com/matheusht/redthread/issues/92) | Robustness: Replace brittle string splitting with structured block parser in MemoryIndex | Implemented; focused checks passed; integration review pending |
| [93](https://github.com/matheusht/redthread/issues/93) | Safety: Comprehensive dictionary value redaction and identifier scrubbing in gepa_side_info.py | External owner — excluded |
| [94](https://github.com/matheusht/redthread/issues/94) | Feature: Add redthread replay run CLI command for offline agentic promotion verification | Implemented; focused checks passed; integration review pending |

## Research and specification

- [Active specification](../../research/open-issues-spec.md) — remaining scope and public test seams.
- [Evaluation research](../../research/open-issues-evaluation.md) — decomposition, evidence fallback, offline replay inspection.
- [Security/runtime research](../../research/open-issues-security-runtime.md) — argument policy, sensitivity authority, specialized routing.
- [Product/storage research](../../research/open-issues-product-storage.md) — launch preset, model decomposition, WAL, locked memory, Markdown clauses.
- Research descriptions retain historical observations for external-owned issues; they do not authorize their implementation.

## Dependencies and verification

- Evaluation extraction precedes fallback metadata; preserve golden fixtures and parsing owned externally.
- Authorization argument validation and authoritative sensitivity share policy contracts; avoid external-owned preset issue 81.
- Specialized routing touches worker boundaries; coordinate with external-owned timeout/cancellation issue 83.
- Memory locking and markdown parsing share MemoryIndex; one owner.
- Launch readiness consumes truthful evaluation/replay/security evidence; integrate after those contracts settle.
- Replay CLI uses existing evaluator. Empty-replay rejection belongs to external-owned issue 80; do not duplicate its fix.

## Open questions

- Resolve reported behavior against actual source; issue descriptions may have stale locations or assumptions.
- Establish baseline suite failures before attributing failures to this work.
- Final remote publication depends on fork/PR permissions; local implementation does not.

## Scope correction

User excluded ten issues after initial research; no runtime implementation had begun. The immutable intake snapshot retains historical scope. Active spec and this ledger reflect the correction. [Published spec](https://github.com/matheusht/redthread/issues/105) tracks only remaining work.

## Storage/model verification checkpoint

Model decomposition, WAL, memory locks, and legacy Markdown parsing have landed. Agent reports 56 focused checks passed and touched-module Ruff/mypy clean. Independent concurrency/parser review is pending. New memory helper modules match an existing broad gitignore rule and must be explicitly included in the final commit.
