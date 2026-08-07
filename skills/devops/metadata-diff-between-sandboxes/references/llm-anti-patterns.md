# LLM Anti-Patterns — Metadata Diff Between Sandboxes

Common mistakes AI coding assistants make when generating or advising on org-to-org metadata diffs.

## Anti-Pattern 1: Asymmetric retrieve manifests

**What the LLM generates:** Retrieves "everything" from Org A using a comprehensive manifest, then retrieves "the same items" from Org B using a manifest derived from what Org A returned.

**Why it happens:** LLM treats the retrieves as serial steps and lets Org A define the scope.

**Correct pattern:** Retrieve both orgs against the **same** package.xml. Asymmetric scope produces false-positive "missing in target" entries.

**Detection hint:** Two `sf project retrieve` calls with different `-x` arguments.

---

## Anti-Pattern 2: Treating profile churn as real drift

**What the LLM generates:** A diff report listing 800 profile changes as "drift to investigate."

**Why it happens:** LLM treats all metadata XML as semantically equal.

**Correct pattern:** Diff-ignore profiles unless profile drift is the question. Use a profile-aware tool when it is.

**Detection hint:** Diff output dominated by `*.profile-meta.xml` entries with no acknowledgment that profile XML auto-rewrites.

---

## Anti-Pattern 3: Inferring deletes from "missing in target" without checking retrievability

**What the LLM generates:** "These types are missing in target — emit them as destructiveChanges."

**Why it happens:** LLM doesn't consider that the target retrieve may have skipped types it doesn't support.

**Correct pattern:** Validate the target retrieve actually attempted the type. Cross-check against the Metadata API Coverage report. Items in unretrievable types must not be inferred as missing.

**Detection hint:** A destructive manifest containing types like `WaveDataset` or `OmniscriptDefinition`.

---

## Anti-Pattern 4: Skipping folder enumeration for folder-bound types

**What the LLM generates:** `<members>*</members>` for `Report` in the package.xml.

**Why it happens:** Wildcard "just works" for most types and the LLM applies the heuristic uniformly.

**Correct pattern:** Reports / Dashboards / EmailTemplates / Documents need explicit folder enumeration. Use `sf org list metadata --metadata-type ReportFolder --target-org <alias>` first, then build per-folder members. The topic is `org`, not `project` — `sf project list metadata` does not exist; the only `sf project list` subcommand is `sf project list ignored`.

**Detection hint:** `<name>Report</name>` paired with `<members>*</members>` (or any folder-bound type with a wildcard).

---

## Anti-Pattern 5: Auto-applying destructiveChanges without human review

**What the LLM generates:** A pipeline that pipes `destructiveChanges.xml` straight into `sf project deploy start --post-destructive-changes`.

**Why it happens:** Treats destructive metadata as reversible.

**Correct pattern:** Field deletions are destructive against data and irreversible without a backup restore. Always gate destructive deploy behind human review and a recent backup checkpoint.

**Detection hint:** Pipeline step that consumes destructiveChanges.xml without an intervening manual approval gate.


---

## Anti-Pattern: Guessing the `sf` CLI **topic** for a command whose verb you remember

**What the LLM generates:** `sf package dependencies list --package <id>`, `sf project list metadata --metadata-type ReportFolder`, `sf org deploy start`, `sf package version dependencies`.

**Why it happens:** The `sfdx force:*:*` → `sf <topic> <verb>` rewrite reshuffled which *topic* owns which noun, and the model reconstructs the command from the noun it needs (`dependencies`, `metadata`) rather than from the topic tree. `sf project …` handles local source and deployments, so "list the metadata" feels like it belongs there; in fact anything that queries a live org lives under `sf org …`. Likewise `dependencies` is a property of a package **version**, not of a package, so the verb hangs off `package version`, not `package`. These fail with a plain command-not-found, which is cheap — but they are usually step 1 of a workflow, so the whole procedure stalls at the first line, and they most often appear in "correct pattern" or "how to avoid" positions where a reader has been told to trust them.

**Correct version:**

| Wrong | Right |
|---|---|
| `sf package dependencies list --package <id>` | `sf package version displaydependencies --package <packageVersionId>` |
| `sf project list metadata --metadata-type X` | `sf org list metadata --metadata-type X --target-org <alias>` |
| (listing available types) | `sf org list metadata-types --target-org <alias>` |

**Detection hint:** two mechanical rules that need no memorisation. (1) **If the command talks to an org, the topic is `org`.** `sf project` is for local source, manifests, and deploy/retrieve; the only `sf project list` subcommand is `list ignored`. (2) **`package` vs `package version`:** anything about the contents, ancestry, or dependencies of a built artifact hangs off `package version`; only lifecycle operations on the container (`create`, `list`, `update`, `delete`, `install`, `uninstall`) hang off `package`. Anything else, check the CLI reference — and note that "this command is fake" is itself a claim needing a source, since `sf project deploy validate` and `sf project deploy preview` are real and are frequently mis-flagged.
