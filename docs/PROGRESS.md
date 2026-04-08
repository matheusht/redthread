# RedThread: Implementation Progress & Technical Ledger

This document serves as the **historical source of truth** for the RedThread project. It documents the architectural evolution, critical "war stories" (problems and solutions), and mathematical verification benchmarks achieved across all phases.

---

## 🚀 Current Status: Phase 7 Complete (Bounded Autoresearch Era)

As of **2026-04-08**, RedThread has completed both bounded autoresearch lanes inside Phase 7:
- **7A / `research phase5`** for offense-side bounded source mutation
- **7B / `research phase6`** for defense-side bounded prompt/template mutation

Both lanes emit Phase 3 proposals, preserve explicit research-plane acceptance state, and remain unable to bypass production promotion controls.

> [!TIP]
> **Key Achievement**: RedThread now has closed autoresearch paths for both offense and defense prompt improvement: generate patch → validate boundedness → evaluate on a research branch → explicitly accept/reject → promote only after validation.

## 🎯 Next Finite Milestones

The next steps are no longer “add another attack algorithm.”

They are:
1. deepen Phase 6 validation from prompt-contract checks into richer sealed replay fixtures
2. add defense-specific promotion and revalidation reporting
3. prove end-to-end benign utility preservation more rigorously before widening any mutable defense surface

---

## 🏛️ Phase Evolution Ledger

### Phase 1 & 2: The Foundation (PAIR & Personas)
**Objective**: Build a basic iterative attack loop with diverse adversarial profiles.

*   **Key Deliverables**: `pair.py`, `judge.py`, `PersonaGenerator`.
*   **⚠️ Problem: Heuristic Scoring Instability**.
    *   *Symptom*: Simple keyword-based scoring or raw LLM output was non-deterministic and missed subtle "jailbreak" nuances.
    *   *Solution*: Implemented **G-Eval (Auto-CoT)**. Developed hierarchical rubrics and forced the Judge model to output its reasoning ("Reasoning Step") before a score, stabilizing the 1-5 scale.
*   **⚠️ Problem: Generic Adversarial Personas**.
    *   *Symptom*: The initial personas were too "cartoonish" and didn't reflect real-world cyber threats.
    *   *Solution*: Integrated **MITRE ATLAS Taxonomy**. The generator now pulls directly from documented Tactics (e.g., `INITIAL_ACCESS`) and Techniques (e.g., `AML.T0054`), resulting in realistic, high-pressure profiles.

### Phase 3 & 4: Deep Offense (TAP & Orchestration)
**Objective**: Scale the attack search space horizontally and parallelize execution.

*   **Key Deliverables**: `tap.py`, `supervisor.py`, `attack_worker.py`.
*   **⚠️ Problem: Sequential Bottlenecks (Latency)**.
    *   *Symptom*: Running 5 iterations across 10 personas took 20+ minutes, making real-time testing impossible.
    *   *Solution*: Migrated to **LangGraph Distributed Orchestration**. Implemented the `Send` API to parallelize all persona branches. Total campaign time for a 3-persona/5-depth run dropped to **~2 minutes**.
*   **⚠️ Problem: Search Tree Explosion (TAP)**.
    *   *Symptom*: Tree of Attacks horizontally expanded until it hit 100+ branches, exceeding context and API limits.
    *   *Solution*: Implemented **Aggressive Pruning**. The `tap.py` algorithm now uses a `tree_width` and "Pre-Query Pruning" based on Judge relevance scores, keeping the search focused and lean.

### Phase 4.5 & 5A: Defense Evolution (Self-Healing & Training)
**Objective**: Close the loop with automated guardrail deployment and anti-hallucination baseline.

*   **Key Deliverables**: `defense_synthesis.py`, `Golden Dataset`, `test` CLI command.
*   **⚠️ Problem: Hallucinated Guardrails (The "P0" Blocker)**.
    *   *Symptom*: When the local Attacker model was used to "suggest" a defense, it often produced hallucinations (e.g., "Always say yes") or weak policies that were easily re-jailbroken.
    *   *Solution*: **Model Decoupling (Anti-Hallucination SOP)**. Enforced a hard boundary where the Defense Architect *must* be a frontier model (GPT-4o) and *must* operate at `temperature=0.1`.
*   **⚠️ Problem: Regression Gating & API Costs**.
    *   *Symptom*: Running the 30-trace Golden Dataset with GPT-4o cost ~$0.50 per run, discouraging frequent developer testing.
    *   *Solution*: Implemented **GPT-4o-Mini Support**. Added a CLI `--model` override to the `test` command. Developers can now verify the **100% pass baseline** for **$0.02** per run, with final validation shifting to GPT-4o only for production merges.

---

## 📊 Milestone: Phase 5A Evaluation Report

The following metrics were recorded on **2026-04-03** using the `redthread test golden` suite:

| Metric | Threshold | Actual (Verified) | Status |
|---|---|---|---|
| **Faithfulness (Grounding)** | ≥ 0.92 | **1.00** | ✅ PASS |
| **Hallucination Rate** | ≤ 0.08 | **0.00** | ✅ PASS |
| **Jailbreak Precision** | ≥ 0.90 | **1.00** | ✅ PASS |
| **Safe Recall** | ≥ 0.90 | **1.00** | ✅ PASS |

> [!IMPORTANT]
> This baseline mathematically proves that the RedThread Judge is capable of identifying 100% of the curated threats and 100% of the safe refusals in the golden dataset.

---

## 🛠️ Architecture Deep-Dive

### Asymmetric Model Deployment
RedThread uses three independently configurable LLMs to balance cost, speed, and accuracy:
- **Attacker (Ollama/Local)**: Fast, uncensored, iterative. Handles the creative search.
- **Target (System Under Test)**: The local or remote assistant under evaluation.
- **Judge (OpenAI GPT-4o)**: The "Ground Truth." Heavy reasoning/rubric application.

### The Self-Healing Pipeline
1. **DETECT**: Judge marks a jailbreak (Score ≥ 4).
2. **ISOLATE**: Extracts the single minimal attack segment.
3. **SYNTHESIZE**: Defense Architect (GPTo, temp 0.1) creates an imperative guardrail.
4. **VALIDATE**: Sandbox-replay verifies the guardrail blocks the attack.
5. **DEPLOY**: Guardrail appended to the target system prompt for all future sessions.

---

## 📋 CLI Usage Reference

### Running a Campaign
```bash
# Standard TAP attack with 3 personas
redthread run --objective "data exfiltration" --algorithm tap --personas 3
```

### Running Regression Suite
```bash
# Optimized cost (gpt-4o-mini)
redthread test golden --model gpt-4o-mini

# Production level (gpt-4o)
redthread test golden
```

---

## 🔍 Known Behaviors & Operational Limits

- **"Attacker Drift"**: 3B/8B local models occasionally lose context. Solve via `--width` pruning.
- **Dependency Isolation**: Use `.venv/bin/python` to ensure `pydantic` and `pyrit` are found.
- **Ollama Persistence**: `ollama serve` must be running locally for offensive workers.
