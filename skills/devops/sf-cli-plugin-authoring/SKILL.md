---
name: sf-cli-plugin-authoring
description: "Use when authoring a custom Salesforce CLI (`sf`) plugin — internal team tooling that wraps deploy/test workflows, an ISV plugin distributed via npm, or migrating a legacy `sfdx`-style plugin to the v2 `sf` topic-and-command shape. Triggers: 'sf plugin generate', 'extend SfCommand class', 'oclif command structure', 'sf-plugins-core flags', 'topic separator sf v2', 'JSON output for plugin', 'plugin hooks prerun command_not_found', 'distribute internal sf plugin npm registry', 'sign Salesforce CLI plugin'. NOT for using existing `sf` plugins in CI automation (use `devops/salesforce-cli-automation`), CPQ price-rule plugins (use `apex/cpq-apex-plugins`), OmniStudio DataPack CLI usage (use `omnistudio/omnistudio-deployment-datapacks`), or generic JS/TS package publishing."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
  - Security
triggers:
  - "how do I scaffold a custom sf CLI plugin from the salesforcecli template"
  - "my plugin command works for sfdx but the v2 sf invocation prints unknown command"
  - "I need a plugin that takes a target-org flag and emits JSON for our CI pipeline"
  - "we want to ship an internal Salesforce CLI plugin from a private npm registry"
  - "how does an oclif prerun hook interact with the sf telemetry and JSON contract"
  - "what is the correct way to migrate an sfdx-namespaced plugin command to sf topic separators"
tags:
  - salesforce-cli
  - sf-cli-v2
  - oclif
  - sf-plugins-core
  - plugin-development
  - typescript
  - npm-distribution
  - cli-tooling
  - devops
inputs:
  - "Plugin purpose: internal team tooling, ISV distribution via AppExchange-adjacent listing, or migration of an existing sfdx-style plugin"
  - "Distribution channel: public npm, private npm registry (Artifactory/GitHub Packages), or `sf plugins link` for local-only use"
  - "Whether commands need an authenticated org (target-org flag), a target dev hub, or run org-less (utility commands)"
  - "Whether the plugin must compose with `--json` output for downstream pipeline parsing"
  - "Existing sfdx command names to preserve as deprecation aliases (if any)"
outputs:
  - "Plugin scaffold: `package.json` with oclif config, `src/commands/<topic>/<command>.ts` extending `SfCommand`, optional `src/hooks/`, `messages/<command>.md`, and a working `bin/dev` and `bin/run`"
  - "JSON-shape contract documentation: every typed return field with a stability note"
  - "Distribution runbook: build, publish, install, verify (`sf plugins inspect`)"
  - "Migration map for sfdx → sf command names with deprecation warnings"
  - "Test scaffold using `@oclif/test` or `nock` for Apex/REST callouts"
dependencies:
  - devops/salesforce-cli-automation
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-09
runtime_orphan: true
---

# sf CLI Plugin Authoring

Activate when a developer or platform team is building a **custom `sf` CLI plugin** — not consuming one. The deliverable is a TypeScript package whose `commands/` tree extends `SfCommand` from `@salesforce/sf-plugins-core`, exposes well-typed flags, emits a stable JSON shape under `--json`, and is distributable via `npm install`, `sf plugins install`, or `sf plugins link` for local development. This skill covers scaffold layout, the `SfCommand` lifecycle, flag patterns (`requiredOrg`, `requiredHub`, `string`, `directory`, `boolean`), JSON contracts, hooks, message catalogs, telemetry hand-off, signed-plugin distribution, and the two migration paths from sfdx-style plugins (colon-separated topics → space-separated, plus the v2 flag and behavior changes).

This skill is not for choosing a CI platform, debugging an existing third-party plugin, or scripting against the stock `sf` commands — those belong to `devops/salesforce-cli-automation`. It is also not for CPQ "plugin" interfaces (`apex/cpq-apex-plugins`) or OmniStudio DataPack tooling (`omnistudio/omnistudio-deployment-datapacks`), which share the word "plugin" but are unrelated technologies.

---

## Before Starting

Gather this context before any code is written:

