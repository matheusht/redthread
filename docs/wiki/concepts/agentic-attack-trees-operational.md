---
title: Agentic AI Attack Trees & Operational Controls Mapping
type: concept
status: active
summary: Attack trees connecting offensive paths to defensive controls.
source_of_truth:
  - https://github.com/requie/AI-Red-Teaming-Guide#agentic-ai-attack-trees--controls-mapping
updated_by: codex
updated_at: 2026-04-26
---

# Agentic AI Attack Trees & Operational Controls Mapping

Source: [AI-Red-Teaming-Guide](https://github.com/requie/AI-Red-Teaming-Guide#agentic-ai-attack-trees--controls-mapping)

Use attack trees to connect offensive testing paths to defensive controls.

## Attack Tree A: Tool Misuse
1. Inject hidden instruction into user-supplied content
2. Agent adopts malicious instruction priority
3. Agent invokes high-privilege tool
4. Agent executes unsafe action

**Controls:**
- **Preventive:** tool allowlists, scoped API tokens, policy checks pre-execution
- **Detective:** anomalous tool-call monitoring, high-risk action alerts
- **Corrective:** transaction rollback, credential rotation, incident playbook

## Attack Tree B: Memory Poisoning
1. Adversary plants false memory artifact
2. Agent persists poisoned state
3. Subsequent sessions trust manipulated context
4. Agent behavior drifts into unsafe decisions

**Controls:**
- **Preventive:** memory write policies, source trust labels, TTL for memory items
- **Detective:** memory integrity diffs, unusual memory mutation alerts
- **Corrective:** memory quarantine/reset, retrospective impact analysis

## Attack Tree C: Inter-Agent Privilege Escalation
1. Compromise low-privilege agent with prompt injection
2. Lateral instruction passing to orchestrator
3. Orchestrator executes action outside original permission boundary
4. Expanded access leads to data exfiltration or sabotage

**Controls:**
- **Preventive:** identity-bound inter-agent authz, least-privilege role boundaries
- **Detective:** cross-agent call graph anomaly detection
- **Corrective:** isolate compromised agent, revoke delegated capabilities
