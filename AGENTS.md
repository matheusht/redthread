# RedThread Agent Architecture

This document dictates the behavior and orchestration of the Antigravity Agent when working within the RedThread repository.

**All behavioral configurations must strictly refer to the `docs/` sources of truth.**

## 1. Core Operating Guidelines
* **Decision Matrix:** Before running *any* operation, the agent must consult [docs/AGENT_DECISION_TREE.md](docs/AGENT_DECISION_TREE.md) to identify which domain document to load based on the user's intent.
* **Working Methodology:** All tasks must follow the RPI (Research → Plan → Implement) flow outlined in [docs/RPI_METHODOLOGY.md](docs/RPI_METHODOLOGY.md). Context must not exceed 40% window utilization.
* **Default Response Style:** Use full caveman mode by default unless the user asks for a different style. That means simple words, short direct sentences, practical structure, low fluff, and clear "what this is / why it matters / what next" guidance.
* **Context Index:** Start broad repository sessions with [docs/ai-context-summary.md](docs/ai-context-summary.md) and [docs/context-index.md](docs/context-index.md). Load large research, logs, and historical docs only on demand.

## 2. The Orchestration Workflow (Principal vs Subagents)
Antigravity operates as the **Principal Agent** inside the RedThread ecosystem. It acts identically to the LangGraph supervisor documented in `docs/PHASE_REGISTRY.md` and `docs/AGENT_ARCHITECTURE.md`—it manages the task graph while delegating execution.

### The Principal Agent Must:
1. Clarify intent.
2. Load relevant `.agent/rules/`.
3. Read the relevant document from `docs/AGENT_DECISION_TREE.md`.
4. Trigger the correct `.agent/skills/`.

### Subagent Usage
When tasks bridge boundaries, the Principal Agent MUST delegate:
* **Research Agent (Model: Opus 4.6):** Use for sweeping file aggregation or reading large datasets. Focuses strictly on extracting context, paths, and patterns without modifying files.
* **Plan Agent / Implement Agent:** Used to isolate complex edits (e.g. creating a PersonaGenerator node) from the Principal Agent's context. Always requires explicit `.agent/skills/` procedures like TAP, PAIR, or G-Eval execution.

## 3. Mandatory Component Rules
Do not maintain rules in this document.
Always apply `.agent/rules/` for global operations. Use `.agent/skills/` for specific tasks.

## 3.0 Mirror Policy
`AGENTS.md` and `docs/` are authoritative. `.agent/` is the Antigravity-facing mirror. `.codex/` is the Codex-facing mirror. When changing shared behavior, update the source doc first, then update both mirrors if the rule applies to both tools. If a mirror intentionally differs, state why in that mirror. Do not let RPI, context budget, code conventions, or skill procedures drift silently.

## 3.0.1 Work Quality Rules
Use code and shell tools for deterministic facts. Use the model for judgment, synthesis, and summarization. Make surgical changes and avoid adjacent refactors. State conflicts instead of blending them. Read immediate callers and shared utilities before code edits. Verify before saying done; if checks are skipped or fail, say so.

## 3.1 Knowledge System Rules
RedThread uses a two-layer knowledge system:
- **MemPalace** for retrieval and session memory
- **`docs/wiki/`** for curated markdown synthesis

Before editing the wiki, agents must read:
1. `docs/WIKI_ARCHITECTURE.md`
2. `docs/WIKI_INGEST_WORKFLOW.md`
3. `docs/wiki/SCHEMA.md`
4. `docs/wiki/index.md`

Wiki rules:
- Search MemPalace before making high-impact wiki edits.
- Treat `docs/` source docs as authoritative engineering references.
- Update `docs/wiki/index.md` and append to `docs/wiki/log.md` for durable wiki changes.
- Use `docs/WIKI_INGEST_WORKFLOW.md` for source-driven updates.
- Use `docs/WIKI_QUERY_TO_PAGE_WORKFLOW.md` for answer-driven updates.
- Do not silently convert uncertain conclusions into settled facts.
- When writing docs or operator guidance, default to full caveman mode unless the user asks for a different tone.

# Clean Code, SOLID, Separation of Concerns, and Performance

## File size limit
No component, hook, or module file may exceed **200 lines**.
Split before or during implementation, never after the fact.
If a change would push a file past the limit, extract sub-components, hooks, or helpers first.

