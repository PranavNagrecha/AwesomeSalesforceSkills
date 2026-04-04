---
name: custom-metadata-types-and-settings
description: "Use when choosing between Custom Metadata Types and Custom Settings, understanding hierarchical vs list settings, deployment behavior, governor limit implications, or accessing either from Apex and Flow. Trigger keywords: 'custom metadata vs custom settings', 'hierarchical settings per user profile', 'deployable config vs runtime settings', 'getValues getInstance in apex', 'flow get records custom settings'. NOT for custom objects (use object-creation-and-design), NOT for Named Credentials (use named-credentials-setup), NOT for general CMT field design in isolation (use custom-metadata-types)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
  - Performance
tags:
  - custom-metadata-types
  - custom-settings
  - hierarchical-settings
  - deployable-config
  - governor-limits
  - configuration
triggers:
  - "should I use custom metadata types or custom settings for this configuration"
  - "how does hierarchical custom settings work for user and profile overrides"
  - "will querying custom settings consume SOQL governor limits in apex"
  - "can I deploy custom settings in a change set or managed package"
  - "how to access custom metadata from flow without using a soql query"
  - "what is the difference between list type and hierarchical custom settings"
  - "custom settings getValues versus getInstance versus get records in flow"
inputs:
  - "whether the configuration must travel through change sets, packages, or CI/CD pipelines"
  - "whether the values need to vary by user, profile, or org level"
  - "how frequently the values change and who owns the changes"
  - "whether Apex, Flow, or both need to read the configuration"
outputs:
  - "storage decision: Custom Metadata Type vs Hierarchical Custom Setting vs List Custom Setting"
  - "Apex access pattern for the chosen storage type with correct method signatures"
  - "Flow access pattern noting governor-limit implications"
  - "deployment-readiness assessment for the chosen approach"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

Use this skill when a requirement involves choosing between Custom Metadata Types and Custom Settings, understanding how hierarchical settings resolve per user or profile, whether the data can be deployed, or how to access configuration from Apex and Flow without hitting governor limits. The key decision driver is whether the configuration must travel with releases or must override at runtime per user.

---

## Before Starting

Gather this context before recommending a storage model:

- Does the value need to vary by User, Profile, or just have a single org-wide value?
- Does the value need to travel through source control, change sets, scratch orgs, or managed packages — or is it fine to set manually in each org?
- How frequently will the value change, and who controls the change: a developer cutting a release, an admin in Setup, or an end-user editing their own preference?
- Will Apex or Flow read this — and how many times per transaction?

---

## Core Concepts

### Custom Metadata Types: Configuration That Ships With The App

Custom Metadata Type (CMT) records are metadata, not data. They move through change sets, unlocked packages, managed packages, and source-control-driven deployments exactly like Apex classes or field definitions. The key facts:

- **SOQL is free**: querying CMT from Apex does not consume the 100 SOQL query governor limit. The platform caches the metadata and serves it without a database round trip.
- **Flow Get Records is also free**: accessing CMT through the Flow Get Records element costs no SOQL queries.
- **Storage cap**: 200 records per type, 10 MB total custom metadata storage per org.
- **Deployment**: included automatically in change sets, scratch org source pushes, and packaging. Records and type definition both move together.
- **Editable in production**: an admin can edit CMT records directly in a production org through Setup. This is unlike Apex, which requires a sandbox round trip, but still treats the record as metadata that should be tracked in source control.
- **No per-user override**: CMT has no built-in hierarchy. All users see the same values for a given record.
- **Relationships**: CMT fields can hold a Metadata Relationship to another CMT type, enabling lookup-style joins entirely within metadata.

### Custom Settings: Two Very Different Types

Salesforce offers two kinds of Custom Settings and they solve different problems.

**Hierarchical Custom Settings** are the most useful kind. They resolve at three levels — User, Profile, and Org Default — with the most specific level winning:

