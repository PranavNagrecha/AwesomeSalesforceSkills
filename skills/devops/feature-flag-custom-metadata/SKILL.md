---
name: feature-flag-custom-metadata
description: "Implement environment-safe feature flags using Custom Metadata Types for Apex, LWC, and Flow. NOT for user-level entitlements or permission sets — use admin/custom-metadata-types."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "feature flag salesforce"
  - "custom metadata toggle"
  - "gradual rollout apex"
  - "kill switch feature"
  - "add a feature flag so we can deploy the code dark and switch it on later"
  - "roll a new Apex feature out to ten percent of users"
  - "turn a feature off in production without a deployment window"
tags:
  - feature-flag
  - custom-metadata
  - release
inputs:
  - "feature name"
  - "rollout criteria"
  - "consuming components"
outputs:
  - "Feature_Flag__mdt record + Apex/LWC/Flow accessor"
dependencies: []
version: 1.2.0
author: Pranav Nagrecha
updated: 2026-10-19
---

# Feature Flags via Custom Metadata

Feature flags decouple deploy from release. Custom Metadata Type records are metadata: they deploy with the codebase, are readable from Apex, flows, formula fields, and validation rules through the application cache, and change per environment through a metadata deployment or Setup. This skill defines a canonical `Feature_Flag__mdt` layout (`Is_Enabled__c`, `Percent_Rollout__c`) and a `FeatureFlags` Apex accessor; the canonical CMDT accessor shape lives in `templates/apex/cmdt/`.

---

## Before Starting

- Is this a release toggle (temporary, org-wide, "is this code path live") or an entitlement ("may this user do this")? Entitlements are Custom Permissions in permission sets, not flags.
- Which consumers read the flag: Apex only, or also LWC (through an `@AuraEnabled` Apex method) and flows?
- Who flips it in each environment, and through what — Setup, a deployment from source control, or an Apex `Metadata.Operations.enqueueDeployment` toggle?

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| What value does the committed record carry, and who enables it per environment? | A record committed enabled turns the feature on the moment the deployment finishes (gotcha 3). | A disabled default in source and a named, per-environment enablement step. |
| Will later deployments re-send the record, and with which `<values>`? | Leaving a field's `<values>` out of an updated record keeps the org's current value; an explicit `xsi:nil` clears it (gotcha 6). | A rule for whether source or the org owns the live value after first deploy. |
| Is the rollout a percentage of users, and must a user see a stable answer? | Random selection flips per evaluation; only a hash of user and flag gives a stable cohort (gotcha 1). | A deterministic bucket function and the seed it uses. |
| Does any flag field hold a list (users, profiles, record types)? | `getAll()` / `getInstance()` return only the first 255 characters of a field, and there is no multi-select field type for custom metadata values (gotcha 4). | Short scalar fields on the flag, with lists moved to permissions or child records. |
| Does anything need to change the flag from code at runtime? | Custom metadata can't be changed with DML; Apex deploys it asynchronously through `Metadata.Operations` (gotcha 5). | A deliberate toggle path (Setup, deployment, or an enqueued deployment with a callback). |
| How will tests control the flag? | Tests cannot insert or update custom metadata records with DML (gotcha 7). | An accessor that accepts an in-memory override so tests never depend on org records. |
| When is the flag deleted? | Dead flags accumulate as permanent branches nobody dares remove (gotcha 2). | A removal date or release, recorded with the flag. |

A properly configured flag adds a disabled default in source, a deterministic rollout, a documented owner of the live value, and a removal date, where "just adding a checkbox" ships a feature that turns itself on at deploy time and never goes away.

---

## Core Concepts

### Why Custom Metadata, not a Custom Setting

Custom metadata records are deployable metadata (`CustomMetadata`, suffix `.md`, folder `customMetadata`). Custom setting rows are data: they are copied into sandboxes but are treated as data for Apex test isolation and are not part of a deployment. The SOQL query limit doesn't apply to custom metadata types — a transaction can run unlimited SOQL against them — and `getAll()` / `getInstance()` read from the application cache without a query at all.

### The flag type and a record

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- customMetadata/Feature_Flag.NewDiscountEngine.md-meta.xml: committed DISABLED -->
<CustomMetadata xmlns="http://soap.sforce.com/2006/04/metadata"
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    <label>New Discount Engine</label>
    <protected>false</protected>
    <values>
        <field>Is_Enabled__c</field>
        <value xsi:type="xsd:boolean">false</value>
    </values>
    <values>
        <field>Percent_Rollout__c</field>
        <value xsi:type="xsd:double">10.0</value>
    </values>