## Separation of concerns
- **Orchestration & State** (LangGraph StateGraph, node functions, state TypedDicts) → `src/redthread/orchestration/`
- **Agent Specialized Logic** (ReconAgent, SocialAgent, ExploitAgent nodes) → `src/redthread/orchestration/agents/`
- **Core Adversarial Algorithms** (PAIR, TAP, MCTS, Crescendo) → `src/redthread/core/`
- **Adversarial Tools** (Typed `RedThreadTool` registry with Pydantic schemas) → `src/redthread/tools/`
- **Evaluation & Scoring** (JudgeAgent, G-Eval, Prometheus 2 integration) → `src/redthread/evaluation/`
- **Adapter Layer** (PyRIT targets, runners, and converters wrappers) → `src/redthread/pyrit_adapters/`
- **Telemetry & Monitoring** (Embeddings, drift detection, ARIMA baselines) → `src/redthread/telemetry/`
- **Memory & Persistence** (Knowledge indexing, dream/consolidation logic) → `src/redthread/memory/`
- **Typed Models & Schemas** (Core dataclass/Pydantic models) → `src/redthread/models.py` or local `models/` folders.
- **CLI & Workflow Entrypoints** (Click/Typer CLI, Engine lifecycle) → `src/redthread/cli.py` & `src/redthread/engine.py`

- **Do not mix** LangGraph orchestration with deep algorithmic logic in the same file.
- Keep agent prompts, tools, and evaluation rubrics in their dedicated layers.
- If one node or tool starts owning multiple concerns, split it before adding more behavior.

## SOLID principles
- **SRP**: Each file has exactly one reason to change (e.g., one node, one tool, one algorithm).
- **OCP**: Use registries or maps for persona generators or converter types instead of hardcoded `if/else` chains.
- **ISP**: Define narrow LangGraph state updates; nodes should only receive the keys they need to operate.
- **DIP**: Inject target LLMs, scorers, and memory providers rather than hardcoding concrete implementations inside core algorithms.
- Prefer composition of small nodes and tools over broad, state-heavy orchestrators.

## No duplication
- If a helper function appears in more than one file, extract it to `src/redthread/core/utils.py` or common module.
- If a Pydantic model is reused across subsystems, pull it into `src/redthread/models.py`.

## Performance
- Optimize only where the code path justifies it (e.g., parallelizing target calls).
- Use LangGraph `Send` API to execute parallel attack branches rather than sequential loops.
- Do not add complex caching or drift detection churn without a concrete requirement in the current loop.
- Prefer server-side or batched work for telemetry (ChromaDB/FAISS) over repeated client recomputation.

# Progressive Disclosure, Context Debloating, and RPI

## Start here
- Start implementation tasks at [docs/ai-context-summary.md](docs/ai-context-summary.md), [docs/context-index.md](docs/context-index.md), root [README.md](README.md), and [docs/TECH_STACK.md](docs/TECH_STACK.md).
- Open the matching repo-local skill before implementation work:
  - New features, architecture changes, multi-file work, or unclear impact → `.agent/skills/plan/SKILL.md` then `.agent/skills/implement/SKILL.md`
  - Small tweaks, isolated bugfixes, copy edits, or low-blast-radius polish → `.agent/skills/mini-rpi/SKILL.md`
- Read only the most relevant focused doc after the index:
  - `docs/TECH_STACK.md`
  - `docs/ANTI_HALLUCINATION_SOP.md`
  - `docs/RPI_METHODOLOGY.md`
  - then one of `docs/algorithms.md`, `docs/AGENT_ARCHITECTURE.md`, or `docs/PHASE_REGISTRY.md`.

## Progressive disclosure
- Start from [README.md](README.md), then open only the most relevant focused doc, then only the source files on the execution path.
- Prefer targeted `rg` searches over broad file reads.
- Do not read whole directories or large files unless the current task requires them.
- When adding docs, keep them hub-and-spoke: one index page plus focused linked pages.

## Context debloating
- Summarize findings before opening more files.
- Avoid restating code that already exists; link to files instead.
- Load only the minimum files needed to answer or implement.
- If a task touches one subsystem, do not preload unrelated subsystems.
- Prefer adding references over expanding instruction files.

