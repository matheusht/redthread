# Anti-Hallucination SOP for LangChain Applications

> **Type**: General Engineering Standard (Reusable)  
> **Version**: 1.0  
> **Last Updated**: 2026-04-03  
> **Applicable To**: Any LangChain-based LLM application  
> **Author**: Matheus

---

## 1. Purpose

This Standard Operating Procedure (SOP) defines the mandatory practices for minimizing hallucinations in LangChain-based applications. Hallucinations — LLM outputs that are factually incorrect, fabricated, or unsupported by source data — represent the single largest reliability risk in production AI systems.

This SOP is structured as **five pillars**, each addressing a different layer of the anti-hallucination defense. All five pillars must be implemented for production-grade reliability.

---

## 2. The Five Pillars

### Pillar 1: Knowledge Grounding (RAG Implementation)

**Objective**: Anchor all LLM responses to verified external data. Never rely on parametric memory for factual claims.

#### Standards

| Component | Requirement |
|---|---|
| **Chunking** | Use semantic-aware or hierarchical chunking. Fixed-size chunking is prohibited for production RAG. |
| **Retrieval** | Implement hybrid search: sparse (BM25/keyword) + dense (vector/semantic) via `EnsembleRetriever`. |
| **Reranking** | All retrieval pipelines MUST include a reranking step (e.g., Cohere Rerank, cross-encoder) before generation. |
| **Similarity Threshold** | Discard retrieved chunks below a validated cosine threshold (default: 0.75). |
| **Source Tracking** | All chains MUST use `return_source_documents=True`. Every fact in the response must be traceable to a source. |
| **Metadata** | All documents MUST include `source_id`, `section_header`, and `chunk_index` in metadata. |

#### Implementation Pattern

```python
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.vectorstores import VectorStoreRetriever

# Hybrid retriever (REQUIRED for production)
ensemble = EnsembleRetriever(
    retrievers=[bm25_retriever, vector_retriever],
    weights=[0.4, 0.6],
)
```

---

### Pillar 2: Prompt Engineering for Accuracy

**Objective**: Constrain the LLM's generation to produce only grounded, verifiable outputs.

#### 2.1 Direct Grounding Instruction (Mandatory)

Every factual prompt MUST include this instruction at the TOP of the system prompt:

```
"Only answer using the provided context. If the answer is not in the context, 
state that you do not know. Do not use outside knowledge."
```

#### 2.2 Chain-of-Verification (CoVe)

For high-stakes outputs (e.g., guardrail synthesis, compliance responses), implement the 4-step CoVe:

1. **Generate Baseline**: Initial unverified draft response
2. **Plan Verifications**: Generate fact-checking questions targeting specific claims
3. **Execute Verifications**: Answer each question independently (isolated LLM calls)
4. **Final Synthesis**: Reconcile baseline with verification answers

> **Critical**: Step 3 MUST use isolated LLM calls per question. Batching verification questions allows the baseline bias to contaminate answers.

#### 2.3 Step-Back Prompting

For complex domain questions:

```
Step 1: "What are the general principles of [topic]?"
Step 2: "Given these principles, answer [specific question]."
```

#### 2.4 Structured Output

All LLM outputs that feed into automated pipelines MUST use Pydantic structured output:

```python
from langchain_core.output_parsers import PydanticOutputParser

class AnalysisOutput(BaseModel):
    category: str
    confidence: float
    evidence: list[str]
    conclusion: str
```

---

### Pillar 3: Model Settings & Control

**Objective**: Configure LLM parameters to minimize creative fabrication in factual contexts.

#### Temperature Matrix (Mandatory)

| Role | Temperature | Rationale |
|---|---|---|
| **Evaluator / Judge** | `0.0` | Deterministic, reproducible scoring |
| **Defense / Generator** (grounded) | `0.1` | Near-deterministic, factually anchored |
| **General QA** | `0.2` | Slight variation, still grounded |
| **Creative / Brainstorming** | `0.7-0.9` | High diversity (acceptable hallucination) |

#### Model Selection

- **Factual/Evaluation tasks**: Use frontier models (GPT-4o, Claude 3.5+) with highest instruction-following capability
- **Grounded generation**: Use mid-tier models (GPT-4o-mini) with low temperature
- **Creative tasks**: Use any model — hallucination is acceptable

> **Rule**: Never use an uncensored or instruction-loose model for factual, evaluative, or defensive tasks. Reserve them exclusively for creative/adversarial use cases.

---

### Pillar 4: Post-Processing & Evaluation

