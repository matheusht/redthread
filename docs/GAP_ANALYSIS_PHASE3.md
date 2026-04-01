# RedThread Phase 3 Gap Analysis

**Audited:** Every file in `src/redthread/`, `tests/`, `docs/`, and `pyproject.toml`.  
**Compared against:** `docs/algorithms.md`, `docs/TECH_STACK.md`, `docs/product.md`.

---

## Summary

| Category | Status | Gap Count |
|---|---|---|
| Data Models (`models.py`) | 🟡 Needs extension | 2 blockers |
| Core Algorithms (`core/`) | 🔴 Major gaps | 3 missing files |
| Evaluation (`evaluation/`) | 🟡 Partially complete | 2 gaps |
| Orchestration (`orchestration/`) | 🔴 Not started | Entire directory missing |
| PyRIT Adapters (`pyrit_adapters/`) | 🟢 Sufficient for Phase 3 | 0 blockers |
| Tools (`tools/`) | 🟡 Skeleton only | 4 missing tools |
| Tasks (`tasks/`) | 🟢 Complete | 0 |
| Personas (`personas/`) | 🟢 Complete | 0 |
| Config (`config/settings.py`) | 🟢 TAP params already present | 0 |
| CLI (`cli.py`) | 🟡 Needs extension | 1 gap |
| Tests | 🟡 Needs extension | 3 missing suites |
| Telemetry (`telemetry/`) | 🔴 Not started | Entire directory missing |
| Memory (`memory/`) | 🔴 Not started | Entire directory missing |

---

## Detailed Gaps by Module

### 1. Data Models — `src/redthread/models.py`

**What exists:**
- `ConversationTurn` — flat, linear: `turn_number`, `attacker_prompt`, `target_response`. No linking.
- `AttackTrace` — contains `turns: list[ConversationTurn]`. Flat list, no tree structure.
- `AttackResult`, `CampaignResult`, `JudgeVerdict` — all complete and clean.

**Gaps:**

> [!WARNING]
> **BLOCKER: No tree-node data model.**
> TAP requires each node to have `id`, `parent_id`, `children_ids`, `branch_score`, and `depth`. `ConversationTurn` has none of these. Without this, TAP cannot track which branch a prompt belongs to, and the pruning phase cannot rank leaves.

> [!IMPORTANT]
> **BLOCKER: No MCTS-specific state.**
> MCTS needs `visit_count (N)`, `cumulative_reward (Q)`, and `uct_value` per node for the UCT formula. These don't exist anywhere.

**What's reusable:** `Persona`, `JudgeVerdict`, `AttackResult`, and `CampaignResult` work perfectly for tree-based algorithms. Only `ConversationTurn` → `AttackNode` evolution is needed.

---

### 2. Core Algorithms — `src/redthread/core/`

**What exists:**
- `pair.py` — Complete. 287 lines. Runs end-to-end against Ollama + GPT-4o.

**Gaps:**

| File | Spec'd in `algorithms.md` | Status | Severity |
|---|---|---|---|
| `tap.py` | Yes (§1B) — 4-phase branch/prune/attack/prune | ❌ Missing | Blocker |
| `crescendo.py` | Yes (§2A) — multi-turn escalation with backtracking | ❌ Missing | Required |
| `mcts.py` | Yes (§2B) — UCT selection, expansion, simulation, backprop | ❌ Missing | Required |
| `defense_synthesis.py` | Yes (§5) — 5-step isolate/classify/generate/validate/deploy | ❌ Missing | Phase 4+ |

**What's reusable from `pair.py`:** The `_ATTACKER_SYSTEM_PROMPT_TEMPLATE`, the `_extract_prompt()` / `_extract_improvement()` parsing logic, and the Judge integration patterns are directly portable. TAP essentially wraps PAIR's single-prompt logic inside a tree loop.

---

### 3. Evaluation — `src/redthread/evaluation/`

**What exists:**
- `judge.py` — JudgeAgent with Auto-CoT, form-filling, and heuristic `evaluate_turn()`. Working.
- `rubrics/authorization_bypass.yaml` — Complete, 5-tier rubric with OWASP threat categories.

**Gaps:**

| Item | Spec | Status | Severity |
|---|---|---|---|
| `probability.py` | Log-prob weighted scoring (G-Eval §3A, line 219-228) | ❌ Missing | Nice-to-have for Phase 3 |
| Additional rubrics | `data_exfiltration.yaml`, `prompt_injection.yaml` | ❌ Missing | Nice-to-have |

**Note:** The current `_parse_verdict()` uses raw integer scores (`float(raw_score)`). The spec calls for `Σ i·P(token_i)` using OpenAI's `logprobs` API parameter. This is a precision improvement, not a blocker — TAP and MCTS can use integer scores and still function correctly.

---

### 4. Engine — `src/redthread/engine.py`

**What exists:**
- `_run_algorithm()` dispatches based on `AlgorithmType`. Currently only handles `PAIR`.
- Lines 127-132: `NotImplementedError` placeholder for TAP/Crescendo/MCTS.

