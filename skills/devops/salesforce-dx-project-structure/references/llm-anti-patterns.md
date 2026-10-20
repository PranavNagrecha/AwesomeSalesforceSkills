# LLM Anti-Patterns — Salesforce DX Project Structure

Common mistakes AI coding assistants make when generating or advising on Salesforce DX project configuration.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Omitting the default Flag from packageDirectories

**What the LLM generates:** A `packageDirectories` array where no entry has `"default": true`.

```json
{
  "packageDirectories": [
    { "path": "force-app" }
  ]
}
```

**Why it happens:** The guide says that with one path "we assume it's the default, so you don't have to explicitly set the default parameter"; with several you must indicate it (sfdx_dev 264 L2363-2364). A model that always demands the flag is over-correcting; a model that omits it from a multi-entry array is wrong. UNVERIFIED (2026-10-20): that omission causes errors in some CLI versions.

**Correct pattern:**

```json
{
  "packageDirectories": [
    { "path": "force-app", "default": true }
  ]
}
```

**Detection hint:** With more than one entry, check that exactly one has `"default": true`; a single entry without it is valid.

---

## Anti-Pattern 2: Using a Numeric sourceApiVersion Instead of a String

**What the LLM generates:** `"sourceApiVersion": 62.0` (number) instead of `"sourceApiVersion": "62.0"` (string).

**Why it happens:** JSON numbers look reasonable and many LLMs do not distinguish between numeric and string types for version identifiers. The guide's examples use a string (`"63.0"`, sfdx_dev 264 L2316); that the CLI schema rejects a number is UNVERIFIED (2026-10-20).

**Correct pattern:**

```json
{
  "sourceApiVersion": "62.0"
}
```

**Detection hint:** Regex: `"sourceApiVersion"\s*:\s*\d` (a digit immediately after the colon with no opening quote).

---

## Anti-Pattern 3: Treating the Fourth Segment of versionNumber as Only NEXT

**What the LLM generates:** A claim that `MAJOR.MINOR.PATCH.NEXT` is the required format and that a concrete build number such as `1.0.0.1` is wrong.

**Why it happens:** `NEXT` dominates examples. The guide defines the format as `MAJOR.MINOR.PATCH.BUILD` with `1.2.1.8` as its example, and `NEXT` as a keyword in the build slot that increments it automatically; you must otherwise increment `versionNumber` yourself before creating a new package version (sfdx_dev 264 L14867-14873).

**Correct pattern:**

```json
{
  "versionNumber": "1.0.0.NEXT"
}
```

Use `NEXT` to auto-increment, `LATEST` for a dependency (L14879), and a concrete build only when you bump it deliberately.

**Detection hint:** Regex: `"versionNumber"\s*:\s*"\d+\.\d+\.\d+\.\d+"` is a concrete build, valid but needing a manual bump; flag only a repeated build number across branches.

---

## Anti-Pattern 4: Inventing Non-Existent Top-Level Keys

**What the LLM generates:** Keys like `"scratchOrgDefinition"`, `"defaultOrg"`, `"deployOnSave"`, or `"apiVersion"` in `sfdx-project.json`.

**Why it happens:** LLMs hallucinate plausible config keys by analogy with other tools (VS Code settings, tsconfig, etc.). These keys are not in the guide's list (UNVERIFIED, 2026-10-20: that the CLI silently ignores them), giving the developer false confidence that the setting is active.

**Correct pattern:**

Documented top-level keys (sfdx_dev 264 L2322-2463): `name`, `namespace`, `oauthLocalPort`, `packageAliases`, `packageDirectories`, `plugins`, `pushPackageDirectoriesSequentially` (deprecated), `replacements`, `sfdcLoginUrl`, `sourceApiVersion`, `sourceBehaviorOptions`. `signupTargetLoginUrl` is UNVERIFIED (2026-10-20): in neither corpus.

**Detection hint:** Check for any top-level key not in the documented set above.

