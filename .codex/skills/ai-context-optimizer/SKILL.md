---
name: ai-context-optimizer
description: Audit and optimize a software repository for future AI coding sessions by finding context bloat, bloated or stale markdown, duplicated specs, old workflow notes, repeated instructions, irrelevant prompt context, and files that should be summarized, archived, indexed, or loaded only on demand. Use when asked to reduce token waste, clean up docs for Codex/Cline/AIDEV/agentic coding tools, create AI-facing context summaries, build context indexes, or propose safe reversible documentation cleanup.
---

# AI Context Optimizer

Use this skill to make a repository easier, cheaper, and safer for future AI agents to work in. Focus on docs, prompts, workflow files, notes, and context-injection rules. Do not change source code unless the user explicitly asks.

## Core Rules

- Never delete, move, or rewrite files without explicit user approval.
- Treat cleanup as reversible. Prefer `docs/archive/` and summary files over destructive cleanup.
- Do not assume a file is useless because it is old. Age is only one signal.
- Preserve architecture decisions, API contracts, database schema notes, security notes, deployment notes, and active roadmap items.
- When uncertain, mark a file as `Review Needed`, not `Archive Candidates`.
- Do not modify source code during this workflow unless the user asks for code changes.
- Before any cleanup, produce a report and a safe plan.
- Keep generated summaries short, factual, and linked to source files.

## Research Workflow

1. Inspect repository shape:

```bash
pwd
rg --files
rg --files -g '*.md' -g '*.mdx' -g '*.txt'
```

2. Find markdown-heavy areas:

```bash
git ls-files "*.md" "*.mdx" "*.txt" | sort
git ls-files "*.md" "*.mdx" | xargs wc -l | sort -n
```

3. Find likely AI-context entrypoints:

```bash
git ls-files | rg '(^|/)(AGENTS|CLAUDE|README|CONTRIBUTING)\.md$|\.rules$|\.md$'
```

4. Search for duplication and stale markers:

```bash
rg -n "TODO|FIXME|deprecated|obsolete|old|archive|draft|WIP|superseded|outdated|legacy|do not use" .
rg -n "source of truth|canonical|decision|ADR|schema|API contract|deployment|security|roadmap" .
```

5. Check recent activity without treating age as proof:

```bash
git ls-files "*.md" "*.mdx" "*.txt" | xargs -I{} git log -1 --format="%ai %h {}" -- {}
```

6. Estimate token pressure by file size and line count:

```bash
git ls-files "*.md" "*.mdx" "*.txt" | xargs wc -c | sort -n
git ls-files "*.md" "*.mdx" "*.txt" | xargs wc -l | sort -n
```

## Classification Heuristics

Use `Keep Active` when a file is current, canonical, short enough, or needed early by future agents. This often includes root README, agent instructions, active architecture docs, current roadmap, API contracts, schema docs, deployment docs, security docs, and task-specific indexes.

Use `Summary Candidates` when a file is important but too long for default prompt loading. The summary should point to the full file and state when to load it.

Use `Archive Candidates` only when a file appears clearly superseded, duplicated, historical, or no longer part of active workflows. Require user approval before moving it.

Use `Review Needed` when a file is ambiguous, old but possibly valuable, contradictory, ownerless, or mentions architecture, security, deployment, schemas, API behavior, migrations, or roadmap decisions.

Use `Duplicate or Overlapping Documents` when files cover the same topic, contain repeated instructions, define the same process, or compete as source of truth.

Use `Outdated or Stale Documents` when a file references removed paths, old commands, obsolete tools, completed phases as future work, stale dates, or contradicted guidance.

## Required Output

When this skill runs, return this exact report shape:

```markdown
# AI Context Optimization Report

## Context Health Score
Score: 0-100
Reason:

## Main Token Waste Sources
- `path`: why it likely wastes context.

## Duplicate or Overlapping Documents
- `path` and `path`: overlap reason.

## Outdated or Stale Documents
- `path`: stale signal and confidence.

## Summary Candidates
- `path`: why summary helps and what the summary must preserve.

## Archive Candidates
- `path`: why it can probably move to archive after approval.

## Keep Active
- `path`: why future AI sessions should load or know this file.

## Review Needed
- `path`: what a human must decide.

## Recommended Cleanup Plan
1. Safe step.
2. Safe step.
3. Stop for approval before moving or deleting files.

## Future Context Injection Rules
- Load by default: `path`, `path`.
- Load on demand: `path`, `path`.
- Do not inject by default: `path`, `path`.
- Search first when task concerns: topic -> path.

## Estimated Token Reduction
Estimate: X-Y%
Reason:
```

## Safe Cleanup Artifacts

Only create these files when the user asks for implementation after reading the report, or when the original request explicitly asks to create them.

### Create `docs/ai-context-summary.md`

Purpose: compact AI-facing map for future agents.

Suggested shape:

```markdown
# AI Context Summary

This file is the compact starting context for AI coding agents.

## Load First
- `README.md`: project purpose and quickstart.
- `docs/context-index.md`: active documentation map.

## Architecture
- Current source of truth:
- Load on demand:

## Workflows
- Current source of truth:
- Load on demand:

## Do Not Load By Default
- Historical or archived docs:

## Open Questions
- Review needed:
```

Create it with approval:

```bash
mkdir -p docs
$EDITOR docs/ai-context-summary.md
```

### Create `docs/context-index.md`

Purpose: map active docs and prevent future agents from loading every markdown file.

Suggested shape:

```markdown
# Context Index

## Default AI Context
- `README.md`
- `AGENTS.md`
- `docs/ai-context-summary.md`

## Active Source Of Truth
- Topic: `path`

## Load On Demand
- Topic: `path`

## Historical Or Archived
- `docs/archive/`

## Review Needed
- `path`: reason
```

Create it with approval:

```bash
mkdir -p docs
$EDITOR docs/context-index.md
```

### Create `docs/archive/`

Purpose: reversible home for duplicate, stale, or historical docs.

```bash
mkdir -p docs/archive
```

Move files only after explicit user approval:

```bash
git mv docs/old-file.md docs/archive/old-file.md
git mv docs/duplicate-spec.md docs/archive/duplicate-spec.md
```

After moving files, update links and indexes:

```bash
rg -n "old-file|duplicate-spec" docs README.md AGENTS.md
$EDITOR docs/context-index.md docs/ai-context-summary.md
```

## Cleanup Plan Rules

- Plan moves in small batches grouped by reason.
- Keep a path mapping: `old path -> new archive path`.
- Update links in active docs after any move.
- Keep archival notes short. State why the file moved and what replaced it.
- If there is no clear replacement, do not archive without human review.
- Never bury security, deployment, schema, API, or architecture decision material.

## Final Verification

After approved cleanup, verify:

```bash
git status --short
rg -n "docs/archive|ai-context-summary|context-index" README.md AGENTS.md docs || true
```

If the repo has docs linting or link checking, run the smallest relevant command. Report any command that cannot run.
