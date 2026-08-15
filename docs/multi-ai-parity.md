# Multi-AI Parity Contract

**What this guarantees:** the same set of skills reaches Claude Code, Cursor and
any MCP client, with byte-identical `SKILL.md` bodies; five more targets get a
best-effort subset.

**Enforced by:**
[`mcp/sfskills-mcp/tests/test_export_parity.py`](../mcp/sfskills-mcp/tests/test_export_parity.py)
(4 assertions) +
[`scripts/export_skills.py --check`](../scripts/export_skills.py), run in
[`.github/workflows/pr-lint.yml`](../.github/workflows/pr-lint.yml) (job
`export-manifest-check`) and
[`.github/workflows/validate.yml`](../.github/workflows/validate.yml) (job
`export-parity-matrix`, Linux **and** macOS).

Verified against this checkout on 2026-08-15.

> **Known drift at time of writing.** `registry/export_manifest.json` records
> 1,007 skills per target while the corpus holds 1,027, and
> `python3 scripts/export_skills.py --check` currently exits non-zero with
> `+20 new skill(s)` on every target. The baseline needs regenerating with
> `python3 scripts/export_skills.py --all --manifest`. Nothing below is wrong
> about the *contract*; the committed baseline is simply behind the tree.

## Tier structure

SfSkills supports **eight** export targets, listed in `PLATFORMS`
(`scripts/export_skills.py:60`). They are not all equal.

### First-class targets

Three platforms get a **strong parity guarantee** — `FIRST_CLASS_TARGETS`
(`scripts/export_skills.py:61`). The SET of skills available is identical across
them; content is equivalent modulo wrapper format; every skill available in one
is available in the other two.

- **Claude Code** (`--target claude`) — canonical SfSkills skill tree. Consumed
  by Claude natively via the `skills/` directory OR via the SfSkills MCP server.
- **Cursor** (`--target cursor`) — `.cursor/rules/*.mdc` format. Consumed by
  Cursor's rules engine.
- **MCP** (`--target mcp`) — same as Claude's skill tree plus
  `registry/skills.json`. Consumed by any MCP-capable client (Claude Desktop,
  Cline, Continue, etc.) via the SfSkills MCP server.

### Second-class targets

Five platforms get a **best-effort subset guarantee**: every skill available in
the first-class targets SHOULD be available here, but format-specific limitations
may cause subset behavior.

- **Agents / cross-tool** (`--target agents`) — vendor-neutral
  `.agents/skills/<slug>/` flat tree per the emerging Agent Skills convention
  (Codex CLI reads it as its primary project path; Gemini CLI gives it
  precedence over `.gemini/skills/`; Cursor ≥2.4 discovers it). Content is the
  unmodified canonical SKILL.md package; slugs are globally unique so the flat
  layout is lossless. Companion installer:
  `python3 scripts/export_skills.py --install <project-dir>` writes this tree
  into a consuming project and symlinks each skill into `.claude/skills/`
  (`--copy` forces copies; `--force` replaces pre-existing directories this tool
  did not create). Pattern adapted, with attribution, from
  Clientell-Ai/salesforce-skills (Apache-2.0).
- **Windsurf** (`--target windsurf`) — `.windsurf/rules/*.md` plus
  `.windsurf/workflows/*.md` for slash commands. Workflows are capped at
  **12,000 characters** (`WINDSURF_WORKFLOW_MAX_CHARS`,
  `scripts/export_skills.py:85`); oversized commands are **skipped with a printed
  warning**, not truncated. Two of the 67 commands currently exceed it —
  `build-skills.md` (13,661 chars) and `onboard-source.md` (13,864).
- **Aider** (`--target aider`) — single `CONVENTIONS.md` concatenation. Cannot
  represent per-skill routing; skills are compressed into one file. Aider has no
  user-extensible slash surface (`SLASH_COMMAND_DEST["aider"] is None`), so
  `commands/*.md` land as a navigation index inside `CONVENTIONS.md` instead.
- **Augment** (`--target augment`) — `.augment/rules/*.md` +
  `.augment/commands/*.md`.
- **Codex CLI** (`--target codex`) — OpenAI Codex CLI. Codex scans only
  top-level Markdown in `~/.codex/prompts/`, at **user scope only** — it has no
  project-scope slash surface. The exporter therefore produces a staging tree
  (`codex-prompts/`, `codex-skills/`) plus an `INSTALL.md` carrying the `cp`
  commands.

### What parity means exactly

