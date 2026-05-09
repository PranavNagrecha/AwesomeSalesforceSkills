# Well-Architected Notes — sf CLI Plugin Authoring

## Relevant Pillars

- **Operational Excellence** — A custom CLI plugin is operational glue: the JSON contract is the operational contract for every pipeline that consumes the plugin. Stable shapes, semver discipline, and pinned versions in CI runners are operational-excellence concerns. Plugins that drift in JSON shape between minor versions fracture the operational story for every consumer at once.
- **Reliability** — Plugins fail in two reliability-relevant ways: silently (a hook crashes and breaks unrelated commands; `console.log` corrupts `--json`) and loudly with bad UX (`process.exit()` skips the JSON envelope, confusing parsers). Reliability work for a plugin is mostly about staying inside the `SfCommand` contract — not inventing shortcuts that break the wrapper.
- **Security** — A plugin runs with the user's local privileges and ambient auth. Hooks execute on every `sf` invocation, so a malicious or careless prerun hook is a privilege escalation surface. Distribution channels matter: signed plugins (Salesforce-signed for AppExchange-adjacent listings) plus version pinning are the reasonable bar.

## Architectural Tradeoffs

**Plugin vs. shell script.** A plugin earns its weight only when (a) the same logic is invoked from many pipelines and benefits from a single update path, (b) the JSON contract is part of the public surface, or (c) ISV distribution is the goal. For ad-hoc team automation, a script is cheaper and clearer. The architectural smell is a one-off command wrapped as a plugin to look "more official."

**Public npm vs. private registry.** Public npm (or Salesforce-signed distribution) maximizes reach and trust but commits the team to release engineering hygiene — semver discipline, deprecation cycles, security disclosures. Private registries (Artifactory, GitHub Packages) keep the surface small but require every CI runner image to embed registry auth. For internal-only tools, private is almost always right; resist the urge to publish for vanity.

**Hooks vs. command logic.** Logic placed in a `prerun` hook runs for every `sf` command on the runner, not just the plugin's own commands. This is convenient ("validate environment once") but couples your plugin to the entire `sf` runtime. The architecturally honest pattern is logic inside command classes; hooks are reserved for environment-wide concerns (telemetry, license checks, deprecation warnings) where pan-command coverage is the actual requirement.

**Aliases vs. clean break on migration.** Holding `sfdx`-style aliases with `deprecateAliases: true` is friendly to consumers but doubles the surface area you must test. A clean break is faster but breaks every consumer's CI on the upgrade. The safe default is one major-version cycle of dual support, then drop.

**Versioning the JSON contract.** Every property on the `Result` type is a public contract. Changes follow semver: additions are minor, renames or removals are major. Practical implication: design the result type carefully on first release; shipping with a flat shape and adding fields later is fine; shipping with `{ data: { ... } }` and later wanting to flatten is a major-version event.

## Anti-Patterns

1. **One-off team automation wrapped as a plugin** — Three lines of bash that call `sf` are not a plugin. The plugin overhead (build pipeline, version management, registry installs) outweighs the benefit. Ship a script in the team's `scripts/` directory and revisit later.
2. **Returning untyped `any` from `run()`** — `SfCommand<any>` makes `--json` output unstable across releases without compiler help. Always declare a typed `Result`. If the result is genuinely heterogeneous, model it as a tagged union.
3. **Hand-parsing `process.argv`** — Bypasses the flag-factory machinery, breaks `--flags-dir`, breaks `--json`, breaks `--help`. There is no good reason to do this; if a flag factory doesn't model your shape, compose two simpler flags or use `Flags.custom()`.
4. **Slow `prerun` hooks** — A 200ms hook compounds across every `sf` command on the runner. The user perceives `sf` itself as slow. Hooks should complete in <50ms in the no-op path or be guarded by an opt-in flag.
5. **Unpinned plugin installs in CI** — `sf plugins install @scope/plugin` (no version) means the pipeline's behavior changes silently on plugin release. Always pin in CI; floating versions are for developer laptops, not pipelines.
6. **Calling `process.exit()` inside `run()`** — Bypasses the JSON envelope, emits zero bytes to stdout in `--json` mode, breaks every consumer that parses the output. Use `this.error('msg', { exit: 1 })` or throw `SfError`.

## Official Sources Used

- Salesforce CLI Reference — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference.htm — authoritative `sf` topic + flag list; the JSON envelope shape and `--json` semantics derive from the same plumbing this guide describes for stock commands.
- Salesforce DX Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_intro.htm — project layout, scratch-org and Dev Hub model relevant to choosing `Flags.requiredOrg()` vs. `Flags.requiredHub()` and to plugin tests run against scratch orgs.
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm — backstop reference when a plugin command exposes deploy/retrieve operations and needs to mirror the contract `sf project deploy start` already provides.
- `salesforcecli/cli` GitHub repository — https://github.com/forcedotcom/cli — the canonical `sf` CLI source, including the upstream of `@salesforce/sf-plugins-core` and the official plugin templates referenced from the Salesforce CLI tooling docs.
- oclif framework — https://oclif.io/docs/introduction — the framework `@salesforce/sf-plugins-core` extends; canonical reference for hook semantics, command lifecycle, and the `topicSeparator` configuration.
