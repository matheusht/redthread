---
title: Tool Technology Slice 10 Implementation Plan
type: research
status: implemented
summary: Bounded plan for turning weak external evidence bundles into candidate campaign/probe-seed artifacts without executing attacks or creating findings.
source_of_truth:
  - docs/wiki/research/tool-technology-incorporation-roadmap.md
  - docs/wiki/research/tool-technology-slice-8-implementation-plan.md
  - docs/wiki/research/tool-technology-slice-9-implementation-plan.md
  - src/redthread/reporting/external_evidence.py
updated_by: codex
updated_at: 2026-04-27
---

# Tool Technology Slice 10 Implementation Plan

## Goal

Turn weak external evidence bundles into RedThread-native candidate campaign hints.

Plain meaning:

```text
redthread.external_evidence_bundle.v1
→ redthread evidence plan
→ candidate probe seeds + campaign config hint
→ operator chooses what to run
```

## Scope

In scope:

- candidate campaign/probe artifact model
- conversion from `ExternalEvidenceBundle`
- static seed replay strategy hint
- custom-policy campaign config hint
- CLI command under `redthread evidence plan`
- tests for probe seed extraction and CLI output

Out of scope:

- no automatic attack execution
- no automatic campaign config write into runtime settings
- no confirmed findings
- no regression cases
- no JudgeAgent behavior changes

## Safety invariant

Candidate campaign artifacts are planning hints.

They do not prove the imported issue exists. They only help an operator run a RedThread-native campaign where JudgeAgent can confirm or reject the issue.

## Implementation checklist

- [x] Add `src/redthread/reporting/external_campaigns.py`.
- [x] Add `ExternalEvidenceCampaignCandidates` model.
- [x] Add `campaign_candidates_from_external_evidence()` helper.
- [x] Add `redthread evidence plan` CLI command.
- [x] Add tests for campaign candidate artifact shape and CLI output.
- [x] Keep new files below 200 lines.

## Artifact schema

```text
redthread.external_campaign_candidates.v1
```

## Command shape

```bash
redthread evidence plan \
  --input artifacts/external-evidence.json \
  --output artifacts/candidate-campaign.json \
  --objective "Validate imported weak evidence with RedThread"
```

## Acceptance criteria

- Probe seeds preserve source lineage.
- Campaign config hint uses `static_seed_replay` as a bounded starting strategy.
- Artifact says imported evidence is not a finding.
- Operator must still run RedThread and rely on JudgeAgent confirmation.
