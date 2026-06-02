# RedThread Experiment B: Autonomous Algorithm Benchmark

Status: research design draft. No runtime behavior changes.

## Purpose

Experiment B compares autonomous jailbreak and red-team strategies under one shared harness.

Core question:

> Which autonomous attack strategies produce the most JudgeAgent-confirmed findings per dollar and per model call under the same target, attacker, judge, seed, retry, and interaction-budget conditions?

This is the current priority. The future closed-loop self-healing study is captured in [scope-a-closed-loop-self-healing.md](scope-a-closed-loop-self-healing.md).

## Why this matters

RedThread is in proof-confidence mode. The useful question is not “which method looks impressive in its own paper?” It is:

- does it create more confirmed findings?
- does it cost less per confirmed finding?
- does it create better replay evidence?
- does it keep operator work simple?

## Materials in this folder

- [experiment-b-protocol.md](experiment-b-protocol.md) — benchmark protocol, candidates, metrics, controls, and safety rules.
- [ledger-schema.md](ledger-schema.md) — simple JSONL + manifest tracking shape.
- [scope-a-closed-loop-self-healing.md](scope-a-closed-loop-self-healing.md) — future experiment scope, not current implementation.

## Candidate strategies

Initial candidates:

1. RedThread baseline direct/replay flow.
2. PAIR-style iterative attacker refinement.
3. TAP-style tree-of-attacks pruning/search.
4. Crescendo-style multi-turn gradual escalation.
5. CoP strategy composition as a RedThread-native candidate.
6. Optional research comparator: Siege-style multi-turn/tree-search approach, if reproducible enough.

## Grounding sources

Attack strategy sources:

- PAIR: https://arxiv.org/html/2310.08419v3
- TAP: https://proceedings.neurips.cc/paper_files/paper/2024/file/70702e8cbb4890b4a467b984ae59828a-Paper-Conference.pdf
- Crescendo: https://arxiv.org/html/2404.01833v3
- Siege: https://arxiv.org/html/2503.10619v3

Benchmark and guardrail-evaluation sources:

- MT-JailBench: https://arxiv.org/html/2605.11002
- JailbreakBench repo: https://github.com/JailbreakBench/jailbreakbench
- MT-JailBench repo: https://github.com/SafetyArena/mt-jailbench
- PandaGuard paper: https://arxiv.org/html/2505.13862v2
- PandaGuard repo: https://github.com/beijing-aisi/panda-guard
- SoK4JailbreakGuardrails paper: https://arxiv.org/abs/2506.10597
- SoK4JailbreakGuardrails repo: https://github.com/xunguangwang/SoK4JailbreakGuardrails

## Non-goals

Do not implement this now.
Do not add dependencies now.
Do not add dashboards, databases, new agents, hidden state machines, or new evidence states.
Do not copy raw jailbreak prompt bodies into docs, tests, prompts, or artifacts.
Do not let external benchmark labels override JudgeAgent.
Do not auto-promote defenses.
