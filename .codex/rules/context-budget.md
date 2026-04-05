---
alwaysApply: true
---

# Context Budget Rule

Stay in the smart zone described by `docs/RPI_METHODOLOGY.md`.

## Budget

| Phase | Budget | Output |
|---|---|---|
| Research | <=25% | paths, constraints, short summary |
| Plan | <=35% | numbered steps, impact, verification |
| Implement | <=40% | only touched files + checks |
| Dumb Zone | >40% | stop, summarize, narrow scope |

## Rules

1. Start broad only once: `README.md` -> focused doc -> execution-path files.
2. Prefer `rg` and targeted reads over loading whole directories.
3. Summarize findings before opening more files.
4. Delegate or narrow scope when context grows faster than progress.
5. Reference files by path instead of restating large blocks.
