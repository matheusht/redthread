---
name: Context7 MCP Integration
description: Instructions for triggering external Context7 connections
---

# Context7 MCP Integration Skill

## Trigger condition:
When a task explicitly requests cross-referencing external databases, third-party project boards, or documentation domains outside the local repository.

## Execution constraints:
1. **Strictly isolate calls**: Only query the MCP capabilities when specifically requested or when you lack the necessary codebase context.
2. Formulate explicit queries to the MCP server endpoint so the subagents or system can return context-rich external documentation.
3. Do not rely on Context7 for purely local coding tasks (e.g. debugging a unit test on `phases.md`).
