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
- Who is the human approval authority for moving a record from `metadata_only` to `approved_replay_seed`?
- What retention period should apply to reviewed prompt material?

## Sources

- [Spiritual Spell corpus map](../research/spiritual-spell-red-teaming-corpus.md)
- [Spiritual Spell source inventory](../research/spiritual-spell-red-teaming-source-inventory.md)
- [Wiki architecture](../../WIKI_ARCHITECTURE.md)
- [Wiki ingest workflow](../../WIKI_INGEST_WORKFLOW.md)
