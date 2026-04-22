---
title: ATP Tennis Bot Live Workflow Test Results
type: research
status: active
summary: Results and interpretation of the live workflow replay pipeline against the ATP Tennis Bot using ZAPI HAR ingestion.
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

The bridge pipeline performed exactly as designed:
1. **Secure Halting**: It carries session state forward but stops immediately (`live_workflow_aborted_count: 1`) when a step fails, preventing aggressive/spammy behavior when contracts break.
2. **Contract Mismatch Identification**: The 400 Bad Request clearly highlights a stateful dependency between steps. 

**How to fix the workflow**:
To make the entire workflow succeed, the `POST /api/chat` payload requires the real `chatId` created in Step 2. This proves the necessity of **Binding Overrides** in the `adopt-redthread` architecture. The operator must instruct the engine to pipe `response.chat.id` from `post_api_chats` into the `chatId` field of `post_api_chat`.