**Objective**: Verify every output before it reaches the user or downstream system.

#### 4.1 Evaluation Framework (DeepEval)

Use Pytest-native evaluation gates.

Important truth boundary:
- sealed dry-run golden checks are offline regression evidence
- successful live judge runs are stronger evidence
- heuristic fallback after judge failure is useful continuity signal, but not equal to successful live judge proof

Use Pytest-native evaluation gates:

```python
# CI/CD gate
def test_faithfulness():
    metrics = evaluate_pipeline(golden_dataset)
    assert metrics.faithfulness >= 0.92, f"Faithfulness: {metrics.faithfulness}"
    assert metrics.hallucination_rate <= 0.08
```

#### 4.2 Key Metrics

| Metric | Definition | CI/CD Threshold |
|---|---|---|
| **Faithfulness** | % of claims supported by context | ≥ 0.92 |
| **Hallucination Rate** | 1 - Faithfulness | ≤ 0.08 |
| **Answer Relevancy** | Cosine similarity(question, answer) | ≥ 0.85 |
| **Context Precision** | % of retrieved chunks that are relevant | ≥ 0.80 |
| **Context Recall** | % of relevant info successfully retrieved | ≥ 0.90 |

#### 4.3 Golden Dataset

Maintain a curated set of ≥ 30 test cases with known-correct outcomes:
- Minimum 10 **positive cases** (expected detection/success)
- Minimum 10 **negative cases** (expected rejection/refusal)
- Minimum 10 **edge cases** (boundary conditions)

**Golden Dataset Rules**:
1. Synthetically bootstrap from production logs for volume
2. Manually review and seal every single trace
3. Run against pipeline on every PR (CI/CD gate)
4. Version the dataset alongside code

#### 4.4 Observability (LangSmith)

For LangGraph-based applications, use LangSmith for:
- End-to-end trace visibility across state graph transitions
- Prompt playground testing before deployment
- Regression detection via automated evaluation runs

```python
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "my-project"
```

---

### Pillar 5: Context Management

**Objective**: Control what the LLM sees to prevent attention dilution and context confusion.

#### 5.1 Context Engineering Strategies

| Strategy | Description | When to Use |
|---|---|---|
| **Write** | Save to external storage | Long-running processes, accumulated state |
| **Select** | Pull only relevant chunks via RAG | All retrieval operations |
| **Compress** | Summarize/filter token volume | Conversation histories > 2000 tokens |
| **Isolate** | Split across multiple agents/contexts | Complex multi-step reasoning |

#### 5.2 Context Budget

- **Factual QA**: Limit context to ≤ 3000 tokens
- **Critical instructions**: Place at START and END of system prompts
- **Conversation history**: Compress beyond 10 turns

#### 5.3 Semantic Routing

Use embedding-based intent classification before generation:

```python
# Route query to specialized chain BEFORE generation
route = classify_intent(query)  # "security" | "general" | "analysis"
chain = route_to_chain[route]    # Each chain has grounded context
response = await chain.invoke(query)
```

**Benefit**: Prevents a general-purpose LLM from attempting to answer outside its knowledge domain.

#### 5.4 Anti-Pattern: Context Confusion

> **Lost-in-the-Middle Effect**: LLMs prioritize information at the beginning and end of context, ignoring content in the middle. Structure your prompts accordingly.

---

## 3. Implementation Checklist

Use this checklist when implementing anti-hallucination for any LangChain project:

- [ ] Hybrid retrieval (BM25 + Dense) is implemented
- [ ] Reranking step is present after retrieval
- [ ] Grounding instruction is in every factual prompt
- [ ] Structured output (Pydantic) is used for automated pipelines
- [ ] Temperature is set per-role according to the matrix
- [ ] Golden Dataset exists with ≥ 30 curated traces
- [ ] CI/CD faithfulness gate is active (≥ 0.92)
- [ ] LangSmith tracing is enabled for production
- [ ] Context budget limits are enforced
- [ ] No uncensored models are used for evaluation or defense tasks

---

## 4. References

- **RAGAS**: Retrieval-Augmented Generation Assessment Suite
- **DeepEval**: Pytest-native LLM evaluation framework
- **LangSmith**: LangChain observability platform
- **G-Eval**: LLM-as-a-Judge with probability-weighted scoring
- **CoVe**: Chain-of-Verification (Dhuliawala et al., Meta AI)
- **OWASP LLM Top-10**: Security evaluation taxonomy
- **MITRE ATLAS**: Adversarial threat landscape for AI systems
