# Gotchas — Git Branching For Salesforce

Non-obvious Salesforce platform behaviors and Git interactions that cause real production problems in this domain.

## Gotcha 1: Profile XML Merge Produces Valid Git but Invalid Metadata

**What happens:** UNVERIFIED (2026-10-20): the element-order and duplicate-entry failure below is field experience; no corpus line says the Metadata API rejects reordered elements. Two developers add FLS entries to the same profile on separate branches. Git merges the XML cleanly because the additions are in different sections. However, the resulting XML may have elements in an order that the Metadata API rejects, or duplicate entries that cause a deploy failure.

**When it occurs:** Any time two branches modify the same profile and are merged. More frequent with monolithic (non-decomposed) metadata format. Even SFDX decomposed format does not fully eliminate this for profiles: Profile is not in the list of decomposable types (sfdx_dev 264 L1613-1625).

**How to avoid:** Prefer permission sets and permission set groups over profile modifications. When profiles must be edited, use `sf project retrieve start --metadata Profile` after merging to normalize XML ordering. Consider a CI step that validates the merged profile deploys cleanly to a scratch org before completing the merge.

---

## Gotcha 2: Scratch Org Source Tracking Diverges After Force-Push

**What happens:** UNVERIFIED (2026-10-20): the source-tracking mechanics after a rebase are not described in the corpus; treat as field experience. A developer rebases or force-pushes a feature branch. The scratch org's source tracking table still reflects the old commit history. Subsequent `sf project deploy start` or `sf project retrieve start` commands may skip files that changed in the rebase or re-deploy files that are unchanged.

**When it occurs:** When a team allows or encourages rebasing feature branches (common in trunk-based development). The scratch org does not know that the local source was rewritten.

**How to avoid:** After a rebase or force-push, run `sf project deploy start --source-dir force-app` (full push) instead of relying on source tracking. Alternatively, delete and recreate the scratch org after a rebase. Document this in the team's branching guide.

---

## Gotcha 3: Destructive Changes Require Separate Manifest and Cannot Be Merged Naively

**What happens:** A feature branch deletes a custom field. In Git, this shows as a file deletion. But Salesforce does not delete metadata on deploy — deletions require a `destructiveChanges.xml` manifest (api_meta 264 L4707, L4746). If the branch merges to `main` and CI runs a standard deploy, the field still exists in the target org.

**When it occurs:** Any branch that removes metadata (fields, classes, triggers, flows). The problem compounds when multiple branches delete different metadata and merge in sequence — each needs its own destructive manifest or a consolidated one.

**How to avoid:** Establish a convention: destructive changes live in a `destructive/` directory in the branch. CI must detect the presence of destructive manifests and include them in the deploy command (the `--pre-destructive-changes` and `--post-destructive-changes` flag names are UNVERIFIED (2026-10-20): not in the corpus; the manifest is `destructiveChanges.xml` and a deployment can combine deletions and additions, api_meta 264 L4746). Review destructive changes separately from additive changes in PRs.

---

## Gotcha 4: A Package Version Is Built From the Source You Pass, Not From a Branch Name

**What happens:** UNVERIFIED (2026-10-20): the 5-30+ minute duration and the "created from the older commit" mechanics are not in the corpus. `sf package version create` can take a while depending on package size. During this time, if another commit lands on the same branch, the version is created from the older commit. The resulting package version does not include the latest changes but is tagged as if it does.

**When it occurs:** When package version creation runs on a shared branch (like `main` or `develop`) with frequent merges. Concurrent merges during the build window cause version-content mismatch.

**How to avoid:** Use a dedicated packaging job that locks the branch or checks out a specific commit. In CI, record the exact commit with `--tag`, not `--branch`: `--branch` tags the version with a branch name ("any alphanumeric value up to 240 characters", sfdx_dev 264 L15993-15998), while `--tag` carries "the git commit ID associated with this package version" (pkg2_dev 264 L18448-18449, sfdx_dev 264 L15593). An earlier version of this gotcha passed a commit SHA to `--branch`. Alternatively, queue package builds so only one runs at a time per package.

---

## Gotcha 5: Sandbox Refresh Resets Org State but Not the Branch

**What happens:** UNVERIFIED (2026-10-20): sandbox refresh semantics are not in the corpus (it only notes that refreshed Developer and Developer Pro sandboxes get source tracking when enabled, sfdx_dev 264 L1019-1020). A sandbox mapped to the `develop` branch is refreshed from production. The sandbox now reflects `main` (production) state, not `develop`. Any metadata that exists on the `develop` branch but not in production is missing from the sandbox. Developers working against this sandbox encounter deploy errors or missing dependencies.

**When it occurs:** After a scheduled or manual sandbox refresh, especially on integration or UAT sandboxes that map to non-production branches.

**How to avoid:** After every sandbox refresh, immediately deploy the mapped branch to the sandbox: `sf project deploy start --source-dir force-app --target-org <sandbox-alias>`. Automate this as a post-refresh step. Document which branch must be deployed after refresh for each sandbox in the branching guide.
