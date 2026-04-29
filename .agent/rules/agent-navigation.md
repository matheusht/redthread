---
alwaysApply: true
---

# Agent Navigation — Master Decision Tree

This is the **primary navigation rule**. It tells you WHERE things are and WHAT to load first.

## File Loading Priority

```
ALWAYS LOADED (Priority 1 — rules):
  .agent/rules/agent-navigation.md    ← you are here
  .agent/rules/rpi-workflow.md        ← RPI phases
  .agent/rules/context-budget.md      ← context limits
  .agent/rules/code-conventions.md    ← code style

ON TASK START (Priority 2):
  AGENTS.md                           ← agent roles & subagent definitions
  docs/AGENT_DECISION_TREE.md         ← task-to-doc routing

ON DEMAND (Priority 3):
  README.md                           ← product quickstart and operator notes
  docs/product.md                     ← product identity and scope
  docs/TECH_STACK.md                  ← services, stack, and architecture patterns
  docs/RPI_METHODOLOGY.md             ← detailed RPI steps + context budget
  docs/AGENT_ARCHITECTURE.md          ← agent/subagent architecture deep-dive
  docs/PHASE_REGISTRY.md              ← current phase registry and roadmap truth

VIA SKILL (Priority 4):
  .agent/skills/research/SKILL.md     ← deep research
  .agent/skills/plan/SKILL.md         ← planning
  .agent/skills/implement/SKILL.md    ← implementation via subagents
  .agent/skills/gap-check/SKILL.md    ← plan gap analysis
  .agent/skills/context7-mcp/SKILL.md ← library docs via Context7 MCP
```

## Decision Tree: What to Do

```
USER REQUEST
  │
  ├─ Multi-file change or architectural? → Follow RPI (see rpi-workflow rule)
  ├─ Need library/framework docs?       → Use context7-mcp skill
  ├─ Need to explore codebase?          → Use research skill
  ├─ Need a detailed plan?              → Use plan skill
  ├─ Ready to code (plan approved)?     → Use implement skill
  └─ Simple single-file fix?            → Do it inline, skip RPI
```
