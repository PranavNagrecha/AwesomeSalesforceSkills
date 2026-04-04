---
name: source-tracking-and-conflict-resolution
description: "Use when diagnosing and resolving SFDX source-tracking conflicts between a local project and a Salesforce org — covering sf project pull/push/retrieve/deploy conflict errors, force overwrite decisions, tracking file corruption, and sandbox source-tracking enablement. Trigger keywords: source tracking, conflict, --force-overwrite, --ignore-conflicts, maxRevision.json, sf project retrieve, source:status. NOT for Git merge conflicts, DevOps Center pipeline conflicts, or change-set deployments."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "sf project retrieve start fails with conflict error and I am not sure which version to keep"
  - "source tracking is out of sync and pull shows everything as changed even though nothing was modified"
  - "how do I enable source tracking in a sandbox so I can use sf project retrieve and deploy"
  - "I accidentally deployed the wrong version and need to force overwrite from the org"
  - "tracking files are corrupted and every component shows as conflicting after a sandbox refresh"
  - "how do I preview what will change before running sf project deploy start with source tracking"
tags:
  - source-tracking
  - sfdx
  - conflict-resolution
  - sandbox
  - sf-cli
  - devops
inputs:
  - "Org type (scratch org, Developer sandbox, Partial Copy sandbox, Full sandbox)"
  - "Whether source tracking is already enabled in the sandbox org preference"
  - "Current sf project deploy/retrieve error message or source:status output"
  - "Whether the conflict is local-wins or org-wins (which version is authoritative)"
  - "Org username or alias from sf org list"
outputs:
  - "Resolved source-tracking state with no pending conflicts"
  - "Decision guidance on --force-overwrite vs --ignore-conflicts vs manual resolution"
  - "Instructions for enabling source tracking in a sandbox"
  - "Recovery procedure for corrupted tracking files"
  - "Pre-deployment conflict preview output from --dry-run"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Source Tracking and Conflict Resolution

This skill activates when a practitioner needs to understand, diagnose, or resolve source-tracking conflicts between a local Salesforce DX project and an org using the `sf` CLI (`sf project retrieve start`, `sf project deploy start`). It covers the mechanics of tracking files, conflict detection via `SourceMember` revision counters, sandbox enablement, force-overwrite and ignore-conflicts flags, and recovery from corrupted tracking state. It does NOT cover Git merge conflicts, DevOps Center pipeline conflicts, or Metadata API-based change-set deployments.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Source tracking is not automatic for sandboxes** — scratch orgs have tracking enabled by default, but Developer, Partial Copy, and Full sandboxes require the "Enable Source Tracking in Sandboxes" org preference to be turned on before any pull/push operation. Without it, `sf project retrieve start` and `sf project deploy start` run in non-tracking (full-metadata) mode and will not detect conflicts.
- **The most common wrong assumption** — practitioners believe that deleting local source files and re-running `sf project retrieve start` will reset tracking state. It does not. The tracking state lives in `.sf/orgs/<orgId>/` on disk, completely independent of the source files. Local source and tracking files are two separate concerns.
- **Revision counters govern conflicts** — the CLI compares the `RevisionCounter` values in `.sf/orgs/<orgId>/maxRevision.json` against the `SourceMember` object in the org. A conflict means both sides have moved past the last known shared revision. The CLI does not read Git history; it reads only its own tracking database.
- **Tracking-file corruption after sandbox refresh** — when a sandbox is refreshed, its org ID changes. The old `.sf/orgs/<oldOrgId>/` directory is now stale. The CLI may either fail silently or show every component as conflicting. Recovery requires deleting the stale tracking directory and re-retrieving from the refreshed org.

---

## Core Concepts

### How Source Tracking Works

Source tracking records the last-known-good revision of every tracked metadata component in `.sf/orgs/<orgId>/maxRevision.json`. When the CLI pulls from the org, it queries the `SourceMember` object — a read-only platform object that Salesforce maintains automatically whenever a component is created or modified in a tracked org. Each `SourceMember` row has a `RevisionCounter` integer that increments on every change.

