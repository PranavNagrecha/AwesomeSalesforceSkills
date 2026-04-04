---
name: omniscript-versioning
description: "Use when managing OmniScript versions: activating new versions, deactivating prior versions, testing a specific version before activation, rolling back to a previous version, or understanding version identity (Type/Subtype/Language triplet). NOT for OmniStudio deployment or DataPack migration (use omnistudio/omnistudio-deployment-datapacks)."
category: omnistudio
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "how do I activate a new version of an OmniScript in production"
  - "how do I roll back to the previous OmniScript version after a bad activation"
  - "I accidentally activated the wrong OmniScript version and users are seeing errors"
  - "what happens to the old OmniScript version when I activate a new one"
  - "how do I test an OmniScript version before activating it in production"
tags:
  - omniscript
  - versioning
  - activation
  - rollback
  - omnistudio
inputs:
  - "OmniScript Type, Subtype, and Language (the identity triplet)"
  - "Current active version number and the new version number to activate"
  - "Test results for the new version in a sandbox"
outputs:
  - "Activation checklist for the target version"
  - "Rollback procedure if the new version needs to be reverted"
  - "Version comparison guidance"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# OmniScript Versioning

This skill activates when a practitioner needs to manage the version lifecycle of an OmniScript: activating a new version, deactivating a prior version, testing a specific version before promotion, or rolling back to a previously active version. OmniScript versioning is identity-based — the combination of Type, Subtype, and Language defines a unique OmniScript, and only one version per triplet can be active at a time.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the OmniScript's identity triplet: **Type** (e.g., `CreateCase`), **Subtype** (e.g., `Default`), and **Language** (e.g., `English`). Every operation targets this specific triplet. Changing any part of the triplet creates a distinct OmniScript.
- Know the current active version number. You can find this in OmniStudio > OmniScripts by filtering on the triplet and looking for the row with Status = Active.
- Confirm that the new version has been tested in the target org or a matching sandbox before activation. There is no staged promotion mechanism — activation is immediate.

---

## Core Concepts

### Version Identity: Type + Subtype + Language

An OmniScript is uniquely identified by its Type, Subtype, and Language triplet. Version numbers exist within that triplet. You can have version 1, 2, 3 of `CreateCase / Default / English` — they are all the same OmniScript at different points in time.

This means:
- If you need to test a change in isolation without affecting production users, you must test in a separate org/sandbox — there is no draft/staging state within a single org.
- If you change the Type or Subtype, you create a completely new OmniScript, not a new version of the existing one.

### Only One Active Version Per Triplet

At any point in time, only one version of a given Type+Subtype+Language triplet can be Active. When you activate version 3, version 2 is implicitly **deactivated**. The platform does not prompt or warn you — the transition is immediate.

Practical implication: if version 2 is active in production and you need to test version 3 before fully replacing it, you cannot run both simultaneously in the same org. You must test in a sandbox that mirrors production, then activate version 3 in production when ready.

### Rollback = Reactivate a Prior Version

There is no dedicated rollback command. Rolling back means reactivating an older version number. If version 3 has a defect after activation:
1. Navigate to the version list for the triplet.
2. Open version 2 (or whichever was previously active).
3. Click Activate.
4. Version 3 is immediately deactivated; version 2 is now active.

The prior version's definition is intact as long as it has not been deleted from the org. Versions are not deleted when deactivated — they persist until manually deleted.

### Activation via Metadata API and DataPacks

OmniScripts can also be activated and deactivated programmatically:
- **Metadata API**: The `OmniProcess` metadata type includes an `IsActive` field. Deploying a version with `IsActive = true` activates it.
- **DataPacks**: When importing a DataPack containing an OmniScript, the `activate` option controls whether the imported version becomes active immediately.

This means CI/CD pipelines must be careful: deploying a DataPack with `activate: true` will immediately deactivate whatever version was previously active in the target org.

---

## Common Patterns

### Activating a New Version

**When to use:** A new version has been built and tested in a sandbox and is ready to replace the current active version in production.