For first-class targets (claude + cursor + mcp):

1. **Set parity.** `registry/export_manifest.json` → `targets.claude.skills` has
   the same KEYS (skill IDs) as `targets.cursor.skills` and
   `targets.mcp.skills`. Enforced by `assert_first_class_parity()`
   (`scripts/export_skills.py:910`), called from both the `--manifest` and
   `--check` paths.
2. **Content fidelity.** Each skill's content is the same, modulo the per-target
   wrapper (Cursor adds `.mdc` frontmatter; MCP adds the registry JSON
   reference). The BODY of SKILL.md is byte-identical.
3. **Determinism.** Three consecutive exports produce byte-identical
   `registry/export_manifest.json` (ignoring the `generated_at` timestamp).
   Enforced by `test_export_is_deterministic_across_three_runs`.

For second-class targets:

1. **Coverage-best-effort.** A skill that exists in first-class targets SHOULD be
   present in second-class targets. If format constraints (e.g. Aider's
   single-file model) force omission, the skill is still conceptually covered via
   the concatenated content — but the skill-id key may not appear. The manifest
   makes this visible: `aider` records a `skill_count` of 1, because its only
   artifact is `CONVENTIONS.md`.
2. **No determinism guarantee on cross-target ordering.** Aider's
   `CONVENTIONS.md` section order is deterministic per-run but not semantically
   meaningful.

## How the contract is enforced

### At author time

Authors of new skills and agents don't have to think about multi-AI parity. The
export pipeline handles it mechanically:

```bash
python3 scripts/skill_sync.py --all                  # rebuild registry + index
python3 scripts/export_skills.py --all --manifest    # rebuild exports + manifest
python3 scripts/export_skills.py --check             # assert tree matches committed manifest
```

The pre-commit hook runs `validate_repo.py --changed-only`, which covers
per-skill structure and drift. The manifest check is NOT in pre-commit (too
slow); it runs in PR CI instead.

### At PR time

Two workflows gate it, and both must pass:

| workflow | job | steps |
|---|---|---|
| `pr-lint.yml` | `export-manifest-check` | `build_index.py` → `export_skills.py --check` → `unittest tests.test_export_parity` |
| `validate.yml` | `export-parity-matrix` (`ubuntu-latest` **and** `macos-latest`) | `build_index.py` → `export_skills.py --check` (cross-OS determinism) → `unittest tests.test_export_parity` |

Both invoke the tests with `working-directory: mcp/sfskills-mcp`, which is where
`test_export_parity.py` actually lives — there is no `tests/test_export_parity.py`
at the repo root. The four assertions are:

| test | asserts |
|---|---|
| `test_export_is_deterministic_across_three_runs` | three runs produce identical manifests |
| `test_first_class_targets_have_identical_skill_sets` | claude ≡ cursor ≡ mcp, by skill id |
| `test_manifest_has_expected_shape` | the manifest schema holds |
| `test_cli_check_mode_against_committed_manifest` | `--check` agrees with what is committed |

If either workflow fails, the PR is blocked.

### At release time

Release tags (`v1.x`, `v2.x`) are cut from main. Each release's manifest is
captured in `registry/export_manifest.json` at that tag. Consumers can pin to a
tag for stable skill IDs.

## Format-specific details

### Claude (`exports/claude/`)

Layout mirrors the source tree one-to-one:

```
exports/claude/
  INDEX.md
  skills/
    admin/
      custom-field-creation/
        SKILL.md
        references/
          examples.md
          gotchas.md
          well-architected.md
          llm-anti-patterns.md
        templates/...
        scripts/...
    apex/
      trigger-framework/
        SKILL.md
        ...
  .claude/commands/          # all 67 slash commands, mirrored
```

Claude Code and MCP clients read SKILL.md directly. No wrapper transformation.

### Cursor (`exports/cursor/`)

Skills flattened into `.cursor/rules/<domain>-<skill-name>.mdc`:

```
exports/cursor/
  .cursor/
    rules/
      INDEX.md
      apex-trigger-framework.mdc
      flow-fault-handling.mdc
      ...
    commands/                # the 67 slash commands, so they appear in Cursor's / menu
```

Each `.mdc` file has YAML frontmatter — `description:` (the skill description's
first sentence, hard-capped at 120 characters) and `alwaysApply: false` — over
the SKILL.md body with `gotchas.md` and `examples.md` appended.

Cursor's rules engine auto-activates relevant rules based on the description plus
file context. The format does NOT carry skill metadata (version, pillars, tags)
beyond the description.