A conflict arises when:
1. The local revision counter stored in `maxRevision.json` is lower than the org's current `RevisionCounter` for a component (org has moved forward), AND
2. The local file on disk also differs from what was last retrieved (local has also moved forward).

If only the org side changed, a plain `sf project retrieve start` succeeds. If only the local side changed, a plain `sf project deploy start` succeeds. A true conflict — both sides changed — blocks both operations unless overridden.

### The Three Resolution Modes

**Mode 1 — Org wins (local overwrite):** Use `sf project retrieve start --ignore-conflicts` to pull org changes and overwrite local files that differ. The local edits are lost. Use this when the org version is authoritative (e.g., declarative changes made by an admin directly in the org that you want to capture).

**Mode 2 — Local wins (org overwrite):** Use `sf project deploy start --ignore-conflicts` to push local changes and overwrite org state, even where a conflict exists. Use this when the local version is authoritative (e.g., a developer made the correct fix locally and the org version is stale).

**Mode 3 — Manual merge then deploy:** Retrieve with `--ignore-conflicts` to get the org version as a reference file. Manually merge the two versions in your editor. Then deploy with a clean status. Use this when both versions contain independent valuable changes that must be reconciled.

Note: `--force-overwrite` was the legacy flag name in older `sfdx force:source:*` commands. In `sf` CLI v2, the flag is `--ignore-conflicts` for both retrieve and deploy. Do not mix the two namespaces.

### Sandbox Source Tracking Enablement

Source tracking in sandboxes is an org-level preference that must be explicitly enabled before the sandbox is created or refreshed. The path is:

1. In the production org: Setup > Sandboxes > Sandbox Settings > check "Enable Source Tracking in Sandboxes"
2. Create or refresh the sandbox after this preference is enabled.

If you enable the preference after the sandbox already exists, you must refresh the sandbox to activate tracking. There is no retroactive activation. Once enabled, the sandbox behaves like a scratch org for tracking purposes: every declarative change made in Setup is recorded in `SourceMember` and becomes visible to `sf project retrieve start`.

### Dry-Run Conflict Preview

Before committing to a deploy or retrieve, use `sf project deploy start --dry-run` (or the equivalent `--check-only` flag) to preview what the CLI intends to push without applying changes. This surfaces conflicts in the output before any data is modified. For retrieve operations, `sf project retrieve start` with `-x package.xml` and `--ignore-conflicts` in a test branch is a common safe-preview approach.

`sf project deploy start --dry-run` runs full validation including Apex test execution rules, but does not write to the org. It is the recommended pre-flight check in any automated pipeline that uses source tracking.

---

## Common Patterns

### Pattern 1: Resolving a Pull Conflict (Org Wins)

**When to use:** An admin made declarative changes directly in a sandbox org (e.g., edited a page layout or validation rule) while you also have local edits to the same file. You want to accept the org version and discard your local draft.

**How it works:**

```bash
# 1. Check current status — look for components with 'u' (unresolved conflict) marker
sf project retrieve start --dry-run --target-org <alias>

# 2. Accept org version, overwrite local files
sf project retrieve start --ignore-conflicts --target-org <alias>

# 3. Confirm status is clean
sf project deploy start --dry-run --target-org <alias>
```

After `--ignore-conflicts` retrieve completes, the tracking counters are updated to match the org. The local files now reflect the org state.

**Why not plain retrieve:** A plain `sf project retrieve start` without `--ignore-conflicts` will abort with a conflict error when both sides have moved. The flag tells the CLI to skip the conflict-abort and proceed with the org version.

### Pattern 2: Recovering From Tracking Corruption After Sandbox Refresh

**When to use:** A sandbox was refreshed and now every component shows as conflicting, or the CLI cannot authenticate to the old org ID stored in `.sf/orgs/`.

**How it works:**

