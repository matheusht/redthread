# Wiki Ingest Workflow

## Purpose

This document defines the repeatable process for taking a new source or durable insight and folding it into RedThread's wiki without losing provenance.

Use this workflow for:
- new architecture or roadmap docs
- research notes added to the repo
- durable answers discovered in chat
- updates that affect multiple wiki pages

## Prerequisites

Before starting, read:
- `docs/WIKI_ARCHITECTURE.md`
- `docs/wiki/SCHEMA.md`
- `docs/wiki/index.md`

If the topic touches memory behavior, also read:
- `docs/MEMPALACE_SETUP.md`

## Standard ingest loop

### 1. Identify the source
Decide what is being ingested.

Examples:
- new document under `docs/`
- task artifact with durable conclusions
- a valuable chat answer that should stop living only in history

### 2. Read the source directly
Do not start by paraphrasing old wiki pages.

Read the authoritative material first.

### 3. Search MemPalace
Before editing the wiki, search for related prior material.

Examples:
```bash
.venv/bin/mempalace search "defense validation"
.venv/bin/mempalace search "telemetry drift" --wing redthread
```

Goal:
- avoid duplicate pages
- recover earlier decisions
- find contradictions or prior framing

### 4. Choose affected page families
Decide what kind of durable artifact this is:
- `entity`
- `concept`
- `decision`
- `system`
- `research`
- `timeline`

A single ingest may update multiple pages.

### 5. Create or update pages
Apply the schema from `docs/wiki/SCHEMA.md`.

Minimum rules:
- add frontmatter
- cite source docs
- mark uncertainty honestly
- prefer additive edits over silent history loss

### 6. Update navigation files
Always do both:
- update `docs/wiki/index.md`
- append to `docs/wiki/log.md`

The index is the content map.
The log is the chronological record.

### 7. Lint the wiki
Run:

```bash
python3 scripts/wiki_lint.py
```

Fix any missing frontmatter, missing index references, or schema issues.

### 8. Re-mine into MemPalace when useful
If the wiki update is durable and likely to matter later, re-mine it:

```bash
.venv/bin/mempalace mine . --agent codex
```

## Query-to-page workflow

If a user asks a strong question and the answer is durable:
1. answer it
2. decide whether it belongs in the wiki
3. update or create the page
4. update index and log
5. lint
6. optionally re-mine

## What not to do

- do not treat wiki pages as automatically more authoritative than source docs
- do not update pages without touching index/log
- do not flatten uncertainty into certainty
- do not use the wiki to silently rewrite historical decisions

## Rule of thumb

If you expect to need the answer again, and it would help a future human or agent, it probably belongs in the wiki.
