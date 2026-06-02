# WHAT REDTHREAD MEANS BY EVIDENCE

> **Scope**: Strict definitions for AI security evidence
> **Style**: Blunt, honest, caveman mode.

Security people lie. We do not lie.
RedThread proves security. We track truth.
Here is what we mean when we say "evidence."

---

## 1. Terminology

### 1.1 Weak Signal
*   **What this is:** Sniff in the wind. Potential anomaly. Unconfirmed risk.
*   **How we get it:** A single rule or heuristic lights up. Prompt might be risky. LLM outputs might look strange.
*   **Why it matters:** Good for warning. Bad for proof. Never treat as fact. Never block live traffic because of weak signal.

### 1.2 Confirmed Finding
*   **What this is:** Verified exploit. Concrete proof of vulnerability.
*   **How we get it:** JudgeAgent inspects full transaction history. Evaluates with scoring rubric. Validates that jailbreak or poison payload succeeded.
*   **Why it matters:** Hard evidence. Target system is broken under this payload. Requires defense synthesis immediately.

### 1.3 Validated Candidate
*   **What this is:** Tested shield. Dry-run guardrail.
*   **How we get it:** Defense generator synthesizes a candidate policy. Replay engine runs exploit probe AND benign control probe against it in sandbox. Candidate blocks exploit. Candidate ALLOWS benign control.
*   **Why it matters:** Ready for promotion. Safe to deploy. Does not break utility.

### 1.4 Active Guardrail
*   **What this is:** Live runtime block. Production guard.
*   **How we get it:** Operator runs explicit promote command (`redthread research promote`). Deploys candidate to live interception plane.
*   **Why it matters:** Active enforcement. Blocks live bad inputs. Enforces policy deterministically. Never auto-promoted by AI. Operator must sign off.

---

## 2. The Evidence Boundary Rule

We never launder simulated containment as live containment.
If a guardrail blocked a sealed test fixture, we call it **simulated containment**.
If a guardrail blocked a live target api call in production, we call it **live runtime containment**.
Any report that mixes these up is a lie.

---

## 3. No Auto-Promotion

We do not trust AI to promote its own defenses to production.
AI creates **Validated Candidates**.
Only human operator creates **Active Guardrails**.
Keeps system safe. Keeps operator in control.