```
User override  >  Profile override  >  Org Default
```

When Apex calls `MySettings__c.getInstance()` or `MySettings__c.getValues(userId)`, the platform returns the most specific record in the hierarchy for the calling or specified user. This makes hierarchical settings ideal for anything that legitimately needs different values for different users without writing custom logic.

**List Custom Settings** are a flat key-value store (the key is the record Name). Salesforce deprecated List Custom Settings in Lightning Experience and recommends using Custom Metadata Types instead for new implementations. Existing List Custom Settings still work, but no new List Custom Settings should be created.

Both types of Custom Settings:
- Are NOT included in change sets or packages by default. They are org-specific runtime data.
- DO consume SOQL governor limits when queried from Apex via the static methods or via Flow's Get Records element.
- Can be edited by admins through Setup without a deployment.
- Support field-level security and visibility controls.

### Governor Limit Implications

This is the most commonly misunderstood difference:

| Access Method | CMT | Hierarchical Custom Setting |
|---|---|---|
| Apex SOQL query | 0 SOQL queries consumed | 1 SOQL query consumed |
| `getInstance()` / `getValues()` | N/A (not applicable) | 1 SOQL query per call (first call cached in request) |
| Flow Get Records | 0 SOQL queries consumed | 1 SOQL query per Get Records element |

Custom Settings are cached at the request level after the first call in a transaction, so multiple calls to `getInstance()` in one transaction do not each cost a SOQL query. However, the first call does count, and in high-volume Apex scenarios (batch, triggers processing many records) this matters.

CMT queries are served from the metadata cache and never count against the SOQL limit regardless of how many times they are called.

### Deployment Behavior Comparison

| Behavior | Custom Metadata Type | Hierarchical Custom Setting | List Custom Setting |
|---|---|---|---|
| Included in change set | Yes (type + records) | No | No |
| Included in packages | Yes | No | No |
| Source control via SFDX | Yes (`customMetadata/`) | No (org-only) | No (org-only) |
| Editable in production without deployment | Yes | Yes | Yes |
| Per-user/profile override | No | Yes (hierarchical) | No |
| SOQL governor cost | None (cached) | Counts (first call) | Counts |

---

## Common Patterns

### Pattern 1: App Configuration That Deploys With Releases

**When to use:** Routing rules, feature flags, thresholds, endpoint paths, or any setting that should be consistent across dev, QA, UAT, and production environments and that changes only with a release.

**How it works:** Model the configuration in a Custom Metadata Type. Store the type definition and records in source control under `force-app/main/default/customMetadata/`. Promote them through the standard deployment pipeline. Apex and Flow read values by `DeveloperName` key.

```apex
// Zero SOQL cost — reads from metadata cache
Feature_Flag__mdt flag = [
    SELECT DeveloperName, Is_Enabled__c
    FROM Feature_Flag__mdt
    WHERE DeveloperName = 'New_Checkout_Flow'
    LIMIT 1
];
if (flag.Is_Enabled__c) {
    // route to new flow
}
```

In Flow, use a Get Records element targeting `Feature_Flag__mdt` filtered by `DeveloperName`. This costs no SOQL queries.

**Why not Custom Settings:** The value is not per-user and it must travel through source control to ensure every sandbox and production sees the same configuration.

---

### Pattern 2: Per-User Or Per-Profile Behavior Overrides

**When to use:** A feature should behave differently for admins vs standard users, or individual users need a personal preference (time zone display, record owner default, notification threshold).

**How it works:** Create a Hierarchical Custom Setting. Set the Org Default in Setup as the baseline. Override at the Profile level for distinct user groups. Override at the User level for individual exceptions. Apex reads the correct level automatically.

```apex
// Returns the most specific value: User > Profile > Org Default
// No explicit level selection needed — the platform resolves it
User_Preferences__c prefs = User_Preferences__c.getInstance();
Integer threshold = (Integer) prefs.Alert_Threshold__c;

// To read for a specific user (e.g. in a batch or trigger context)
User_Preferences__c prefsForUser = User_Preferences__c.getInstance(targetUserId);
```

