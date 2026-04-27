---
title: Spiritual Spell Red Teaming Corpus
type: research
status: active
summary: Safe RedThread ingest map for the Goochbeater Spiritual-Spell-Red-Teaming jailbreak corpus.
source_of_truth:
  - https://github.com/Goochbeater/Spiritual-Spell-Red-Teaming
  - docs/WIKI_ARCHITECTURE.md
  - docs/WIKI_INGEST_WORKFLOW.md
  - docs/wiki/SCHEMA.md
  - docs/algorithms.md
  - src/redthread/core/strategies/static_seed_replay.py
  - src/redthread/core/strategies/builtin.py
  - src/redthread/core/plugins/builtin.py
updated_by: pi
updated_at: 2026-04-26
---

## Research question

How should RedThread use the public `Goochbeater/Spiritual-Spell-Red-Teaming` corpus: wiki-only research, standalone eval benchmark, persona-generation input, attack-strategy source, or hybrid?

## Current synthesis

Use it as a **hybrid curated benchmark source**.

Best fit:
1. **First:** safe metadata-only corpus inventory in the wiki.
2. **Next:** operator-reviewed static replay fixtures for local or approved targets only.
3. **Then:** method-family tags that can seed personas, TAP branches, Crescendo narratives, and JudgeAgent rubric context.
4. **Not now:** bulk raw prompt import, live third-party model testing, or automatic defense promotion.

Why this matters: this corpus is broad and real-world. It covers many model families and prompt styles. But it also contains raw jailbreak prompts and alleged leaked system prompts. RedThread should use the structure and eval signal, not blindly copy all prompt text into normal code paths.

## Source scope inspected

