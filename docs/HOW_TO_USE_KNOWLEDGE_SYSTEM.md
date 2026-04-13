# How to Get the Most Out of RedThread's Knowledge System

## Purpose

This guide explains, in simple terms, how to get the best results from the knowledge system we added to RedThread.

That system now has **two parts**:

1. **MemPalace** — the AI's memory and retrieval layer
2. **The wiki (`docs/wiki/`)** — the AI's curated markdown knowledge base

Think of it like this:

- **MemPalace remembers**
- **The wiki explains**

Both are useful on their own, but they become much more powerful when used together.

---

# 1. The simple mental model

## MemPalace
MemPalace is where the agent can **search past knowledge**.

Use it for:
- recalling prior decisions
- searching repo knowledge semantically
- reloading context after time passes
- avoiding repeated rediscovery
- helping the agent answer "what have we seen before?"

## The wiki
The wiki is where the agent can **store durable explanations**.

Use it for:
- system overviews
- decision records
- timelines
- research synthesis
- glossary/entity pages
- process explanations

## Raw docs
The existing docs under `docs/` are still the **source of truth**.

Use them for:
- engineering truth
- architecture references
- current phase/roadmap state
- exact policy or implementation constraints

## Best way to think about all 3 together

- **Raw docs** = truth and evidence
- **MemPalace** = memory and retrieval
- **Wiki** = persistent understanding

---

# 2. What happens automatically vs what needs your direction

## What the AI can do automatically
The agent can now:
- use the documented workflows
- use the wiki schema and structure
- search MemPalace before making important wiki changes
- update wiki pages
- update the wiki index and log
- run wiki lint checks
- re-mine the repo into MemPalace

So a lot of the mechanics are already set up.

## What still benefits a lot from your direction
You still get the best results when you tell the agent things like:
- what matters most
- what should become durable documentation
- what is still uncertain
- what deserves a dedicated wiki page
- what should stay experimental vs become standard guidance

The AI is good at maintenance.
You are still best at **prioritization and judgment**.

## Rule of thumb
If you want the best outcomes, don't just ask for an answer.
Ask for one of these:
- **answer only**
- **answer + update wiki**
- **answer + search memory first**
- **answer + turn this into a durable page**
- **research this topic and update the relevant wiki pages**

That makes the agent act more like a knowledge maintainer than a chatbot.

---

# 3. Best practices for daily use

## Pattern A — ask normal questions, but ask for persistence when it matters
If you ask:

> "How does defense promotion work here?"

You may get a good answer.

But if you ask:

> "Explain how defense promotion works here, verify against docs, and update the wiki if the answer is durable."

That is much better.

Why?
Because now the answer can become part of the system instead of disappearing into chat.

## Pattern B — ask the agent to search memory first
If the topic may have prior history, ask:

> "Search MemPalace first, then answer."

Best for:
- recurring architecture questions
- past decisions
- research themes
- operational workflows
- anything you discussed before

## Pattern C — ask for wiki maintenance explicitly
If you notice a concept is becoming important, ask:

> "Make this a proper wiki page."

or

> "Add this to the right wiki page and update the index/log."

This is one of the highest-leverage uses of the new system.

## Pattern D — use the wiki as the stable briefing surface
For reusable knowledge, the best path is:

1. ask the question
2. let the agent answer
3. ask it to persist the result if useful
4. next time, have the agent start from the wiki and verify against source docs as needed

That way the system compounds over time.

---

# 4. The highest-value ways to use this system

## 1. Architecture understanding
Use the knowledge system when you want the agent to answer:
- how a subsystem works
- how two systems relate
- why a design choice exists
- what changed over time

Best prompt pattern:

> "Explain this system simply, verify against the source docs, and persist the explanation if it would be useful again."

## 2. Research accumulation
This is one of the best uses.

Use it when:
- you're exploring a topic across many sessions
- you are reading multiple docs over time
- you want synthesis, not just retrieval

Best prompt pattern:

> "Research this topic, compare it against what we already know, search memory first, and update the research wiki page."

## 3. Decision memory
If you make a meaningful decision, capture it.

Best prompt pattern:

> "Record this as a decision page or update the existing decision page, with the reasons and consequences."

## 4. Onboarding yourself and future sessions
The wiki is now the best place for:
- entity definitions
- system overviews
- timelines
- process docs

This reduces re-explaining.

## 5. Preventing chat-only knowledge loss
This is probably the biggest win.

Without the new system:
- good answers vanish into conversation history

With the new system:
- strong answers can become durable artifacts

---

# 5. When to rely on MemPalace vs the wiki

