# Multi-AI Parity Contract

**Status:** Wave 6 contract (partially ratified in Wave 2's manifest work; this doc declares the full parity guarantee).
**Enforced by:** [`mcp/sfskills-mcp/tests/test_export_parity.py`](../mcp/sfskills-mcp/tests/test_export_parity.py) + [`.github/workflows/pr-lint.yml`](../.github/workflows/pr-lint.yml) + [`scripts/export_skills.py --check`](../scripts/export_skills.py).

## Tier structure

SfSkills supports six AI-coding-assistant + AI-agent platforms. They are not all equal.

### First-class targets

Three platforms get a **strong parity guarantee**: the SET of skills available is identical across them; content is equivalent modulo wrapper format; every skill available in one is available in the other two.

- **Claude Code** (`--target claude`) — canonical SfSkills skill tree. Consumed by Claude natively via the `skills/` directory OR via the SfSkills MCP server.
- **Cursor** (`--target cursor`) — `.cursor/rules/*.mdc` format. Consumed by Cursor's rules engine.
- **MCP** (`--target mcp`) — same as Claude's skill tree + `registry/skills.json`. Consumed by any MCP-capable client (Claude Desktop, Cline, Continue, etc.) via the SfSkills MCP server.

### Second-class targets

Three platforms get a **best-effort subset guarantee**: every skill available in the first-class targets SHOULD be available here, but format-specific limitations may cause subset behavior.

- **Windsurf** (`--target windsurf`) — `.windsurf/rules/*.md` format.
- **Aider** (`--target aider`) — single `CONVENTIONS.md` concatenation. Cannot represent per-skill routing; skills compressed into one file.
- **Augment** (`--target augment`) — `.augment/rules/*.md` format.

### What parity means exactly

For first-class targets (claude + cursor + mcp):

1. **Set parity.** `registry/export_manifest.json` → `targets.claude.skills` has the same KEYS (skill IDs) as `targets.cursor.skills` and `targets.mcp.skills`. Enforced by `assert_first_class_parity()` in `scripts/export_skills.py`.
2. **Content fidelity.** Each skill's content is the same, modulo the per-target wrapper (Cursor adds `.mdc` frontmatter; MCP adds the registry JSON reference). The BODY of SKILL.md is byte-identical.
3. **Determinism.** Three consecutive exports produce byte-identical `registry/export_manifest.json` (ignoring `generated_at` timestamp). Enforced by `test_export_is_deterministic_across_three_runs`.

For second-class targets:

1. **Coverage-best-effort.** A skill that exists in first-class targets SHOULD be present in second-class targets. If format constraints (e.g. Aider's single-file model) force omission, the skill is still conceptually covered via the concatenated content — but the skill-id-key may not appear.
2. **No determinism guarantee on cross-target ordering.** Aider's CONVENTIONS.md section order is deterministic per-run but not semantically meaningful.

## How the contract is enforced

### At author time

Authors of new skills and agents don't have to think about multi-AI parity. The export pipeline handles it mechanically:

```bash
python3 scripts/skill_sync.py --all         # Rebuild registry + index
python3 scripts/export_skills.py --all --manifest   # Rebuild exports + manifest
python3 scripts/export_skills.py --check    # Assert tree matches committed manifest
```

The pre-commit hook runs `validate_repo.py --changed-only` which covers per-skill structure + drift. Manifest check is NOT in pre-commit (too slow); it's in PR CI instead.

### At PR time

[`.github/workflows/pr-lint.yml`](../.github/workflows/pr-lint.yml) runs:

1. `python3 scripts/export_skills.py --check` — fails if the PR's tree would produce a different manifest than what's committed.
2. `python3 -m unittest tests.test_export_parity` — runs the 4 parity assertions.

If either fails, the PR is blocked.

### At release time

Release tags (`v1.x`, `v2.x`) are cut from main. Each release's manifest is captured in `registry/export_manifest.json` at that tag. Consumers can pin to a tag for stable skill IDs.

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
```

Each `.mdc` file has YAML frontmatter (`description:` + `alwaysApply: false`) and the SKILL.md body + references concatenated.

Cursor's rules engine auto-activates relevant rules based on the description + file context. The format does NOT carry skill metadata (version, pillars, tags) beyond the description.

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

The extra `registry/skills.json` lets an MCP server serve `search_skill` and `get_skill` tools against this bundle without rebuilding state from the raw tree. Use this target when distributing SfSkills as a standalone MCP-accessible knowledge base.

### Windsurf (`exports/windsurf/`)

Similar to Cursor but in Windsurf's `.windsurf/rules/*.md` format:

```
exports/windsurf/
  .windsurf/
    rules/
      apex-trigger-framework.md
      ...
```

Frontmatter: `description`, `triggers` (array).

### Aider (`exports/aider/`)

Single-file concatenation:

```
exports/aider/
  CONVENTIONS.md   # ~10 MB of all skills concatenated by domain
```

Aider's model treats conventions as one large context. No per-skill activation; the whole file is provided on every Aider invocation. This works for small skill libraries but produces context-pressure on a 686-skill library. Use with a narrow `--domain` filter when invoking export for Aider in a specific project.

### Augment (`exports/augment/`)

Similar to Cursor in layout; Augment's `.augment/rules/*.md` format.

## Regenerating exports locally

Consumers regenerate whenever they upgrade SfSkills:

```bash
git pull
python3 scripts/export_skills.py --target cursor   # or whichever target
# Copy the generated exports/<target>/ into your project
```

`exports/` is gitignored (~130 MB for all six targets) so each consumer builds their own. The committed `registry/export_manifest.json` guarantees the build is reproducible.

## Version-compatibility commitments

### What's guaranteed stable across minor versions

- Skill IDs (`<domain>/<slug>`) — once published, never renamed within a major version.
- Finding codes (`VR_MISSING_BYPASS`, `PICKLIST_NO_GVS`, etc.) — stable across runs within a major version.
- MCP tool names (`search_skill`, `get_skill`, `probe_apex_references`, etc.) — stable across minor versions.
- Agent IDs in `list_agents()` — stable, except for the documented deprecation window.

### What changes between minor versions

- Skill CONTENT may evolve (new examples, updated gotchas, tightened rules). Content hashes in the manifest will change.
- New skills added; new agents added.
- Skills may move to `status: beta` or `status: deprecated` with documented replacement.
- Finding codes may be added (never removed within a major version except via the `_V2` suffix + deprecation pattern).

### What changes between major versions

- Deprecated agents removed (per [`docs/MIGRATION.md`](./MIGRATION.md) timeline).
- Schema breaking changes possible (flagged in CHANGELOG.md with explicit migration steps).
- Finding codes with `_V2` suffixes become canonical; pre-V2 codes removed.

## For second-class platforms: how to get first-class treatment

If a currently-second-class platform wants to become first-class:

1. Propose a `.mdc`-style wrapper format that preserves skill metadata.
2. Demonstrate deterministic export (3-run test passes).
3. Demonstrate set-parity test feasibility (can be added to the export_parity test).
4. Submit a PR with:
   - New exporter function in `scripts/export_skills.py`.
   - Extension of `FIRST_CLASS_TARGETS` in the same file.
   - Updated tests asserting set parity for the new target.
   - Doc update in this file.

Reviewer gate: maintainer sign-off + green CI.

## CI matrix (Wave 6)

The PR-lint workflow runs on:
- Ubuntu 24.04 (primary target for Python validation)
- (Matrix expansion candidate: macOS latest — adds coverage for dev-machine parity)

Export determinism is verified on Ubuntu. If macOS produces different hashes, that's a bug — the `stable_hash_for_files` fix (Wave 1.1 hotfix commit `09ef622`) made the hash path-independent, so cross-OS drift should not recur.

## FAQ

### Why Apache 2.0 license instead of MIT?

Apache 2.0 grants a patent license alongside the copyright grant, which protects corporate consumers from patent-assertion attacks. MIT doesn't. Given SfSkills is consumed inside enterprise Salesforce work, Apache 2.0 is the more defensive choice.

### What if I want to ship SfSkills as part of a commercial product?

Apache 2.0 allows that. Include the license, attribution, and any changes you made — details in [LICENSE](../LICENSE).

### Can I rename skills in my fork?

Yes, but understand that:
- Finding codes are tied to skill IDs in some cases.
- Upstream consumers of your fork lose the ability to point at upstream docs.
- Merging upstream changes becomes hard.

Prefer namespacing (`mycompany_<domain>/<slug>`) to renaming. Better yet: propose the rename upstream.

### Does parity work if I have network-restricted Salesforce org?

Yes. SfSkills' MCP tools use `sf` CLI, not direct API calls. If your `sf` CLI works, the MCP tools work. Skills themselves are offline content.

### What happens if a test fails in CI after a manifest commit?

The PR that caused the failure is blocked. Three typical resolutions:
1. The manifest is stale — run `python3 scripts/export_skills.py --all --manifest` locally + commit the regenerated manifest.
2. The change broke determinism — investigate `scripts/export_skills.py` for non-deterministic ordering or timestamp leaks.
3. The change broke set parity (a skill exists in claude but not cursor) — debug the specific exporter.

## See also

- [LICENSE](../LICENSE) — Apache 2.0.
- [MIGRATION.md](./MIGRATION.md) — deprecation timeline + retired-agent mapping.
- [CONTRIBUTING.md](../CONTRIBUTING.md) — how to contribute skills + agents.
- [SECURITY.md](../SECURITY.md) — disclosure process.
- [CHANGELOG.md](../CHANGELOG.md) — release notes.
- [`registry/export_manifest.json`](../registry/export_manifest.json) — the canonical baseline this doc's contract diff against.
