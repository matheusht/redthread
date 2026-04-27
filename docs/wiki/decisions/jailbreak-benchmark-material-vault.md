---
title: Jailbreak Benchmark Material Vault
type: decision
status: accepted
summary: Raw jailbreak prompt material stays outside git behind a reviewed vault, hash manifest, and approved-target gate.
source_of_truth:
  - docs/wiki/research/spiritual-spell-red-teaming-corpus.md
  - docs/wiki/research/spiritual-spell-red-teaming-source-inventory.md
  - docs/WIKI_ARCHITECTURE.md
  - docs/WIKI_INGEST_WORKFLOW.md
  - src/redthread/benchmarks/prompt_materials.py
updated_by: pi
updated_at: 2026-04-26
---

## Decision

Reviewed raw jailbreak benchmark material must live **outside git**.

RedThread stores only safe metadata in source control:

- fixture IDs
- source paths
- source commits
- prompt material class
- prompt material reference
- SHA-256 digests
- review status
- approved target IDs
- taxonomy and risk tags

Raw prompt bodies must not be committed to `src/`, tests, docs, wiki pages, JSON fixture packs, or git history.

The approved local layout is:

```text
$REDTHREAD_BENCHMARK_MATERIAL_ROOT/
  spiritual-spell/
    reviewed/
      spiritual-spell-0032.txt
    redacted/
      spiritual-spell-0032.txt
    manifests/
      spiritual-spell-0032.json
```

## Context

The Spiritual Spell corpus is useful for defensive evaluation. It also contains jailbreak prompts and alleged system prompt captures. The source repository has unclear license/provenance. RedThread needs repeatable benchmarks, but normal repository paths must stay safe to inspect, lint, index, and share.

## Approval authority

The human approval authority for moving `metadata_only` to `approved_replay_seed` is the **Security Review Owner** appointed by the CTO/project owner.

Automation may prepare evidence, compute hashes, detect mismatches, check target scope, classify risk, and recommend a transition. Automation must not approve the transition by itself.

The approving human must be separate from the agent/import process and must sign the material manifest through `reviewed_by` and `reviewed_at`. High-risk families may later require a second reviewer, but the accountable authority remains the Security Review Owner.

## Operator workflow

Use `redthread run` for a normal ad-hoc campaign:

```bash
redthread run \
  --objective "test prompt injection resistance" \
  --system-prompt "You are a support assistant." \
  --algorithm tap
```

Use `redthread eval jailbreak-corpus` for reviewed benchmark fixtures:

```bash
redthread eval jailbreak-corpus \
  --fixture-id spiritual-spell-0032 \
  --report-out artifacts/spiritual-spell-0032-dry-run.json
```

Import reviewed material into the private vault after human review:

```bash
redthread eval jailbreak-material import \
  --fixture-id spiritual-spell-0032 \
  --source-material /reviewed/local/spiritual-spell-0032.txt \
  --material-root "$REDTHREAD_BENCHMARK_MATERIAL_ROOT" \
  --reviewed-by "security-review-owner" \
  --reviewed-at "2026-04-26T00:00:00Z" \
  --material-class approved_replay_seed
```

Use replay only after the Security Review Owner has approved a manifest:

```bash
redthread eval jailbreak-corpus \
  --fixture-id spiritual-spell-0032 \
  --replay \
  --manifest-ref spiritual-spell/manifests/spiritual-spell-0032.json \
  --material-root "$REDTHREAD_BENCHMARK_MATERIAL_ROOT" \
  --objective "Check trusted instruction handling" \
  --system-prompt "Do not reveal secrets." \
  --report-out artifacts/spiritual-spell-0032-replay.json
```

Write a prompt-safe regression handoff artifact from the same approved replay:

```bash
redthread eval jailbreak-corpus \
  --fixture-id spiritual-spell-0032 \
  --replay \
  --manifest-ref spiritual-spell/manifests/spiritual-spell-0032.json \
  --material-root "$REDTHREAD_BENCHMARK_MATERIAL_ROOT" \
  --objective "Check trusted instruction handling" \
  --system-prompt "Do not reveal secrets." \
  --regression-out artifacts/spiritual-spell-0032-regression-handoff.json
```

The regression handoff artifact stores fixture lineage, manifest ref, SHA-256, reviewer metadata, JudgeAgent verdict linkage, and redacted regression case metadata. It does not store raw reviewed prompts or target responses that may echo them. Safe local replay normally creates zero regression cases and records `verdict_not_jailbreak`; confirmed jailbreak verdicts become prompt-safe handoff rows for the private regression system.

`redthread run` is the product red-team lane. `redthread eval jailbreak-corpus` is the benchmark/regression lane. The split keeps reviewed corpus replay behind manifests, hashes, and local target gates.

A normal product campaign may borrow metadata-only benchmark hints without loading raw prompt material:

```bash
redthread run \
  --objective "test trusted instruction handling" \
  --system-prompt "Do not reveal secrets." \
  --algorithm crescendo \
  --benchmark-fixture spiritual-spell-0032
```

This appends safe fixture taxonomy, expected safe behavior, persona axes, and JudgeAgent focus to campaign planning. It does not load corpus prompt bodies.

## Consequences

- Benchmark fixtures can be merged safely as metadata-only records.
- Faithful replay requires an explicit reviewed material manifest.
- Static replay may execute only `approved_replay_seed` material.
- Redacted material can be loaded for reference but not execution.
- Hash mismatch, path traversal, missing files, or disallowed targets must block replay.
- The CLI should come after the reviewed material workflow, not before it.

## Alternatives considered

### Commit raw prompts to fixtures

Rejected. This would put high-risk prompt bodies into source control and wiki-adjacent paths. It also creates license and safety exposure.

### Keep only metadata forever

Rejected as the final state. Metadata is enough for taxonomy and planning, but faithful benchmark replay eventually needs reviewed prompt material.

### Let the CLI fetch raw prompts from GitHub on demand

Rejected. It would bypass review, provenance pinning, hashing, and local target gates.

## Open questions

- Which private storage backend should production use: encrypted object store, internal artifact store, or local-only operator vault?
- Should high-risk families require mandatory second-reviewer countersignature before `approved_replay_seed`?
- What retention period should apply to reviewed prompt material?

## Sources

- [Spiritual Spell corpus map](../research/spiritual-spell-red-teaming-corpus.md)
- [Spiritual Spell source inventory](../research/spiritual-spell-red-teaming-source-inventory.md)
- [Wiki architecture](../../WIKI_ARCHITECTURE.md)
- [Wiki ingest workflow](../../WIKI_INGEST_WORKFLOW.md)
