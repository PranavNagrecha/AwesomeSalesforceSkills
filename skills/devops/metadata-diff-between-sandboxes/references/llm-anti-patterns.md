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

**Correct pattern:** Reports / Dashboards / EmailTemplates / Documents need explicit folder enumeration. Use `sf project list metadata --metadata-type ReportFolder` first, then build per-folder members.

**Detection hint:** `<name>Report</name>` paired with `<members>*</members>` (or any folder-bound type with a wildcard).

---

## Anti-Pattern 5: Auto-applying destructiveChanges without human review

**What the LLM generates:** A pipeline that pipes `destructiveChanges.xml` straight into `sf project deploy start --post-destructive-changes`.

**Why it happens:** Treats destructive metadata as reversible.

**Correct pattern:** Field deletions are destructive against data and irreversible without a backup restore. Always gate destructive deploy behind human review and a recent backup checkpoint.

**Detection hint:** Pipeline step that consumes destructiveChanges.xml without an intervening manual approval gate.
