---
title: Agentic Confused Deputy
type: concept
status: active
summary: Privilege escalation in multi-agent systems via indirect prompt injection.
source_of_truth:
  - https://www.reddit.com/r/LangChain/comments/1rtxzvm/a_poisoned_resume_langgraph_and_the_confused/
updated_by: codex
updated_at: 2026-04-16
---

# Agentic Confused Deputy

## Definition

A high-privilege agent does bad things because a low-privilege agent told it to. 

The low-privilege agent was hacked by a bad document (Indirect Prompt Injection).

## Why it matters

Multi-agent systems like LangGraph share "state".
If one agent is fooled, it can pass bad instructions to "trusted" nodes.
Administrative nodes may execute these because they trust the sender.

## How it appears in RedThread

RedThread uses a supervisor-worker architecture.
Workers handle outside data.
If a worker is compromised by a target model's output, it could trick the supervisor.

## Recommended Fixes

- **Scope Validation:** Check if sender has right to ask for that action.
- **Permission Inheritance:** Do not give child agents more power than parents.
- **Sidecar Checks:** Use a separate tool to verify every delegation.

## Sources

- [Reddit: A Poisoned Resume, LangGraph, and the Confused Deputy](https://www.reddit.com/r/LangChain/comments/1rtxzvm/a_poisoned_resume_langgraph_and_the_confused/)