- **Why a plugin and not a script?** A shell script that invokes stock `sf` commands is the right answer for one-off team automation. A plugin earns its weight when (a) the same logic is invoked from many pipelines and benefits from a single update path, (b) the JSON contract for callers needs to be stable across versions, (c) the workflow composes existing `sf` commands plus custom logic that benefits from typed flags and `--json` plumbing, or (d) it is being distributed to customers as part of an ISV offering. If none of those apply, write a script and stop here.
- **`sf` topic separator is a space, not a colon.** v2 commands look like `sf my topic my command`. The legacy `sfdx force:apex:test:run` style is colon-separated. A plugin authored for v2 must declare `topicSeparator: " "` in `package.json` `oclif.topics` configuration, and command files belong in nested directories matching the topic tree.
- **Stay on `@salesforce/sf-plugins-core`, not `@oclif/core` directly.** `SfCommand` extends `Command` from oclif but adds the JSON wrapper, telemetry hooks, prompt helpers (`this.confirm`, `this.prompt`), spinner integration, and the standard `--json` and `--flags-dir` behavior. Authoring directly against `@oclif/core` reinvents these — and breaks the JSON contract callers rely on.
- **Decide the org-flag posture up front.** A command that requires an authenticated org uses `Flags.requiredOrg()`. A command that targets a Dev Hub for scratch-org work uses `Flags.requiredHub()`. A utility command (e.g., a metadata transform that runs offline) declares no org flag. Mixing these midway through development requires re-templating the command class.
- **Plan the JSON contract before the human output.** `sf` invocations from CI parse `--json` output. Every property of the typed `Result` interface returned from `run()` becomes part of the public contract. Renaming or restructuring fields after release is a breaking change.

---

## Core Concepts

### Project layout from the template

The canonical scaffold is generated by `sf dev generate plugin` (which forks `salesforcecli/plugin-template-sf` for internal Salesforce-owned plugins or `plugin-template-sf-external` for community/ISV plugins). The result:

```text
my-plugin/
├── package.json              # oclif config, sf-plugins-core peer dep, scripts
├── bin/
│   ├── dev.js                # local dev runner (ts-node + register hooks)
│   └── run.js                # production runner (compiled JS)
├── messages/
│   └── mytopic.mycommand.md  # localizable summary, description, examples, errors
├── src/
│   ├── commands/
│   │   └── mytopic/
│   │       └── mycommand.ts  # the command class
│   └── hooks/                # optional prerun, postrun, command_not_found
├── test/
│   └── commands/
│       └── mytopic/
│           └── mycommand.nut.ts   # NUT (non-unit, end-to-end) tests
└── tsconfig.json
```

`messages/` is loaded by `Messages.loadMessages('my-plugin', 'mytopic.mycommand')`. Strings live in markdown headings (`# summary`, `# description`, `# examples`, `# flags.target-org.summary`) so translators and reviewers can find them without grepping code.

### `SfCommand` lifecycle

A minimal command:

```ts
import { Flags, SfCommand } from '@salesforce/sf-plugins-core';
import { Messages } from '@salesforce/core';

Messages.importMessagesDirectory(__dirname);
const messages = Messages.loadMessages('my-plugin', 'mytopic.mycommand');

export type MycommandResult = {
  recordsFound: number;
  ids: string[];
};

export default class Mycommand extends SfCommand<MycommandResult> {
  public static readonly summary = messages.getMessage('summary');
  public static readonly description = messages.getMessage('description');
  public static readonly examples = messages.getMessages('examples');

  public static readonly flags = {
    'target-org': Flags.requiredOrg(),
    name: Flags.string({
      summary: messages.getMessage('flags.name.summary'),
      char: 'n',
      required: true,
    }),
  };

  public async run(): Promise<MycommandResult> {
    const { flags } = await this.parse(Mycommand);
    const conn = flags['target-org'].getConnection();
    const result = await conn.query<{ Id: string }>(
      `SELECT Id FROM Account WHERE Name LIKE '${flags.name}%' LIMIT 200`
    );
    this.log(`Found ${result.totalSize} records.`);
    return { recordsFound: result.totalSize, ids: result.records.map(r => r.Id) };
  }
}
```

Key behaviors:

- The generic parameter `<MycommandResult>` is what `--json` emits under the `result` key. Always type it.
- `this.parse(Mycommand)` returns flags and args parsed against the static schema. Do not access `this.argv` directly.
- `this.log()`, `this.warn()`, `this.error()` are buffered. In `--json` mode they are suppressed and replaced by structured fields. Never `console.log()` directly — it leaks into the JSON stream and breaks parsers.
- The return value of `run()` becomes the `result` field in `--json` output. The wrapping object also includes `status`, `warnings`, and (on failure) `name`, `message`, `stack`, `actions`.

