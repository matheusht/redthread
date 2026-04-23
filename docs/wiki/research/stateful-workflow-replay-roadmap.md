---
title: Stateful Workflow Replay — Next-Phase Roadmap
type: research
status: active
summary: Concrete near-term roadmap for evolving bounded stateful workflow replay into a more assisted, partially-autonomous system. Derived from lessons learned during the ATP Tennis Bot live workflow test.
source_of_truth:
  - ../WIKI_QUERY_TO_PAGE_WORKFLOW.md
  - /Users/matheusvsky/Documents/personal/adopt-redthread/docs/live-attack-implementation-plan.md
updated_by: codex
updated_at: 2026-04-22
---

# Stateful Workflow Replay — Next-Phase Roadmap

## Background

The ATP Tennis Bot live workflow test crossed from simple bounded replay into **bounded stateful replay**. Three structural challenges emerged and were solved one by one:

1. HAR ingestors strip request bodies → solved by approved fallback body templates
2. Multi-slot ID validation → solved by multi-target declared bindings
3. Session cookie rotation → solved by native `request_header` binding support

Solving these exposed the right shape for the next phase of the engine.

The design principle is fixed:

> **Machine does the analysis and proposal. Human approves the dangerous parts. Engine replays cleanly.**

This document translates the lessons from that test into a concrete, ordered roadmap.

---

## What Does Not Change

Before the roadmap, the boundaries that hold:

- The engine does **not** silently mutate arbitrary bodies.
- The engine does **not** infer new nested JSON structures from scratch.
- The engine does **not** rewrite cookies or auth headers without an explicit approved binding.
- The engine does **not** retry writes with guessed values.
- The engine does **not** branch into new workflow paths automatically.

Any improvement that requires crossing these lines is out of scope.

---

## Phase A: Candidate Dependency Discovery (Near-term)

**Goal**: Engine auto-proposes bindings instead of requiring human detective work.

### A1 — Response-to-Request Field Matching

The engine inspects the full workflow plan and for each step pair (step N → step N+1) it:

1. Walks all JSON fields returned in `response_json` at step N.
2. Walks all JSON fields in the `request_body_json` template at step N+1.
3. Emits candidate bindings when field names match by exact key or known alias table (e.g., `id` → `chatId`, `resource.id` → `resourceId`).
4. Assigns a **confidence tier**: `exact_name_match`, `alias_match`, `heuristic_match`.

Candidate bindings are written to the **review manifest** only — not applied automatically.

**Operator action**: Approve, replace, or reject each candidate binding before replay.

### A2 — Alias Table Bootstrap

Seed the alias table from patterns already proven in practice:

| Source key | Target field | Tier |
|---|---|---|
| `resource.id` | `body.resourceId` | alias_match |
| `chat.id` | `body.chatId` | alias_match |
| `chat.id` | `body.id` | alias_match |
| `thread.id` | `body.threadId` | alias_match |
| `session.id` | `query.sessionId` | alias_match |

This is a narrow, manually-curated list. No broad semantic inference yet.

### A3 — Path Slot Matching

Engine also inspects URL templates at step N+1 for `{placeholder}` slots. If a prior response JSON contains a field matching the placeholder name (exact or alias), it emits a candidate path binding.

---

## Phase B: Session Continuity Detection (Near-term)

**Goal**: Engine notices rotated session state without requiring human to read raw network traces.

### B1 — Set-Cookie Response Detection

After each step, if the response contains a `set-cookie` header, the engine:

1. Parses the cookie names.
2. Checks if any subsequent step sends a `cookie` header in its approved context.
3. If the cookie name appears in a later step, emits a candidate header binding.

The binding is marked `candidate_header_binding` and goes into the review manifest.

**Operator action**: Approve the binding and set the `{{PLACEHOLDER}}` in the write context header. This matches the pattern we manually established in the ATP test.

### B2 — Session Continuity Contract Emitted in Plan

When the engine detects a candidate header binding, the `live_workflow_plan.json` explicitly notes:

```json
"session_continuity_note": "step 2 response may rotate session cookie; step 3 candidate header binding required"
```

This replaces the current situation where the operator has to infer this themselves from HTTP logs.

---

## Phase C: Operator Manifest First Flow (Near-term)

**Goal**: A single artifact shows everything the operator needs before deciding to run live replay.

### C1 — Unified Pre-Run Manifest

The engine builds a `workflow_review_manifest.json` before execution with:

| Section | Contents |
|---|---|
| `required_contexts` | Auth context, write context, any template fields needed |
| `candidate_bindings` | Auto-proposed response-to-request field bindings with confidence tier and reason |
| `candidate_header_bindings` | Cookie rotation or session continuity candidates |
| `body_template_gaps` | Fields in approved body templates that are still static/placeholder |
| `open_questions` | "Step 3 body field `id` has no candidate source — is this intentional?" |

The operator reviews this manifest, annotates decisions (approve/replace/reject per binding), and then runs replay. **No live execution before manifest review.**

### C2 — Improved Failure Explanation

When replay aborts, current messages are generic (`http_error`, `response_binding_target_missing`). Replace with operator-readable plain-English explanations:

| Current | Better |
|---|---|
| `response_binding_target_missing` | "Body field `chatId` has no value: HAR body was stripped and no fallback template provided" |
| `http_error: 404` | "404 received after binding `chat.id` into body — session cookie may not have been forwarded" |
| `timeout` | "Request accepted by server but response stream did not complete within timeout — likely AI inference endpoint" |

This should go into both the `live_workflow_replay.json` per-step evidence and a `workflow_failure_narrative` block in the summary.

