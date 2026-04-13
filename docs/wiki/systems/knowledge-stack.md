---
title: Knowledge Stack
type: system
status: active
summary: How RedThread combines raw sources, MemPalace, and a maintained wiki.
source_of_truth:
  - docs/WIKI_ARCHITECTURE.md
  - docs/MEMPALACE_SETUP.md
updated_by: codex
updated_at: 2026-04-13
---

# Knowledge Stack

## Scope

This page describes how knowledge should flow through RedThread's documentation and memory system.

## Layers

### Raw sources
Immutable or near-authoritative inputs.

Examples:
- engineering docs under `docs/`
- source code comments when relevant
- task artifacts
- imported research notes

### MemPalace
Persistent retrieval and memory layer.

Use it for:
- search
- wake-up context
- prior session continuity
- person/project/topic recall

### Wiki
Persistent synthesis layer in `docs/wiki/`.

Use it for:
- stable concept explanations
- decisions and rationale
- system summaries
- research pages
- timelines

## Working rule

When a topic matters enough to come up repeatedly, it should stop living only in chat history.

First persist the evidence and memory; then maintain the synthesis page.

## Practical workflow

1. read source docs
2. search MemPalace for related prior work
3. update or create wiki pages
4. update the wiki index and log
5. re-mine durable wiki changes when useful

## Risks

- synthesis drifting away from source docs
- duplicate wiki pages with overlapping scope
- stale conclusions remaining marked as current

## Mitigations

- cite source docs
- use explicit page types and statuses
- log meaningful updates
- lint the wiki periodically

## Related pages

- [../SCHEMA.md](../SCHEMA.md)
- [../decisions/adopt-mempalace-plus-llm-wiki.md](../decisions/adopt-mempalace-plus-llm-wiki.md)
- [../../MEMPALACE_SETUP.md](../../MEMPALACE_SETUP.md)