### Flag patterns

`@salesforce/sf-plugins-core` provides flag factories that wrap oclif's primitives with sf-specific validation and the standard `--flags-dir` machinery:

| Flag | When to use | Behavior |
|---|---|---|
| `Flags.requiredOrg()` | Command targets a single authenticated org | Resolves to an `Org` instance; respects `--target-org` alias, `target-org` config, and `SF_TARGET_ORG` env |
| `Flags.optionalOrg()` | Org is sometimes needed (e.g., a transform that can either read from disk or from an org) | Same resolution, but undefined if not provided |
| `Flags.requiredHub()` | Command targets a Dev Hub (scratch-org work) | Resolves to a `Org` instance; respects `--target-dev-hub` alias |
| `Flags.string({ ... })` | String input | Adds `summary`, `char` shortcut, `required`, validation |
| `Flags.boolean({ ... })` | Toggle | `--flag` / `--no-flag` |
| `Flags.directory({ exists: true })` | Path to existing directory | Validates existence pre-run |
| `Flags.file({ exists: true })` | Path to existing file | Same |
| `Flags.integer({ min, max })` | Numeric input with bounds | Validates range pre-run |
| `Flags.salesforceId({ length: 18 })` | sObject Id input | Validates 15/18-char Id format |
| `Flags.duration({ unit: 'minutes' })` | Wait/timeout flags | Returns a `Duration` object with helpful arithmetic |
| `Flags.orgApiVersion()` | API version override | Validates against the org's supported versions |

Avoid hand-rolling validation in `run()` — pre-run flag validation produces cleaner error messages with suggested actions, and works correctly in `--json` mode.

### JSON contract and `--json` semantics

The wrapper around `run()`'s return value is fixed:

```json
{
  "status": 0,
  "result": {
    "recordsFound": 12,
    "ids": ["001...", "001..."]
  },
  "warnings": []
}
```

On error (any uncaught throw or `this.error(...)` call):

```json
{
  "status": 1,
  "name": "MissingNameError",
  "message": "The --name flag is required.",
  "exitCode": 1,
  "stack": "..."
}
```

Treat the `result` shape as a public API. Add fields freely; rename or restructure only on a major version bump and after deprecation warnings emitted via `this.warn(messages.getMessage('warning.deprecated-shape'))`. The `status` field is `0` on success, `1` on caught error, `2` on uncaught — do not invent your own status codes.

### Hooks

Hooks are functions that run at well-defined lifecycle points. The most useful for sf plugins:

