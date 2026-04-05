---
alwaysApply: true
---

# RPI Workflow Rule

Any task with architectural impact, unclear blast radius, or edits across more than one file must follow Research -> Plan -> Implement.

## Research

- identify entrypoints, constraints, neighboring files, and tests
- use the matching focused docs under `docs/`
- do not edit during this phase

## Plan

- write a concise numbered plan
- name touched areas, risks, and verification
- run a gap-check before major implementation

## Implement

- make the smallest coherent change set
- verify iteratively with focused commands
- stop and rescope if the task expands beyond the plan

## Exception

Single-file, low-risk edits can use `mini-rpi`, but still require a brief research and plan pass.
