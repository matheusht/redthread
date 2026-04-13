---
title: MemPalace
type: entity
status: active
summary: Persistent retrieval and memory layer used by RedThread through Codex MCP integration.
source_of_truth:
  - docs/MEMPALACE_SETUP.md
  - docs/WIKI_ARCHITECTURE.md
updated_by: codex
updated_at: 2026-04-13
---

# MemPalace

## What it is

MemPalace is RedThread's persistent memory and retrieval layer.

It provides:
- semantic search
- wake-up context
- durable session memory
- structured organization by wings and rooms
- Codex MCP integration for memory-aware agent behavior

## Responsibilities

- retain retrievable context across sessions
- support search-before-answer behavior
- surface prior work before wiki edits or high-impact claims
- store mined repo and wiki content for later recall

## Interfaces

Primary local interfaces:
- `.venv/bin/mempalace search ...`
- `.venv/bin/mempalace mine . --agent codex`
- `.venv/bin/python -m mempalace.mcp_server`

Primary repo docs:
- [../../MEMPALACE_SETUP.md](../../MEMPALACE_SETUP.md)
- [../../WIKI_ARCHITECTURE.md](../../WIKI_ARCHITECTURE.md)

## Relationship to the wiki

MemPalace is not the wiki.

- MemPalace = retrieval and continuity
- wiki = curated markdown synthesis

The two are designed to reinforce each other.

## Related pages

- [../systems/knowledge-stack.md](../systems/knowledge-stack.md)
- [../decisions/adopt-mempalace-plus-llm-wiki.md](../decisions/adopt-mempalace-plus-llm-wiki.md)

## Sources

- [../../MEMPALACE_SETUP.md](../../MEMPALACE_SETUP.md)
- [../../WIKI_ARCHITECTURE.md](../../WIKI_ARCHITECTURE.md)