External source: [Goochbeater/Spiritual-Spell-Red-Teaming](https://github.com/Goochbeater/Spiritual-Spell-Red-Teaming)

Local research clone used for inventory: `/tmp/pi-github-repos/Goochbeater/Spiritual-Spell-Red-Teaming`

Observed shape:

Full source-path inventory: [spiritual-spell-red-teaming-source-inventory.md](spiritual-spell-red-teaming-source-inventory.md).

| Area | Files | Notes |
|---|---:|---|
| Repository total | 210 | 184 markdown, 25 text, 1 extensionless/odd file. |
| `Jailbreak-Guide/Anthropic` | 59 | Claude, Opus, Sonnet, Claude Code, Rufus, Perplexity-Claude material. |
| `Jailbreak-Guide/ChatGPT` | 8 | ChatGPT/o3 family prompt material. |
| `Jailbreak-Guide/ENI-Tutor` | 6 | Curriculum, lab, interview, quick reference files. |
| `Jailbreak-Guide/Gemini` | 11 | Gemini, Antigravity, Jules, Portraits material. |
| `Jailbreak-Guide/Grok` | 17 | Grok 4.x, Grok Heavy, agent-injection material. |
| `Jailbreak-Guide/Jailbroken POE bots` | 1 | POE bot note. |
| `Jailbreak-Guide/Other LLMs` | 77 | DeepSeek, Kimi, Qwen, Mistral, GLM, MiniMax, Falcon, ERNIE, and more. |
| `Jailbreak-Guide/System Prompts` | 27 | Alleged system prompt captures and tool/schema captures. |

License signal: no `LICENSE` or `LICENSE.md` was found in the clone. Treat reuse rights as **uncertain**. Do not copy raw corpus text into RedThread until license and safety review are done.

## Method-family taxonomy

This is the safe RedThread taxonomy. It documents all discovered families without reproducing raw jailbreak text.

| Family | Count | Source signal | RedThread category | Recommended use |
|---|---:|---|---|---|
| Model-specific base jailbreaks | 59 | Files named for one target/model jailbreak. | prompt injection, policy bypass | Eval metadata + reviewed fixture candidates. |
| README / directory notes | 42 | `README.md` files across provider folders. | source provenance | Wiki-only and operator notes. |
| System prompt / tool schema captures | 35 | Files named `System Prompt`, `Full System Prompt`, `Tools Full JSON`. | system prompt leakage, tool metadata exposure | High-value eval category, but raw text must stay gated. |
| ENI variants | 27 | Files named `ENI`, `ENI Lite`, `ENI Smol`, `ENI for ...`. | persona conditioning, emotional anchoring | Persona seed metadata only; no direct prompt import. |
| ENI LIME | 15 | Files named `ENI LIME`, `LIME`, or lemon/lime variants. | layered persona conditioning | TAP/Crescendo strategy labels after review. |
| Persona/preferences/style conditioning | 8 | Preferences, personalities, style, `be You`, persona files. | persona generation | Useful for RedThread persona generator feature flag. |
| Tutorial/curriculum/labs | 4 | ENI Tutor curriculum, labs, quick reference. | method guide | Wiki summary only; no training agent to create abuse. |
| ENI NEPTUNE | 4 | Files named `NEPTUNE`. | model-specific jailbreak family | Reviewed benchmark metadata candidate. |
| Loki variants | 3 | Files named `Loki`. | role/persona jailbreak | Reviewed benchmark metadata candidate. |
| Push Prompt | 2 | `Push Prompt` guide/files. | prompt pressure / instruction push | Map to static replay and TAP branch seed. |
| Policy jailbreak | 2 | Files named `Policy Jailbreak`. | policy bypass | Eval fixture candidate. |
| Writer/erotica specialization | 2 | Writer/erotica files. | content-policy bypass | High risk. Wiki-only unless approved. |
| Chain of Draft | 2 | Chain-of-draft files. | reasoning-format pressure | Research-only until safe reproduction design exists. |
| Flash Thought | 1 | Flash-thought file. | reasoning-format pressure | Research-only. |
| Document-based | 1 | Document-based jailbreak file. | indirect prompt injection | Good fit for RAG/tool-agent eval later. |
| Coder specialization | 1 | Malicious coder / coder file. | harmful code bypass | High risk. Do not replay without strict local target. |
| Agent injection | 1 | Agent injection / agent prompt file. | agentic prompt injection | Good fit for Phase 8 runtime review, metadata first. |

## Inventory by target family

| Target family | Source paths | Main value |
|---|---|---|
| Anthropic / Claude / Opus / Sonnet | `Jailbreak-Guide/Anthropic/**` | Largest provider group. Strong signal for persona, preference, system prompt leakage, and Claude Code agentic seams. |
| ChatGPT / o3 | `Jailbreak-Guide/ChatGPT/**` | Useful for policy-bypass and reasoning-model eval labels. |
| Gemini / Antigravity / Jules | `Jailbreak-Guide/Gemini/**` | Useful for agentic IDE and browser/workflow attack planning. |
| Grok | `Jailbreak-Guide/Grok/**` | Useful for agent injection, brute-force style, and custom-instruction cases. |
| Other LLMs | `Jailbreak-Guide/Other LLMs/**` | Broad cross-model generalization set. Best used as benchmark metadata, not raw import. |
| ENI Tutor | `Jailbreak-Guide/ENI-Tutor/**` | Method education source. Keep as wiki synthesis only. |
| System Prompts | `Jailbreak-Guide/System Prompts/**` | High-value leakage regression target. Also highest provenance and safety risk. |

## RedThread fit map

| RedThread surface | Fit | Why |
|---|---|---|
| `StaticSeedReplayRunner` | Strong MVP fit | Existing low-cost replay path already executes planned static seeds and attaches judge-required metadata. |
| Risk plugin registry | Strong fit | Existing plugins already cover prompt injection, system prompt leakage, sensitive data exfiltration, unauthorized action, and unsafe tool use. |
| Attack strategy registry | Strong fit | Existing strategies already include `static_seed_replay`, `tap`, `pair`, `crescendo`, and `gs_mcts`. |
| Persona generator | Medium fit | ENI/persona/style families can become metadata hints, but raw persona prompts should not be copied. |
| TAP | Strong fit | Method families can seed branch labels and diversity hints. |
| Crescendo | Strong fit | Persona/preference/style conditioning maps well to multi-turn narrative pressure. |
| JudgeAgent rubrics | Strong fit | Existing rubrics can score prompt injection, sensitive info, authority, urgency, social proof, and fear. |
| Phase 8 agentic runtime review | Strong fit for agent-injection subset | Agent injection and tool-schema/system-prompt files are relevant to tool metadata and confused-deputy testing. |
| Golden dataset | Medium fit | Only after manual review. Golden traces must be sealed and source/licensing-safe. |

## CTO recommendation

Build a **Curated Jailbreak Benchmark lane**.

CLI shape for future implementation:

```bash
redthread eval jailbreak-corpus \
  --source spiritual-spell \
  --mode metadata-only \
  --strategy static_seed_replay \
  --risk prompt_injection \
  --target local-dev \
  --dry-run
```

Then later:

```bash
redthread run \
  --benchmark spiritual-spell \
  --benchmark-family eni_lime \
  --algorithm tap \
  --personas 3 \
  --dry-run
```

Design rule: the benchmark flag selects **reviewed RedThread fixture records**, not arbitrary raw files from GitHub.

## Proposed data model

Use a new reviewed fixture layer. Keep it separate from code algorithms.

Fields:

- `id`
- `source_repo`
- `source_path`
- `source_commit`
- `license_status`
- `family`
- `target_family`
- `risk_plugin_id`
- `strategy_id`
- `rubric_id`
- `prompt_material_ref`
- `prompt_material_class`: `metadata_only`, `redacted`, `approved_replay_seed`
- `expected_behavior`
- `safety_level`
- `review_status`
- `notes`

This model keeps raw prompt handling explicit. It also lets RedThread prove where every benchmark case came from.

## End-to-end workflow proposal

1. **Ingest metadata** from source paths and filenames.
2. **Classify** each file into a method family, risk plugin, target family, and safety level.
3. **Review** candidate fixtures by a human operator.
4. **Promote** approved seeds into a sealed fixture pack.
5. **Plan** a campaign with `CampaignPlan` using selected risk plugins and strategies.
6. **Run** local or approved targets only.
7. **Score** with JudgeAgent rubrics. Detector hints stay weak signals, not verdicts.
8. **Record** source lineage in `AttackTrace.metadata`.
9. **Convert confirmed failures** into `RegressionCase` records only after review.
10. **Feed defense synthesis** only from confirmed traces, then sandbox validate before promotion.

## Safety boundaries

- Do not bulk-copy raw jailbreak prompts into `src/` or normal docs.
- Do not run this corpus against live third-party targets without explicit approval.
- Do not treat alleged system prompts as verified secrets.
- Do not auto-promote defenses from corpus results.
- Do not train persona generation directly on raw prompt text.
- Mark license and provenance as uncertain until reviewed.

## Near-term MVP

Create no new dependencies.

1. Add a docs-backed fixture schema for reviewed corpus records.
2. Add a small manually reviewed sample pack with redacted or safe local seeds.
3. Wire the pack to existing `static_seed_replay` only.
4. Attach source metadata to traces.
5. Run only dry-run and fake/local target tests first.

## Future path

1. Add family selectors: `eni`, `eni_lime`, `system_prompt_leakage`, `agent_injection`, `policy_bypass`.
2. Let TAP use family labels as branch diversity hints.
3. Let Crescendo use approved persona/style metadata as narrative guidance.
4. Add a Phase 8 subset for agent injection and tool-schema attacks.
5. Add sealed regression promotion for confirmed local failures.

## Open questions

- License is unclear. Raw corpus reuse needs review.
- Some files claim leaked system prompts. Provenance is uncertain.
- Some prompts target current named commercial models. Live replay must stay blocked unless approved.
- The repo changes over time. A real fixture pack should pin a commit hash.

## Sources

- [External repository root](https://github.com/Goochbeater/Spiritual-Spell-Red-Teaming)
- [RedThread algorithms](../../algorithms.md)
- [Static seed replay runner](../../../src/redthread/core/strategies/static_seed_replay.py)
- [Built-in strategies](../../../src/redthread/core/strategies/builtin.py)
- [Built-in risk plugins](../../../src/redthread/core/plugins/builtin.py)
- [Wiki ingest workflow](../../WIKI_INGEST_WORKFLOW.md)