```bash
# 1. Find the stale tracking directory
ls ~/.sf/orgs/
# or relative to your project:
ls .sf/orgs/

# 2. Identify the old org ID (it will differ from the new sandbox's org ID)
sf org display --target-org <refreshed-alias>

# 3. Delete the stale tracking directory
rm -rf .sf/orgs/<oldOrgId>/

# 4. Re-authorize and re-retrieve from the refreshed org
sf org login web --alias <refreshed-alias>
sf project retrieve start --target-org <refreshed-alias>
```

After deletion and re-retrieve, the CLI rebuilds `maxRevision.json` from the current org state. All components are treated as freshly retrieved with no conflicts.

**Why not edit maxRevision.json manually:** The file schema can change between CLI versions, and manually edited revision counters can cause the CLI to silently skip components or produce ghost conflicts. Always delete and rebuild.

### Pattern 3: Local Wins Deploy With Conflict Override

**When to use:** You have correct fixes locally and the org has diverged (e.g., someone deployed a broken version directly). You want to push your local version and overwrite the org state.

**How it works:**

```bash
# 1. Preview the deploy to verify scope
sf project deploy start --dry-run --target-org <alias>

# 2. Deploy with conflict override — local wins
sf project deploy start --ignore-conflicts --target-org <alias>

# 3. Verify post-deploy status
sf project retrieve start --dry-run --target-org <alias>
```

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Org has org-only declarative changes, local is clean | `sf project retrieve start` (no flag needed) | No conflict exists; plain retrieve works |
| Both org and local changed the same component, org is authoritative | `sf project retrieve start --ignore-conflicts` | Discards local edits, accepts org version |
| Both org and local changed the same component, local is authoritative | `sf project deploy start --ignore-conflicts` | Overwrites org with local version |
| Both sides have independent valuable edits that must be merged | Retrieve with `--ignore-conflicts`, merge manually, deploy | Neither side can be discarded outright |
| Sandbox was refreshed and tracking is corrupted | Delete `.sf/orgs/<oldOrgId>/`, re-retrieve | Stale revision counters must be rebuilt |
| Source tracking not enabled in sandbox | Enable "Enable Source Tracking in Sandboxes" in prod, refresh sandbox | No retroactive activation possible |
| Want to preview conflicts without committing changes | `sf project deploy start --dry-run` | Safe pre-flight validation |
| Every component shows as modified after a clean checkout | Delete tracking dir, run fresh retrieve | Tracking DB and source files are out of sync |

---

## Recommended Workflow

Step-by-step instructions for diagnosing and resolving a source-tracking conflict:

1. **Check current status** — run `sf project deploy start --dry-run --target-org <alias>` and `sf project retrieve start --dry-run --target-org <alias>` to identify which components are conflicting and whether the conflict is a pull-side or push-side block. Note any components marked with `u` (unresolved).

2. **Determine which version is authoritative** — ask: was the org-side change intentional and should be kept, or was the local change the correct version? If unsure, retrieve with `--ignore-conflicts` to a scratch branch to compare both versions side-by-side before deciding.

3. **Enable sandbox source tracking if missing** — if `sf project retrieve start` reports that tracking is unavailable for the target org, confirm the "Enable Source Tracking in Sandboxes" preference is on in production Setup, then refresh the sandbox before proceeding. You cannot enable tracking on an existing sandbox retroactively.

4. **Apply the resolution** — execute the appropriate Mode 1, 2, or 3 pattern from the Common Patterns section. For Mode 3 (manual merge), retrieve first with `--ignore-conflicts`, perform the merge in your editor, then deploy the merged result.

5. **Confirm clean state** — run `sf project deploy start --dry-run` again after resolution. If the output shows zero conflicts and zero pending changes, the tracking state is clean.

6. **Recover corrupted tracking if needed** — if every component still appears conflicted after resolution attempts, delete `.sf/orgs/<orgId>/` and run a full `sf project retrieve start` to rebuild the tracking database from current org state.

