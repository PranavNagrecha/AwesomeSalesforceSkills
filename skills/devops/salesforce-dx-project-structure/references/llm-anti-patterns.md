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

**Why it happens:** Training data includes older project configs or incomplete examples that predate the strict requirement. The CLI technically defaults the first entry, but omitting the flag causes errors in some sf CLI versions and confuses tooling.

**Correct pattern:**

```json
{
  "packageDirectories": [
    { "path": "force-app", "default": true }
  ]
}
```

**Detection hint:** Check that exactly one entry in `packageDirectories` has `"default": true`.

---

## Anti-Pattern 2: Using a Numeric sourceApiVersion Instead of a String

**What the LLM generates:** `"sourceApiVersion": 62.0` (number) instead of `"sourceApiVersion": "62.0"` (string).

**Why it happens:** JSON numbers look reasonable and many LLMs do not distinguish between numeric and string types for version identifiers. The Salesforce CLI schema requires a string.

**Correct pattern:**

```json
{
  "sourceApiVersion": "62.0"
}
```

**Detection hint:** Regex: `"sourceApiVersion"\s*:\s*\d` (a digit immediately after the colon with no opening quote).

---

## Anti-Pattern 3: Using Build Numbers Instead of NEXT in versionNumber

**What the LLM generates:** `"versionNumber": "1.0.0.1"` with a hardcoded build number.

**Why it happens:** LLMs treat version numbers like semver where all four segments are concrete. In Salesforce DX, the fourth segment should be `NEXT` so the CLI auto-increments during `sf package version create`.

**Correct pattern:**

```json
{
  "versionNumber": "1.0.0.NEXT"
}
```

**Detection hint:** Regex: `"versionNumber"\s*:\s*"\d+\.\d+\.\d+\.\d+"` — if the fourth segment is a digit, it should likely be `NEXT`.

---

## Anti-Pattern 4: Inventing Non-Existent Top-Level Keys

**What the LLM generates:** Keys like `"scratchOrgDefinition"`, `"defaultOrg"`, `"deployOnSave"`, or `"apiVersion"` in `sfdx-project.json`.

**Why it happens:** LLMs hallucinate plausible config keys by analogy with other tools (VS Code settings, tsconfig, etc.). These keys are silently ignored by the CLI, giving the developer false confidence that the setting is active.

**Correct pattern:**

Valid top-level keys are: `packageDirectories`, `namespace`, `sourceApiVersion`, `sfdcLoginUrl`, `signupTargetLoginUrl`, `plugins`, `packageAliases`, and `oauthLocalPort`. Any other key is either ignored or invalid.

**Detection hint:** Check for any top-level key not in the known set: `packageDirectories`, `namespace`, `sourceApiVersion`, `sfdcLoginUrl`, `signupTargetLoginUrl`, `plugins`, `packageAliases`, `oauthLocalPort`.

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

**Why it happens:** A large volume of training data uses the legacy `sfdx` CLI namespace. Salesforce deprecated the `sfdx` command in favor of `sf` starting in 2023, and the `force:` topic commands are being removed.

**Correct pattern:**

Use `sf` commands: `sf project deploy start`, `sf project retrieve start`, `sf org create scratch`, `sf package version create`.

**Detection hint:** Any occurrence of `sfdx force:` in generated commands or documentation.

---

## Anti-Pattern 7: Assuming packageDirectories Order Determines Deploy Order

**What the LLM generates:** Advice like "put your base package first in the array so it deploys before dependent packages."

**Why it happens:** LLMs assume array order implies execution order. In reality, for `sf project deploy`, all directories are deployed together. For `sf package version create`, the CLI resolves build order from the `dependencies` graph, not array position.

**Correct pattern:**

Declare dependencies explicitly in each packageDirectory entry. The CLI resolves the correct build/install order from the dependency graph. Array order in `packageDirectories` is irrelevant for build sequencing.

**Detection hint:** Advice mentioning "order" or "sequence" of `packageDirectories` as a deployment mechanism.
