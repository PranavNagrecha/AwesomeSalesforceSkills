# Gotchas — sf CLI Plugin Authoring

Non-obvious behaviors that bite real plugin authors.

## Gotcha 1: `console.log` corrupts `--json` output

**What happens:** A plugin command invoked with `--json` returns malformed output. Pipeline parsers fail with `Unexpected token`. The malformed bytes look like the plugin's debug `console.log('value=', x)` interleaved with a JSON envelope.

**When it occurs:** Any time the command body or a transitive dependency writes to stdout outside the `SfCommand` logging API. Common offenders: HTTP libraries with debug=true, crypto libraries logging key material in dev, custom logger imports.

**How to avoid:** Use `this.log()`, `this.warn()`, `this.error()` exclusively. They are buffered and silenced when `--json` is set. Audit transitive dependencies — set `process.env.DEBUG = ''` at the top of `run()` if a noisy library can't be tamed otherwise. In CI, run `sf <topic> <command> --json | jq .` as a smoke test in your release pipeline; jq fails loudly on malformed JSON.

---

## Gotcha 2: `process.exit(N)` emits empty stdout in `--json` mode

**What happens:** A pipeline calls `sf myco do-thing --json`, expects a JSON envelope, and receives zero bytes followed by exit code N. Subsequent steps that parse the output break with "no input" errors.

**When it occurs:** Anywhere `process.exit()` is called inside `run()` or inside async work spawned from `run()`. The `SfCommand` envelope is written from a `finally`-style hook that doesn't fire when the process is hard-exited.

**How to avoid:** Replace `process.exit(1)` with `this.error('msg', { exit: 1 })` (writes a typed error envelope and exits non-zero) or `throw new SfError('msg')`. For success paths, return from `run()` — don't call `process.exit(0)`.

---

## Gotcha 3: `sf plugins link` runs compiled `lib/`, not `src/`

**What happens:** A developer changes a TypeScript source file, re-runs the linked command, and observes no behavior change. Hours of debugging follow.

**When it occurs:** After `sf plugins link <path>` was used to install the plugin from a local working copy. `sf plugins link` symlinks the package directory but the runtime entry (`bin/run.js`) imports compiled JavaScript from `lib/`, which is not auto-rebuilt on file change.

**How to avoid:** Run `npm run build -- --watch` (or `tsc --watch`) in a separate terminal during plugin development. Alternatively, develop using `./bin/dev.js <topic> <command> [flags]` — `bin/dev.js` registers `ts-node` so source files are transpiled on demand. Use `bin/run.js` only for testing the production code path.

---

## Gotcha 4: Topic separator default differs across `@oclif/core` versions

**What happens:** A plugin scaffolded from a stale template registers commands as `sf mytopic:mycommand` (colon-style) even though the team intended v2 space-style.

**When it occurs:** Templates pinned to old `@oclif/core` versions before the v2 default flip; `package.json` `oclif.topicSeparator` left unset.

**How to avoid:** Always set `"oclif": { "topicSeparator": " " }` explicitly in `package.json`, even though it's the v2 default. Verify with `sf <plugin-topic> --help` — if invocation requires `:` between segments, the config is wrong.

---

## Gotcha 5: `Flags.requiredOrg()` failure happens during flag parsing, not in `run()`

**What happens:** Tests that expect to catch a `NoAuthInfoFoundError` inside `run()` never see it; instead, the error bubbles up from `this.parse()`, often with a confusing stack trace that doesn't reference the test setup.

**When it occurs:** Whenever the user (or test harness) passes a target-org alias whose auth has been logged out or expired. Flag resolution invokes `Org.create(...)` which throws synchronously on missing auth.

**How to avoid:** Wrap the entire `this.parse(MyCommand)` line in test code with the error expectation, not just the inner logic. In production, surface the error with a `this.error(...)` call from a `prerun` hook if you need a more user-friendly message than the default.

---

## Gotcha 6: Unversioned `sf plugins install` in CI silently drifts

**What happens:** A pipeline that has run identically for months suddenly fails or produces different output after a Tuesday plugin release. Logs show no pipeline change.

**When it occurs:** CI runner setup includes `sf plugins install @scope/plugin` (no version) or `sf plugins install @scope/plugin@latest`. The pipeline always pulls the newest version on each run.

**How to avoid:** Pin every plugin version in CI: `sf plugins install @scope/plugin@1.4.0`. Pre-bake plugin installs into the runner image rather than installing on every job. Use `sf plugins inspect @scope/plugin` to verify the installed version at the start of a pipeline; fail fast if it's wrong.

---

## Gotcha 7: Hooks execute even for unrelated commands

**What happens:** A plugin registers a `prerun` hook for telemetry. Users of unrelated plugins (e.g., the official `salesforcecli/plugin-deploy-retrieve`) report 200ms slowdowns on every `sf project deploy start` invocation, even though they don't use the custom plugin's commands.

**When it occurs:** `prerun` hooks fire for every command in every plugin installed in the same `sf` runtime, not just commands from the registering plugin.

**How to avoid:** Gate hook logic on `Command.id.startsWith('myco ')` to short-circuit for commands outside your plugin. Keep all hooks under 50ms in the no-op path. If logic is unavoidable and slow, move it to `postrun` (after the user-visible command finished) or to an opt-in flag rather than a hook.

---

## Gotcha 8: Private-registry plugins fail silently in CI without auth

**What happens:** A pipeline step `sf myco do-thing` runs and emits `command not found`, exits non-zero, but the cause is an earlier `npm install -g @company/sf-plugin` step that failed silently because the runner's `~/.npmrc` didn't have the registry token.

**When it occurs:** First-time CI runner provisioning, after a registry token rotation, after a runner image rebuild that didn't bake in `.npmrc`.

**How to avoid:** Run `sf plugins inspect @company/sf-plugin` immediately after the install step. If it errors, the install failed — fail the pipeline now with a clear message rather than letting the missing-command error confuse downstream steps. Better: bake plugins into the runner image and verify at image-build time.

---

## Gotcha 9: `sf` does not auto-update plugins; consumers must run `sf plugins update`

**What happens:** A team ships a critical fix in plugin v1.4.1 and wonders why customer pipelines still hit the bug. Investigation reveals the customer runners installed v1.4.0 weeks ago and never updated.

**When it occurs:** Whenever a plugin uses `sf plugins install` with no version pin and the installer doesn't run `sf plugins update` periodically; or any time consumers pin to a specific version (the right approach for stability) and don't get told to bump.

**How to avoid:** Communicate releases with a clear "bump from X to Y" message. For breaking fixes, emit a `this.warn('this version has known issue; update to >=1.4.1')` from a `prerun` hook that checks `this.config.version` against a known-broken floor — yes, this means the broken version is responsible for warning about itself, but it still helps customers who haven't updated yet.
