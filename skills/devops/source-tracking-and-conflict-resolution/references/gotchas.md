# Gotchas — Source Tracking and Conflict Resolution

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

---

## Gotcha 1: Sandbox Source Tracking Cannot Be Enabled Retroactively

**What happens:** A developer enables the "Enable Source Tracking in Sandboxes" org preference in production, then immediately runs `sf project retrieve start` against an existing sandbox — and finds that tracking is still not working. The CLI either ignores conflicts entirely or retrieves all components as if tracking does not exist.

**When it occurs:** The preference controls whether newly created or refreshed sandboxes have tracking enabled. Turning on the preference does not activate tracking for sandboxes that already exist. The sandbox must be created or refreshed after the preference is enabled for tracking to take effect.

**How to avoid:** Enable "Enable Source Tracking in Sandboxes" in production Setup before you create or refresh the sandbox. If you have an existing sandbox that lacks tracking, you must refresh it to activate the feature. Plan sandbox refresh windows accordingly and communicate the downtime to the team.

---

## Gotcha 2: `--ignore-conflicts` on Retrieve Destroys Uncommitted Local Work With No Warning

**What happens:** `sf project retrieve start --ignore-conflicts` silently overwrites any local file that conflicts with the org version. The CLI does not prompt for confirmation, does not create a backup, and does not display the diff before overwriting. There is no "undo" command — the local version is gone from the filesystem.

**When it occurs:** Any time `--ignore-conflicts` is used on a retrieve when the developer has local edits that have not been committed to Git. This most commonly affects developers who iterate quickly in a sandbox and forget to commit before resolving a conflict from a colleague's change.

**How to avoid:** Always run `git status` and commit or stash any local changes before using `--ignore-conflicts` on a retrieve. If you want to compare both versions before deciding, use `git stash`, retrieve with `--ignore-conflicts`, then `git stash show -p` to inspect what was stashed.

---

## Gotcha 3: Not All Metadata Types Are Source-Tracked by SourceMember

**What happens:** A developer modifies a metadata type that is not covered by `SourceMember` tracking (e.g., some Standard Value Sets, certain Settings metadata, or components inside managed packages). The component does not appear in `sf project deploy start --dry-run` output even though it exists in the org. The developer assumes it is in sync, but deploying a full `package.xml` retrieve later reveals the org has a different version.

**When it occurs:** When a skill or workflow assumes all metadata types are source-tracked. Tracking coverage depends on the Salesforce API version and component type. The Metadata Coverage Report (`https://developer.salesforce.com/docs/metadata-coverage`) documents which types support source tracking.

**How to avoid:** Check the Metadata Coverage Report for any metadata type you are working with. For non-tracked types, use `sf project retrieve start -m <MetadataType>:<componentName>` (explicit Metadata API retrieve) rather than relying on source tracking to detect changes. Include non-tracked types explicitly in your `package.xml` rather than expecting them to appear in `sf project deploy start` output.

---

## Gotcha 4: CI Systems Cloning Fresh Always Lose Tracking State

**What happens:** A CI pipeline clones the repository fresh on every run (e.g., a GitHub Actions workflow with `actions/checkout`). The `.sf/` directory is not committed to Git (correct behavior), so every CI run starts with no tracking state. The first `sf project retrieve start` in the CI job retrieves every tracked component from the org — not just the delta — causing the job to be extremely slow or to fail on large orgs due to timeout.

**When it occurs:** Any automated pipeline that runs `sf project retrieve start` without pre-seeding tracking state, particularly in environments that do not cache `.sf/` across runs.

**How to avoid:** In CI, prefer `sf project deploy start --source-dir force-app --ignore-conflicts` (explicit directory deploy, not source-tracking-aware) for deployment steps, or use `sf project deploy start -x manifest/package.xml` with an explicit `package.xml`. Reserve source-tracking-aware commands for local developer workflows. If tracking-based delta deploys in CI are required, cache the `.sf/orgs/<orgId>/` directory between pipeline runs using the CI provider's caching mechanism.

---

## Gotcha 5: `sf project deploy start --dry-run` Does Not Show Retrieve-Side Conflicts

**What happens:** A developer runs `sf project deploy start --dry-run` and sees "No conflicts detected." They proceed with the actual deploy — which succeeds — but then immediately run `sf project retrieve start` and hit a conflict because the org had incoming changes the deploy did not overwrite.

**When it occurs:** Dry-run only previews the deploy direction (local → org). It does not query the org for changes that would conflict on the next retrieve (org → local direction). A clean dry-run does not mean a subsequent retrieve will be conflict-free.

**How to avoid:** Run both `sf project deploy start --dry-run` and `sf project retrieve start --dry-run` before any deployment to get a full picture of both directions. If the retrieve dry-run shows incoming conflicts, resolve them first before deploying to avoid a mixed state where the deploy succeeded but the retrieve leaves tracking out of sync.
