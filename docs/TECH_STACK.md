# RedThread — Technology Stack

> Architecture modeled after the Claude Code source code leak. Language is Python (not TypeScript), but every structural decision is directly traceable to a Claude Code pattern.

---

## 1. Design Philosophy

Claude Code's architecture demonstrates several non-obvious but critical principles that RedThread adopts wholesale:

1. **CLI-first, headless-capable** — The `QueryEngine` class owns the full query lifecycle and session state. No UI dependency in the core loop. RedThread mirrors this: the engine runs headless, the CLI wraps it, and any future UI is a consumer.
2. **Typed tool registry with permission gates** — Every tool has an `inputSchema`, `checkPermissions`, `validateInput`, `isReadOnly`, and `isDestructive`. RedThread does the same with Pydantic models and a permission layer.
3. **Coordinator/Worker decomposition** — Claude Code's coordinator spawns parallel workers with isolated context. Workers report structured results. The coordinator *synthesizes* findings before delegating follow-up work. RedThread's LangGraph supervisor does exactly this.
4. **Task state machine** — `pending → running → completed | failed | killed`. Every background operation is a typed task with deterministic ID generation and a cleanup hook.
5. **Dream/consolidation as a first-class concern** — Background memory consolidation runs as a forked subagent with read-only access. RedThread uses this for attack knowledge persistence.

---

## 2. Core Stack

### Language & Runtime
| Component | Choice | Rationale |
|---|---|---|
| **Language** | Python 3.12+ | Industry standard for ML/AI, PyRIT compatibility, LangGraph native |
| **Type Safety** | Pydantic v2 + `mypy --strict` | Mirrors Claude Code's TypeScript strictness via Zod schemas |
| **Linting** | `ruff` | Fast, opinionated, replaces flake8/isort/black |
| **Package Manager** | `uv` | Modern, fast `pip` replacement with lockfile support |
| **Build/Entry** | `pyproject.toml` + CLI via `click` or `typer` | Claude Code uses Bun bundler; we use standard Python packaging |

### PyRIT Integration Layer
| Component | Role |
|---|---|
| `pyrit` (pip dependency) | **Target abstraction** — handles API connections, retries, rate-limiting to target LLMs |
| | **Orchestrator base** — provides the send/receive interaction loop |
| | **Converters** — base64, translation, encoding transformations for payload obfuscation |
| | **Scoring base** — classifier interface we override with our JudgeAgent |

PyRIT is treated as **infrastructure plumbing** via the Adapter/Wrapper pattern. RedThread classes inherit from or wrap PyRIT base classes, keeping all proprietary logic (search algorithms, defense synthesis, evaluation math) in our own code.

---

## 3. Multi-Agent Orchestration

### Hybrid Architecture (Claude Code's Coordinator Pattern)

```
┌─────────────────────────────────────────────────────┐
│                  LangGraph Supervisor               │
│         (coordinator — manages macro-workflow)       │
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │ Persona  │  │  Attack  │  │  Judge   │          │
│  │Generator │→ │ Runners  │→ │  Agent   │          │
│  │  (1x)    │  │ (N×par.) │  │  (1x)    │          │
│  └──────────┘  └──────────┘  └──────────┘          │
│                      │                              │
│               ┌──────┴──────┐                       │
│               │   Defense   │                       │
│               │  Synthesis  │                       │
│               │   Engine    │                       │
│               └─────────────┘                       │
└─────────────────────────────────────────────────────┘
```

| Layer | Technology | Claude Code Analog |
|---|---|---|
| **Macro-Workflow (Supervisor)** | LangGraph StateGraph | `coordinatorMode.ts` — centralized orchestrator evaluates state and delegates to worker nodes |
| **Parallel Attack Execution** | LangGraph `Send` API → parallel subgraphs | `AgentTool` spawns concurrent workers with isolated context |
| **Micro-Specialist Agents** | Stateless Python classes with system prompts + tools | Swarm-like OpenAI pattern: Agents, Routines, Handoffs |
| **Inter-Agent Communication** | Structured `AttackTrace` dataclass via state channels | `<task-notification>` XML messages between coordinator and workers |

### Why Hybrid?
- **LangGraph Supervisor** for deterministic state management, inspectable execution traces, and strict phase ordering (Generate → Execute → Judge → Defend).
- **Parallel SubGraphs** for high-throughput attack execution — the bottleneck is API latency to the target, not coordination overhead. Fan out N runners, fan in scored results.

---

## 4. Tool Registry (Claude Code's `Tool.ts` Pattern)

Every operation in RedThread is a **typed, schema-validated tool** with a consistent interface:

