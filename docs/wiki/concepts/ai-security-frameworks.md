---
title: AI Security Frameworks
type: concept
status: active
summary: Major external frameworks for AI security and threat modeling.
source_of_truth:
  - https://github.com/requie/AI-Red-Teaming-Guide
updated_by: codex
updated_at: 2026-04-26
---

# AI Security Frameworks

Source: [AI-Red-Teaming-Guide](https://github.com/requie/AI-Red-Teaming-Guide)

This page maps the primary external frameworks and models relevant to AI security and RedThread's threat modeling.

## NIST AI Risk Management Framework (AI RMF)
- **Overview**: Emphasizes continuous testing and evaluation throughout the AI lifecycle. It provides a structured approach via four core functions: GOVERN, MAP, MEASURE, and MANAGE.
- **Key Focus**: Trustworthiness characteristics, risk tracking, and red teaming as a recommended approach under the "MEASURE" function.
- **Related Tools**: [Dioptra Testbed](https://pages.nist.gov/dioptra/) (NIST's open-source security testbed).
- **Documents**: AI RMF (NIST AI 100-1), GenAI Profile (NIST AI 600-1).

## OWASP GenAI Red Teaming Guide & LLM Top 10
- **Overview**: Provides a practical approach to evaluating LLM and Generative AI vulnerabilities.
- **Key Focus**: Model-level vulnerabilities (toxicity, bias), prompt injection, system-level pitfalls, and agentic vulnerabilities.
- **Documents**: [GenAI Red Teaming Guide](https://genai.owasp.org/), [LLM Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/).

## MITRE ATLAS
- **Overview**: A comprehensive framework designed specifically for AI security, modeled after MITRE ATT&CK. It provides a knowledge base of adversarial AI tactics and techniques.
- **Tactics Include**: ML Model Access, ML Attack Staging, Defense Evasion, Exfiltration.
- **Focus**: Data poisoning, model evasion, model inversion, and adversarial examples.
- **Reference**: [atlas.mitre.org](https://atlas.mitre.org/)

## Cloud Security Alliance (CSA) Agentic AI Guide
- **Overview**: Explains how to test critical vulnerabilities in autonomous agent deployments.
- **Key Focus**: Permission escalation, orchestration flaws, memory manipulation, tool misuse, and supply chain risks in agentic workflows.
- **Reference**: [Agentic AI Red Teaming Guide](https://cloudsecurityalliance.org/artifacts/agentic-ai-red-teaming-guide)
