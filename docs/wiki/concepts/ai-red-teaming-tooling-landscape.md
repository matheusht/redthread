---
title: AI Red Teaming Tooling Landscape
type: concept
status: active
summary: Open-source and commercial tooling for AI red teaming.
source_of_truth:
  - https://github.com/requie/AI-Red-Teaming-Guide
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
| **[Garak](https://github.com/leondz/garak)** | Quick vulnerability scans, CI/CD integration | LLM vulnerability scanner | 50+ specialized probes, automated scanning |
| **[promptfoo](https://github.com/promptfoo/promptfoo)** | LLM red teaming, security testing, CI/CD pipelines | Evaluation & CLI Red Teaming | Adversarial attacks (PAIR, Crescendo, many-shot), multi-provider support |
| **[IBM ART](https://github.com/Trusted-AI/adversarial-robustness-toolbox)** | Classical ML attacks, computer vision | Adversarial Robustness | Evasion, poisoning, extraction, and inference attacks on ML models |
| **[Giskard](https://github.com/Giskard-AI/giskard)** | Production LLM agents, RAG systems | AI Testing Platform | Dynamic multi-turn stress tests, 50+ probes, context-dependent discovery |
| **[BrokenHill](https://github.com/BishopFox/BrokenHill)** | Jailbreak research, adversarial testing | Automatic Jailbreak Generator | Genetic algorithm optimization, automated jailbreak discovery |
| **[Counterfit](https://github.com/Azure/counterfit)** | Getting started, educational purposes | Security Testing Tool | Interactive CLI, multiple attack frameworks |
| **[Gideon](https://github.com/Cogensec/Gideon)** | Defensive security research, threat intelligence | Autonomous Defensive Assistant | CVE research, IOC reputation, hardening policy generation, daily briefings |

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
