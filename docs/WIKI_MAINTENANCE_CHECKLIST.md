# Wiki Maintenance Checklist

## Purpose

Use this as the day-to-day operational checklist for maintaining RedThread's wiki without losing provenance, structure, or memory continuity.

## Daily / per-change checklist

### Before editing
- [ ] Read `docs/WIKI_ARCHITECTURE.md`
- [ ] Read `docs/WIKI_INGEST_WORKFLOW.md` for source-driven updates
- [ ] Read `docs/WIKI_QUERY_TO_PAGE_WORKFLOW.md` for answer-driven updates
- [ ] Read `docs/wiki/SCHEMA.md`
- [ ] Read `docs/wiki/index.md`
- [ ] Read the relevant source-of-truth docs in `docs/`
- [ ] Search MemPalace for related prior work

Example searches:

```bash
.venv/bin/mempalace search "evaluation pipeline"
.venv/bin/mempalace search "promotion evidence" --wing redthread
```

### While editing
- [ ] Use the correct page type: `entity`, `concept`, `decision`, `system`, `research`, or `timeline`
- [ ] Add or preserve YAML frontmatter
- [ ] Cite the relevant source docs
- [ ] Mark uncertainty honestly
- [ ] Prefer additive history over silent rewrites
- [ ] Keep filenames semantic and stable

### After editing
- [ ] Update `docs/wiki/index.md`
- [ ] Append to `docs/wiki/log.md`
- [ ] Run `python3 scripts/wiki_lint.py` or `make wiki-lint`
- [ ] Re-mine into MemPalace if the update is durable

```bash
.venv/bin/mempalace mine . --agent codex
```

## Quick rules

- Do not treat wiki pages as more authoritative than source docs.
- Do not add high-impact claims without citations.
- Do not skip index/log updates for durable changes.
- Do not flatten open questions into settled facts.

## Rule of thumb

If the result would help a future human or future agent avoid re-deriving the same insight, it probably belongs in the wiki.