### MCP (`exports/mcp/`)

Same layout as Claude, plus `registry/skills.json`:

```
exports/mcp/
  INDEX.md
  skills/
    <same as Claude>
  registry/
    skills.json
```

The extra `registry/skills.json` lets an MCP server serve `search_skill` and
`get_skill` against this bundle without rebuilding state from the raw tree. Use
this target when distributing SfSkills as a standalone MCP-accessible knowledge
base. Note that the bundle carries no `vector_index/` — that is gitignored and
built locally, so a bundle-only install is lexical-search-less until an index is
built. See [architecture.md](architecture.md).

### Per-agent bundles (`exports/agent-bundles/<agent-id>/`)

A separate exporter installs one agent into another project. Unlike the
target-wide exports above (which ship the whole skill library in a platform's
format), a per-agent bundle ships one `AGENT.md` plus only the files it declares
in its frontmatter `dependencies` block.

```bash
python3 scripts/export_agent_bundle.py --agent user-access-diff --rewrite-paths
python3 scripts/export_agent_bundle.py --all-runtime          # every active agent
```

See [`docs/installing-single-agents.md`](./installing-single-agents.md) for the
three supported install paths (MCP server, bundle drop-in, git subtree) and when
each applies.

**Why both exist:** the eight-platform exports under `exports/<target>/` are for
library-wide distribution. Per-agent bundles are for single-agent install — the
case where a team wants `user-access-diff` in their project without the other 75
agents (76 total: 48 active run-time, 14 build-time, 14 deprecated). The parity
contract applies to both surfaces: first-class targets get identical skill
content; agent bundles carry their declared dependencies with byte-for-byte
fidelity.

### Windsurf (`exports/windsurf/`)

```
exports/windsurf/
  .windsurf/
    rules/
      apex-trigger-framework.md
      ...
    workflows/               # slash commands, 12,000-char cap
```

