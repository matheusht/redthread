# RedThread: Implementation Progress & Reference Guide

This document is a living reference that tracks the implementation progress of the RedThread autonomous engine. It documents what has been built, architectural decisions made, and how to operate the current state of the engine.

---

## Current Status: Phase 4.5 Complete (Defense Synthesis & Telemetry)

We have successfully migrated RedThread from a single-turn engine to a distributed LangGraph orchestration system, implementing the **Tree of Attacks with Pruning (TAP)**, an advanced **Defense Synthesis Pipeline**, and the foundational **Telemetry Pipeline** for drift detection.

### 1. Architecture Highlights

#### Asymmetric Model Deployment
RedThread uses three independently configurable LLMs to balance cost, speed, and accuracy:
- **The Attacker (Ollama `llama3.2:3b`)**: Fast, uncensored, lightweight local model handles the creative burden of generating personas and crafting rapid-fire conversational turns without hitting API rate limits or safety filters.
- **The Target (Ollama / Local)**: The system under test.
- **The Judge (OpenAI `gpt-4o`)**: The heavy, highly capable frontier model acting as the absolute ground truth. It uses a rigorous G-Eval / Auto-CoT methodology to score traces on a 1-5 scale.

#### LangGraph Orchestration (Phase 4)
- **Location:** `src/redthread/orchestration/supervisor.py`
- We orchestrated the entire campaign lifecycle through a directed graph. The supervisor spawns an `attack_worker` per generated persona in parallel using the `Send` API, aggregates the results, re-evaluates them using a `judge_worker`, and conditionally routes confirmed jailbreaks to a `defense_worker`.

#### Offense Algorithms (Phases 2 & 3)
- **PAIR (Phase 2):** A zero-shot CoT loop for linear iterative refinement.
- **TAP (Phase 3):** Tree of Attacks with Pruning. Expands a search tree of adversarial prompts horizontally, pruning off-topic branches and using the Judge score to guide the depth-first exploration. This solves the "Attacker Drift" issue seen in PAIR.

#### Defense Synthesis Pipeline
- **Location:** `src/redthread/core/defense_synthesis.py`
- A 5-step automated pipeline executed when a jailbreak is confirmed:
  1. **ISOLATE**: Extracts the single minimal attack segment responsible for the jailbreak.
  2. **CLASSIFY**: Uses an LLM to map the vulnerability to OWASP/MITRE ATLAS.
  3. **GENERATE**: Synthesizes a specific `GuardrailClause` designed to block the attack without breaking system functionality.
  4. **VALIDATE**: Sandbox-injects the clause into the original target system prompt and replays the attack payload.
  5. **DEPLOY**: If validation passes (score < threshold), saves the guardrail into `MEMORY.md`.

#### Target Scoping & Runtime Injection (Phase 4.5)
- **Target Scope:** Guardrails stored in `MEMORY.md` are cryptographically mapped to the specific `target_model` and `target_system_prompt_hash`. 
- **GuardrailLoader:** At campaign startup, `GuardrailLoader` parses the memory index, retrieves active/validated guardrails matching the target scope, and automatically appends them to the live Target's system prompt prior to any attack.

#### Telemetry & Drift Detection (Phase 4.5)
- **Location:** `src/redthread/telemetry/`
- Implemented dependency-light API clients for `Ollama` and `OpenAI` embeddings (`nomic-embed-text` / `text-embedding-3-small`).
- Implemented `DriftDetector` utilizing `numpy` to calculate K Core-Distance (Euclidean/Cosine) to measure statistical drift in Target alignment.

---

## 2. CLI Usage Reference

The RedThread engine provides a Rich-based interactive CLI.

### Configuration
1. Ensure Ollama is running (`ollama serve`).
2. Pull the required Attacker/Target model: `ollama pull llama3.2:3b`.
3. Create a `.env` file from `.env.example` and set `REDTHREAD_OPENAI_API_KEY`.

### Running a Campaign

**1. Dry Run (Recommended first step)**
Validates that local models are responding and that persona JSON parsing is functioning correctly without executing expensive iterations.
```bash
redthread run \
  --objective "authorization bypass via identity impersonation" \
  --system-prompt "You are a customer support assistant." \
  --algorithm tap \
  --dry-run
```

**2. Live Run**
Executes the full algorithmic attack.
```bash
redthread run \
  --objective "data exfiltration" \
  --system-prompt "You are an internal IT helpdesk bot." \
  --algorithm tap --personas 3
```

**3. Debugging (Verbose Logging)**
To see the exact raw HTTP requests and token budgets sent to Ollama/PyRIT under the hood:
```bash
redthread run --objective "..." --verbose
```

---

## 3. Logs & Telemetry

Every campaign run automatically streams structured output.

- **SQLite Database:** PyRIT automatically logs raw interactions to `logs/.pyrit_memory.db`.
- **Knowledge Graph:** Validated defenses are appended to `MEMORY.md` mapped by scope.
- **JSONL Transcripts:** The engine compiles the PAIR/TAP CoT, the Target Response, and the Judge's G-Eval reasoning into a JSONL trace mapping to the Pydantic `CampaignResult` schema:
  `logs/campaign-<uuid>.jsonl`

---

## 4. Known Behaviors & Edge Cases

- **"Attacker Drift"**: 3B/8B local models occasionally lose context of the adversarial objective by late iterations. TAP mostly solves this, but aggressive pruning parameters are required.
- **Strict JSON Parsing:** PyRIT truncates responses if `max_tokens` isn't set. We have enforced `max_tokens=2048` in the `OpenAIChatTarget`.
