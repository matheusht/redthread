---
title: Hide Learning Complexity From The Operator
type: decision
status: accepted
summary: RedThread should keep adaptive learning inside the engine, reduce operator friction, and prove result gains before adding more visible flags, files, or schemas.
source_of_truth:
  - docs/product.md
  - docs/wiki/research/open-source-redteam-tool-integration-strategy.md
  - docs/wiki/research/tool-technology-incorporation-roadmap.md
  - docs/wiki/research/tool-technology-slice-16-adaptive-persona-weighting.md
  - docs/wiki/research/tool-technology-slice-17-persona-weighting-report-artifacts.md
  - docs/wiki/research/tool-technology-slice-18-persona-weighting-cli-reuse.md
updated_by: pi
updated_at: 2026-04-28
---

# Hide Learning Complexity From The Operator

## Decision

Keep RedThread's learning system, but hide its complexity from the normal operator flow.

The preferred experience is still simple:

```bash
redthread run --objective "test this agent" --report-dir reports
```

RedThread should do smart work quietly under the hood.

The operator should not need to learn many new flags, schema names, sidecar files, or manual tuning steps just to get better results.

## Direction

Do not add the next slice as more adaptive-persona artifact plumbing.

Before expanding adaptive persona weighting, run a small end-to-end proof:

1. Baseline run.
2. Adaptive run.
3. Same objective, target, and budget.
4. Compare:
   - strategy coverage
   - JudgeAgent scores
   - confirmed findings
   - useful runtime signal

If adaptive weighting improves results, make it automatic or near-automatic.

If it does not improve results, keep the existing code as internal/debug support and stop expanding the surface.

## Why this fits RedThread

RedThread's product direction is a CLI-first engine that owns:

```text
attack → judge → defend → validate → regress
```

It should not become a toolkit where the operator manually wires every intermediate artifact.

External tools and internal sidecars can broaden coverage, but RedThread should preserve the higher-value experience: one clear command, better findings, and less manual work.

## What this changes

### Keep

- adaptive persona learning
- weak persona outcome telemetry
- safe debug artifacts
- JudgeAgent-owned findings
- prompt-safe boundaries

### Hide or de-emphasize

- manual persona weighting plan selection
- schema names in normal operator docs
- sidecar files as required workflow steps
- extra flags unless they are clearly advanced/debug controls

### Prove before expanding

Future adaptive-learning work must show at least one practical gain:

- more JudgeAgent-confirmed findings
- better strategy coverage
- better average JudgeAgent score under the same budget
- fewer wasted personas
- faster useful campaigns
- better replay or defense validation value

If a change only adds knobs, files, docs, or concepts, defer it.

## CTO review rule

Before adding a new feature, decision, slice, CLI flag, artifact type, or operator-facing concept, consult the `redthread-cto` subagent.

The CTO review must answer:

- Does this reduce operator friction?
- Does this improve results?
- Can the engine do this quietly instead?
- Is this another manual step?
- Does this add concepts the user must learn?
- Are we proving value or just adding structure?
- Does it preserve JudgeAgent as the owner of confirmed findings?

The CTO agent is allowed to recommend reject, defer, or hide even if the implementation is technically clean.

## Consequences

### Positive

- normal operator flow stays simple
- internal learning can still improve campaigns
- roadmap work must prove user value
- fewer flags and files become part of the main workflow
- future agents get a clear anti-overengineering gate

### Costs

- some advanced controls may stay undocumented or debug-only
- adaptive behavior needs an evidence pass before more buildout
- automatic reuse needs careful explainability so operators know what happened without managing it manually

## Alternatives considered

### Expose all adaptive controls

Rejected. It makes RedThread feel like a manual toolkit and increases operator burden.

### Remove adaptive learning

Rejected. The idea is useful if it improves results quietly.

### Keep adaptive learning as explicit artifact workflow only

Rejected for normal use. Sidecars can remain debug and reproducibility support, but they should not be the main path.

## Sources

- [../../product.md](../../product.md)
- [../research/open-source-redteam-tool-integration-strategy.md](../research/open-source-redteam-tool-integration-strategy.md)
- [../research/tool-technology-incorporation-roadmap.md](../research/tool-technology-incorporation-roadmap.md)
- [../research/tool-technology-slice-16-adaptive-persona-weighting.md](../research/tool-technology-slice-16-adaptive-persona-weighting.md)
- [../research/tool-technology-slice-17-persona-weighting-report-artifacts.md](../research/tool-technology-slice-17-persona-weighting-report-artifacts.md)
- [../research/tool-technology-slice-18-persona-weighting-cli-reuse.md](../research/tool-technology-slice-18-persona-weighting-cli-reuse.md)