```python
@dataclass
class RedThreadTool:
    name: str
    input_schema: Type[BaseModel]       # Pydantic model (≈ Zod schema)
    is_read_only: bool = False
    is_destructive: bool = False
    max_result_size_chars: int = 50_000

    async def validate_input(self, input: BaseModel) -> ValidationResult: ...
    async def check_permissions(self, input: BaseModel, ctx: ToolContext) -> PermissionResult: ...
    async def call(self, input: BaseModel, ctx: ToolContext) -> ToolResult: ...
```

### Core Tools

| Tool | Type | Description |
|---|---|---|
| `PersonaGenerateTool` | Read-only | Generates adversarial persona profiles from MITRE ATLAS taxonomy |
| `AttackRunTool` | Destructive | Executes an adversarial payload against a target via PyRIT |
| `JudgeEvalTool` | Read-only | Scores an attack trace using G-Eval/Prometheus 2 |
| `DefenseSynthTool` | Destructive | Generates a candidate guardrail from a successful exploit trace |
| `SandboxValidateTool` | Read-only | Spins up a target replica and re-runs the attack to verify a guardrail |
| `DriftDetectTool` | Read-only | Computes embedding drift via K Core-Distance on vector telemetry |

---

## 5. Task & Campaign Lifecycle (Claude Code's `Task.ts` Pattern)

```python
class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    KILLED = "killed"

class TaskType(Enum):
    CAMPAIGN = "campaign"          # Top-level red-team run
    ATTACK_RUN = "attack_run"      # Single attacker vs. target session
    JUDGE_EVAL = "judge_eval"      # Evaluation of a single trace
    DEFENSE_SYNTH = "defense_synth" # Guardrail generation
    SANDBOX_TEST = "sandbox_test"  # Regression validation
    DREAM = "dream"                # Memory consolidation
```

Every task gets a deterministic ID (prefixed by type), tracks `start_time`/`end_time`/`total_paused_ms`, and writes output to a structured log file. This mirrors Claude Code's `createTaskStateBase()` exactly.

---

## 6. Evaluation & Scoring Stack

| Component | Technology | Purpose |
|---|---|---|
| **Judge Model** | Prometheus 2 (open-source) | Fine-tuned for direct assessment against custom security rubrics |
| **Scoring Framework** | G-Eval (custom implementation) | Auto-CoT + probability-weighted token summation → continuous float scores |
| **Rubric Source** | OWASP Top 10 for LLMs + MITRE ATLAS | Structured failure taxonomies for security-specific evaluation |
| **CI/CD Evaluation** | DeepEval (Pytest-native) | Regression gates: faithfulness ≥ 0.92, hallucination rate ≤ 0.08 |
| **Golden Dataset** | 30 curated traces | 10 jailbreak + 10 safe + 10 guardrail validation test cases |
| **Observability** | LangSmith (planned Phase 5D) | First-party LangGraph tracing, prompt playground, regression monitoring |

### Defense Architect Model (Phase 5A — Anti-Hallucination SOP)

The Defense Architect is **decoupled from the Attacker model** as a critical anti-hallucination measure.

| Setting | Default | Rationale |
|---|---|---|
| `defense_architect_model` | `gpt-4o` | Frontier model with highest instruction-following capability |
| `defense_architect_backend` | `openai` | API access to frontier models |
| `defense_architect_temperature` | `0.1` | Near-deterministic for grounded guardrail synthesis |

**Rule**: Never use an uncensored or instruction-loose model for guardrail synthesis. The Defense Architect produces security policies that directly affect production systems.

### Per-Role Temperature Matrix

| Role | Setting | Default | Rationale |
|---|---|---|---|
| **Attacker** | `attacker_temperature` | `0.8` | Creative diversity for adversarial prompts |
| **Judge** | `judge_temperature` | `0.0` | Deterministic, reproducible evaluation |
| **Defense Architect** | `defense_architect_temperature` | `0.1` | Factually grounded guardrail synthesis |

## 7. Telemetry & Drift Detection

| Component | Technology | Purpose |
|---|---|---|
| **Embedding Generation** | Sentence Transformers (768-dim) | Convert agent interactions to vector representations |
| **Vector Storage** | ChromaDB (local) or FAISS (in-memory) | Store + query embedding timeseries |
| **Drift Algorithm** | K Core-Distance | Non-distributional semantic shift detection on high-dimensional vectors |
| **Time-Series Baseline** | ARIMA (lightweight) | Track latency, token velocity, error rate anomalies |

---

## 8. Persistence & Memory