Rule frontmatter: `description` (truncated at 200 characters) and `triggers` (up
to the skill's first three).

### Aider (`exports/aider/`)

Single-file concatenation:

```
exports/aider/
  CONVENTIONS.md   # every skill concatenated by domain, plus a command index
```

Aider's model treats conventions as one large context. There is no per-skill
activation; the whole file is provided on every Aider invocation. On the last
full local build `CONVENTIONS.md` measured **17 MB** — at 1,027 skills this is
context pressure, not a working configuration. Use a narrow `--domain` or
`--skill` filter when exporting for Aider in a specific project.

### Augment (`exports/augment/`)

`.augment/rules/*.md` for skills, `.augment/commands/*.md` for the 67 slash
commands.

## Regenerating exports locally

Consumers regenerate whenever they upgrade SfSkills:

```bash
git pull
python3 scripts/export_skills.py --target cursor   # or whichever target
# Copy the generated exports/<target>/ into your project
```

`exports/` is gitignored (`.gitignore:54`) so each consumer builds their own —
the last full local build of all eight targets measured **255 MB**
(`du -sh exports/`), and that figure scales with the corpus. The committed
`registry/export_manifest.json` is what makes the build reproducible.

## Version-compatibility commitments

### What's guaranteed stable across minor versions

- Skill IDs (`<domain>/<slug>`) — once published, never renamed within a major
  version.
- Finding codes (`VR_MISSING_BYPASS`, `PICKLIST_NO_GVS`, etc.) — stable across
  runs within a major version.
- MCP tool names (`search_skill`, `get_skill`, `probe_apex_references`, etc.) —
  stable across minor versions.
- Agent IDs in `list_agents()` — stable, except for the documented deprecation
  window.

### What changes between minor versions

- Skill CONTENT may evolve (new examples, updated gotchas, tightened rules).
  Content hashes in the manifest will change.
- New skills added; new agents added.
- Skills may move to `status: beta` or `status: deprecated` with a documented
  replacement.
- Finding codes may be added (never removed within a major version except via the
  `_V2` suffix + deprecation pattern).

### What changes between major versions

- Deprecated agents removed (per [`docs/MIGRATION.md`](./MIGRATION.md) timeline).
- Schema breaking changes possible (flagged in CHANGELOG.md with explicit
  migration steps).
- Finding codes with `_V2` suffixes become canonical; pre-V2 codes removed.

## For second-class platforms: how to get first-class treatment

If a currently-second-class platform wants to become first-class:

1. Propose a `.mdc`-style wrapper format that preserves skill metadata.
2. Demonstrate deterministic export (the 3-run test passes).
3. Demonstrate set-parity test feasibility (can be added to `test_export_parity`).
4. Submit a PR with:
   - New exporter function in `scripts/export_skills.py`.
   - Extension of `FIRST_CLASS_TARGETS` in the same file.
   - Updated tests asserting set parity for the new target.
   - A doc update here.

Reviewer gate: maintainer sign-off + green CI.

## CI matrix

Every workflow in this repo runs on `ubuntu-latest`; no job pins a specific
Ubuntu release. The only OS matrices are in `validate.yml`, on
`[ubuntu-latest, macos-latest]`:

- `validate-agents` — `validate_repo.py --agents` on both OSes.
- `export-parity-matrix` — `export_skills.py --check` on both OSes, which is the
  cross-OS determinism gate. `pr-lint.yml`'s `export-manifest-check` runs the
  same check on Linux only.

macOS-vs-Linux hash drift was a real failure once. The fix was
`pipelines/frontmatter.py::stable_hash_for_files` (`:56`), which since commit
`09ef62239` ("Wave 1.1 hotfix 3: make content_hash machine-independent") takes a
`root` and digests POSIX paths relative to it, instead of absolute paths that
differed between `/Users/…` and `/home/runner/…`.

## FAQ

### Why PolyForm Small Business instead of an open-source license?

SfSkills is source-available, not open source. Everything here is readable and
forkable, but free *use* is conditional: companies under 100 people and under
USD 1M in prior-year revenue pay nothing, and larger organisations need a
commercial licence. The intent is that individuals and small consultancies keep
full access while enterprise use funds the work.

Like Apache 2.0, PolyForm Small Business grants a patent licence alongside the
copyright grant, so that protection is not lost in the move. What is lost is OSI
approval — if an OSI-approved licence is a hard procurement requirement on your
side, this project will not satisfy it. See [`LICENSING.md`](../LICENSING.md).

### Can I ship SfSkills as part of a commercial product?

Only under a commercial licence. Embedding any part of SfSkills in a product or
service you distribute is outside the free grant regardless of your company's
size, because the free grant covers use "for the benefit of your company", not
redistribution inside something you sell. Email <pranav.nagrecha11@gmail.com>.

### We forked it under Apache-2.0 before the change. Where does that leave us?

Exactly where you were. The grant you received cannot be withdrawn, so the copy
you already have stays under Apache-2.0 forever, as do `sfskills-mcp` 0.4.6 and
0.4.7 from PyPI under MIT. The new licence governs releases from 2026-08-15
onward — pulling those is what brings you under it.

### Can I rename skills in my fork?

Yes, but understand that:

- Finding codes are tied to skill IDs in some cases.
- Upstream consumers of your fork lose the ability to point at upstream docs.
- Merging upstream changes becomes hard.

Prefer namespacing (`mycompany_<domain>/<slug>`) to renaming. Better yet: propose
the rename upstream.

### Does parity work with a network-restricted Salesforce org?

Yes. SfSkills' MCP org tools shell out to the `sf` CLI rather than calling the
API directly. If your `sf` CLI works, the MCP tools work. Skills themselves are
offline content.

### A parity test failed in CI after I committed. Now what?

The PR that caused the failure is blocked. Three typical resolutions:

1. **The manifest is stale** — run
   `python3 scripts/export_skills.py --all --manifest` locally and commit the
   regenerated manifest. This is the common case, and it is the state the tree
   is in as of this writing.
2. **The change broke determinism** — investigate `scripts/export_skills.py` for
   non-deterministic ordering or timestamp leaks.
3. **The change broke set parity** (a skill exists in claude but not cursor) —
   debug the specific exporter.

## See also

- [LICENSE](../LICENSE) — PolyForm Small Business 1.0.0 (source-available).
- [LICENSING.md](../LICENSING.md) — who uses it free, who needs to buy.
- [architecture.md](architecture.md) — what ships versus what has to be built locally.
- [MIGRATION.md](./MIGRATION.md) — deprecation timeline + retired-agent mapping.
- [CONTRIBUTING.md](../CONTRIBUTING.md) — how to contribute skills + agents.
- [SECURITY.md](../SECURITY.md) — disclosure process.
- [CHANGELOG.md](../CHANGELOG.md) — release notes.
- [`registry/export_manifest.json`](../registry/export_manifest.json) — the baseline this contract diffs against.