## RPI workflow
- Use full `Research -> Plan -> Implement` for any new feature or medium/large change.
- `Research`: inspect current flow, constraints, affected interfaces, and neighboring files before editing.
- `Plan`: define behavior, touched areas, tests, and acceptance criteria before editing.
- `Implement`: make the smallest coherent change set, then verify it.
- Do not begin implementation until research has identified the real entrypoints and constraints.

## Mini-RPI
- Use `Research -> Plan -> Implement` in a reduced form for small tweaks, bugfixes, copy edits, or isolated UI polish.
- `Research`: inspect 1-3 directly relevant files.
- `Plan`: state the intended change, impact surface, and quick verification.
- `Implement`: patch only the minimal affected slice.
- Escalate from mini-RPI to full RPI whenever the tweak crosses subsystem boundaries, changes data flow, or risks regressions.

<!-- clarity-begin -->
<!-- clarity-meta
schema_version: 1
mode: embedded
protocol_dir_name: .clarity-protocol
processes_dir: .clarity-agent/processes
-->
<!-- Clarity manages this block; edits between the clarity-begin / clarity-end markers will be overwritten on the next project open. Put project-specific guidance outside the markers. -->

## Clarity Protocol

This project uses the Clarity Protocol for structured thinking about consequential decisions — what to build and why, how it should be designed, where it might fail. Protocol documents live in `.clarity-protocol/`. Process guides live in `.clarity-agent/processes/`; the entry point for any Clarity work is `.clarity-agent/processes/clarity-agent.md`.

### When to engage

**Before building — think when it matters.** Two triggers:

1. *The user asks.* When they want to explore what to build, clarify requirements, brainstorm risks, or work through a decision: call the `run_clarity` MCP tool, or read and follow `.clarity-agent/processes/clarity-agent.md` if MCP isn't available.

2. *You recognize an inflection point.* Before making choices that would be expensive to reverse — new services, auth/trust models, data schemas, external integrations, significant API contracts — call `check_decision` with what you plan to do. It returns existing decisions, requirements, and architecture so you can check for conflicts. Don't interrupt for routine implementation. The test: "If this turns out wrong, is it a 5-minute fix or a multi-day rework?" Interrupt for the latter.

**After building — keep the record current.** After significant implementation work (new features, architectural changes), call `get_packet_status` to find stale protocol documents. Update them with `read_protocol_document` / `write_protocol_document`. Record significant choices with `record_decision`; add risks with `record_failure`.

### Behaviors (apply throughout)

**Move quickly through what's obvious.** Many processes have multiple steps, but sometimes the answer to a step is already clear from context. When it is, just do it — write the result and present a summary for confirmation. Don't stop to ask permission at every small step. The goal is a natural conversation, not a checklist. Reserve interactive discussion for genuine ambiguity, tradeoffs, or decisions that need the user's judgment.

**Keep outputs narrative but brief.** All `.md` files in this project — protocol documents, process guides, and instructions — are repeatedly read by both humans and LLMs. They should read as smooth, concise narrative: easy to understand on first read, with nothing that wastes the reader's attention. A reader must immediately understand both the "what" and the "why." Cut anything that doesn't carry meaningful information. Since many of these files are instructions for LLMs which create further `.md` files, they should encourage the same discipline.

**Use `.clarity-protocol/notes.md` as shared memory.** At the start of every process, read `.clarity-protocol/notes.md` for guiding principles and cross-phase observations. When you notice something worth remembering — a design philosophy, a team constraint, an insight relevant to a future phase — add it. Tag actionable items for a specific phase with `[for: <phase>]` (e.g., `[for: failure-analysis] Authentication is a single point of failure`). When acting on a tagged item, remove it. Keep the file compact: consolidate redundant entries and remove items that have been absorbed into the relevant protocol documents.

**Generate threat model artifacts.** When writing or updating `solution/architecture.md`, include a Mermaid threat model diagram directly in the file as a fenced ` ```mermaid ` block — the packet generator extracts it automatically. Write the diagram yourself; you'll produce a better diagram than any code generator. Also write `.clarity-protocol/system-design.json` with structured component/flow/threat data for tooling. After failure brainstorming or analysis, write `.clarity-protocol/threat-model.md` — a concise threat model summary (1-2 pages max) with top risks, severities, one-line mitigations, and single points of failure.

<!-- clarity-end -->
