---
alwaysApply: true
---

# RPI Workflow Rule

Every task that touches **more than one file** or has **architectural impact** MUST follow RPI.

## Phases

1. **Research** — Find files, read only what's needed. Output: paths + summary. Budget: ≤25%.
2. **Plan** — Define changes in numbered steps. No code edits. Budget: ≤30%.
3. **Implement** — Execute the plan step-by-step. Run tests. Budget: ≤35%.

## Enforcement

- Before editing code, confirm Research and Plan are done.
- If skipping straight to Implement, document WHY it's safe (single-file trivial fix).
- After Plan, run the `gap-check` skill to validate.

## Reference

Full methodology details: `docs/RPI_METHODOLOGY.md`
