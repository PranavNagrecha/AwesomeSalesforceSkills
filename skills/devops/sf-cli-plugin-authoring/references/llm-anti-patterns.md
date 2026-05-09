# LLM Anti-Patterns — sf CLI Plugin Authoring

Mistakes AI coding assistants make when generating or advising on `sf` CLI plugin code. Each entry shows the wrong pattern, why LLMs default to it, the correct approach, and a detection hint.

---

## Anti-Pattern 1: Generating colon-separated topic syntax for v2 commands

**What the LLM generates:**

```ts
// In package.json:
"oclif": {
  "commands": "./lib/commands",
  "topicSeparator": ":"
}

// And invocation examples in README:
sf myco:org:diff --source SourceOrg --target TargetOrg
```

**Why it happens:** Pre-2023 training data is dominated by `sfdx` examples. The colon separator was the default for `sfdx` and for early oclif versions. LLMs reproduce the pattern they have most examples of even when generating v2 plugin code.

**Correct pattern:**

```ts
// In package.json:
"oclif": {
  "commands": "./lib/commands",
  "topicSeparator": " "
}
```

```text
# Invocation
sf myco org diff --source SourceOrg --target TargetOrg
```

**Detection hint:** Grep generated `package.json` for `"topicSeparator": ":"` — wrong. Grep README and command examples for invocations like `sf foo:bar:baz` — also wrong (legacy aliasing fine in `aliases` arrays, but main invocation should use spaces).

---

## Anti-Pattern 2: Using `console.log` inside `run()` for status messages

**What the LLM generates:**

```ts
public async run(): Promise<MyResult> {
  console.log('Starting...');
  const result = await doWork();
  console.log(`Found ${result.length} records`);
  return { records: result };
}
```

**Why it happens:** `console.log` is the universal "print a message" reflex from Node.js training data. The LLM has not internalized that `SfCommand` provides its own logging API that integrates with `--json` mode.

**Correct pattern:**

```ts
public async run(): Promise<MyResult> {
  this.log('Starting...');
  const result = await doWork();
  this.log(`Found ${result.length} records`);
  return { records: result };
}
```

**Detection hint:** Grep the plugin's `src/` for `console.log`, `console.error`, `console.warn`. Any hits inside command class methods (other than during early bootstrap before SfCommand is loaded) are bugs that will break `--json` consumers.

---

## Anti-Pattern 3: Returning `any` or untyped result from `run()`

**What the LLM generates:**

```ts
export default class MyCommand extends SfCommand<any> {
  public async run() {
    return await fetchSomething();
  }
}
```

**Why it happens:** TypeScript's `any` is the lazy escape hatch. LLMs reach for it when the return shape isn't immediately obvious from a single example. The implications for the public JSON contract aren't visible in the local code.

**Correct pattern:**

```ts
export type MyCommandResult = {
  fetchedAt: string;
  items: Array<{ id: string; status: 'ready' | 'pending' }>;
};

export default class MyCommand extends SfCommand<MyCommandResult> {
  public async run(): Promise<MyCommandResult> {
    const items = await fetchSomething();
    return { fetchedAt: new Date().toISOString(), items };
  }
}
```

**Detection hint:** Grep for `extends SfCommand<any>` or `extends SfCommand<unknown>`. Either is a smell. Also flag `: Promise<any>` on `run()` return signatures. The typed result is the public JSON contract; missing types means the contract is undefined and will drift.

---

## Anti-Pattern 4: Suggesting `process.exit()` for error termination

**What the LLM generates:**

```ts
public async run(): Promise<MyResult> {
  const { flags } = await this.parse(MyCommand);
  if (!flags.input) {
    console.error('--input is required');
    process.exit(1);
  }
  // ...
}
```

**Why it happens:** Generic Node.js CLI tutorials use `process.exit()` as the canonical error-and-exit pattern. The LLM doesn't know that `SfCommand` wraps `run()` in a JSON envelope that depends on a clean return or a controlled error throw.

**Correct pattern:**

```ts
public async run(): Promise<MyResult> {
  const { flags } = await this.parse(MyCommand);
  if (!flags.input) {
    this.error('--input is required.', { exit: 1 });
  }
  // ...
}
```

If the flag is `required: true` in the flag definition, the framework rejects the missing input pre-run with a structured error — even better.

**Detection hint:** Grep generated plugin code for `process.exit(`. Any match inside `run()` (or async helpers reachable from `run()`) is a bug that produces empty stdout in `--json` mode.

---

## Anti-Pattern 5: Inventing flag types that don't exist on `Flags` factory

**What the LLM generates:**

```ts
public static readonly flags = {
  email: Flags.email({ required: true }),  // does not exist
  url: Flags.url({ required: true }),      // does not exist
  json: Flags.json({ required: true }),    // does not exist as a flag type (--json is reserved)
};
```

**Why it happens:** LLMs pattern-match from "lots of frameworks have `Flags.email()` or `Flags.url()`" without checking the actual `@salesforce/sf-plugins-core` API. The `--json` confusion specifically conflates the reserved framework-level `--json` flag with a user-defined JSON-input flag.

**Correct pattern:**

```ts
public static readonly flags = {
  // For email: use string with custom parse/validate
  email: Flags.string({
    required: true,
    parse: async (raw: string) => {
      if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(raw)) {
        throw new Error(`Invalid email: ${raw}`);
      }
      return raw;
    },
  }),
  // For URL: use Flags.url is NOT in sf-plugins-core; use string + URL constructor
  url: Flags.string({
    required: true,
    parse: async (raw: string) => {
      try { new URL(raw); return raw; } catch { throw new Error(`Invalid URL: ${raw}`); }
    },
  }),
  // For JSON file input: use Flags.file
  payload: Flags.file({ required: true, exists: true }),
};
```

The actual factories are: `string`, `boolean`, `integer`, `directory`, `file`, `salesforceId`, `duration`, `orgApiVersion`, `requiredOrg`, `optionalOrg`, `requiredHub`, `optionalHub`, plus `custom<T>({ parse })` for everything else.

**Detection hint:** Grep `Flags.<name>(` for any name not in the canonical list above. Especially watch for `Flags.email`, `Flags.url`, `Flags.password`, `Flags.json`, `Flags.regex` — none exist; `Flags.custom` is the right answer.

---

## Anti-Pattern 6: Conflating "CLI plugin" with "CPQ plugin" or "OmniStudio plugin"

**What the LLM generates:** When asked about "Salesforce plugin," the LLM returns CPQ price-rule plugin examples (`SBQQ.CalculatorPlugin` interface), or OmniStudio DataPack tooling, even when the question is unambiguously about `sf` CLI plugins.

**Why it happens:** "Plugin" is heavily overloaded in the Salesforce ecosystem. Training data conflates them; the LLM picks whichever has more examples in context.

**Correct pattern:** When the prompt mentions `sf`, `oclif`, `SfCommand`, `npm`, TypeScript, `package.json`, or CLI commands — the topic is CLI plugin authoring (this skill). When the prompt mentions CPQ, pricing, quote calculation, or `SBQQ`, route to `apex/cpq-apex-plugins`. When it mentions OmniStudio, DataPacks, or `vlocity_*`, route to `omnistudio/omnistudio-deployment-datapacks`.

**Detection hint:** Generated answer mentions `SBQQ__CustomScript__c`, `CalculatorPlugin`, `SBQQ.CustomScripts`, or `vlocity_*` in response to a CLI plugin question — wrong skill activated.