## Use MemPalace when:
- you want retrieval
- you think something was discussed before
- you want search across prior materials
- you want to recover context fast
- you want the agent to recall related concepts before answering

## Use the wiki when:
- you want a stable explanation
- you want a human-readable page
- you want an evolving synthesis
- you want something to be easy to revisit later
- you want stronger documentation and onboarding

## Use both when:
- the topic is important
- there may be prior history
- the result should be reusable
- the answer should become documentation

That is the highest-value path.

---

# 6. The best prompt patterns to use

## Simple strong prompts

### For retrieval-first answers
> Search MemPalace first, then answer simply.

### For durable answers
> Answer this, verify against the source docs, and persist it to the wiki if it is reusable.

### For source-driven ingestion
> Read this source, search memory for related context, and update the right wiki pages.

### For answer-driven persistence
> This answer is important. Turn it into a wiki page or update the relevant page.

### For research growth
> Research this topic across the existing docs and memory, then update the research wiki page with current synthesis and open questions.

### For maintenance
> Do a wiki maintenance pass on this topic: check the current pages, search memory, fix stale sections, update index/log, and run wiki lint.

---

# 7. What the maintenance workflows are for

We created several docs so the agent does not drift.

## `docs/WIKI_ARCHITECTURE.md`
Use this when you want to understand the whole system.

## `docs/WIKI_INGEST_WORKFLOW.md`
Use this when new source material should be folded into the wiki.

## `docs/WIKI_QUERY_TO_PAGE_WORKFLOW.md`
Use this when a strong chat answer should become durable.

## `docs/WIKI_MAINTENANCE_CHECKLIST.md`
Use this for practical upkeep and consistency.

## `docs/wiki/SCHEMA.md`
Use this to keep page types, frontmatter, and wiki structure consistent.

---

# 8. How to get the best results in practice

## The highest-leverage behavior
Whenever a result feels reusable, say so.

Examples:
- "persist this"
- "make this a wiki page"
- "update the decision page"
- "add this to the timeline"
- "turn this into durable docs"

That one habit will dramatically increase the value of the system over time.

## Don't wait too long to persist useful answers
If you wait until much later, the context is fuzzier.

The best time to persist is right after:
- a good explanation
- a meaningful decision
- a useful comparison
- a clarified process
- a resolved ambiguity

## Prefer refining existing pages over making duplicates
If a page already exists, it's often better to improve it than to create another page with overlapping scope.

A good instruction:

> "Update the existing page if there is one; only create a new page if the topic genuinely deserves its own home."

## Ask for uncertainty to be preserved
This matters a lot.

Good instruction:

> "If anything is uncertain, mark it as uncertain rather than presenting it as fact."

That keeps the wiki honest.

---

# 9. Recommended workflows you can follow

## Workflow 1 — learn something and keep it
1. Ask your question
2. Get the answer
3. Ask: "Persist this if it's reusable"
4. The agent updates wiki/index/log
5. Optionally re-mine into MemPalace

## Workflow 2 — add new source material
1. Add the new doc or source
2. Ask the agent to ingest it into the wiki
3. Agent reads source + searches memory
4. Agent updates pages/index/log
5. Agent lints and re-mines

## Workflow 3 — grow a research topic over time
1. Start with a research page
2. Revisit topic over multiple sessions
3. Ask the agent each time to update synthesis, contradictions, and next questions
4. Let the page compound instead of starting from scratch each time

## Workflow 4 — maintain system clarity
From time to time ask:

> "Do a maintenance pass on the wiki. Look for stale pages, missing links, missing citations, or topics that should be upgraded into proper pages."

This is a very good periodic cleanup task.

---

# 10. Commands that are useful to know

## Validate the wiki
```bash
python3 scripts/wiki_lint.py
```

or

```bash
make wiki-lint
```

## Re-mine the repo into MemPalace
```bash
.venv/bin/mempalace mine . --agent codex
```

## Search memory
```bash
.venv/bin/mempalace search "your query here"
```

## Load wake-up context
```bash
.venv/bin/mempalace wake-up --wing redthread
```

---

# 11. What success looks like

You are using the system well when:
- fewer good insights are lost in chat history
- repeated questions get better answers faster
- the wiki becomes easier to browse over time
- important knowledge becomes stable and easy to find
- the agent increasingly starts from existing knowledge instead of rebuilding everything from scratch

---

# 12. The most important guideline

If you remember only one thing, remember this:

> **When something is useful twice, it should probably become part of the wiki.**

And if it might have happened before, ask the agent to search MemPalace first.

That simple habit will give you most of the value of everything we built.