**Gap:** Adding `elif self.settings.algorithm == AlgorithmType.TAP:` dispatch. Straightforward, mechanical — ~5 lines per algorithm.

---

### 5. Config — `src/redthread/config/settings.py`

**What exists and is ready for Phase 3:**
- `AlgorithmType` enum already includes `TAP`, `CRESCENDO`, `MCTS` ✅
- `branching_factor: int = 3` (TAP B) ✅
- `tree_depth: int = 5` (TAP D) ✅
- `tree_width: int = 10` (TAP W) ✅

**Gap:** MCTS-specific params (`exploration_constant: float = 1.41`, `num_simulations: int = 100`) are missing. Low-effort addition.

---

### 6. CLI — `src/redthread/cli.py`

**What exists:**
- `--objective`, `--system-prompt`, `--rubric`, `--personas`, `--target-model`, `--dry-run`, `--verbose`.

**Gap:** No `--algorithm` flag. The CLI hardcodes PAIR via `settings.algorithm` default. Need to add:
```python
@click.option("--algorithm", "-a", type=click.Choice(["pair", "tap", "crescendo", "mcts"]))
```

---

### 7. PyRIT Adapters — `src/redthread/pyrit_adapters/`

**What exists:**
- `targets.py` — `RedThreadTarget` wrapper, `build_attacker()`, `build_target()`, `build_judge_llm()`, `CentralMemory` initialization. All working.

**Gap per TECH_STACK.md:**

| File | Spec | Status | Needed for Phase 3? |
|---|---|---|---|
| `runner.py` | PyRIT send/receive loop adapter | ❌ Missing | No — `RedThreadTarget.send()` already handles this |
| `converters.py` | Payload obfuscation (base64, encoding) | ❌ Missing | No — Phase 4+ feature |
| `scorers.py` | Override PyRIT's scorer with JudgeAgent | ❌ Missing | No — we bypass PyRIT scoring entirely |

**Verdict:** No blockers. The existing adapter is sufficient for TAP and MCTS.

---

### 8. Tools — `src/redthread/tools/`

**What exists:**
- `base.py` — `RedThreadTool` ABC with `ToolContext`, `ValidationResult`, `PermissionResult`, `ToolResult`. Solid foundation.

**Missing per TECH_STACK.md §4:**

| Tool | Status | Needed for Phase 3? |
|---|---|---|
| `attack_tool.py` | ❌ Missing | Not a blocker — algorithms call targets directly |
| `judge_tool.py` | ❌ Missing | Not a blocker — judge is called inline |
| `defense_tool.py` | ❌ Missing | Phase 4+ |
| `sandbox_tool.py` | ❌ Missing | Phase 4+ |

**Verdict:** The tool registry is an abstraction layer for the LangGraph supervisor (Phase 4+). Phase 3 algorithms call their dependencies directly. Not a blocker.

---

### 9. Orchestration — `src/redthread/orchestration/`

**Status:** ❌ Entire directory missing.  
**Needed for Phase 3?** No. The current `engine.py` dispatches algorithms sequentially. LangGraph orchestration is a Phase 4 concern (parallel attack execution, fan-out/fan-in).

---

### 10. Telemetry — `src/redthread/telemetry/`

**Status:** ❌ Entire directory missing.  
**Spec'd:** K Core-Distance, ARIMA, ASI, Sentence Transformers embeddings.  
**Needed for Phase 3?** No. This is Phase 5 (production monitoring).

---

### 11. Memory — `src/redthread/memory/`

**Status:** ❌ Entire directory missing.  
**Spec'd:** Dream consolidation, `MEMORY.md` index.  
**Needed for Phase 3?** No. This is Phase 4+ (cross-campaign knowledge persistence).

---

### 12. Tests — `tests/`

**What exists:**
- `test_tasks.py` — 10 tests (state machine) ✅
- `test_judge.py` — 8 tests (rubric, scoring, mocked G-Eval) ✅
- `test_pair.py` — 3 tests (jailbreak, failure, dry run) ✅

**Gaps for Phase 3:**

| Test File | Status |
|---|---|
| `test_tap.py` | ❌ Missing — needs tree expansion, pruning, width/depth constraint tests |
| `test_crescendo.py` | ❌ Missing — needs backtracking and multi-turn escalation tests |
| `test_mcts.py` | ❌ Missing — needs UCT selection, rollout simulation, backpropagation tests |

---

## Phase 3 Critical Path (Blockers Only)

These are the **only changes needed** to unblock TAP implementation:

1. **`models.py`** — Add `AttackNode` model (extends `ConversationTurn` with `id`, `parent_id`, `children_ids`, `depth`, `branch_score`).
2. **`core/tap.py`** — Implement the 4-phase algorithm: Branch → Pre-Query Prune → Attack+Assess → Post-Score Prune.
3. **`engine.py`** — Add TAP dispatch in `_run_algorithm()`.
4. **`cli.py`** — Add `--algorithm` flag.
5. **`tests/test_tap.py`** — Unit tests for tree expansion and pruning.

Everything else (MCTS, Crescendo, orchestration, telemetry, memory, defense synthesis) can wait.
