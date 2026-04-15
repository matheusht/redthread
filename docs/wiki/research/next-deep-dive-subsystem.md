---
title: Next Deep-Dive Subsystem
type: research
status: complete
summary: Historical research result that selected the defense synthesis/validation plus promotion/revalidation deep dive.
source_of_truth:
  - docs/PHASE_REGISTRY.md
  - docs/PROGRESS.md
  - docs/REDTHREAD_STATUS_AUDIT.md
  - docs/wiki/systems/subsystem-focus-map.md
  - docs/wiki/systems/defense-synthesis-and-validation.md
  - docs/wiki/systems/promotion-and-revalidation.md
  - README.md
updated_by: codex
updated_at: 2026-04-15
---

# Next Deep-Dive Subsystem

## Research question

After telemetry and evaluation truth hardening, which subsystem should receive the next deep technical investigation?

## Research result

Next subsystem is:
- **defense synthesis and validation**
- **plus promotion and revalidation**

## Why

Why this subsystem wins now:
- this is the next hardening track in source docs
- this is RedThread's core special thing
- code is real, but the trust story still needed stronger evidence layers

## What the deep dive needed to answer

1. **What does defense validation actually prove?**
   - sealed dry-run replay versus live replay
   - exploit blocking versus benign utility preservation
   - operator evidence versus promotion-grade evidence

2. **How broad is the replay proof?**
   - whether replay cases were too narrow
   - whether benign utility checks were too shallow
   - whether narrow fixes could still over-refuse normal work

3. **How should promotion interpret defense evidence?**
   - what should block promotion
   - what counts as weak evidence
   - how operators should inspect failures without reading raw JSON by hand

4. **How should docs talk about defense confidence?**
   - what replay proves
   - what replay only suggests
   - what promotion approval means and does not mean

## Expected outputs

- explicit defense evidence classes
- stronger replay confidence tests
- clearer promotion evidence buckets
- docs/wiki that separate live proof, sealed replay, and operator inspection honestly

## Outcome note

This research result was used to launch the defense-confidence hardening pass.
That pass is now complete for this round.
