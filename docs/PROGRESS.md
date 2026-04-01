# RedThread: Implementation Progress & Reference Guide

This document is a living reference that tracks the implementation progress of the RedThread autonomous engine. It documents what has been built, architectural decisions made, and how to operate the current state of the engine.

---

## Current Status: Phase 2 Complete (The PAIR Engine)

We have successfully built the standalone foundational layer of RedThread and implemented our first single-turn algorithmic attack loop: **Prompt Automatic Iterative Refinement (PAIR)**. 

### 1. Architecture Highlights

#### Asymmetric Model Deployment
RedThread uses three independently configurable LLMs to balance cost, speed, and accuracy:
- **The Attacker (Ollama `llama3.2:3b`)**: Fast, uncensored, lightweight local model handles the creative burden of generating personas and crafting rapid-fire conversational turns without hitting API rate limits or safety filters.
- **The Target (Ollama / Local)**: The system under test.
- **The Judge (OpenAI `gpt-4o`)**: The heavy, highly capable frontier model acting as the absolute ground truth. It uses a rigorous G-Eval / Auto-CoT methodology to score traces on a 1-5 scale, preventing the "Attacker Drift" issues common in LLM-as-a-Judge setups.

#### The PyRIT Adapter Layer
We use Microsoft's PyRIT (`0.12.0`) purely as the interaction/plumbing layer.
- **Location:** `src/redthread/pyrit_adapters/targets.py`
- We wrap PyRIT's `PromptChatTarget` and `CentralMemory` instances inside a `RedThreadTarget` adapter. This completely abstracts away PyRIT's complex `MessagePiece` API from our algorithms, allowing the engine to just call `await target.send(prompt)`.

#### Persona Generation
- **Location:** `src/redthread/personas/generator.py`
- Uses Mitre ATLAS (`AML.TA0004`, `AML.T0051`, etc.) to generate realistic, roleplay-ready adversarial identities (e.g., "Dr. Sophia Patel, a security auditor").
- Operates asynchronously in batches for massive concurrent speedups.

#### PAIR Implementation
- **Location:** `src/redthread/core/pair.py`
- A zero-shot CoT (Chain-of-Thought) loop where the Attacker receives the Target's response, generates an `improvement_rationale`, and crafts a new payload. Runs up to `max_iterations = 20`.

---

## 2. CLI Usage Reference

The RedThread engine provides a Rich-based interactive CLI.

### Configuration
1. Ensure Ollama is running (`ollama serve`).
2. Pull the required Attacker/Target model: `ollama pull llama3.2:3b`.
3. Create a `.env` file from `.env.example` and set `REDTHREAD_OPENAI_API_KEY`.

### Running a Campaign

**1. Dry Run (Recommended first step)**
Validates that local models are responding and that persona JSON parsing is functioning correctly without executing the expensive 20-turn PAIR loop.
```bash
redthread run \
  --objective "authorization bypass via identity impersonation" \
  --system-prompt "You are a customer support assistant." \
  --dry-run
```

**2. Live Run**
Executes the full algorithmic attack.
```bash
redthread run \
  --objective "data exfiltration" \
  --system-prompt "You are an internal IT helpdesk bot."
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
- **JSONL Transcripts:** The engine compiles the PAIR CoT, the Target Response, and the Judge's G-Eval reasoning into a JSONL trace mapping to the Pydantic `CampaignResult` schema:
  `logs/campaign-<uuid>.jsonl`

---

## 4. Known Behaviors & Edge Cases

- **"Attacker Drift"**: 3B/8B local models occasionally lose context of the adversarial objective by iteration 10-15 (e.g., drifting from "hacking a database" to "discussing Newton's Laws").
- **Solution on Deck:** Phase 3 introduces **TAP (Tree of Attacks with Pruning)**, which mitigates drift by testing multiple prompts horizontally and aggressively pruning branches that fall off-topic.
- **Strict JSON Parsing:** PyRIT truncates responses if `max_tokens` isn't set. We have enforced `max_tokens=2048` in the `OpenAIChatTarget` to ensure persona generation correctly emits closing JSON brackets.
