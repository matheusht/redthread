# RedThread: Implementation Progress & Technical Ledger

This document serves as the **historical source of truth** for the RedThread project. It documents the architectural evolution, critical "war stories" (problems and solutions), and mathematical verification benchmarks achieved across all phases.

---

## 🚀 Current Status: Phase 7 Complete (Bounded Autoresearch Era)

As of **2026-04-08**, RedThread has completed both bounded autoresearch lanes inside Phase 7:
- **7A / `research phase5`** for offense-side bounded source mutation
- **7B / `research phase6`** for defense-side bounded prompt/template mutation

Both lanes emit Phase 3 proposals, preserve research-plane acceptance state in their artifacts, and remain unable to bypass production promotion controls.

> [!TIP]
> **Key Achievement**: RedThread now has closed autoresearch paths for both offense and defense prompt improvement: generate patch → validate boundedness → evaluate on a research branch → review the resulting proposal artifacts → promote only after validation.

## 🎯 Next Finite Milestones

The next steps are no longer “add another attack algorithm.”

The recent self-healing hardening tranche has now delivered:
1. richer sealed replay suites with case-level replay evidence
2. defense-specific validation reports and promotion evidence
3. promotion-time utility-gate enforcement
4. explicit protected surfaces for replay/reporting/utility-gate code

So the next milestones are now:
1. validate the hardened path against more live scenarios and curated runtime replay fixtures
2. keep operator inspection UX strong for deployment validation and promotion evidence
3. align the historical docs with the current hardened runtime behavior before considering any broader mutable defense surface

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
    *   *Solution*: Implemented **GPT-4o-Mini Support**. Added a CLI `--model` override to the `test` command. Developers can now run lower-cost curated dataset checks quickly, while deeper live-provider validation can still be run separately with GPT-4o when needed.

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
> This recorded run achieved perfect scores on the curated golden dataset. It is strong evidence for the current benchmark set, but it should not be treated as a permanent proof of live-model behavior across all environments.

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
# Lower-cost curated dataset run
redthread test golden --model gpt-4o-mini

# Live-provider validation
redthread test golden
```

---

## 🔍 Known Behaviors & Operational Limits

- **"Attacker Drift"**: 3B/8B local models occasionally lose context. Solve via `--width` pruning.
- **Dependency Isolation**: Use `.venv/bin/python` to ensure `pydantic` and `pyrit` are found.
- **Ollama Persistence**: `ollama serve` must be running locally for offensive workers.
- **Sealed CI vs live validation**: PR CI commonly uses sealed dry-run golden checks; full live-provider validation is a separate confidence pass.
- **Evaluation evidence modes**: sealed dry-run heuristic scoring, live judge scoring, and live-judge failure fallback are now treated as different evidence classes and should not be read as equally strong.
- **Dry-run semantics**: `redthread run --dry-run` now stays on a sealed offline path for campaign execution, with deterministic persona generation, lazy provider construction, and telemetry skipped.
