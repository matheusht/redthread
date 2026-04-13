---
title: Adopt MemPalace Plus LLM Wiki
type: decision
status: accepted
summary: RedThread uses MemPalace for retrieval and a markdown wiki for curated synthesis.
source_of_truth:
  - docs/WIKI_ARCHITECTURE.md
  - docs/MEMPALACE_SETUP.md
  - docs/AGENT_ARCHITECTURE.md
updated_by: codex
updated_at: 2026-04-13
---

# Adopt MemPalace Plus LLM Wiki

## Decision

Use **MemPalace** as the persistent retrieval layer and **`docs/wiki/`** as the persistent synthesis layer.

## Context

RAG-style retrieval alone forces the LLM to repeatedly rediscover the same relationships from raw material. RedThread also needs a durable, human-browsable explanation layer so architecture, memory strategy, and research synthesis do not disappear into chat history.

## Why this choice fits RedThread

- MemPalace gives recall, search, wake-up context, and continuity.
- The wiki gives structured markdown pages that accumulate over time.
- The combination supports both machine retrieval and human navigation.
- The resulting system is easier to maintain than a pure manual wiki.

## Consequences

### Positive
- repeated questions can build on prior synthesis
- durable decisions can live in markdown, not just chat
- future sessions have a clearer navigation surface

### Costs
- index and log maintenance becomes part of normal workflow
- stale or weakly-sourced wiki claims must be actively managed
- agents must distinguish between source docs and synthesis pages

## Alternatives considered

### MemPalace only
Rejected because retrieval alone is not an ideal human-facing knowledge base.

### Wiki only
Rejected because wiki pages benefit from a retrieval layer and durable session memory.

### Raw-doc RAG only
Rejected because it fails to accumulate durable synthesis effectively.

## Sources

- [../../WIKI_ARCHITECTURE.md](../../WIKI_ARCHITECTURE.md)
- [../../MEMPALACE_SETUP.md](../../MEMPALACE_SETUP.md)
- [../../AGENT_ARCHITECTURE.md](../../AGENT_ARCHITECTURE.md)