Setting values at each level:

```apex
// Org default
User_Preferences__c orgDefault = new User_Preferences__c(
    SetupOwnerId = UserInfo.getOrganizationId(),
    Alert_Threshold__c = 10
);
upsert orgDefault;

// Profile override
User_Preferences__c profileSetting = new User_Preferences__c(
    SetupOwnerId = profileId,
    Alert_Threshold__c = 5
);
upsert profileSetting;

// User override
User_Preferences__c userSetting = new User_Preferences__c(
    SetupOwnerId = userId,
    Alert_Threshold__c = 1
);
upsert userSetting;
```

**Why not CMT:** CMT has no hierarchy resolution. Replicating per-user overrides in CMT requires custom logic and creates maintenance overhead. Hierarchical Custom Settings are purpose-built for this pattern.

**Deployment note:** The Custom Setting field definition deploys. The records (org default, profile, user overrides) do not deploy — they must be set in each org through Setup or via Apex scripts run post-deploy.

---

### Pattern 3: Migrating List Custom Settings To Custom Metadata

**When to use:** Existing code uses `List_Setting__c.getValues('KeyName')` and the values are stable org-level config that should really be deployable.

**How it works:** Create a replacement CMT with equivalent fields. Set `DeveloperName` on each record to match the old setting Name. Update Apex to query CMT by `DeveloperName` instead of calling `getValues()`. Update Flow to use Get Records on the CMT.

```apex
// OLD — List Custom Setting, costs SOQL, not deployable
Integration_Config__c config = Integration_Config__c.getValues('PaymentGateway');
String endpoint = config.Endpoint_URL__c;

// NEW — Custom Metadata Type, zero SOQL cost, deployable
Integration_Config__mdt config = [
    SELECT Endpoint_URL__c
    FROM Integration_Config__mdt
    WHERE DeveloperName = 'PaymentGateway'
    LIMIT 1
];
String endpoint = config.Endpoint_URL__c;
```

**Why migrate:** List Custom Settings are deprecated in Lightning, consume SOQL limits, and are not deployable. The migration cost is low and the long-term reliability gain is high.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Values must deploy with releases through CI/CD | Custom Metadata Type | CMT records are metadata — they travel with the codebase |
| Values vary by user or profile | Hierarchical Custom Setting | Purpose-built hierarchy resolution; no custom code required |
| High-volume Apex reads, SOQL limits are a concern | Custom Metadata Type | CMT SOQL is free; Custom Settings count against the 100 SOQL limit |
| Feature flags that ship across orgs | Custom Metadata Type | Flags must be consistent per environment, not set per org manually |
| Quick admin-managed org default with no deployment overhead | Hierarchical Custom Setting (Org level) | Editable in Setup, readable via `getInstance()`, no deploy needed |
| New list-type configuration (flat key-value) | Custom Metadata Type | List Custom Settings are deprecated in Lightning |
| Existing List Custom Setting, low change frequency | Migrate to CMT | Reduces SOQL consumption and enables deployment |
| Per-user personal preference that admins do not manage | Hierarchical Custom Setting (User level) | User can own their own record if given FLS permissions |
| Values are secrets, tokens, or credentials | Named Credential or Protected Custom Metadata with external secret store | Neither CMT nor Custom Settings are secure secret storage |

---

## Recommended Workflow