- `prerun` — receives `{ Command, argv, config }`; runs before every command (yours or another plugin's, depending on registration scope). Used for licence checks, environment validation, telemetry.
- `postrun` — receives `{ Command, result, argv, config }`; runs after every command. Used for cleanup or success telemetry.
- `command_not_found` — runs when no command matches. Used to suggest similar commands; respect this hook rather than reinventing fuzzy-match.

Register in `package.json`:

```json
{
  "oclif": {
    "hooks": {
      "prerun": "./lib/hooks/prerun"
    }
  }
}
```

Hooks should be **idempotent and fast**. A 200ms hook compounds across every command in CI.

---

## Common Patterns

### Pattern 1 — Wrapping a stock `sf` command with org-aware logic

**When to use:** Internal tooling that pre-validates org state (e.g., "before deploy, ensure no test classes are missing `@isTest`"), then delegates to `sf project deploy start`.

**How it works:** Implement the command, run validation against the org via `flags['target-org'].getConnection()`, and shell out to `sf` for the actual deploy with `child_process.execFile` capturing JSON. Re-emit a merged result containing your validation summary plus the deploy outcome.

```ts
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const exec = promisify(execFile);

const { stdout } = await exec('sf', ['project', 'deploy', 'start', '--json', '--target-org', flags['target-org'].getUsername()!]);
const deployResult = JSON.parse(stdout);
return { validationFindings: findings, deploy: deployResult.result };
```

**Why not the alternative:** A bash wrapper script can't return a typed JSON contract; downstream pipelines parse plain stdout and break on warning messages.

### Pattern 2 — Migrating an `sfdx` plugin to `sf` v2 with deprecation aliases

**When to use:** An ISV or internal plugin currently exposes `sfdx mytopic:mycommand`; consumers' CI scripts will break if the legacy name is removed wholesale.

**How it works:** In v2, command files live at `src/commands/mytopic/mycommand.ts`, invoked as `sf mytopic mycommand`. Add an alias entry to the command class:

```ts
public static readonly aliases = ['mytopic:mycommand'];
public static readonly deprecateAliases = true;
```

`deprecateAliases: true` emits a deprecation warning when the colon-style invocation is used, prompting consumers to migrate. Hold the alias for at least one major version. Document both spellings in `examples` so search hits match either.

### Pattern 3 — Distributing a private internal plugin

**When to use:** A platform team builds a plugin used only inside the organization; publishing to public npm is not appropriate.

**How it works:** Publish to a private registry (Artifactory, GitHub Packages, AWS CodeArtifact). In CI runner setup, configure `~/.npmrc` with the registry URL and auth token, then `sf plugins install @company/sf-plugin-name@1.4.0`. Pin the version — the CI image must have a deterministic plugin set.

For developer machines, prefer `sf plugins link <local-path>` during plugin development; this symlinks the working copy and avoids the install/uninstall churn while iterating.

**Why not the alternative:** Distributing the plugin via `git clone` plus `npm install` works locally but skips the `sf plugins` registry step that allows `sf plugins inspect` and unloading on conflict.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| One-off team automation that just calls stock `sf` commands | Bash or Node script, not a plugin | Plugin overhead unjustified; no stable JSON contract needed |
| Repeated logic invoked from 3+ pipelines with typed JSON | Plugin extending `SfCommand` | Single update path, JSON contract stays stable |
| Needs to authenticate against a target org | `Flags.requiredOrg()` | Honors aliases, env vars, and config; consistent UX with stock commands |
| Targets a Dev Hub (scratch-org work) | `Flags.requiredHub()` | Distinct flag; clearer error when wrong org type used |
| ISV plugin distributed via AppExchange-adjacent npm | `plugin-template-sf-external` template | Includes signing, lint config, release workflow tuned for external consumers |
| Internal Salesforce-team plugin | `plugin-template-sf` (Salesforce-internal template) | Includes Salesforce-specific test infrastructure |
| Migrating from `sfdx` topic naming | Add `aliases` + `deprecateAliases: true` | Consumers transition gradually with warnings |
| Need to run logic before every command | `prerun` hook | Standard oclif lifecycle; respects `--json` mode |
| Need to react when no command matches | `command_not_found` hook | Better UX than silent failure |

---

## Recommended Workflow

1. Confirm a plugin is the right answer (see *Before Starting*); if a script suffices, write a script and stop.
2. Choose the template: `plugin-template-sf-external` for ISV/community plugins, `plugin-template-sf` for Salesforce-internal. Generate the scaffold with `sf dev generate plugin --name <plugin-name>`.
3. Decide the topic tree before writing code; the directory structure under `src/commands/` mirrors the runtime topic tree (`mytopic/mycommand.ts` becomes `sf mytopic mycommand`).
4. Write the JSON result type first — `type CommandResult = { ... }` — and treat it as the public contract from day one.
5. Implement the command class extending `SfCommand<CommandResult>`. Use `Flags.requiredOrg()` / `Flags.requiredHub()` / `Flags.string()` rather than parsing manually.
6. Write the messages markdown file (`messages/<command>.md`) for `summary`, `description`, `examples`, and any flag summaries.
7. Add at least one NUT test (`test/commands/<topic>/<command>.nut.ts`) that runs the real command end-to-end against a scratch org or mocked HTTP responses (`nock` for callouts).
8. Locally link the plugin with `sf plugins link .` and exercise both human and `--json` output. Verify `--json` output against the typed contract.
9. Update the README with the JSON shape spec and any required org permissions.
10. Publish (private or public registry); consumers install with `sf plugins install <name>@<version>`. Document the install line in the README.

---

## Review Checklist

Run through these before merging plugin changes:

- [ ] Every command class declares `<ResultType>` on `SfCommand<ResultType>` — no `any` or unparameterized returns.
- [ ] No `console.log` / `console.error` calls — use `this.log` / `this.warn` / `this.error` so `--json` mode stays clean.
- [ ] Every flag has a `summary` (and a `description` if behavior is non-obvious) sourced from the `messages/` catalog.
- [ ] The JSON return shape is documented in the README and unchanged from the previous patch version.
- [ ] If migrating from `sfdx`, command-level `aliases` array is set and `deprecateAliases: true` so consumers see a warning.
- [ ] At least one NUT test exercises the command; if the command makes HTTP callouts, they're mocked with `nock`.
- [ ] The plugin's `package.json` `oclif.topicSeparator` is `" "` (space), not `:` — v2 default.
- [ ] Hooks (if any) are idempotent and complete in <100ms or guarded by a feature flag.
- [ ] Private-registry plugins pin the version in CI runners; public-registry plugins follow semver discipline.

---

## Salesforce-Specific Gotchas

Non-obvious behaviors that bite real plugin authors:

1. **`console.log` from inside `run()` corrupts `--json` output.** A stray `console.log('debug')` is interleaved with the JSON envelope; downstream JSON parsers fail with `Unexpected token`. Use `this.log()` exclusively — it's suppressed in `--json` mode by `SfCommand`. The same trap fires for libraries that log to stdout (some crypto libraries, some HTTP clients in debug mode); audit transitive dependencies.
2. **`Flags.requiredOrg()` resolves the org before `run()` executes.** If the user has stale auth (`sf org logout` after token expiry) the failure happens during flag parsing, not in `run()`. Catch this in NUT tests by setting up a deliberately-stale auth and asserting the right error path. The error message is `NoAuthInfoFoundError`, not a generic auth failure.
3. **Plugin install order affects `command_not_found` hook resolution.** If two plugins register the same hook, the order is alphabetical by plugin name, not install order. Don't rely on "last installed wins" — that's an oclif core, not sf, behavior.
4. **`sf plugins link` does NOT recompile TypeScript on save.** The linked plugin runs from `lib/` (the compiled output), not `src/`. Either run `npm run build --watch` in a separate terminal or use `bin/dev.js` (which uses ts-node) for live iteration. Many "my changes aren't taking effect" reports trace to this.
5. **`oclif.topicSeparator` defaults to `:` in older `@oclif/core` versions.** A scaffold generated from a stale template will produce `sf mytopic:mycommand` and break v2 consumers. Confirm `package.json` sets `topicSeparator: " "` explicitly, even though it's the v2 default.
6. **Private npm registries need explicit auth in the CI runner image, not just the developer's `~/.npmrc`.** The runner's `npm install -g @scope/plugin` will silently fail if the registry token isn't configured; the failure surfaces only when the plugin's command is invoked and `command_not_found` fires. Pre-warm with `sf plugins install <name>` in the image build, not just in the pipeline step.
7. **`SfCommand` swallows `process.exit()` calls in `--json` mode.** Calling `process.exit(1)` inside `run()` bypasses the JSON envelope and emits an empty stdout — pipeline parsers receive zero bytes. Throw a typed error or call `this.error('msg', { exit: 1 })` instead; both go through the JSON wrapper.
8. **Version pinning in CI runner images vs. plugin install commands.** `sf plugins install @scope/plugin` (no version) installs latest; in CI this means a release on Tuesday silently changes pipeline behavior on Wednesday. Always pin: `sf plugins install @scope/plugin@1.4.0`.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Plugin scaffold | `package.json` + `src/commands/<topic>/<command>.ts` + `messages/<command>.md` + `bin/run.js` + `bin/dev.js` |
| JSON contract documentation | README section listing every field in the typed `Result`, with stability notes |
| NUT test | `test/commands/<topic>/<command>.nut.ts` exercising at minimum the success and one failure path |
| Migration map | If migrating from sfdx: table of `sfdx topic:command` → `sf topic command`, with deprecation timeline |
| Distribution runbook | Build, publish (registry-specific), install (`sf plugins install`), verify (`sf plugins inspect`) |

---

## Related Skills

- devops/salesforce-cli-automation — for consuming `sf` (including custom plugins) inside CI scripts
- apex/sf-cli-and-sfdx-essentials — foundational `sf` daily-use command coverage
- devops/salesforce-dx-project-structure — project layout the plugin's commands typically operate against
- devops/salesforce-code-analyzer — model for an officially-maintained sf plugin (good reference reading)
