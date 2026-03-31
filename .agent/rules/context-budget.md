---
alwaysApply: true
---

# Context Budget Rule

Stay in the **SMART ZONE** (≤40% of context window). Quality drops above 40%.

## Budget Allocation

| Phase | Budget | Notes |
|-------|--------|-------|
| Research | ≤25% | File paths + short summary only |
| Plan | ≤30% | Numbered steps, minimal snippets |
| Implement | ≤35% | Only files being edited |
| **DUMB ZONE** | >40% | **STOP — summarize or delegate** |

## Rules

1. **Reference by path** — never paste entire docs into context
2. **Progressive Disclosure** — load high-level first, drill down only as needed:
   - `docs/ARCHITECTURE.md` → domain doc → source files
3. **Use subagents** to split work when context is heavy
4. **Summarize before discarding** — keep findings, drop raw content

## Decision Tree

```
Context approaching 35%?
  ├─ Can I summarize existing context? → Summarize, continue
  ├─ Can I delegate remaining work? → Spawn subagent
  └─ Neither? → Finish current step, report partial results
```

## Reference

Full heuristics: `docs/RPI_METHODOLOGY.md`
