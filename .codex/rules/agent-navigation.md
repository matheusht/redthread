---
alwaysApply: true
---

# Codex Navigation Rule

This is the primary navigation rule for Codex inside RedThread.

## File Loading Priority

```text
ALWAYS LOADED (Priority 1 - rules):
  .codex/rules/agent-navigation.md
  .codex/rules/rpi-workflow.md
  .codex/rules/context-budget.md
  .codex/rules/code-conventions.md

ON TASK START (Priority 2):
  AGENTS.md
  README.md
  docs/AGENT_DECISION_TREE.md

ON DEMAND (Priority 3):
  docs/TECH_STACK.md
  docs/RPI_METHODOLOGY.md
  docs/AGENT_ARCHITECTURE.md
  docs/ANTI_HALLUCINATION_SOP.md
  docs/PHASE_REGISTRY.md
  docs/algorithms.md

VIA SKILL (Priority 4):
  .codex/skills/research/SKILL.md
  .codex/skills/plan/SKILL.md
  .codex/skills/gap-check/SKILL.md
  .codex/skills/implement/SKILL.md
  .codex/skills/feature-rpi/SKILL.md
  .codex/skills/mini-rpi/SKILL.md
  .codex/skills/context7-mcp/SKILL.md
```

## Decision Tree

```text
USER REQUEST
  |
  |- Deep understanding / discovery?     -> use research
  |- New feature or multi-file change?   -> use feature-rpi
  |- Small local tweak?                  -> use mini-rpi
  |- Need a concrete execution plan?     -> use plan, then gap-check
  |- Ready to edit and verify?           -> use implement
  |- Need external library docs?         -> use context7-mcp
```

## Live Repo Map

- Orchestration: `src/redthread/orchestration/`
- Core algorithms: `src/redthread/core/`
- Evaluation: `src/redthread/evaluation/`
- Telemetry: `src/redthread/telemetry/`
- Memory: `src/redthread/memory/`
- Tools: `src/redthread/tools/`
- PyRIT adapters: `src/redthread/pyrit_adapters/`
- Personas: `src/redthread/personas/`
- Research runtime: `src/redthread/research/`

Prefer the current repository layout over stale filenames referenced in older guidance.