1. **Identify the override requirement** — determine whether the value needs to vary by User, Profile, or only at the org level. If the answer is "User or Profile," Hierarchical Custom Setting is likely correct.
2. **Identify the deployment requirement** — determine whether the value must travel with a release through source control, packages, or change sets. If yes, Custom Metadata Type is likely correct.
3. **Assess governor limit exposure** — if the configuration is read in a high-volume context (trigger, batch, loop), confirm whether SOQL governor limits are a concern. CMT eliminates the risk; Custom Settings carry it.
4. **Design the storage type** — define fields, keys (use `DeveloperName` for CMT), and the hierarchy levels for Custom Settings.
5. **Implement and test Apex and Flow access** — use the correct access pattern for the chosen type (see Common Patterns). Write Apex tests that assert the correct value is returned, especially for hierarchical resolution edge cases.
6. **Define the post-deploy data strategy** — for Custom Settings, document how org defaults, profile overrides, and user overrides are set in each environment after deployment. CMT records deploy automatically; Custom Setting records must be set manually or via script.
7. **Validate against the Review Checklist** — confirm limits, deployment approach, and access patterns are correct before marking complete.

---

## Review Checklist

- [ ] The requirement is confirmed as configuration (not business data with reporting/CRUD needs).
- [ ] If per-user or per-profile override is needed, Hierarchical Custom Setting is the choice — not CMT.
- [ ] If the value must deploy with releases, Custom Metadata Type is the choice — not Custom Settings.
- [ ] No List Custom Settings are being created new; existing ones are candidates for migration to CMT.
- [ ] CMT queries use stable `DeveloperName` keys, not labels or record IDs.
- [ ] Custom Setting access in Apex uses `getInstance()` or `getValues()` (not a bare SOQL query), and the transaction's SOQL budget has been reviewed.
- [ ] Post-deploy data setup is documented for Custom Settings (records do not deploy).
- [ ] No secrets, passwords, or API tokens are stored in CMT or Custom Settings.
- [ ] Flow Get Records on CMT is confirmed free; Get Records on Custom Settings is counted.

---

## Salesforce-Specific Gotchas

1. **Custom Setting records do not deploy** — the field definition deploys, but the org default, profile-level, and user-level records are org-specific data. A post-deploy script or manual Setup step is required in every target org. Teams repeatedly discover this the hard way after deploying to UAT and finding all Custom Setting values blank.
2. **List Custom Settings are deprecated** — creating new List Custom Settings works technically but is unsupported in Lightning and Salesforce intends to remove them. Code using `getValues('Name')` on a List Custom Setting carries risk; migrate to CMT.
3. **`getInstance()` without arguments returns the running user's hierarchy** — in a trigger or Apex running as another user (via `runAs` in tests, or System mode in certain contexts), `getInstance()` may return org-default values rather than the user's personal settings. Use `getInstance(userId)` when you need a specific user's resolved value.
4. **CMT SOQL in Apex tests does not return records by default** — test methods run in an isolated metadata context. CMT records visible in the org are accessible in tests, but records inserted only in test setup are not queryable via normal CMT SOQL within the same test unless the test explicitly creates and queries them. Use `[SELECT ... FROM MyType__mdt]` in tests and include seed records or use `Test.loadData()` patterns carefully.
5. **CMT 200-record limit per type** — each Custom Metadata Type allows a maximum of 200 records. This is sufficient for most configuration use cases, but designs that attempt to store operational or transactional data in CMT will hit this wall. If more than ~100 records are anticipated, reconsider whether this is truly configuration.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Storage decision | Recommendation of CMT vs Hierarchical Custom Setting with rationale |
| Apex access pattern | Correct method signatures and query patterns for the chosen storage type |
| Flow access guidance | How to use Get Records with CMT or Custom Settings, noting governor-limit implications |
| Deployment checklist | Steps for deploying type definition and handling post-deploy data setup for Custom Settings |

---

## Related Skills

- `admin/custom-metadata-types` — use when the decision is made (CMT) and the focus is type design, field modeling, protection, and packaging.
- `admin/named-credentials-setup` — use when the values are secrets, tokens, or credentials that should not live in CMT or Custom Settings.
- `admin/object-creation-and-design` — use when the records are business data, not configuration (frequent edits, reporting, CRUD by users).
