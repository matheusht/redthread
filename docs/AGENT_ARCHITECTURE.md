# Agent Architecture

> **Source of Truth** for how agents, subagents, rules, skills, and MCPs work together in this repository.

---

## Principal Agent

The **principal agent** is the orchestrator that talks directly to the human.

### Responsibilities
1. Read user instructions
2. Load rules, skills, and relevant docs **on demand** (progressive disclosure)
3. Decide when to delegate to subagents
4. Consolidate subagent results into a cohesive response
5. Maintain context within the SMART ZONE (≤40%)

### When to Delegate
- Task spans **3+ files** → use Implementation subagent
- Need to **explore** a large area of the codebase → use Research subagent
- Context is approaching **35%** → offload work to subagents
- Need **library documentation** → use Context7 subagent

---

## Subagents

Subagents are **context compression tools**, not team members. Each one:
- Has its own **isolated context** with narrow focus
- Returns a **summarized result** (never a massive context dump)
- Can use different models (faster/cheaper when appropriate)

### Available Subagents

| Subagent | Skill Used | Model | Purpose |
|----------|-----------|-------|---------|
| **Research** | `research` | Opus 4.6 | Deep codebase research, file discovery |
| **Planner** | `plan` | Plan Mode | Create detailed implementation plans |
| **Implementer** | `implement` | Default | Execute plan steps via focused edits |
| **Gap Checker** | `gap-check` | Default | Validate plans for missed risks |
| **Context7** | `context7` | Default | Fetch library docs via MCP |

### Subagent Rules
1. **Limit scope** — each subagent gets ONE well-defined task
2. **Don't use for trivial work** — if it fits in current context, do it inline
3. **Expect summaries** — subagents return paths + findings, not raw dumps
4. **Chain when needed** — Research → Plan → Gap-Check → Implement

---

## Where Things Live

### Decision Tree: What Goes Where

```
Is it a rule/convention that must ALWAYS be followed?
  └── Yes → .agent/rules/  (alwaysApply: true)

Is it a procedure/workflow triggered by intent?
  └── Yes → .agent/skills/<name>/SKILL.md

Is it about the agent system architecture?
  └── Yes → AGENTS.md (root) + docs/AGENT_ARCHITECTURE.md

Is it access to an external tool (API, database, service)?
  └── Yes → Configure/use via MCP, document in skill

Is it reference documentation about the codebase?
  └── Yes → docs/<TOPIC>.md

None of the above?
  └── Probably domain documentation → docs/
```

---

## File Loading Priority

When starting any task, agents should load files in this order:

```
Priority 1 (Always Loaded):
  .agent/rules/agent-navigation.md   ← master decision tree
  .agent/rules/rpi-workflow.md        ← RPI enforcement
  .agent/rules/context-budget.md      ← context limits
  .agent/rules/code-conventions.md    ← code style

Priority 2 (Load on Task Start):
  AGENTS.md                           ← agent/subagent definitions
  docs/ARCHITECTURE.md                ← system overview

Priority 3 (Load on Demand):
  docs/TECH_STACK.md                  ← when touching services/config
  docs/RPI_METHODOLOGY.md             ← when planning complex changes
  docs/SPEAKER_ATTRIBUTION.md         ← when touching speaker pipeline
  docs/TESTING.md                     ← when writing/running tests

Priority 4 (Load via Skill):
  .agent/skills/*/SKILL.md            ← only the skill matching the intent
```

---

## Rules vs Skills vs AGENTS.md

| Aspect | Rules | Skills | AGENTS.md |
|--------|-------|--------|-----------|
| **When loaded** | Always (alwaysApply) | On demand (by intent) | On task start |
| **Purpose** | Constraints & conventions | Workflows & procedures | Architecture & delegation |
| **Size** | Lean (< 40 lines) | Detailed (steps + examples) | Medium (definitions + refs) |
| **Changes** | Rarely | When workflows evolve | When agent roles change |

---

## MCP Integrations

| MCP | Purpose | Documented In |
|-----|---------|---------------|
| **Context7** | Fetch up-to-date library/framework docs | `.agent/skills/context7/SKILL.md` |
| **MemPalace** | Persistent retrieval and session memory via Codex MCP | `docs/MEMPALACE_SETUP.md` |

### When to Use MCP vs Docs
- **MCP**: External library docs, APIs you don't control, or persistent retrieval such as MemPalace
- **docs/**: Internal project knowledge, architecture, patterns

## Wiki Maintenance

When maintaining the repo-local wiki under `docs/wiki/`:
- read `docs/WIKI_ARCHITECTURE.md`, `docs/WIKI_INGEST_WORKFLOW.md`, and `docs/wiki/SCHEMA.md` first
- treat the wiki as a synthesis layer, not the source-of-truth engineering layer
- update `docs/wiki/index.md` and `docs/wiki/log.md` when making durable wiki changes
- search MemPalace before making high-impact architecture or research edits
- run `python3 scripts/wiki_lint.py` or `make wiki-lint` before considering the wiki update complete
