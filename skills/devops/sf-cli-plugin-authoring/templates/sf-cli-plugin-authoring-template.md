# sf CLI Plugin Authoring — Work Template

Use this template when scaffolding, refactoring, or migrating a Salesforce CLI (`sf`) plugin.

## Scope

**Skill:** `devops/sf-cli-plugin-authoring`

**Request summary:** (fill in what the user asked for — e.g., "scaffold a new internal plugin", "migrate sfdx plugin to v2", "audit existing plugin for --json safety")

---

## Context Gathered

Answer these before starting work:

- **Plugin purpose:** [ ] internal team tooling   [ ] ISV/external distribution   [ ] migration of existing sfdx plugin   [ ] other: ____________
- **Distribution channel:** [ ] public npm   [ ] private registry (which: ____________)   [ ] `sf plugins link` only (local dev)
- **Org-flag posture:** [ ] requires authenticated org (`Flags.requiredOrg`)   [ ] requires Dev Hub (`Flags.requiredHub`)   [ ] org-less (no org flag)
- **JSON contract consumers:** [ ] CI pipelines parse `--json` output   [ ] Human-only consumption (CLI users only)
- **Existing sfdx command names to preserve as deprecation aliases:** ____________ (or N/A)
- **Plugin-internal commands count (estimated):** _______ commands across _______ topics

---

## Approach

Pick the pattern from SKILL.md that applies and note the choice:

- [ ] Pattern 1 — Wrapping a stock `sf` command with org-aware logic
- [ ] Pattern 2 — Migrating sfdx → sf with deprecation aliases
- [ ] Pattern 3 — Distributing a private internal plugin
- [ ] New pattern (document below)

**Why this pattern:** ____________

---

## Implementation Checklist

### Scaffold

- [ ] Generated from `plugin-template-sf` (internal) or `plugin-template-sf-external` (ISV) via `sf dev generate plugin --name <name>`
- [ ] `package.json` `oclif.topicSeparator` is `" "` (space, v2 style)
- [ ] `package.json` lists `@salesforce/sf-plugins-core` as a dependency
- [ ] `bin/dev.js` and `bin/run.js` exist and are executable

### Per command

- [ ] Class extends `SfCommand<TypedResult>` — typed, never `any`
- [ ] `summary`, `description`, `examples` sourced from `messages/<command>.md`
- [ ] Flags use factory functions (`Flags.string`, `Flags.requiredOrg`, etc.) — no hand-parsing of `process.argv`
- [ ] No `console.log` / `console.error` / `console.warn` calls — use `this.log` / `this.warn` / `this.error`
- [ ] No `process.exit()` — use `this.error('msg', { exit: N })` or throw `SfError`
- [ ] If migrating from sfdx: `aliases` array set + `deprecateAliases = true`
- [ ] At least one NUT test (`test/commands/<topic>/<command>.nut.ts`) covering success and one failure path

### Hooks (only if needed)

- [ ] Hook completes in <50ms in the no-op path
- [ ] Hook is idempotent (safe to re-run)
- [ ] Hook is gated on `Command.id.startsWith('<plugin-topic> ')` if logic is plugin-specific

### Distribution

- [ ] README documents the JSON contract for every command (every `Result` field with stability note)
- [ ] README documents the install command, version-pinned: `sf plugins install @scope/plugin@1.0.0`
- [ ] CI runner image (if applicable) bakes in plugin install with pinned version
- [ ] `sf plugins inspect @scope/plugin` runs in CI to verify install before any plugin command is invoked

### Validation

- [ ] `python3 skills/devops/sf-cli-plugin-authoring/scripts/check_sf_cli_plugin_authoring.py --plugin-root <path>` exits 0
- [ ] `sf <topic> <command> --json | jq .` parses without error against a happy-path invocation
- [ ] `sf plugins inspect <name>` shows the expected version

---

## Notes

Record deviations from the standard pattern and why:

____________