7. **Commit the resolved source** — after all conflicts are resolved and the dry-run is clean, commit the resolved local source files to Git. Do not commit `.sf/` tracking directories — they should be in `.gitignore`.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] `sf project deploy start --dry-run` shows zero conflicts and zero unexpected pending changes
- [ ] `.sf/` directory is listed in `.gitignore` and tracking files are not committed to Git
- [ ] Sandbox source-tracking preference was confirmed enabled before retrieve/deploy was attempted
- [ ] No manual edits were made to `.sf/orgs/<orgId>/maxRevision.json` or any tracking JSON file
- [ ] If a sandbox refresh occurred, the old tracking directory was deleted and rebuilt via fresh retrieve
- [ ] The correct `--ignore-conflicts` flag (not the legacy `--force-overwrite`) was used in all `sf` v2 commands
- [ ] Post-resolution, the org and local source agree — confirmed by a clean dry-run on both sides

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Sandbox refresh invalidates the org ID silently** — when a sandbox is refreshed, Salesforce assigns a new org ID. The `.sf/orgs/` directory on disk still contains the old org ID. The CLI does not automatically clean up stale entries. If the developer authenticates using the alias (which resolves to the new org ID), the CLI will behave as if it has never seen this org before and attempt to retrieve everything, often creating ghost conflicts with pre-existing local files. Always confirm the current org ID with `sf org display` before running any source tracking command after a refresh.

2. **`--ignore-conflicts` on retrieve silently discards local changes** — unlike a Git stash or merge, there is no undo. If you run `sf project retrieve start --ignore-conflicts` and local files had unsaved work, those edits are overwritten with no recovery path outside of Git history. Always commit or stash local work before using `--ignore-conflicts` on a retrieve operation.

3. **Source tracking does not cover all metadata types** — some metadata types are not tracked by `SourceMember` at all (e.g., certain platform event settings, some managed package components, and any component not in the tracked metadata coverage list). These components will never show as conflicting, but they also will not be retrieved automatically by source-tracking-aware commands. Always verify coverage with the Metadata Coverage Report at `https://developer.salesforce.com/docs/metadata-coverage` before assuming a missing component is not present in the org.

4. **`sf project deploy start --dry-run` does not simulate retrieve conflicts** — dry-run validates what would be deployed from local to org. It does not show whether the org has incoming changes that would conflict on the next retrieve. Run both a deploy dry-run and a retrieve dry-run to get a full picture of the conflict surface.

5. **`.sf/` tracking directory scope is per-project, not per-machine** — if two developers clone the same repo and both retrieve from the same sandbox, their `.sf/orgs/<orgId>/` directories will drift apart over time as each developer makes local changes. This is expected behavior, not corruption. However, if a CI system clones the repo fresh on every run, it will always start with no tracking state and treat every component as new on the first retrieve — leading to full retrieves rather than delta retrieves.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Clean `sf project deploy start --dry-run` output | Confirms zero conflicts and zero pending unintended changes before any real deploy |
| Updated `.sf/orgs/<orgId>/maxRevision.json` | Rebuilt tracking database after recovery from corruption — generated by `sf project retrieve start`, never edited manually |
| Resolved local source files | Metadata files that have been merged or overwritten to match the authoritative version, ready for Git commit |
| Sandbox source-tracking enablement confirmation | Screenshot or Setup audit trail showing "Enable Source Tracking in Sandboxes" is active in the production org |

---

## Related Skills

- `sf-cli-and-sfdx-essentials` — foundational CLI setup, org authorization, and basic push/pull commands; use this when the practitioner is new to SFDX and needs pre-requisites before conflict resolution applies
- `devops-center-pipeline` — DevOps Center-specific conflict resolution between Work Items and pipeline stages; use when the deployment tool is DevOps Center, not the CLI directly
- `scratch-org-management` — scratch org lifecycle and shape management; overlaps with source tracking since scratch orgs have tracking enabled by default
- `cicd-pipeline-setup` — integrating `sf project deploy start` into automated pipelines; use when the conflict resolution needs to be handled non-interactively in CI
