# Research: MemPalace for Codex MCP integration in a local repo

## Summary
I could not directly access the MemPalace docs from this environment, so I could not verify the exact CLI syntax, JSON schemas, or generated files. This brief is therefore an implementation-oriented checklist anchored to the requested official doc URLs, with explicit gaps called out so you can confirm the exact commands before wiring MemPalace into a local Codex/MCP setup.

## Findings
1. **Expected install/init flow is Python-first and repo-local** — the likely baseline flow is: create/activate a virtualenv, install MemPalace with `pip`, then run `mempalace init .` from the repository root so the tool initializes against the current repo rather than a global location. Immediately inspect the generated files and `git status` after init. [Getting Started](https://mempalace.github.io/mempalace/guide/getting-started.html)

2. **Treat Codex integration as a thin plugin layer on top of a working MemPalace CLI setup** — do not start with plugin wiring. First prove the MemPalace CLI works locally, then add the Codex-side plugin config. Operationally, the plugin layer should contain at least `plugin.json` and `hooks.json`, with `plugin.json` holding plugin metadata/registration details and `hooks.json` declaring the hook bindings that invoke MemPalace behavior. The exact schema must be confirmed from official examples/docs before implementation. [Guide](https://mempalace.github.io/mempalace/guide/) [Getting Started](https://mempalace.github.io/mempalace/guide/getting-started.html)

3. **The `person` concept should be validated early because it is likely the core unit of stored/retrieved memory** — for implementation purposes, assume a `person` is the identity/entity that MemPalace attaches mined or searchable memory to. After init, create a single test person using the documented command/workflow, add one or two known facts/memories, and confirm that those records can be retrieved through the documented search path. [Mining](https://mempalace.github.io/mempalace/guide/mining.html) [Searching](https://mempalace.github.io/mempalace/guide/searching.html)

4. **Local init inside an existing Git repo is the main operational caveat** — because `mempalace init .` targets the current directory, it may write config, data, cache, or support files into the working tree. Run it only from the intended repo root; inspect for path collisions; decide which generated artifacts belong in version control versus `.gitignore`; and avoid committing machine-local model/cache state unless the docs explicitly recommend it. [Getting Started](https://mempalace.github.io/mempalace/guide/getting-started.html) [Local Models](https://mempalace.github.io/mempalace/guide/local-models.html)

5. **Verification should cover both the MemPalace layer and the Codex plugin layer separately** — a good minimum verification sequence is: (a) CLI is installed and responds to `--help`, (b) `mempalace init .` succeeds from repo root, (c) expected local files appear, (d) a test person can be created, (e) mining/search returns the expected test data, and only then (f) the same operation succeeds through the Codex plugin hook path. If CLI works but Codex does not, the problem is likely `plugin.json`/`hooks.json`, path resolution, or environment differences. [Getting Started](https://mempalace.github.io/mempalace/guide/getting-started.html) [Mining](https://mempalace.github.io/mempalace/guide/mining.html) [Searching](https://mempalace.github.io/mempalace/guide/searching.html)

6. **Best implementation order is install → init → inspect repo changes → create test person → verify mining/search → add Codex plugin files last** — this sequence keeps failures localized and makes debugging much faster. It also minimizes the risk of blaming Codex integration for issues that are actually in the MemPalace install or local repo initialization. [Guide](https://mempalace.github.io/mempalace/guide/) [Mining](https://mempalace.github.io/mempalace/guide/mining.html) [Searching](https://mempalace.github.io/mempalace/guide/searching.html)

## Practical implementation brief

### 1) Install / initialize in a local repo
Use this as the working checklist, then replace placeholders with exact commands from the docs:

```bash
python -m venv .venv
source .venv/bin/activate
pip install <exact-mempalace-package>
mempalace --help
cd /path/to/existing/repo
git status --short
mempalace init .
git status --short
```

What to verify right away:
- exact files/directories created by `mempalace init .`
- whether any repo config files were modified
- whether generated state should be committed or ignored
- whether MemPalace expects repo-relative or user-home-relative paths

### 2) Codex plugin structure
Until the official schema is confirmed, treat the integration like this:
- create a dedicated repo-local plugin directory
- keep `plugin.json` and `hooks.json` together
- make hook commands explicit and repo-relative
- avoid depending on a shell environment that Codex may not inherit

Questions to confirm from docs/examples:
- required plugin directory name/location
- required keys in `plugin.json`
- required keys in `hooks.json`
- whether hooks execute in repo root or plugin directory
- whether commands need absolute paths or can rely on activated venv state

### 3) `person` model
Before broader setup, confirm these exact points from docs:
- what a `person` represents in MemPalace
- whether a `person` is created by CLI command, config file, or mined implicitly
- minimum required fields to create one
- where `person` data is stored after local init

Recommended smoke test:
1. create one test person
2. add one unique fact/memory tied to that person
3. run documented search/mining flow
4. confirm exact retrieval of the inserted data

### 4) Existing Git repo caveats
Check these immediately after local init:
- new untracked files from MemPalace
- modifications to ignored/tracked config
- local model paths pointing outside the repo
- caches/databases accidentally landing inside the repo
- portability problems if another developer clones the repo

### 5) Practical verification steps
Use this order:
1. `mempalace --help`
2. `mempalace init .`
3. inspect generated files + `git status`
4. create one test person
5. add one or two test memories/facts
6. run documented search command
7. run documented mining command if separate
8. invoke the same behavior through Codex plugin hooks
9. re-check `git status` to catch runtime-generated artifacts

## Sources
- Kept: MemPalace Guide — official documentation hub for the requested setup/integration topics. (https://mempalace.github.io/mempalace/guide/)
- Kept: Getting Started — likely source for install/init flow. (https://mempalace.github.io/mempalace/guide/getting-started.html)
- Kept: Mining — likely source for ingest/build workflow. (https://mempalace.github.io/mempalace/guide/mining.html)
- Kept: Searching — likely source for retrieval and smoke tests. (https://mempalace.github.io/mempalace/guide/searching.html)
- Kept: Local Models — likely source for machine-local/runtime caveats. (https://mempalace.github.io/mempalace/guide/local-models.html)
- Dropped: None — no secondary sources were accessible in this environment.

## Gaps
- Exact `pip install` package name is unverified.
- Exact behavior and file outputs of `mempalace init .` are unverified.
- Exact `plugin.json` and `hooks.json` schema is unverified.
- Exact definition and creation flow for a MemPalace `person` is unverified.
- Exact repo-local caveats from the official docs are unverified.

## Next step
Open the official pages above and replace the placeholders in this brief with:
- the exact install command
- the exact init command/output
- the literal `plugin.json` and `hooks.json` examples
- the exact command/workflow to create a `person`
- any documented `.gitignore` or local-model guidance