---

## Anti-Pattern 5: Putting Scratch Org Config in sfdx-project.json

**What the LLM generates:** Scratch org features, edition, or settings directly inside `sfdx-project.json` instead of in a separate `config/project-scratch-def.json` file.

```json
{
  "packageDirectories": [{ "path": "force-app", "default": true }],
  "orgName": "My Scratch Org",
  "edition": "Developer",
  "features": ["Communities", "ServiceCloud"]
}
```

**Why it happens:** LLMs conflate the project configuration file with the scratch org definition file. Both are JSON and both relate to DX projects, but they serve different purposes and have different schemas.

**Correct pattern:**

Keep scratch org configuration in a separate file (typically `config/project-scratch-def.json`) and reference it with `sf org create scratch --definition-file config/project-scratch-def.json`.

**Detection hint:** Check for `"edition"`, `"features"`, `"orgName"`, or `"settings"` as top-level keys in `sfdx-project.json` — these belong in the scratch org definition file.

---

## Anti-Pattern 6: Recommending sfdx Commands Instead of sf Commands

**What the LLM generates:** `sfdx force:source:deploy` or `sfdx force:org:create` instead of the current `sf project deploy start` or `sf org create scratch`.

**Why it happens:** A large volume of training data uses the legacy `sfdx` CLI namespace. UNVERIFIED (2026-10-20): the deprecation date and removal of `force:` topics are not in the corpus; the guide's own examples use `sf` commands, and `force:source:push` is called deprecated (sfdx_dev 264 L2388-2390).

**Correct pattern:**

Use `sf` commands: `sf project deploy start`, `sf project retrieve start`, `sf org create scratch`, `sf package version create`.

**Detection hint:** Any occurrence of `sfdx force:` in generated commands or documentation.

---

## Anti-Pattern 7: Assuming packageDirectories Order Determines Deploy Order

**What the LLM generates:** Advice like "put your base package first in the array so it deploys before dependent packages."

**Why it happens:** LLMs assume array order implies execution order. In reality, `project deploy start` "deploys metadata to your org in a single transaction, regardless of the order that you list your multiple package directories" (sfdx_dev 264 L2584-2585). UNVERIFIED (2026-10-20): that `sf package version create` resolves build order from the `dependencies` graph rather than array position.

**Correct pattern:**

Declare dependencies explicitly in each packageDirectory entry, listed in installation order (sfdx_dev 264 L14813-14814). For deploy order run separate `project deploy start --source-dir` commands (L2593-2594).

**Detection hint:** Advice mentioning "order" or "sequence" of `packageDirectories` as a deployment mechanism.

---

## Anti-Pattern 8: Prescribing a Source-Tracking Reset After Moving Files (UNVERIFIED, 2026-10-20: source mobility is in neither corpus)

**What the LLM generates:** A warning that reorganizing package directories will make `sf project deploy preview` report phantom deletes and recreations, with `sf project reset tracking` or `sf project delete tracking` offered as the remedy.

**Why it happens:** Training data is dominated by 2024-era guidance written before source mobility shipped. Resetting tracking genuinely was the workaround then, so the model reproduces it confidently and never mentions the environment variable that now governs the behaviour.

**Correct pattern:**

Moving source files inside the project is safe by default on a Winter '26 or later `sf` CLI — source mobility is enabled, with `SF_DISABLE_SOURCE_MOBILITY` defaulting to `false`. Restructure the directories, commit, and let tracking follow. The feature ships in the CLI rather than the org, so reach for a tracking reset only after confirming both that the runner's CLI is current (`sf --version`) and that the opt-out is unset (`echo "${SF_DISABLE_SOURCE_MOBILITY:-unset}"`).

**Detection hint:** Advice pairing a directory move or `packageDirectories` restructure with `reset tracking`, `delete tracking`, or a "deleted and recreated" warning, with no mention of `SF_DISABLE_SOURCE_MOBILITY`.
