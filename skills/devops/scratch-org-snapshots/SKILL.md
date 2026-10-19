---
name: scratch-org-snapshots
description: "Use Scratch Org Snapshots to reduce CI bring-up time from 10–20 minutes to under 2. NOT for persistent sandbox provisioning — use devops/scratch-org-pools."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Operational Excellence
triggers:
  - "slow scratch org creation"
  - "snapshot scratch org"
  - "speed up ci salesforce"
  - "source push is slow"
  - "create scratch orgs from a snapshot instead of installing packages every run"
  - "rebuild our scratch org snapshot every night"
  - "why are named credentials missing in a scratch org made from a snapshot"
tags:
  - scratch-org
  - ci
  - snapshots
inputs:
  - "Dev Hub"
  - "base scratch org definition"
  - "managed package install list"
outputs:
  - "Snapshot + nightly refresh job + CI consumption pattern"
dependencies: []
version: 1.2.0
author: Pranav Nagrecha
updated: 2026-10-19
---

# Scratch Org Snapshots

A scratch org snapshot is a point-in-time copy of a configured scratch org — installed packages, features, limits, licenses, metadata, and data — that new scratch orgs can be created from, so CI stops repeating package installs and setup on every run. This skill covers enabling snapshots, building the source org, naming and allocation limits, consuming a snapshot from a definition file, rebuilding on a schedule, and what a snapshot never carries.

---

## Before Starting

- Confirm the Dev Hub edition — it sets how many snapshots you can hold and create per day.
- List what the CI org needs: managed packages, settings, baseline metadata, reference data, credentials.
- Confirm Scratch Org Snapshots is enabled in the Dev Hub and who (besides admins) needs permissions to create or view snapshots.
- Check whether the project uses a namespace.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Which Dev Hub edition, and how many snapshots will exist at once? | Active and daily snapshot allocations are per Dev Hub by edition (Developer 3, Enterprise 40, Unlimited and Performance 100) (gotcha 2). | A naming and rebuild cadence that fits the allocation. |
| Does the CI org need connected apps, external credentials, or named credentials? | Those aren't copied into a snapshot (gotcha 1). | A post-create step that deploys credential metadata and sets secrets from CI. |
| Will the source org be built fresh, or from another snapshot? | You can't snapshot an org that was created from a snapshot or with a namespace (gotcha 3). | A nightly build from the definition file and the install list. |
| What name will the snapshot have? | Names are at most 15 alphanumeric characters (gotcha 4). | A valid name, with detail in `--description`. |
| How does CI know the new snapshot is ready? | Creation is asynchronous; use it only after the status is `Active` (gotcha 5). | A poll on `OrgSnapshot.Status` before consumers switch. |
| What happens when the snapshot is missing or expired? | Snapshots expire after 90 days and allocations can run out (gotcha 6). | A fallback to the definition-file path that CI exercises regularly. |
| Will snapshots be used across a Salesforce release preview? | During preview a scratch org takes the snapshot's release version, not the Dev Hub's (gotcha 7). | Release-aware rebuilds around preview windows. |

A properly configured snapshot pipeline adds a nightly rebuild from source, a readiness check, a credential step, and a fallback, where "just snapshotting a dev org" produces a CI base that silently lacks credentials and stops working the day it expires.

---

## Core Concepts

### What a snapshot is — and isn't

A snapshot is static: to update it, delete it and create another. You create snapshots only from scratch orgs and create only scratch orgs from snapshots. Snapshots share the scratch org 200-MB data storage limit and must belong to the Dev Hub you use to create the scratch org. Connected apps, external credentials, and named credentials aren't copied, because they risk exposing sensitive data or secrets. The guide is explicit that a snapshot doesn't replace source-driven development or sandboxes for UAT.

### Enable it in the Dev Hub

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- excerpt: settings/DevHub.settings in the Dev Hub (production) org -->
<DevHubSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableScratchOrgManagementPref>true</enableScratchOrgManagementPref>
    <enableScratchOrgSnapshotPref>true</enableScratchOrgSnapshotPref>
</DevHubSettings>
```

`enableScratchOrgSnapshotPref` is available from API 61.0. Non-admin users also need a supported license and access to the Org Snapshots object through a permission set.

### Create, check, consume

```bash
sf org create snapshot --name cibase --source-org snapshot-source \
  --target-dev-hub my-dev-hub --description "CI base: packages + baseline metadata"
