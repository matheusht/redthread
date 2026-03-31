---
name: Deep Research & Context Gathering
description: Sweeping file aggregation and pattern recognition across the repository. Does not modify files.
---

# Deep Research Skill

## Trigger condition: 
When the task involves understanding large swathes of the codebase, exploring patterns, or finding documentation context prior to planning. 

## Requirements:
1. **Model Selection:** Use **Opus 4.6** for executing this Research skill. Do not rely on smaller/tier-two models for deep cross-module correlation.
2. **Behavior constraint:** You are restricted entirely from modifying files, creating structures, or proposing code diffs.
3. **Execution pattern:**
    - Use `grep_search` and `view_file`.
    - Extract paths and explicit line numbers `(e.g., path/file.py#L40-L50)`.
    - Synthesize an objective summary.
    - Validate your token footprint. If >25% context, prune redundant returns.
