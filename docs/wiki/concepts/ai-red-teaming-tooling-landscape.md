---
title: AI Red Teaming Tooling Landscape
type: concept
status: active
summary: Open-source and commercial tooling for AI red teaming.
source_of_truth:
  - https://github.com/requie/AI-Red-Teaming-Guide
  - https://github.com/NVIDIA/garak
  - https://github.com/promptfoo/promptfoo
  - https://github.com/usestrix/strix
  - docs/wiki/research/open-source-redteam-tool-integration-strategy.md
updated_by: codex
updated_at: 2026-04-26
---

# AI Red Teaming Tooling Landscape

Source: [AI-Red-Teaming-Guide](https://github.com/requie/AI-Red-Teaming-Guide)

A survey of the current tooling ecosystem for LLM vulnerability scanning, adversarial robustness, and defensive security.

## Open-Source Tools Comparison Matrix

| Tool | Best For | Primary Focus | Key Features |
|------|----------|---------------|--------------|
| **[PyRIT](https://github.com/microsoft/PyRIT)** | Internal red teams, research, comprehensive testing | Orchestrating LLM attack suites | 40+ attack strategies, multi-turn conversation support, local/cloud models |
| **[DeepTeam (Deepeval)](https://github.com/confident-ai/deepeval)** | RAG systems, chatbots, autonomous agents | Stress-testing AI agents | OWASP Top 10 alignment, NIST AI RMF compliance, 40+ vulnerability classes |
| **[garak](https://github.com/NVIDIA/garak)** | Quick vulnerability scans, baseline probe coverage | LLM vulnerability scanner | Broad probe/detector library for prompt injection, jailbreaks, leakage, hallucination, unsafe content, encoding attacks, web injection, and more |
| **[promptfoo](https://github.com/promptfoo/promptfoo)** | LLM red teaming, security testing, CI/CD pipelines, reports | Evaluation & CLI red teaming | YAML configs, broad plugin taxonomy, custom policies, provider ecosystem, caching, CI/report workflow |
| **[IBM ART](https://github.com/Trusted-AI/adversarial-robustness-toolbox)** | Classical ML attacks, computer vision | Adversarial Robustness | Evasion, poisoning, extraction, and inference attacks on ML models |
| **[Giskard](https://github.com/Giskard-AI/giskard)** | Production LLM agents, RAG systems | AI Testing Platform | Dynamic multi-turn stress tests, 50+ probes, context-dependent discovery |
| **[Strix](https://github.com/usestrix/strix)** | Agentic appsec, source-aware scans, PoC validation | Autonomous security agents | Browser/proxy/terminal/Python tools, sandboxed execution, CI mode, source-aware vulnerability validation |
| **[BrokenHill](https://github.com/BishopFox/BrokenHill)** | Jailbreak research, adversarial testing | Automatic Jailbreak Generator | Genetic algorithm optimization, automated jailbreak discovery |
| **[Counterfit](https://github.com/Azure/counterfit)** | Getting started, educational purposes | Security Testing Tool | Interactive CLI, multiple attack frameworks |
| **[Gideon](https://github.com/Cogensec/Gideon)** | Defensive security research, threat intelligence | Autonomous Defensive Assistant | CVE research, IOC reputation, hardening policy generation, daily briefings |

## RedThread integration and incorporation stance

Use these tools as **surface expanders**, but also absorb their best internal patterns when they strengthen RedThread's closed loop.

- **garak**: import scan reports, re-score with JudgeAgent, use probes as PAIR/TAP/Crescendo seeds, and absorb probe/detector metadata as RedThread `DetectorHint`/seed concepts.
- **promptfoo**: export/import eval artifacts, generate custom-policy regression tests, use report/CI workflows, and absorb plugin/strategy/target thinking as RedThread-native `RiskPlugin` and `AttackStrategy` abstractions.
- **Strix**: ingest validated appsec findings as upstream objectives and absorb scope/sandbox lessons as `AuthorizedScope` and safer tool execution boundaries.

See [Open-Source Red Team Tool Integration Strategy](../research/open-source-redteam-tool-integration-strategy.md) for the external-tool strategy, [AI Red Teaming Guide Use-Case Map for RedThread](../research/ai-red-teaming-guide-redthread-use-case-map.md) for the exact workflow/infrastructure map, [Tool Technology Incorporation Assessment](../research/tool-technology-incorporation-assessment.md) for what RedThread should absorb natively versus keep external, and [Tool Technology Incorporation Roadmap](../research/tool-technology-incorporation-roadmap.md) for implementation sequencing.

## Commercial Tools
- [Mindgard](https://mindgard.ai/)
- [Lakera Guard](https://www.lakera.ai/)
- [Adversa AI](https://adversa.ai/)
- [Pillar Security](https://www.pillar.security/)
- [Splx AI](https://splx.ai/)
- [NeuralTrust](https://neuraltrust.ai/)

## Practice Platforms and Challenges
- **[Lakera Gandalf](https://gandalf.lakera.ai/)**: Hands-on prompt injection challenges.
- **[PromptArmor](https://promptarmor.com/)**: Security exercises.
- **[AI Village CTF](https://aivillage.org/)**: Specialized capture the flag competitions for AI security.