---

## Phase D: Streaming Endpoint Awareness (Medium-term)

**Goal**: Distinguish "stream opened successfully" from "request genuinely failed with timeout."

### D1 — First-Chunk Evidence

**Status (2026-04-22): shipped in `adopt-redthread`.**

When the server sends a chunked streaming response, the engine:

1. Reads the **first chunk only** (or up to 512 bytes).
2. Records `stream_opened: true`, `first_chunk_bytes: N`, `first_chunk_preview: "..."` in the step evidence.
3. Classifies the outcome as `stream_open_partial_read` rather than `timeout`.

This allows the operator to distinguish:
- `timeout` = connection opened but no chunks received (genuine network issue or unaccepted request)
- `stream_open_partial_read` = request accepted, LLM generating, engine stopped reading early

### D2 — Configurable Stream Read Budget

**Status (2026-04-22): shipped in `adopt-redthread`.**

Replay now accepts `stream_max_bytes` (default: `512`) on the bounded live replay entrypoints. Operators can raise it when they need slightly more stream evidence for review without turning the engine into a full stream client.

---

## Phase E: Pattern Learning (Longer-term, explicitly bounded)

**Goal**: Engine recognizes recurring patterns across multiple runs and pre-populates binding suggestions.

### E1 — Per-Run Binding Outcome Recording

**Status (2026-04-22): shipped in `adopt-redthread`.**

After each successful workflow replay, record which bindings were applied to a `binding_history.jsonl` append log:

```json
{"source_field": "chat.id", "target_field": "chatId", "target_type": "body", "outcome": "success", "app_host": "atp-tennis-bot.vercel.app"}
```

The current bounded implementation records one append-only JSONL row per successful applied binding outcome, including the workflow id, source case id, source metadata, target metadata, and app host. It does not promote patterns yet.

### E2 — Pattern Promotion

**Status (2026-04-22): bounded review loop partially shipped in `adopt-redthread`; proposal artifact and reviewed alias artifact exist, curated alias-table mutation still not implemented.**

If the same `source_field → target_field` pair appears with `outcome: success` across 3+ distinct apps, promote it to the alias table.

The current bounded implementation now ships two explicit human-reviewed steps before any future curated-table promotion:

1. it reads `binding_history.jsonl`, groups repeated success patterns, and emits a proposal-only `binding_pattern_candidates.json` artifact with counts like success total, distinct app count, and promotion readiness
2. a separate reviewed step can turn approved proposal entries into an `approved_binding_aliases.json` artifact that future workflow planning loads on the next run

That second artifact is intentionally **not** a mutation of the curated alias table. It is a bounded, operator-approved runtime input that lets the next workflow plan reuse reviewed body-field aliases without widening replay autonomy.

This makes the loop concrete and testable today:

`binding_history.jsonl` → `binding_pattern_candidates.json` → human review input → `approved_binding_aliases.json` → next-run workflow plan/replay

**Human-in-loop requirement**: Pattern promotion still requires explicit operator review. The engine proposes candidates, a human approves reviewed aliases, and curated alias-table changes remain a separate future step.

### E3 — Scope

Pattern learning applies only to:
- Exact JSON field name → JSON body field name pairs
- Known cookie name → header placeholder pairs

It does not apply to:
- Full body schema inference
- Semantic field intent matching
- Free-form mutation

---

## What Stays Out of Scope (This Roadmap)

These are explicitly deferred:

| Item | Why deferred |
|---|---|
| CSRF token refresh patterns | Requires mid-session GET + re-parse; adds complex branching |
| Full cookie jar lifecycle management | Broad surface area; dangerous without tighter session boundary controls |
| Non-linear / branching workflows | Current engine is linear; branching needs a different execution model |
| Nested body schema inference | Too much free-form mutation risk |
| Retry/repair on partial failure | Needs explicit human approval for re-execution of write paths |
| Ambiguous multi-candidate auto-resolution | When 2+ candidates exist, human always chooses |

---

## Summary: Human vs Machine Responsibility

| Task | Machine | Human |
|---|---|---|
| Candidate binding discovery | ✅ Auto-proposes | Reviews and approves |
| Session continuity detection | ✅ Auto-proposes | Reviews and approves |
| Alias table lookup | ✅ Auto-applies (low tier) | Reviews new additions |
| Fallback body template use | ✅ Automatic when `use_bound_body_json: true` | Provides and approves template |
| Header/cookie binding | ✅ Proposes | **Must approve before live** |
| Write body invention | ❌ Never autonomous | Always human-provided |
| Ambiguous multi-candidate resolution | ❌ Flags, does not choose | Chooses |
| Live write execution | ❌ Blocked without approval | Explicitly approves |

---

## Ordered Execution Priority

1. **Phase C1** (Unified pre-run manifest) — highest leverage, enables everything else to be reviewable
2. **Phase A1 + A2** (Candidate binding discovery + alias table) — removes biggest human toil
3. **Phase C2** (Better failure explanations) — makes the current engine dramatically more usable
4. **Phase B1 + B2** (Session continuity detection) — solves the hardest class of stateful bugs
5. **Phase D1** (Streaming endpoint first-chunk evidence) — makes AI inference endpoints legible
6. **Phase A3** (Path slot matching) — incremental value, lower priority
7. **Phase D2** (Configurable stream read budget) — convenience
8. **Phase E** (Pattern learning) — longer-term, needs base of production data

---

*Derived from the ATP Tennis Bot live workflow test. See `research/atp-tennis-live-workflow-test.md` for the concrete test evidence this roadmap is grounded in.*