sf org get snapshot --snapshot cibase --target-dev-hub my-dev-hub      # wait for Active
sf org list limits -o my-dev-hub                                        # ActiveOrgSnapshots, DailyOrgSnapshots
```

Consume it from a definition file that names `snapshot` instead of `edition`, and leaves out `edition`, `features`, `hasSampleData`, `release`, and `sourceOrg`:

```json
{
  "orgName": "CI PR check",
  "snapshot": "cibase"
}
```

`sf org create scratch --definition-file config/ci-scratch-def.json --target-dev-hub my-dev-hub --wait 10`; the guide suggests a larger `--wait` because creating from a snapshot can take longer. Settings that aren't inherited from the snapshot can be added under `settings` in the same file.

---

## Recommended Workflow

1. Enable Scratch Org Snapshots in the Dev Hub and grant non-admin users the Org Snapshots object permissions.
2. Build the source org nightly from `config/project-scratch-def.json` (not from a snapshot, without a namespace), install packages, deploy baseline metadata, load only static reference data; finish configuring before running the snapshot command.
3. Create the snapshot with an alphanumeric name of 15 characters or fewer, alternating two names so the previous one stays usable; poll until `Active`.
4. Point `config/ci-scratch-def.json` at the active snapshot and run `python3 skills/devops/scratch-org-snapshots/scripts/check_scratch_org_snapshots.py --manifest-dir .` — it ERRORs on invalid names and on `edition`/`features`/`hasSampleData`/`release`/`sourceOrg` next to `snapshot`.
5. In every CI job, add the credential step and the fallback path from `references/examples.md`; delete the old snapshot only after consumers have switched.

---

## Decision Guidance

| Situation | Approach | Why |
|---|---|---|
| Package installs dominate CI bring-up | Snapshot with packages installed | Installs happen once per rebuild, not per run |
| Small Developer Edition Dev Hub | One or two long-lived names, rebuilt on a schedule | Allocation is 3 active and daily |
| CI needs callouts | Deploy credential metadata and set secrets after create | Credentials aren't copied into snapshots |
| Namespaced project | Snapshot a `--no-namespace` source org, create namespaced orgs from it | Namespaced orgs can't be snapshotted but can be created from one |
| Release preview window | Rebuild the snapshot on the release the tests should run on | The scratch org takes the snapshot's release version |

---

## Review Checklist

- [ ] Snapshot names are alphanumeric and 15 characters or fewer
- [ ] Snapshot definition files omit `edition`, `features`, `hasSampleData`, `release`, `sourceOrg`
- [ ] The source org is rebuilt from source, not from a snapshot, and has no namespace
- [ ] CI waits for `Active` before switching consumers
- [ ] A credential step runs after every create from a snapshot
- [ ] The definition-file fallback runs on a schedule
- [ ] Allocation (`ActiveOrgSnapshots`, `DailyOrgSnapshots`) is monitored
- [ ] The checker exits 0

---

## Salesforce-Specific Gotchas

Full list in `references/gotchas.md`. The two that break CI most often:

1. **No credentials in snapshots** — connected apps, external credentials, and named credentials aren't copied.
2. **90-day expiry** — a snapshot nobody rebuilds disappears from under the pipeline.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Snapshot | Alphanumeric name, rebuilt nightly from source |
| `config/ci-scratch-def.json` | `snapshot` key plus non-inherited settings |
| Nightly rebuild workflow | Build source org → snapshot → poll `Active` → switch → delete old |
| CI consumption pattern | Create from snapshot, credential step, fallback |

---

## Reference Files

| File | Use it for |
|---|---|
| `references/examples.md` | Consuming a snapshot with a credential step and fallback; a nightly rebuild within the allocation |
| `references/gotchas.md` | Seven snapshot behaviours with avoidance steps |
| `references/llm-anti-patterns.md` | Snapshot mistakes AI assistants make |
| `references/well-architected.md` | Pillar framing and the guide lines behind each claim |
| `references/snapshot-operations.md` | Allocation table, status values, permissions, and release-version behaviour in one place |

---

## Related Skills

- `devops/scratch-org-pools` — pre-warmed pools of scratch orgs
- `devops/scratch-org-management` — scratch org lifecycle in general
- `devops/org-shape-and-scratch-definition` — the definition file's edition, features, and settings keys
