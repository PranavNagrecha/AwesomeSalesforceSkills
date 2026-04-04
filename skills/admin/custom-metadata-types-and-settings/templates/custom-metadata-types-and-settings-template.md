# Custom Metadata Types And Settings — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `custom-metadata-types-and-settings`

**Request summary:** (fill in what the user or ticket asked for)

---

## Context Gathered

Answer these before recommending a storage model:

- **Per-user or per-profile override needed?**
  [ ] Yes — Hierarchical Custom Setting is likely correct
  [ ] No — Custom Metadata Type is the default

- **Must values deploy with releases (change set / package / SFDX)?**
  [ ] Yes — Custom Metadata Type required
  [ ] No — Custom Setting is acceptable

- **Who changes the values?**
  [ ] Release team (dev/admin via deployment) → CMT
  [ ] Admin in Setup (without deployment) → Custom Setting
  [ ] End-user for their own preferences → Hierarchical Custom Setting (User level)

- **Read volume / governor limit concern?**
  [ ] High-volume Apex (batch, trigger) → CMT preferred (zero SOQL cost)
  [ ] Low-volume / standard transactions → either is acceptable

- **Is this a new implementation or a migration?**
  [ ] New — avoid List Custom Settings entirely
  [ ] Migration from List Custom Setting → migrate to CMT
  [ ] Migration from Hierarchical Custom Setting → confirm override behavior is preserved

---

## Decision

**Chosen storage type:** (Custom Metadata Type / Hierarchical Custom Setting)

**Rationale:** (one sentence)

---

## Implementation Plan

### Type Definition

| Field Name | Field Type | Notes |
|---|---|---|
| (field name) | (Text / Number / Checkbox / etc.) | (purpose) |

### Key / Lookup Strategy

- CMT: `DeveloperName` = (stable key value, e.g. `Payment_Gateway_Config`)
- Custom Setting: `SetupOwnerId` levels to populate: Org / Profile (which profiles?) / User (which users?)

### Apex Access Pattern

```apex
// Paste the access pattern from references/examples.md appropriate to the chosen type
```

### Flow Access

- CMT: Get Records element on `[TypeName]__mdt`, filter by `DeveloperName` — zero SOQL cost
- Custom Setting: Get Records element on `[SettingName]__c` — counts 1 SOQL query per element

---

## Deployment And Post-Deploy Setup

### For Custom Metadata Types
- [ ] Type definition and records committed to source control under `force-app/main/default/customMetadata/`
- [ ] Records included in change set or package
- [ ] `DeveloperName` values are stable and documented as part of the access contract

### For Hierarchical Custom Settings
- [ ] Field definition committed to source control
- [ ] Post-deploy script documented and included in pipeline:
  - Org default record upsert (required for every org)
  - Profile-level records upsert (if applicable)
  - User-level records: document who sets these and how
- [ ] Runbook updated with setup steps for new sandboxes and scratch orgs

---

## Checklist

Copy from SKILL.md Review Checklist and tick items as complete:

- [ ] Requirement confirmed as configuration, not business data
- [ ] Per-user/profile override requirement correctly drives storage choice
- [ ] Deployment requirement correctly drives storage choice
- [ ] No List Custom Settings created new
- [ ] CMT queries use stable `DeveloperName` keys
- [ ] Custom Setting Apex access uses `getInstance()` / `getValues()` with null checks
- [ ] SOQL governor budget reviewed for transaction context
- [ ] Post-deploy data setup documented for Custom Settings
- [ ] No secrets stored in either storage type
- [ ] Flow governor-limit implications noted and accepted

---

## Notes

(Record any deviations from the standard pattern and why.)
