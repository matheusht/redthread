---
title: Next Deep-Dive Subsystem
type: research
status: active
summary: Recommendation for the next subsystem RedThread should study in depth after the current hardening tranche.
source_of_truth:
  - docs/PHASE_REGISTRY.md
  - docs/PROGRESS.md
  - docs/REDTHREAD_STATUS_AUDIT.md
  - docs/wiki/systems/subsystem-focus-map.md
  - docs/wiki/systems/telemetry-and-monitoring.md
  - README.md
updated_by: codex
updated_at: 2026-04-14
---

# Next Deep-Dive Subsystem

## Research question

After verification, governance, runtime-truth, and defense-confidence hardening are complete, which subsystem should receive the next deep technical investigation?

## Recommendation

The next deep dive should be **Telemetry and Monitoring**.

More specifically, the deep dive should focus on:
- the practical meaning of ASI and drift scores
- the quality of the benign baseline and canary probes
- how much operator trust should be placed in monitoring-triggered conclusions
- how telemetry evidence should relate to campaign, defense, and promotion evidence without being overstated

## Why this subsystem wins now

### 1. It is important, but not yet the best-understood truth layer

The current hardening tranche improved:
- verification truth
- governance truth
- sealed runtime truth
- defense replay confidence

That shifts the next unanswered question from “is the core loop trustworthy?” to “how much should operators trust the stability layer that watches the core loop over time?”

Telemetry is already wired into the product story, the phase history, and the daemon behavior.
But the wiki summary for telemetry is still comparatively thin, and the project docs repeatedly warn against overclaiming what telemetry proves.

### 2. The subsystem has real architectural weight

`docs/PHASE_REGISTRY.md` and `docs/PROGRESS.md` show that telemetry is not a side note.
It includes:
- embedding-based drift detection
- ARIMA-based anomaly detection
- ASI composite scoring
- a monitoring daemon that can trigger follow-up activity

That means telemetry influences operator judgment and runtime posture, even though it is not the main exploit-validation layer.

### 3. It is the highest-value place to reduce future overclaim risk

`docs/wiki/systems/subsystem-focus-map.md` already says telemetry should be interpreted conservatively and should not be over-invested in before trust gaps shrink.
Those earlier trust gaps are now materially smaller.
So the next sensible move is not to expand telemetry features blindly, but to understand:
- what telemetry is truly measuring
- where the baselines are fragile
- what noise or false positives may exist
- which telemetry outputs are safe to act on automatically versus only inspect manually

### 4. It bridges runtime, operations, and future product trust

Telemetry sits between:
- campaigns
- defense validation outcomes
- monitor daemon behavior
- future claims about target degradation or instability

A deep dive here would improve not only the telemetry subsystem itself, but also how RedThread explains long-running safety posture to operators.

## Why not the other subsystems first

### Offense algorithms
Not first.
Breadth is already strong, and the focus map explicitly says not to add another major attack family yet.
The next value is not more search families.

### Judge and evaluation
Not first.
This just received the highest-priority hardening pass and the default verification baseline is green again.
It should keep being maintained, but it is no longer the best candidate for the next *deep* investigation.

### Defense synthesis and validation
Close second, but not first.
This area was just strengthened with richer replay evidence and clearer report inspection.
It still matters, but a telemetry deep dive now would complement the newly hardened defense evidence rather than duplicate it immediately.

### Research and bounded autoresearch
Important, but not first.
The main governance mismatch has already been re-audited and documented.
The next marginal win is less about the accept/reject boundary and more about operational truth over time.

## Deep-dive questions to answer later

1. **How reliable is ASI as an operator signal?**
   - What concrete failure modes does it catch well?
   - What important degradations can it miss?

2. **How strong are the canary probes and benign baselines?**
   - Are the probes too shallow?
   - Are they representative enough to detect meaningful utility drift?

3. **How should drift evidence interact with campaign evidence?**
   - Should telemetry inform campaign launch decisions only?
   - Should it also influence defense revalidation or promotion review?

4. **What daemon actions are safe to automate from telemetry?**
   - Which outcomes can trigger bounded follow-up automatically?
   - Which outcomes should remain strictly advisory?

5. **How should telemetry truth be documented?**
   - What does the current stack prove?
   - What does it only suggest?
   - Where is the line between monitoring and validation?

## Expected outputs of that future deep dive

- a sharper subsystem map for telemetry internals
- explicit trust boundaries for ASI, drift, and daemon-trigger behavior
- recommendations for better probe design or baseline management
- documentation updates that separate operator signal from proof

## Bottom line

After the current hardening tranche, the next deep-dive target should be **Telemetry and Monitoring**.

It is important enough to matter, connected enough to influence operator trust, and still ambiguous enough that a careful research pass would likely produce meaningful clarity without prematurely widening RedThread's scope.
