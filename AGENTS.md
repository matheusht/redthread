# RedThread Agent Architecture

This document dictates the behavior and orchestration of the Antigravity Agent when working within the RedThread repository.

**All behavioral configurations must strictly refer to the `docs/` sources of truth.**

## 1. Core Operating Guidelines
* **Decision Matrix:** Before running *any* operation, the agent must consult [docs/AGENT_DECISION_TREE.md](docs/AGENT_DECISION_TREE.md) to identify which domain document to load based on the user's intent.
* **Working Methodology:** All tasks must follow the RPI (Research → Plan → Implement) flow outlined in [docs/RPI_METHODOLOGY.md](docs/RPI_METHODOLOGY.md). Context must not exceed 40% window utilization.
* **Default Response Style:** Use full caveman mode by default unless the user asks for a different style. That means simple words, short direct sentences, practical structure, low fluff, and clear "what this is / why it matters / what next" guidance.

## 2. The Orchestration Workflow (Principal vs Subagents)
Antigravity operates as the **Principal Agent** inside the RedThread ecosystem. It acts identically to the LangGraph supervisor defined in Phase 1 of `phases.md`—it manages the task graph while delegating execution.

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
- Start implementation tasks at root [README.md](README.md) and [docs/TECH_STACK.md](docs/TECH_STACK.md).
- Open the matching repo-local skill before implementation work:
  - New features, architecture changes, multi-file work, or unclear impact → `.agent/skills/feature-rpi/SKILL.md`
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
 risks regressions

