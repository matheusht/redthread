# MemPalace Codex plugin

Repo-local Codex MCP wiring for MemPalace.

## Files

- `plugin.json` registers the MemPalace MCP server for Codex.
- `hooks.json` wires Codex stop/precompact hooks to MemPalace.
- `hooks/*.sh` are thin wrappers around `mempalace hook run --harness codex`.

## Notes

- Uses the repo virtualenv at `.venv/bin/python` and `.venv/bin/mempalace`.
- MemPalace data itself lives in the standard `~/.mempalace/` location.
- Repo taxonomy lives in `mempalace.yaml` and detected entities in `entities.json`.

## Verify

```bash
.venv/bin/python -m mempalace.mcp_server --help
mempalace status
```
