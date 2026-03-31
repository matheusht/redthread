# RedThread — Product Document

> **Status**: Architecture Review & Prototyping  
> **Product Type**: Autonomous AI Red-Teaming & Self-Healing Defense Engine (CLI)  
> **Target Environment**: Standalone (Phase 1) → Enterprise Integration (Phase 2+)  
> **Author**: Matheus

---

## 1. What Is RedThread?

RedThread is a **standalone, CLI-first autonomous red-teaming engine** for Large Language Model (LLM) deployments. Inspired architecturally by Claude Code's multi-agent orchestration, tool system, and task lifecycle, RedThread treats AI security testing as a first-class engineering discipline — not a one-off audit.

It does three things no other tool on the market does simultaneously:

1. **Automated, algorithmic adversarial attack generation** — using PAIR, TAP, Crescendo, and GS-MCTS to generate and execute attacks that are mathematically optimized, not manually written.
2. **Precision evaluation** — replacing subjective human scoring with probability-weighted, float-precision JudgeAgent scoring powered by Prometheus 2 and G-Eval.
3. **Self-healing defense synthesis** — automatically converting successful exploit traces into deployed semantic guardrails, re-validating them in a sandbox, and pushing them to production. The attack pipeline *fixes what it breaks*.

RedThread uses **PyRIT** (Python Risk Identification Toolkit) as its foundational plumbing layer for target interaction, orchestration loops, and payload conversion — while keeping all proprietary intelligence (search algorithms, defense synthesis, evaluation logic) in its own codebase.

---

## 2. Problem Statement

Deploying autonomous AI agents introduces **probabilistic vulnerabilities** — semantic data leakage, goal hijacking, conversational authorization bypasses — that deterministic security tools cannot detect. Currently:

- Adversarial testing of LLMs is **manual, unscalable, and expensive**.
- Testing is **decoupled from the defense layer** — findings generate reports, not fixes.
- Standard LLM-as-a-Judge evaluation suffers from **score clustering and verbosity bias**, making automated scoring unreliable for security use cases.
- No existing tool covers the full attack lifecycle: **generate → execute → judge → defend → verify**.

---

## 3. Core Architecture — Inspired by Claude Code

RedThread borrows key architectural patterns directly from the Claude Code source:

### From Claude Code's Coordinator Mode → RedThread's Supervisor
Claude Code's `coordinatorMode.ts` implements a **coordinator that spawns, directs, and manages parallel workers** — each with isolated context, autonomous execution, and structured result reporting via `<task-notification>` XML. RedThread's LangGraph supervisor follows the exact same pattern:

| Claude Code Pattern | RedThread Analog |
|---|---|
| **Coordinator** spawns `AgentTool` workers | **Supervisor** spawns `AttackRunner` sub-graphs |
| Workers report via `<task-notification>` | Runners report via structured `AttackTrace` objects |
| **Synthesis** — coordinator reads findings and crafts implementation specs | **Synthesis** — supervisor reads scored traces and routes to DefenseSynthesizer |
| Parallel research → sequential implementation | Parallel attack runs → sequential evaluation → defense |
| `SendMessageTool` continues workers | LangGraph `Send API` fans out parallel runs |

### From Claude Code's Tool System → RedThread's Tool Registry
Claude Code's `Tool.ts` defines a **typed, schema-validated tool registry** with `inputSchema`, `checkPermissions`, `validateInput`, `isReadOnly`, `isDestructive`, and progress callbacks. RedThread mirrors this for its own internal tools:

- `AttackTool` — executes a single adversarial payload via PyRIT
- `JudgeTool` — evaluates a trace against a scoring rubric
- `DefenseTool` — generates a candidate guardrail from an exploit trace
- `SandboxTool` — spins up a target replica and re-runs the attack

### From Claude Code's Task System → RedThread's Campaign Lifecycle
Claude Code's `Task.ts` defines typed task states (`pending`, `running`, `completed`, `failed`, `killed`) with deterministic ID generation. RedThread uses the same lifecycle for **attack campaigns**: each campaign is a top-level task that spawns sub-tasks (individual attack runs), each tracked through the same state machine.

### From Claude Code's Dream System → RedThread's Memory Consolidation
Claude Code's `autoDream` is a forked subagent that consolidates memory across sessions. RedThread uses the same concept for **attack memory** — a dream-like consolidation pass that synthesizes past attack results, prunes stale findings, and updates the system's threat knowledge base between campaign runs.

---

## 4. Core Use Cases

### Use Case 1: Pre-Deployment Penetration Testing
An engineering team is about to deploy a multi-agent customer service assistant. RedThread ingests the agent's system prompt and tool schemas, generates adversarial personas using MITRE ATLAS, and autonomously executes hundreds of multi-turn attacks across parallel runners. The team gets a severity-rated threat matrix before a single user touches the system.

### Use Case 2: CI/CD Behavioral Regression Testing
A developer updates a system prompt to make an agent "more helpful." RedThread, triggered via a CI hook, runs its baseline attack suite against the new build. The JudgeAgent calculates that resistance to "Authority Impersonation" has degraded by 40% — the build fails before the prompt reaches production.

### Use Case 3: Autonomous Guardrail Synthesis (The Defense Loop)
A TAP attack successfully bypasses a staging agent's defenses using a novel prompt injection. Instead of merely logging the failure, RedThread's Defense Synthesis Engine isolates the exact conversational pivot, generates a semantic blocking policy, deploys it to a sandbox, re-runs the attack to verify the fix, and pushes the validated guardrail to production. **Attack Success Rate drops from 100% to 0% — autonomously.**

---

## 5. Key Performance Indicators

| KPI | Target |
|---|---|
| **Attack Success Rate (ASR)** | Maximize during discovery (Phase 1-2), drive to 0% after guardrail deployment (Phase 5) |
| **Judge Agreement Rate** | >92% correlation with human-labeled baseline |
| **Novel Vulnerability Discovery Rate** | % of findings absent from standard positive-path testing |
| **Guardrail Validation Velocity** | < 5 minutes from exploit → validated defense |

---

## 6. What RedThread Is NOT

- **Not a web UI tool** — it's a CLI engine, like Claude Code. UI comes later.
- **Not coupled to Adopt AI** — Phase 1 is fully standalone. Enterprise integrations (ZAPI, Widdle, agent-orchestrator) are Phase 2+.
- **Not a PyRIT fork** — PyRIT is `pip install pyrit`, used as a library dependency via the Adapter pattern. RedThread's algorithms, evaluation, and defense synthesis are entirely proprietary.