**How it works:**
1. Open OmniStudio > OmniScripts.
2. Filter by Type and Subtype to find all versions of the triplet.
3. Confirm the new version number exists and has Status = Inactive.
4. Click the row menu > Activate on the new version.
5. Confirm: the new version shows Active; the previously active version shows Inactive.
6. Test the live OmniScript immediately post-activation (launch URL or embedded component).

**Why not activate in production directly after editing:** Editing an OmniScript in production does not create a new version automatically. You must explicitly save as a new version and then activate it. Editing the active version in place is not recommended — it changes the definition live without a rollback point.

### Rolling Back to a Prior Version

**When to use:** The newly activated version has a defect and the prior version must be restored.

**How it works:**
1. Open OmniStudio > OmniScripts.
2. Filter by Type and Subtype.
3. Identify the version that was active before the bad activation (e.g., version 2 if version 3 just broke things).
4. Click Activate on version 2.
5. Version 3 is deactivated immediately. Version 2 is now serving users.
6. Document the rollback and create a work item to fix version 3 before re-promoting.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Testing new version without affecting active users | Test in sandbox, not same production org | Only one active version per triplet — you cannot run a draft alongside the live version |
| CI/CD pipeline importing DataPack with OmniScript | Set `activate: false` on import in UAT, `activate: true` only in scheduled production deployment | Prevents accidental activation in wrong environment |
| Defect in newly activated version | Activate the prior version number immediately | Fastest recovery; no deployment needed |
| Version accidentally deleted before rollback | Retrieve from DataPack backup, re-import with activate flag | Always export DataPacks before making version changes in production |
| Comparing two versions side by side | Export both versions as JSON, diff the files | No native compare UI; JSON export enables text diff |

---

## Recommended Workflow

1. Identify the OmniScript triplet (Type + Subtype + Language) and the target version number to activate.
2. Confirm the version has been fully tested in a sandbox that reflects the production configuration.
3. Export a DataPack of the currently active version to a backup location before making any changes. This is your rollback artifact.
4. In the target org, navigate to OmniStudio > OmniScripts and activate the new version.
5. Immediately test the live OmniScript by launching it directly and running through the key steps.
6. If a defect is found, activate the prior version number within the same triplet to roll back.
7. Document the version change in your release notes: old version number, new version number, change summary, and activation timestamp.

---

## Review Checklist

- [ ] OmniScript Type, Subtype, and Language triplet confirmed
- [ ] New version tested in a matching sandbox before production activation
- [ ] DataPack backup of the current active version exported and stored
- [ ] Activation completed and confirmed (new version Active, old version Inactive)
- [ ] Post-activation smoke test executed and passed
- [ ] Version change documented in release notes with activation timestamp

---

## Salesforce-Specific Gotchas

1. **Activating a new version immediately deactivates the prior one** — there is no grace period, staged rollout, or warning. Users currently mid-session on the OmniScript may experience an interruption if a session was in progress during activation. Schedule activations during low-traffic windows.
2. **DataPack import with activate:true bypasses your approval process** — if your CI/CD pipeline automatically imports DataPacks with activation enabled, a bad push to the deployment branch will activate an untested version in production. Always control the activate flag explicitly in CI pipelines.
3. **Deleted versions cannot be recovered from the UI** — if you delete version 2 and then need to roll back from version 3, the only recovery path is re-importing from a DataPack backup. Export DataPacks before destructive operations.
4. **Activation does not validate OmniScript correctness** — activating a version with a misconfigured step, broken Remote Action reference, or invalid LWC element succeeds silently. The error only surfaces when a user runs the script. Always test before activating.
5. **Version numbers are sequential integers, not semantic versions** — OmniScript version numbers auto-increment (1, 2, 3...). You cannot set a custom version label. Document the business meaning of each version number in your release notes or a companion custom object.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Activation checklist | Ordered pre/during/post activation steps for the specific triplet being promoted |
| DataPack backup | Exported DataPack of the currently active version before any version change |
| Rollback procedure | Named steps to reactivate the prior version and verify the rollback succeeded |

---

## Related Skills

- omnistudio/omnistudio-deployment-datapacks — DataPack export, import, and CI/CD for OmniStudio components
- omnistudio/omniscript-design-patterns — OmniScript design and step configuration
- omnistudio/omnistudio-debugging — debugging OmniScript runtime errors
