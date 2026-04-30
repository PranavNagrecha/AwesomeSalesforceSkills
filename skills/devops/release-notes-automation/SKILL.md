---
name: release-notes-automation
description: "Use when generating customer- or stakeholder-facing release notes from git history, Jira/ADO ticket links, and Salesforce metadata diffs at deploy time. Triggers: 'auto-generate release notes', 'changelog from commits', 'release notes from PR titles', 'what changed in this deployment'. NOT for managed-package version creation, push upgrades, or org assessment."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
triggers:
  - "auto-generate release notes from git tags"
  - "changelog generator for the next salesforce release"
  - "summarize what changed in a sandbox deployment"
  - "Jira ticket aggregation into stakeholder-facing release notes"
  - "release notes pipeline failing to find the previous tag"
tags:
  - release
  - changelog
  - ci-cd
  - automation
inputs:
  - "git repository with conventional or PR-based commits"
  - "previous release tag and the head ref to compare"
  - "ticket-tracker integration (Jira/ADO/GitHub Issues) credentials, optional"
outputs:
  - "ordered, deduplicated release notes (Markdown)"
  - "metadata-diff summary attached to the release"
  - "release tag or GitHub Release entry"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-30
---

# Release Notes Automation

Activate when an engineering team is shipping Salesforce work on a regular cadence (weekly, monthly, per-sprint) and the release notes are still being hand-written. The skill produces a deterministic pipeline that turns the git diff between two refs plus linked tickets into stakeholder-facing notes, attaches the metadata diff, and posts the result to the release tracking surface.

---

## Before Starting

Gather this context before working on anything in this domain:

- The repo's commit-message convention (Conventional Commits, "JIRA-1234: Title", PR-squashed, freeform). Without a convention, the pipeline can only group by file path or PR title — both noisier than ticket-keyed grouping.
- Whether the team uses GitHub Releases, Bitbucket Tags, Azure DevOps Releases, or a wiki page. The output shape needs to match.
- Who reads the notes. A "developer changelog" lists every PR; a "stakeholder release note" hides infra commits and groups by feature. Often you need both, generated from the same source.

---

## Core Concepts

### Range of changes

Release notes always span `from-ref...to-ref`. The pipeline must resolve `from-ref` deterministically — usually the previous git tag matching a release pattern (e.g., `v*`). `git describe --tags --abbrev=0 --match 'v*' to-ref^` is the canonical resolver. Fallbacks include "first commit" for the initial release and a manually overridden previous-ref for hotfix branches.

### Categorization

Conventional Commits give the pipeline `feat:`, `fix:`, `chore:`, `refactor:` prefixes — the cheapest possible grouping. Where the team uses Jira keys instead, fetch issue type from the tracker and map to Added/Fixed/Changed/Deprecated/Removed/Security (Keep a Changelog convention). PR labels are the third option, useful when the merge-commit subject is squashed.

### Metadata diff

For Salesforce-specific notes, the package-level diff matters: which Apex classes, LWCs, Flows, custom objects, and permission sets changed. `sf project deploy preview` or a `git diff --name-only` filtered to `force-app/main/default/...` gives a metadata-aware section that complements the human-readable Jira summary.

---

## Common Patterns

### Pattern: Conventional Commits + git tag pipeline

**When to use:** Team disciplines commits with `feat:`/`fix:`/etc.

**How it works:** GitHub Action triggered on tag push. Resolves previous tag, runs `git log` between tags, groups by Conventional Commits prefix, posts a GitHub Release with the grouped Markdown.

**Why not the alternative:** Hand-typing release notes from `git log` output is reliable for releases 1–3 and degrades fast.

### Pattern: Jira-keyed grouping

**When to use:** Commit messages contain `ABC-1234` keys but no convention prefix.

**How it works:** Pipeline parses Jira keys from each commit subject, calls Jira's `/rest/api/3/issue/{key}` once per unique key (with caching), groups by issue type (Story/Bug/Task), and emits the title from Jira plus a link.

### Pattern: Salesforce metadata-diff section

**When to use:** Product manager wants to know "did Apex change in this release?"

**How it works:** Append a section listing changed `force-app/main/default/<type>/<name>` paths grouped by metadata type, derived from `git diff --name-status from-ref to-ref -- force-app/`.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Brand-new repo, no convention yet | Conventional Commits + commitlint pre-commit hook | Cheapest discipline; pipeline is generic |
| Established repo with Jira keys in commits | Jira-keyed grouping with caching | Existing data; no commit-flow churn |
| Mixed audience (dev + stakeholders) | Generate two outputs from the same run | Devs see commits; PMs see Jira summaries |
| Hotfix release off a previous tag | Manual `from-ref` override input | Auto-resolution of previous tag picks the wrong base |

---

## Recommended Workflow

1. Confirm the commit/PR convention. If absent, propose adopting one before automating.
2. Decide the trigger: tag push, manual workflow dispatch, or the deployment-promotion pipeline. Tag push is simplest; deployment-promotion ties notes to the actual production change.
3. Implement the from-ref resolver. Use `git describe --tags --abbrev=0 --match '<release-tag-pattern>' <to-ref>^`. Add a fallback for the initial release.
4. Implement the grouping. Conventional Commits is regex; Jira-keyed needs API token storage in the pipeline secret manager (see `devops/pipeline-secrets-management`).
5. Append the Salesforce metadata-diff section using `git diff --name-status from-ref to-ref -- force-app/`. Group by `<type>/<name>`.
6. Render Markdown and post to GitHub Release / Bitbucket Tag / wiki. Store the artifact alongside the release tag for audit.
7. Validate the output on a real release before declaring done. Hand-review the first three runs; tune category mappings.

---

## Review Checklist

- [ ] `from-ref` resolution is deterministic and survives hotfix branches
- [ ] Output is reproducible — re-running on the same range yields byte-identical Markdown
- [ ] Jira/ADO API tokens are stored in the secret manager, not the workflow YAML
- [ ] Salesforce metadata-diff section grouped by metadata type
- [ ] Two output flavors (dev / stakeholder) wired if both audiences exist
- [ ] Failed pipeline does not silently drop notes — tag push without notes is alerted

---

## Salesforce-Specific Gotchas

1. **Squashed PR commits lose individual ticket keys** — Whatever the merge-commit subject contains is the only data the pipeline sees. Discipline merge subjects, or read PR descriptions via the Git host API.
2. **Metadata-diff on `force-app/` misses `manifest/package.xml` changes** — Adding a new metadata type via package.xml without source files (rare but real) shows up as zero source-file changes. Diff `manifest/package.xml` separately if you generate it.
3. **Tag pattern collisions** — `git describe --match 'v*'` matches `v1.0.0` and a stray `version-x` tag from a contributor. Pin the pattern (`v[0-9]*`) precisely.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| RELEASE_NOTES.md | The grouped, audience-targeted Markdown |
| metadata-diff.md | Per-type list of changed metadata source paths |
| GitHub/Bitbucket Release | The hosted artifact, tagged at `to-ref` |

---

## Related Skills

- devops/git-branching-for-salesforce — branching model determines what `from-ref` and `to-ref` mean
- devops/pipeline-secrets-management — for storing Jira/ADO tokens used by the categorizer
- devops/managed-package-development — when the deliverable is a package version, the version's release notes feed the same artifact
