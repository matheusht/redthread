---
title: ATP Tennis Bot Live Workflow Test Results
type: research
status: active
summary: Results and interpretation of the live workflow replay pipeline against the ATP Tennis Bot using ZAPI HAR ingestion.
source_of_truth:
  - ../WIKI_QUERY_TO_PAGE_WORKFLOW.md
  - /Users/matheusvsky/Documents/personal/adopt-redthread/docs/live-attack-implementation-plan.md
updated_by: codex
updated_at: 2026-04-22
---

# ATP Tennis Bot Live Workflow Test Results

## Overview

We executed the Adopt-RedThread bridge pipeline against a live ZAPI HAR capture (`demo_session_filtered.har`) for the application `atp-tennis-bot.vercel.app`.

The testing occurred in two phases:
1. **Planning & Gating (`runs/atp_tennis_01`)**: Initial ingestion and plan generation, which halted at the pre-publish gate.
2. **Live Execution (`runs/atp_tennis_01_live`)**: Live workflow replay using explicit, human-approved auth and write contexts.

---

## Phase 1: Planning and Gating (`runs/atp_tennis_01`)

During the first run, the bridge pipeline successfully ingested the HAR file, normalized the API endpoints, and generated a **Live Attack Plan** (`live_attack_plan.json`).

### Findings
- The pipeline extracted **5 API cases** grouped into a single workflow.
  - **3 Safe Reads (GET)**: `GET /api/chats`, `GET /api/chats/{id}`
  - **2 Writes (POST)**: `POST /api/chats`, `POST /api/chat`
- The system correctly flagged the endpoints as `authenticated_surface` and `sensitive_data_surface`, and the POST requests as `mutating_http_method`.
- **Gate Verdict (`gate_verdict.json`)**: The pre-publish security gate issued a decision of **`review`** (rather than `approve`), explicitly citing `manual_review_required_for_write_paths`.
- **Execution**: The pipeline **did not** attack the live application. It securely halted at the review gate, waiting for human-approved context.

---

## Phase 2: Live Execution (`runs/atp_tennis_01_live`)

To proceed with live testing, we provided the pipeline with explicit context:
- `approved_auth_context.json`: Providing a real session `cookie`.
- `approved_write_context.json`: Providing approved, hardcoded JSON payloads for the `POST` endpoints.

We re-ran the pipeline with flags to execute the live workflow replay.

### Workflow Replay Sequence & Results

The engine executed the workflow linearly. Here is the step-by-step breakdown from `live_workflow_replay.json`:

1. **Step 1: `GET /api/chats` (Success)**
   - **Result**: `200 OK`
   - **Response**: `{"chats": []}`
   - **Note**: The server successfully returned an empty array of chats.

2. **Step 2: `POST /api/chats` (Success)**
   - **Result**: `201 Created`
   - **Response**: `{"chat": {"id": "iRNw0T1nL6V1ZYbxHO39x", "sessionId": "dedf75fa-90ed-479c-be53-e1d027cb6717", "title": "New chat", ...}}`
   - **Note**: The engine successfully injected the approved cookie header and the server created a new chat with a dynamic ID.

3. **Step 3: `POST /api/chat` (Failed ❌)**
   - **Result**: `400 Bad Request`
   - **Why it failed**: We hardcoded `"chatId": "test_chat_123"` in our `approved_write_context.json`. The server rejected the request because `test_chat_123` is not a valid chat ID. It expected the dynamic `chat.id` generated in Step 2.

### Takeaway & Next Steps

The bridge pipeline performed exactly as designed initially:
1. **Secure Halting**: It carries session state forward but stops immediately (`live_workflow_aborted_count: 1`) when a step fails, preventing aggressive/spammy behavior when contracts break.
2. **Contract Mismatch Identification**: The 400 Bad Request clearly highlights a stateful dependency between steps. 

---

## Phase 3: Stateful Execution & Core Engine Upgrades (`runs/atp_tennis_01_live_bound`)

To resolve the 400 Bad Request, we needed to dynamically pass the `chat.id` into the `POST /api/chat` payload. However, we discovered several deep structural challenges that required upgrading the RedThread engine itself.

### Challenge 1: HAR Ingestion Stripping (Fallback Body)
ZAPI HAR ingestors intentionally strip request bodies for privacy. This meant the engine lacked a structural JSON blueprint to apply bindings to.
**Solution**: We modified the engine (`adapters/live_replay/workflow_bindings.py` and `adapters/live_replay/workflow_executor.py`) to inject the `approved_write_context.json` body as a fallback blueprint when `use_bound_body_json: true` is set.

### Challenge 2: Dual ID Validation (404 Not Found)
After binding `chatId`, the server returned a `404 Not Found`. We discovered the Vercel AI SDK expects both `chatId` AND `id` in the JSON payload to match the backend chat ID.
**Solution**: We expanded `binding_overrides_atp.json` to map `chat.id` into both `request_body_json.chatId` and `request_body_json.id`.

### Challenge 3: Session Cookie Rotation (404 Not Found)
Even with correct IDs, the server returned `404 Not Found`. We discovered that `POST /api/chats` issues a brand new session cookie (`tennisbot_session`) in its response. Because the engine was using the hardcoded cookie from `approved_write_context.json`, the server created the chat in one session, but we attempted to append messages to it from a different session!
**Solution: Request Header Bindings**
We implemented native `request_header` binding support into the RedThread engine:
1. Expanded `SUPPORTED_BINDING_TARGETS` in `workflow_bindings.py`.
2. Passed `approved_write_headers` through the workflow executor to establish placeholder baselines.
3. Updated `_approved_write_request` to merge bound headers.
4. Added a binding to map `chat.sessionId` from the `POST /api/chats` response into the `cookie` header of `POST /api/chat`, replacing a `{{SESSION_ID}}` placeholder.

### Final Execution Result
With all three engine upgrades in place, we ran the pipeline with `binding_overrides_atp.json`.

- **Result**: `live_workflow_aborted_count: 0`
- **Result**: `applied_response_binding_count: 3` (chatId, id, cookie)
- **Result**: At the time of this test, the engine handled the Vercel AI SDK streaming chunked response by logging a bounded `timeout` instead of crashing.

### Follow-up after this test

This ATP run exposed the next honest gap clearly: we still could not tell the difference between "the stream opened" and "no useful bytes ever arrived." That gap drove Phase D of the roadmap.

As of 2026-04-22, `adopt-redthread` now has the bounded follow-up:
- first-chunk / first-byte stream evidence (`stream_opened`, `first_chunk_bytes`, `first_chunk_preview`)
- `stream_open_partial_read` classification instead of flattening every streaming case into `timeout`
- configurable `stream_max_bytes` budget for small operator-tunable evidence capture

### Final Takeaway
The Adopt-RedThread bridge now supports **one stronger bounded class** of stateful workflows. This includes:
- dynamic body-field mutation
- reviewed fallback body templates
- reviewed header/session injection
- multi-step replay with evidence carry-forward

The next operator-facing layer is now in place too:
- the workflow review manifest is written before live workflow replay
- it now surfaces `required_contexts`, `body_template_gaps`, and `open_questions`
- replay now adds plain-English failure narratives instead of leaving operators with reason codes alone

While a major milestone, this is not a generally solved problem. Broader real-world statefulness (e.g., chunked stream aware response handling, CSRF refresh patterns, broader cookie jar lifecycle, complex branching, or retry logic) remains out of scope for the current engine layer.
