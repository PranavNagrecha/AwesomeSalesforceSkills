---
name: metadata-diff-between-sandboxes
description: "Use when comparing metadata between two Salesforce orgs (UAT vs Prod, dev sandbox vs full copy, fork sandbox vs source) to surface drift, identify items needing deployment, or build a destructive-changes manifest. Triggers: 'compare two sandboxes', 'org diff tool', 'metadata drift between UAT and prod', 'find missing metadata in target org'. NOT for code-level diffs in version control or for deploying packages."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "compare metadata between UAT and production"
  - "find what's missing in target org before deploy"
  - "identify drift introduced by a hotfix in production"
  - "diff two sandboxes after a partial copy refresh"
  - "destructive-changes.xml from sandbox comparison"
tags:
  - org-diff
  - drift
  - deployment
  - metadata
inputs:
  - "two Salesforce org connections (DX auth aliases or username/password)"
  - "metadata types in scope (or default-all)"
  - "ignore list (.forceignore equivalent for diff)"
outputs:
  - "categorized diff report (in source not target / in target not source / different)"
  - "deployable package.xml + (optional) destructiveChanges.xml"
  - "drift inventory for the org-drift-detector agent"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-30
---

# Metadata Diff Between Sandboxes

Activate when an engineer needs to know "what's different between Org A and Org B at the metadata level" — typically before a deploy, after a hotfix, or when investigating mysterious behavior that diverges between environments. The skill produces a categorized diff (source-only / target-only / changed), a deployable manifest, and a drift inventory.

---

## Before Starting

Gather this context before working on anything in this domain:

- The two org auth contexts. DX auth aliases (`sf org list`) are the simplest. Long-lived integration users with API-only profiles are safer than personal credentials.
- The metadata types in scope. A "full diff" requests every type and is slow (>30 minutes for large orgs); a focused diff (Apex + LWC + Flow + custom objects) is usually enough.
- Whether the goal is *deploy* (build a package.xml and ship), *destructive* (delete from target what no longer exists in source), *audit* (just inventory drift), or some combination.

---

## Core Concepts

### Approach families

| Approach | Tool | Best for | Cost |
|---|---|---|---|
| Retrieve both orgs to local dirs and `git diff` | `sf project retrieve start` × 2 + `git diff --no-index` | Generic, unbeaten clarity | Two retrieve cycles |
| Manifest-only diff | `sf project retrieve preview` | Quick inventory of what would be retrieved | Misses content-level diffs |
| Tooling-specific | sfdx-hardis `org:diff`, Gearset, Copado | Mature workflows, UI, dependencies | License or third-party trust |
| API-level | Tooling API SOQL on `MetadataContainer` / `*Member` objects | Programmatic checks of single types | Doesn't cover all types |

### Drift classes

The diff is meaningful only when categorized. Always emit four buckets:

1. **Source-only** — exists in Org A, missing in Org B. Candidate for deploy.
2. **Target-only** — exists in Org B, missing in Org A. Candidate for destructive change *or* a hotfix you need to back-port.
3. **Changed** — exists in both, content differs. Candidate for deploy with merge review.
4. **Identical** — drop from the report. Noise.

### Ignore lists

Some metadata types diff dirty by design: profiles (auto-edited by Setup), installed packages, environmental fields (org-specific custom labels). Honor `.forceignore` and add a separate `diff-ignore.txt` for items that exist in both orgs intentionally.

---

## Common Patterns

### Pattern: pre-deploy "what's missing" diff

**When to use:** Before promoting a UAT-tested change to production, confirm production has all transitive dependencies.

**How it works:** Retrieve from UAT and Prod in parallel. `git diff --name-status` between the two retrieves. Filter to source-only items. Build a deployable `package.xml` for those items.

**Why not the alternative:** Deploying without this check often fails on a missing dependency (custom field, perm set) that wasn't in the change set.

### Pattern: post-hotfix drift inventory

**When to use:** Production hotfix landed; UAT and Dev sandboxes don't have it yet.

**How it works:** Run the diff with Prod as source and Dev as target. Source-only items are the hotfix; target-only items are work-in-progress that needs to be reconciled.

### Pattern: destructive-changes generator

**When to use:** Cleanup PR removing 12 unused custom fields. Source repo is the source of truth.

**How it works:** Run diff with the repo (or a fresh sandbox built from repo) as source and Prod as target. Target-only items become the destructiveChanges.xml entries.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| One-off check, two orgs, you trust git | Retrieve + `git diff` | Cheapest, no plugin |
| Recurring, audited, multi-team | sfdx-hardis or commercial tool | Reproducible, UI for non-engineers |
| Need diff of one specific type (e.g., flows) | Targeted retrieve with `-m Flow:*` | Avoid 30-minute full retrieve |
| Profile drift specifically | Use a profile-aware diff (sfdx-hardis) | Standard `git diff` is noise on profile XML |

---

## Recommended Workflow

1. Identify the two orgs and authenticate (`sf org login web --alias prod` etc.). Confirm both auth contexts have read access to the metadata in scope.
2. Choose the metadata-type scope. Start narrow (Apex + LWC + Flow + custom objects). Expand if drift surfaces in another type.
3. Retrieve both orgs to separate working directories. Use the same package.xml for both retrievals so the type set is symmetric.
4. Diff: `git diff --no-index --name-status orgA-source/ orgB-source/`. Pipe through a categorizer that maps to source-only / target-only / changed.
5. Apply the ignore list. Profiles, packageVersions, and any team-defined exclusions drop here.
6. Render the categorized report (Markdown table). For deploy intent, emit `package.xml`. For destructive intent, emit `destructiveChanges.xml`.
7. Hand to the deploy pipeline (or stop here for audit-only).

---

## Review Checklist

- [ ] Both orgs authenticated; auth survives the full retrieve duration
- [ ] Symmetric retrieve manifests (same types requested from both)
- [ ] Categorized output (not a single flat list)
- [ ] Ignore list applied (profiles, installed packages, sandbox-only artifacts)
- [ ] Generated `package.xml` validated against target org with `sf project deploy preview`
- [ ] `destructiveChanges.xml` reviewed by humans before any apply

---

## Salesforce-Specific Gotchas

1. **Profile XML is auto-edited by Setup** — Permissions on a field that was added in one org are silently rewritten when an admin opens the profile UI in the other. Diff-ignore profiles or use a profile-aware tool.
2. **Retrieve does not bring everything** — Some metadata types are not retrievable via Metadata API (or require Tooling API). The Metadata API Coverage report is the source of truth; assume gaps exist.
3. **Folder-bound types** (Reports, Dashboards, Email Templates) require both folder and item retrieve. A naive `Report:*` misses items in folders not enumerated.
4. **Custom labels are translation-aware** — A custom label translated in one org but not the other shows as a "changed" diff, even though the source-language version is identical.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| diff-report.md | Categorized table of source-only / target-only / changed items |
| package.xml | Deployable manifest of source-only items |
| destructiveChanges.xml | Manifest of items to remove from target (audit before apply) |
| ignore-applied.log | What was filtered and why |

---

## Related Skills

- devops/metadata-api-retrieve-deploy — for the underlying retrieve mechanics and limits
- devops/metadata-api-coverage-gaps — for which types cannot be retrieved/diffed
- devops/destructive-changes-deployment — to safely apply the destructiveChanges.xml output
- devops/sandbox-refresh-and-templates — when post-refresh drift is the actual problem to solve
