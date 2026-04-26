---
title: Open-Source Red Team Tool Integration Strategy
type: research
status: active
summary: How RedThread should use garak, promptfoo, and Strix without losing its closed-loop attack-judge-defend identity.
source_of_truth:
  - README.md
  - docs/product.md
  - docs/TECH_STACK.md
  - docs/algorithms.md
  - docs/wiki/concepts/ai-red-teaming-tooling-landscape.md
  - https://github.com/NVIDIA/garak
  - https://github.com/promptfoo/promptfoo
  - https://github.com/usestrix/strix
updated_by: codex
updated_at: 2026-04-26
---

# Open-Source Red Team Tool Integration Strategy

## Research question

How should RedThread use open-source AI security tools such as garak, promptfoo, and Strix to improve results without becoming a wrapper around another scanner?

## Current synthesis

RedThread should treat external tools as **surface expanders**, not replacements for its core loop.

RedThread's durable identity remains:

```text
attack generation → target execution → JudgeAgent scoring → defense synthesis → sandbox validation → regression evidence
```

This is stronger than plain scanning because RedThread aims to turn a confirmed exploit into a validated defensive change. See [README.md](../../../README.md), [docs/product.md](../../product.md), [docs/TECH_STACK.md](../../TECH_STACK.md), and [docs/algorithms.md](../../algorithms.md).

## Tool-by-tool fit

### garak

**What it is:** NVIDIA garak is an Apache-2.0 LLM vulnerability scanner. It uses generators, probes, detectors, payload transformations, and reports to test LLM failure modes such as prompt injection, jailbreaks, leakage, hallucination, unsafe content, encoding attacks, web injection, and related model/application failures.

**Best RedThread use:** broad probe and detector coverage.

**Recommended integration:**

1. `redthread import garak <report.jsonl>` converts garak attempts into RedThread `AttackTrace`-like evidence.
2. RedThread re-scores imported attempts with JudgeAgent for semantic severity.
3. High-confidence failures can enter defense synthesis and replay validation.
4. garak payload/probe families can seed PAIR/TAP/Crescendo starting points, but RedThread should keep its own algorithm implementations.

**Avoid now:** deep-forking garak internals or replacing PyRIT adapters with garak generators.

### promptfoo

**What it is:** promptfoo is an MIT-licensed eval and red-team framework with YAML config, many providers, red-team plugins, custom policies, caching, CI/CD, and report views.

**Best RedThread use:** developer workflow, CI, policy packs, and reporting.

**Recommended integration:**

1. `redthread export promptfoo --campaign <id>` emits `promptfooconfig.yaml` plus policy/intent tests from RedThread findings and defenses.
2. `redthread import promptfoo <results>` ingests promptfoo failures as external findings.
3. Defense synthesis can generate promptfoo custom-policy tests as permanent CI regressions.
4. Promptfoo plugin taxonomy should inform RedThread rubric gaps, especially RAG, MCP, memory poisoning, tool discovery, coding-agent secret reads, sandbox escape, terminal-output injection, delayed CI exfiltration, and verifier sabotage.

**Avoid now:** moving RedThread's core orchestration into TypeScript or making promptfoo the campaign engine.

### Strix

**What it is:** Strix is an Apache-2.0 agentic appsec/pentest platform. It runs autonomous security agents with sandboxed tools, browser/proxy/terminal/Python capabilities, source-aware scanning, CI integration, and PoC-oriented vulnerability validation.

**Best RedThread use:** appsec-to-agent security bridge and Phase 8-style runtime lessons.

**Recommended integration:**

1. `redthread ingest strix <report>` accepts app vulnerabilities as upstream signals.
2. RedThread turns Strix findings into LLM-agent attack objectives, e.g. “Can the support agent be tricked into using this IDOR endpoint?”
3. RedThread borrows architectural lessons: explicit authorized target scope, sandboxed tool execution, scan modes, and PoC-quality reproduction artifacts.
4. Strix-style scope context can harden RedThread's own agentic-security runtime.

**Avoid now:** making Strix a runtime dependency or importing broad browser/terminal/proxy powers into RedThread core before permission boundaries are mature.

## What RedThread can do now

### Near-term implementation slices

1. **External finding schema**
   - Add a small typed model for external findings.
   - Fields: `source`, `category`, `severity`, `prompt`, `response`, `evidence`, `raw_path`, `metadata`.
   - Map imported findings into RedThread traces for JudgeAgent re-scoring.

2. **promptfoo export**
   - Emit `promptfooconfig.yaml` from a RedThread campaign.
   - Include custom-policy plugins from validated defenses.
   - Include intent tests from successful attack prompts.
   - This is the fastest value path because it improves CI and reporting without changing core attack logic.

3. **garak import**
   - Parse garak JSONL reports.
   - Preserve raw detector/probe labels.
   - Re-score in RedThread.
   - Optionally promote strong findings to defense synthesis.

4. **tool taxonomy mapping**
   - Create a mapping table from garak probes and promptfoo plugins to RedThread rubrics and OWASP/MITRE categories.
   - Use it to identify coverage gaps.

5. **Strix report bridge later**
   - Start as ingest-only.
   - Convert validated appsec findings into agent attack objectives.
   - Keep Strix out of core runtime until RedThread's tool authorization model is stronger.

## Recommended order

1. **Promptfoo export/import first** — practical CI/reporting win, low coupling.
2. **garak import/runner second** — broad LLM probe coverage, Python-friendly, useful for baseline scans.
3. **Strix ingest third** — powerful, but broader appsec scope; best once Phase 8 boundaries are stable.

## Decision stance

RedThread should become the **closed-loop consumer and producer of security evidence**:

```text
external scanner finds or frames a failure
→ RedThread reproduces or imports evidence
→ RedThread JudgeAgent scores it
→ RedThread Defense Architect proposes a fix
→ RedThread validates replay
→ RedThread exports regression tests
```

This keeps RedThread differentiated. It lets garak and promptfoo broaden coverage, lets Strix surface real app vulnerabilities, and lets RedThread own the higher-value loop: judge, defend, validate, and regress.

## Contradictions / uncertainty

- promptfoo has a strong plugin ecosystem, but some advanced plugin generation may use remote inference. RedThread should mark remote-generation requirements clearly in generated artifacts.
- garak detector failures may not equal RedThread semantic jailbreaks. Re-scoring is mandatory before defense synthesis.
- Strix has powerful tools. Importing those tools directly could expand RedThread's blast radius. Start with reports and scope lessons, not runtime powers.

## Related pages

- [AI Red Teaming Tooling Landscape](../concepts/ai-red-teaming-tooling-landscape.md)
- [Agentic Security Runtime](../systems/agentic-security-runtime.md)
- [Defense Synthesis and Validation](../systems/defense-synthesis-and-validation.md)
- [Evaluation and Anti-Hallucination](../systems/evaluation-and-anti-hallucination.md)

## Sources

- [RedThread README](../../../README.md)
- [Product document](../../product.md)
- [Technology stack](../../TECH_STACK.md)
- [Algorithms](../../algorithms.md)
- [NVIDIA garak](https://github.com/NVIDIA/garak)
- [promptfoo](https://github.com/promptfoo/promptfoo)
- [Strix](https://github.com/usestrix/strix)
