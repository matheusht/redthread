# Wiki Query-to-Page Workflow

## Purpose

This document defines how to convert a valuable chat answer into a durable wiki artifact.

Use it when:
- a user question produces a reusable explanation
- a comparison or synthesis is likely to be needed again
- a conversation resolves ambiguity across multiple docs
- a response would help future humans or future agents

## Principle

Not every answer belongs in the wiki.

A response should become a page or page update when it is:
- reusable
- grounded in source material
- likely to matter again
- clearer in persistent form than in chat history alone

## Workflow

### 1. Answer the question normally
Focus first on being useful in the conversation.

### 2. Decide whether the answer is durable
Good candidates:
- architecture synthesis
- process clarification
- decision rationale
- glossary/entity explanation
- roadmap interpretation
- recurring operational guidance

Weak candidates:
- one-off convenience answers
- ephemeral local state that will quickly expire
- speculative claims with weak evidence

### 3. Identify the right target
Decide whether to:
- create a new wiki page
- update an existing page
- append to a timeline
- record a decision status change

### 4. Verify against sources
Before persisting the answer:
- re-open the source docs if needed
- search MemPalace for prior relevant context
- make uncertainty explicit

### 5. Write the page or update
Apply `docs/wiki/SCHEMA.md`.

Common outcomes:
- `entity` page for "what is X?"
- `system` page for "how does this flow work?"
- `decision` page for "why did we choose this?"
- `research` page for synthesis with unresolved uncertainty
- `timeline` page for historical evolution

### 6. Update navigation
Always:
- update `docs/wiki/index.md`
- append to `docs/wiki/log.md`

### 7. Lint
Run:

```bash
python3 scripts/wiki_lint.py
```

### 8. Re-mine if valuable
If the new page should influence future recall:

```bash
.venv/bin/mempalace mine . --agent codex
```

## Rule of thumb

If a future session would benefit from reading the answer instead of re-deriving it, persist it.

## Relationship to ingest workflow

- `docs/WIKI_INGEST_WORKFLOW.md` covers source-driven updates
- this document covers answer-driven updates

Together they define the two main ways the wiki should grow.