</CustomMetadata>
```

`Is_Enabled__c` is a Checkbox (`xsd:boolean`); `Percent_Rollout__c` is a Number with scale 1 (`xsd:double`; a scale-0 Number would be `xsd:int`). The type definition (`objects/Feature_Flag__mdt/`) is shown in `references/metadata-examples.md`.

### Reading the flag

Apex reads through `Feature_Flag__mdt.getInstance('NewDiscountEngine')`, which returns null when no record matches — treat null as "off". LWC calls an `@AuraEnabled(cacheable=true)` Apex method that wraps the same accessor. Flows read the record directly, since custom metadata is exposed to flows as well as Apex. Keep the read above any per-record loop: the query is exempt from the SOQL limit, not from CPU time.

---

## Recommended Workflow

1. Answer the Questions table; if any answer describes an entitlement, stop and design a Custom Permission instead.
2. Create `Feature_Flag__mdt` with `Is_Enabled__c` (Checkbox) and `Percent_Rollout__c` (Number, 0–100) — start from `templates/apex/cmdt/` and `references/metadata-examples.md`.
3. Commit each flag record with `Is_Enabled__c = false` under `customMetadata/`, and write the `FeatureFlags` accessor from `references/examples.md` (deterministic hash, null-safe, test override).
4. Run `python3 skills/devops/feature-flag-custom-metadata/scripts/check_feature_flag_custom_metadata.py --manifest-dir force-app` and fix every ERROR (enabled-by-default record, missing `Is_Enabled__c`) before merging.
5. Enable per environment through Setup or a targeted deployment, and record who enabled it and when.
6. After the rollout, delete the flag and its branch in code in the next release, or keep it deliberately as a documented kill switch.

---

## Decision Guidance

| Need | Use | Not |
|---|---|---|
| Org-wide on/off for a code path | `Feature_Flag__mdt.Is_Enabled__c` | Hierarchy Custom Setting (data, not deployed) |
| Stable percentage rollout | Hash of user ID + flag name, compared to `Percent_Rollout__c` | `Math.random()` |
| Per-user or per-profile permanent access | Custom Permission + permission set, `FeatureManagement.checkPermission` | Allow-list text on a flag |
| Flip from an admin screen | `Metadata.Operations.enqueueDeployment` + `Metadata.DeployCallback` | `update` on the `__mdt` record |
| Long configuration text | SOQL on the `__mdt` type | `getInstance()` (255-character truncation) |

---

## Review Checklist

- [ ] Every committed flag record has `Is_Enabled__c` set to `false`
- [ ] Rollout uses a deterministic hash seeded with user ID and flag name
- [ ] No list-valued fields on the flag are read through `getAll()` / `getInstance()`
- [ ] The accessor treats a missing record as "off" and supports a test override
- [ ] Entitlements use Custom Permissions, not flag fields
- [ ] Each flag has a removal release recorded
- [ ] The checker exits 0 on the package directory

---

## Salesforce-Specific Gotchas

Full list in `references/gotchas.md`. The two that cause incidents:

1. **Committed enabled** — the record deploys enabled and the feature is live at deploy time.
2. **Omitted values persist** — re-deploying a record without a field's `<values>` leaves the org's current value in place.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `Feature_Flag__mdt` type | Checkbox + percentage fields, deployed with the source |
| Flag records | One `.md-meta.xml` per flag, committed disabled |
| `FeatureFlags` accessor | Null-safe, deterministic rollout, test override |
| Checker output | `check_feature_flag_custom_metadata.py` run attached to the PR |

---

## Reference Files

| File | Use it for |
|---|---|
| `references/examples.md` | The accessor with a deterministic canary, and an admin toggle via `Metadata.Operations` |
| `references/gotchas.md` | Seven behaviours that break flags in production |
| `references/llm-anti-patterns.md` | Flag mistakes AI assistants make, with detection hints |
| `references/well-architected.md` | Pillar reasoning and the corpus lines behind each claim |
| `references/metadata-examples.md` | The `Feature_Flag__mdt` type definition and a test override pattern |

---

## Related Skills

- `apex/feature-flags-and-kill-switches` — release practice around flags: canary design, kill-switch drills, flag lifecycle
- `apex/custom-metadata-in-apex` — general CMDT access patterns in Apex
- `admin/custom-metadata-types` — designing custom metadata types declaratively
- `devops/environment-specific-value-injection` — per-environment values that are configuration rather than release toggles