| Concern | Approach | Claude Code Analog |
|---|---|---|
| **Session transcripts** | JSONL append-only logs per campaign | `recordTranscript()` in `QueryEngine.ts` |
| **Attack knowledge** | Markdown files in a `memory/` directory with an index file | `MEMORY.md` + topic files in `memdir/` |
| **Dream consolidation** | Forked background process, read-only access, 4-phase consolidation | `autoDream/consolidationPrompt.ts` |
| **Configuration** | TOML/YAML config file + env var overrides | `utils/config.ts` + `getGlobalConfig()` |

---

## 9. Repository Structure

```
redthread/
├── pyproject.toml                 # Dependencies (including pyrit), build config
├── README.md
│
├── src/redthread/
│   ├── __init__.py
│   ├── cli.py                     # CLI entry point (click/typer)
│   ├── engine.py                  # QueryEngine analog — campaign lifecycle
│   │
│   ├── core/                      # Proprietary algorithms (RedThread IP)
│   │   ├── pair.py                # PAIR algorithm
│   │   ├── tap.py                 # TAP tree search with pruning
│   │   ├── crescendo.py           # Multi-turn escalation
│   │   ├── mcts.py                # GS-MCTS for conversation planning
│   │   └── defense_synthesis.py   # Self-healing guardrail generation
│   │
│   ├── orchestration/             # LangGraph supervisor + subgraphs
│   │   ├── supervisor.py          # Coordinator mode
│   │   ├── graphs/
│   │   │   ├── attack_graph.py    # AttackRunner subgraph
│   │   │   ├── judge_graph.py     # JudgeAgent subgraph
│   │   │   └── defense_graph.py   # Defense synthesis subgraph
│   │   └── agents/
│   │       ├── recon_agent.py     # Reconnaissance micro-specialist
│   │       ├── social_agent.py    # Social engineering micro-specialist
│   │       └── exploit_agent.py   # Exploitation micro-specialist
│   │
│   ├── pyrit_adapters/            # Integration layer (Wrapper pattern)
│   │   ├── targets.py             # Wrapping PyRIT Target classes
│   │   ├── runner.py              # PyRIT send/receive loop adapter
│   │   ├── converters.py          # Combining PyRIT converters with personas
│   │   └── scorers.py             # Base scorer override → JudgeAgent
│   │
│   ├── evaluation/                # JudgeAgent internals
│   │   ├── judge.py               # Prometheus 2 integration
│   │   ├── geval.py               # G-Eval framework + Auto-CoT
│   │   ├── rubrics/               # YAML scoring rubrics per threat type
│   │   └── probability.py         # Log-probability extraction + weighted sum
│   │
│   ├── telemetry/                 # Drift detection & monitoring
│   │   ├── embeddings.py          # Sentence Transformer embedding pipeline
│   │   ├── drift.py               # K Core-Distance algorithm
│   │   ├── arima.py               # Time-series anomaly baseline
│   │   └── asi.py                 # Agent Stability Index composite
│   │
│   ├── tools/                     # Typed tool registry (Claude Code pattern)
│   │   ├── base.py                # RedThreadTool base class
│   │   ├── attack_tool.py
│   │   ├── judge_tool.py
│   │   ├── defense_tool.py
│   │   └── sandbox_tool.py
│   │
│   ├── tasks/                     # Task state machine (Claude Code pattern)
│   │   ├── base.py                # TaskState, TaskType, generate_task_id()
│   │   ├── campaign.py            # Campaign-level task
│   │   └── dream.py               # Memory consolidation task
│   │
│   ├── memory/                    # Attack knowledge persistence
│   │   ├── consolidation.py       # Dream-like 4-phase consolidation
│   │   └── index.py               # MEMORY.md index management
│   │
│   ├── personas/                  # Persona generation
│   │   ├── generator.py           # MITRE ATLAS-based profile creation
│   │   ├── atlas_taxonomy.py      # Tactic/technique definitions
│   │   └── seed_data/             # AdvBench, Pretext Project seeds
│   │
│   └── config/                    # Configuration
│       ├── settings.py            # Global config model (Pydantic)
│       └── defaults.toml          # Default configuration
│
├── tests/                         # Test suite
├── docs/                          # Architecture docs
└── memory/                        # Runtime attack knowledge (gitignored)
```

---

## 10. Development & CI

| Concern | Tool |
|---|---|
| **Virtual Environment** | `uv venv` |
| **Dependency Install** | `uv pip install -e ".[dev]"` |
| **Run Engine** | `python -m redthread run --target <config>` |
| **Run Tests** | `pytest` |
| **Type Check** | `mypy --strict src/` |
| **Lint** | `ruff check src/` |
| **CI Pipeline** | GitHub Actions — lint → typecheck → test → baseline attack suite |
