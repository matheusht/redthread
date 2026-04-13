# MemPalace Setup for RedThread

## Status

MemPalace is installed and initialized for this repository.

### Repo-local setup

- Python package installed in: `.venv`
- Repo initialized with: `mempalace init . --yes`
- Repo taxonomy file: `mempalace.yaml`
- Repo-detected entities file: `entities.json`
- Codex plugin directory: `.codex-plugin/`

### Codex MCP wiring

Files:

- `.codex-plugin/plugin.json`
- `.codex-plugin/hooks.json`
- `.codex-plugin/hooks/mempal_save_hook.sh`
- `.codex-plugin/hooks/mempal_precompact_hook.sh`

The plugin uses the repo virtualenv explicitly:

- MCP server command: `.venv/bin/python -m mempalace.mcp_server`
- Hook command path: `.venv/bin/mempalace hook run ...`

## What was added

### 1. Person added to MemPalace registry

A real person was added to the MemPalace global entity registry:

- `Matheus` — context: `work`, relationship: `repo owner`

This lives in the global MemPalace registry under `~/.mempalace/`, not in git.

## What “person” means in MemPalace

In MemPalace, a **person** is a recognized human/entity in the memory model.

Hierarchy:

- **wing** = person or project
- **room** = topic
- **hall** = conceptual category
- **drawer** = stored verbatim memory text

So a person is part of structured recall, not just a string match.

Example:

- wing: `Matheus`
- room: `auth-migration`
- drawer: exact text about something Matheus said, decided, or worked on

Important distinction:

- **person** = human/entity remembered by the system
- **agent** = AI worker/diary identity, such as `reviewer` or `codex`

They are related concepts, but not the same thing.

## How to add another person

### Option A — add to global entity registry

Use the repo venv:

```bash
.venv/bin/python - <<'PY'
from mempalace.entity_registry import EntityRegistry

r = EntityRegistry.load()
r.confirm_research(
    'Alice',
    entity_type='person',
    relationship='teammate',
    context='work',
)
print(r.summary())
PY
```

### Option B — update repo-local detected entities

Edit `entities.json`, then re-run:

```bash
.venv/bin/mempalace init . --yes
```

This is lighter-weight and repo-specific.

## Mining the repo

The repository was mined with:

```bash
.venv/bin/mempalace mine . --agent codex
```

Result from the run:

- files processed: `7`
- files skipped as already filed: `204`
- drawers filed: `21`

This tagged the mining pass with agent name `codex`.

## Useful commands

### Verify install

```bash
.venv/bin/python -m mempalace.mcp_server --help
.venv/bin/mempalace status
```

### Re-mine repo

```bash
.venv/bin/mempalace mine . --agent codex
```

### Search memory

```bash
.venv/bin/mempalace search "auth decisions"
.venv/bin/mempalace search "evaluation" --wing redthread
```

### Wake-up context

```bash
.venv/bin/mempalace wake-up --wing redthread
```

## Codex verification

Run these in your local Codex environment:

```bash
codex --plugins
codex /init
```

If the plugin is detected, Codex should be able to start the MemPalace MCP server and use the configured hooks.

## Notes

- MemPalace project data lives in the standard global location under `~/.mempalace/`.
- Repo taxonomy/config lives in this repo (`mempalace.yaml`, `entities.json`, `.codex-plugin/`).
- The hook wrappers use MemPalace’s built-in Codex hook runner instead of custom logic.
