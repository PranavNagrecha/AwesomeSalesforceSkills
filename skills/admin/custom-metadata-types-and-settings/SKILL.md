---
name: custom-metadata-types-and-settings
description: "Use when choosing between Custom Metadata Types and Custom Settings, understanding hierarchical vs list settings, deployment behavior, governor limit implications, or accessing either from Apex and Flow. Trigger keywords: 'custom metadata vs custom settings', 'hierarchical settings per user profile', 'deployable config vs runtime settings', 'getValues getInstance in apex', 'flow get records custom settings'. NOT for modelling the CMT itself or protecting packaged defaults — use admin/custom-metadata-types. NOT for records users edit as business data — use admin/object-creation-and-design. NOT for secrets — use integration/named-credentials-setup. More trigger keywords: customSettingsType, customSettingsVisibility, SetupOwnerId, getOrgDefaults, getAll, DUPLICATE_VALUE in test, SeeAllData custom settings, enableAdvancedCSSecurity, customSettingAccesses, org default profile user override."
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
  - "custom setting value is blank after deploying to a new sandbox"
  - "getvalues returns null for a field that is set at the org level"
  - "duplicate_value error inserting a custom setting in a test method"
  - "write the xml for a hierarchy custom setting and its permission set"
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
  - "deployable CustomObject, CustomField, PermissionSet and Schema settings XML for the setting"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
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

## Questions to Ask Before Configuring

Ask these before creating anything. Each answer decides an element you will have to write into the XML or a line of the seed script, and an LLM that skips them ships a setting that deploys cleanly and then reads back empty in every org but the one it was built in.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which org actually needs these values, and who puts them there after the deploy?" | Only definitions travel; the rows do not. Packages carry no data at all, and a fresh scratch org starts empty | A named owner and a seed script committed next to the metadata |
| "Does any value legitimately differ by user or profile, or is that just convenience?" | It picks `customSettingsType`, and the element defaults to `Hierarchy` when omitted | The `customSettingsType` value, chosen rather than defaulted |
| "Which fields will be set at the org level only?" | `getInstance()` merges those down; `getValues(id)` returns null for them | The Apex accessor each consumer must call, per field |
| "Will this ever ship inside a managed package?" | `Protected` restricts nothing outside one, and inside one the subscriber can neither edit nor read the values from Apex | The `visibility` value and, if Protected, who configures it post-install |
| "Who reads these values besides Apex — Flow, formulas, a SOAP integration?" | `enableAdvancedCSSecurity` defaults to false, so SOAP/WSDL readers see the values today and break the moment it is switched on | The consumer list and a deliberate `Schema.settings` decision |
| "Which non-admin profiles must read this?" | Read access is a `customSettingAccesses` grant, not a side effect of the deploy | The permission set that ships alongside the definition |
| "How will the tests get their data?" | Custom settings data is invisible to Apex tests unless the test inserts it; and inserting the same `SetupOwnerId` in both `@TestSetup` and a test method throws `DUPLICATE_VALUE` | A `@TestSetup` seeding plan with one owner per level |

What a proper configuration adds over just creating the setting in Setup: the definition, its fields, the permission set that makes it readable, and the org security switches all deploy together; the rows are created by a reviewed script rather than remembered; and every consumer calls the accessor that actually resolves the value it expects.

---

## Core Concepts

### Custom Metadata Types: Configuration That Ships With The App

Custom Metadata Type (CMT) records are metadata, not data. They move through change sets, unlocked packages, managed packages, and source-control-driven deployments exactly like Apex classes or field definitions. The key facts:

| Fact | Detail |
|---|---|
| SOQL is free | "This limit doesn't apply to custom metadata types. In a single Apex transaction, custom metadata records can have unlimited SOQL queries" (App Limits Cheat Sheet, SOQL limit footnote 1) |
| Flow Get Records is also free | Accessing CMT through the Flow Get Records element costs no SOQL queries. UNVERIFIED (2026-09-05): grounded for Apex transactions in the cheat sheet above; the extracted guides make no equivalent statement about Flow |
| Storage cap | UNVERIFIED (2026-09-05): the commonly quoted "200 records per type, 10 MB per org" appears in none of the extracted guides, and the App Limits Cheat Sheet has no custom metadata storage row. Treat as a planning heuristic and confirm against Setup → Storage Usage |
| Deployment | Included automatically in change sets, scratch org source pushes, and packaging. Records and type definition both move together. |
| Editable in production | An admin can edit CMT records directly in a production org through Setup. This is unlike Apex, which requires a sandbox round trip, but still treats the record as metadata that should be tracked in source control. |
| No per-user override | CMT has no built-in hierarchy. All users see the same values for a given record. |
| Relationships | CMT fields can hold a Metadata Relationship to another CMT type, enabling lookup-style joins entirely within metadata. |

This skill owns the *comparison* and the Custom Settings side. For the CMT type design itself — `visibility` vs record-level `protected`, `fieldManageability`, `xsi:type`, `xsi:nil`, `MetadataRelationship`, the 255-character truncation on `getAll()` — read `admin/custom-metadata-types` rather than reconstructing it here.

### Custom Settings: One Element Decides Everything Else

`customSettingsType` is what makes a `CustomObject` a custom setting, and it takes exactly two values (Metadata API Developer Guide, `CustomObject`):

| `customSettingsType` | Guide's own words | Apex methods that apply |
|---|---|---|
| `Hierarchy` (the **default** when the element is omitted) | "static data stored in cache, accessed as part of your application, and available based on a hierarchy of user, profile, or org" | `getInstance()`, `getInstance(userId)`, `getInstance(profileId)`, `getOrgDefaults()`, `getValues(userId)`, `getValues(profileId)` |
| `List` | "static data stored in cache, accessed as part of your application, and available org-wide" | `getAll()`, `getInstance(dataSetName)`, `getValues(dataSetName)` |

The two method families are not interchangeable, and the mismatch compiles. `scripts/check_custom_metadata_types_and_settings.py` flags it.

### Hierarchy Resolution: Three Levels, Merged Per Field

"The hierarchy logic checks the organization, profile, and user settings for the current user and returns the most specific, or 'lowest,' value. In the hierarchy, settings for an organization are overridden by profile settings, which, in turn, are overridden by user settings" (Apex Developer Guide, *Custom Settings*).

```
User row  >  Profile row  >  Org Default row      (SetupOwnerId = User Id / Profile Id / Org Id)
```

The merge is **per field**, not per record. In the Apex Reference Guide's own example, a hierarchy setting has `OverrideMe` set at all three levels and `DontOverrideMe` set only at the org level:

| Call | `OverrideMe` | `DontOverrideMe` |
|---|---|---|
| `getInstance()` | `Fluffy` (user) | `World` (merged down from org) |
| `getInstance(SysAdminId)` | `Goodbye` (profile) | `World` (merged down from org) |
| `getOrgDefaults()` | `Hello` (org) | `World` |
| `getValues(RobertId)` | `Fluffy` | **null** — no merge |
| `getValues(SysAdminId)` | `Goodbye` | **null** — no merge |

`getInstance()` "is equivalent to a method call to `getInstance(User_Id)` for the current user", and when nothing is defined it returns a new object with a null Id and empty fields — **not** null. `getOrgDefaults()` likewise returns an empty object. Only Apex saved using API version 21.0 or earlier returned null.

### Visibility, Packaging, And Who Can Read The Values

| Concern | Behaviour | Source |
|---|---|---|
| `visibility` element | `Public` (default) / `Protected`; `PackageProtected` is CMT-only | Metadata API Developer Guide, `CustomObject.visibility` (34.0+) |
| `customSettingsVisibility` | Available API 17.0–33.0 only; superseded by `visibility` | Metadata API Developer Guide |
| `Protected` outside a package | Inert — the setting is "readable for all profiles, including the guest user" | Apex Developer Guide, *Custom Settings* |
| `Protected` inside a managed package | The subscribing org "can't edit the values or access them using Apex" | Apex Developer Guide, *Custom Settings* |
| Package contents | "Only custom settings definitions are included in packages, not data" — the subscriber's org is populated by Apex you ship | Apex Developer Guide, *Custom Settings* |
| Sandbox copies | Custom settings data **is** included in sandbox copies | Apex Developer Guide, *Custom Settings* |
| Non-admin read access | `customSettingAccesses` on a PermissionSet (47.0+); `ProfileCustomSettingAccesses` is the profile form | Metadata API Developer Guide |
| SOAP / WSDL exposure | `SchemaSettings.enableAdvancedCSSecurity` defaults to **false**, so values are exposed outside Apex/Flow/formula until you switch it on | Metadata API Developer Guide, `SchemaSettings` |
| Creating List settings | `SchemaSettings.enableListCustomSettingCreation` defaults to **false** | Metadata API Developer Guide, `SchemaSettings` |

UNVERIFIED (2026-09-05): the frequently repeated claim that List Custom Settings are *deprecated in Lightning Experience* appears nowhere in the extracted Metadata API, Apex Developer, Apex Reference, or Object Reference guides, which describe list settings as a current feature. What is grounded is the creation switch above. Prefer a Custom Metadata Type for new flat configuration on the deployability argument, not on a deprecation claim you cannot cite.

### Governor Limit Implications

This is the most commonly misunderstood difference, and the direction of the misunderstanding is not the obvious one:

| Access path | Custom Metadata Type | Custom Setting (List or Hierarchy) |
|---|---|---|
| Apex custom settings methods (`getInstance`, `getValues`, `getAll`, `getOrgDefaults`) | n/a | **0 SOQL** — "Because the data is cached, access is low-cost and efficient: you don't have to use SOQL queries that count against your governor limits" |
| `[SELECT … FROM Type__mdt]` | **0 SOQL**, unlimited per transaction | n/a |
| `[SELECT … FROM Setting__c]` | n/a | **Counts** — "querying custom settings data using SOQL doesn't use the application cache and is similar to querying a custom object" |
| Flow Get Records | 0 SOQL. UNVERIFIED (2026-09-05) — see the CMT table above | UNVERIFIED (2026-09-05): the guides state the cache serves flows, but do not say whether a Flow Get Records element on a custom setting uses that cache or issues a query |

The practical rule: in runtime Apex, never SOQL a custom setting. The cached accessor is both correct and free; the query that looks identical is neither.

### Deployment Behavior Comparison

| Behavior | Custom Metadata Type | Hierarchical Custom Setting | List Custom Setting |
|---|---|---|---|
| Definition deploys | Yes | Yes | Yes |
| **Records** deploy | Yes (`customMetadata/`) | **No** — org data | **No** — org data |
| Included in a managed package | Type + records | Definition only | Definition only |
| Present after a sandbox refresh | Yes | Yes (data is copied) | Yes (data is copied) |
| Present in a fresh scratch org | Yes | No | No |
| Per-user/profile override | No | Yes | No |
| Runtime SOQL cost | None | None via accessors | None via accessors |

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

In Flow, use a Get Records element targeting `Feature_Flag__mdt` filtered by `DeveloperName`.

**Why not Custom Settings:** The value is not per-user and it must travel through source control to ensure every sandbox and production sees the same configuration.

---

### Pattern 2: Per-User Or Per-Profile Behavior Overrides

**When to use:** A feature should behave differently for admins vs standard users, or individual users need a personal preference (time zone display, record owner default, notification threshold).

**How it works:** Create a Hierarchical Custom Setting. Set the Org Default in Setup as the baseline. Override at the Profile level for distinct user groups. Override at the User level for individual exceptions. Apex reads the correct level automatically.

```apex
// Returns the most specific value per field: User > Profile > Org Default.
// Never returns null — an unseeded org yields an object with empty fields,
// so guard the FIELD, not the record.
Alert_Config__c cfg = Alert_Config__c.getInstance();
Integer threshold = cfg.Alert_Threshold__c == null ? 20 : (Integer) cfg.Alert_Threshold__c;

// Resolve for a specific user (batch, trigger, queueable running as someone else)
Alert_Config__c cfgForUser = Alert_Config__c.getInstance(targetUserId);
```

Seeding each level — note `getValues` here is deliberate, because it tells you whether a row exists *at that level*:

```apex
Alert_Config__c orgDefault = Alert_Config__c.getOrgDefaults();
orgDefault.SetupOwnerId = UserInfo.getOrganizationId();
orgDefault.Alert_Threshold__c = 10;
upsert orgDefault;

Alert_Config__c profileRow = Alert_Config__c.getValues(profileId);
if (profileRow == null) { profileRow = new Alert_Config__c(SetupOwnerId = profileId); }
profileRow.Alert_Threshold__c = 5;
upsert profileRow;
```

**Why not CMT:** CMT has no hierarchy resolution. Replicating per-user overrides in CMT requires custom logic and creates maintenance overhead.

**Deployment note:** The definition and its fields deploy. The rows do not — see `references/metadata-examples.md` for the seed script and the package.xml that carries everything except the data.

---

### Pattern 3: Migrating List Custom Settings To Custom Metadata

**When to use:** Existing code uses `List_Setting__c.getValues('KeyName')` and the values are stable org-level config that should really be deployable.

**How it works:** Create a replacement CMT with equivalent fields. Set `DeveloperName` on each record to match the old setting Name. Update Apex to query CMT by `DeveloperName` instead of calling `getValues()`. Update Flow to use Get Records on the CMT.

```apex
// OLD — List Custom Setting: cached and free to read, but the rows are org data
Integration_Config__c config = Integration_Config__c.getValues('PaymentGateway');
String endpoint = config.Endpoint_URL__c;   // null-safe check omitted for brevity

// NEW — Custom Metadata Type: the record itself deploys with the release
Integration_Config__mdt config = [
    SELECT Endpoint_URL__c
    FROM Integration_Config__mdt
    WHERE DeveloperName = 'PaymentGateway'
    LIMIT 1
];
String endpoint = config.Endpoint_URL__c;
```

**Why migrate:** deployability, not read cost. Both storage types read from a cache; only one of them carries its values into the next org.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Values must deploy with releases through CI/CD | Custom Metadata Type | CMT records are metadata — they travel with the codebase |
| Values vary by user or profile | Hierarchical Custom Setting | Purpose-built per-field hierarchy resolution; no custom code required |
| Values are read inside a loop and the SOQL budget is tight | Either, via its cached accessor | Both are cached; the mistake is SOQL against a `__c` setting, not the storage choice |
| Feature flags that ship across orgs | Custom Metadata Type | Flags must be consistent per environment, not set per org manually |
| Quick admin-managed org default with no deployment overhead | Hierarchical Custom Setting (Org level) | Editable in Setup, readable via `getOrgDefaults()`, no deploy needed |
| New list-type configuration (flat key-value) | Custom Metadata Type | The records deploy; List settings need creation enabled in `SchemaSettings` and their rows never travel |
| Existing List Custom Setting, low change frequency | Migrate to CMT | Makes the values part of the release rather than a per-org setup task |
| Per-user personal preference that admins do not manage | Hierarchical Custom Setting (User level) | User can own their own record if granted `customSettingAccesses` |
| A coordinate, latitude/longitude, or geolocation value | Neither, as a Location field | Geolocation fields aren't supported in custom settings |
| Values are secrets, tokens, or credentials | Named Credential or encrypted custom field | The Apex Developer Guide says so explicitly for anything outside a managed package |

---

## Recommended Workflow

1. **Answer the seven questions above** — they decide `customSettingsType`, `visibility`, the permission set, and the seeding plan before any file exists.
2. **Route the decision** — if the rows must travel with the release, stop here and use `admin/custom-metadata-types`. If any value legitimately differs per user or profile, continue with a Hierarchy custom setting.
3. **Write the definition** — copy the `CustomObject`, `CustomField`, `PermissionSet` and `Schema.settings` shapes from `references/metadata-examples.md`; set `customSettingsType` and `visibility` explicitly, never `customSettingsVisibility`.
4. **Write the accessor** — `getInstance()` / `getInstance(id)` for anything consuming a resolved value; `getAll()` / `getValues(name)` only against a List setting; `getValues(id)` only in seeding and migration code. Guard the field for null, not the record.
5. **Write the seed script and the tests together** — the org-default upsert in `scripts/apex/`, and a `@TestSetup` block that owns one `SetupOwnerId` per level (`references/metadata-examples.md` § Test-data pattern).
6. **Run the checker** — `python3 skills/admin/custom-metadata-types-and-settings/scripts/check_custom_metadata_types_and_settings.py --manifest-dir force-app/main/default`, then deploy with `--dry-run` before the real deploy.
7. **Verify in the target org** — run the verification SOQL and the `getOrgDefaults()` / `getInstance()` debug pair from `references/metadata-examples.md` § Verify, as a non-admin user as well as an admin.

---

## Review Checklist

- [ ] The requirement is confirmed as configuration (not business data with reporting/CRUD needs).
- [ ] If per-user or per-profile override is needed, Hierarchical Custom Setting is the choice — not CMT.
- [ ] If the values must deploy with releases, Custom Metadata Type is the choice — not Custom Settings.
- [ ] `customSettingsType` is stated explicitly rather than left to its `Hierarchy` default.
- [ ] `visibility` is stated explicitly; `customSettingsVisibility` appears nowhere in the manifest.
- [ ] Every Apex call site uses a method that belongs to the declared setting type.
- [ ] No runtime Apex issues SOQL against a `__c` custom setting.
- [ ] A permission set carrying `customSettingAccesses` ships with the definition for every non-admin reader.
- [ ] `Schema.settings` has been retrieved and `enableAdvancedCSSecurity` decided, not inherited.
- [ ] Tests insert their own custom setting data; no `SeeAllData=true`; one `SetupOwnerId` owner per level.
- [ ] Post-deploy seeding is a committed, reviewed script — not a runbook step.
- [ ] No secrets, passwords, or API tokens are stored in CMT or Custom Settings.

---

## Salesforce-Specific Gotchas

Full detail, with guide citations, in `references/gotchas.md`. The short list:

1. Custom Setting rows never deploy — packages carry definitions only, and a fresh scratch org starts empty.
2. `getInstance()` and `getOrgDefaults()` return an empty object rather than null, so record-level null guards never fire.
3. `getValues(userId)` does not merge the hierarchy; `getInstance(userId)` does.
4. The Apex accessors cost no SOQL; a SOQL query against the same setting object does.
5. Inserting the same `SetupOwnerId` in both `@TestSetup` and a test method throws `DUPLICATE_VALUE` at API 42.0 and later.
6. Apex tests see no existing custom settings data without `SeeAllData=true` — seed it instead.
7. `Protected` visibility restricts nothing outside a managed package; inside one, the subscriber cannot read it from Apex either.
8. `customSettingsVisibility` was superseded at API 34.0 and a file carrying only it deploys as Public.
9. `enableAdvancedCSSecurity` defaults to false, so SOAP and WSDL readers can see the values.
10. Non-admins need `customSettingAccesses`, and `isAccessible()` lied about it before API 54.0.
11. Geolocation fields aren't supported in custom settings, and List setting creation can be switched off org-wide.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Storage decision | Recommendation of CMT vs Hierarchical vs List Custom Setting with rationale |
| Deployable metadata | `CustomObject` + `CustomField` + `PermissionSet` + `Schema.settings` XML and the package.xml that carries them |
| Seed script | Idempotent Apex that upserts the org default and any profile/user rows in a new org |
| Apex access pattern | The accessor each consumer must call, matched to the declared `customSettingsType` |
| Test plan | `@TestSetup` seeding with one `SetupOwnerId` owner per level, and the assertions that prove the merge |
| Verification steps | SOQL over `SetupOwner.Type` plus the `getOrgDefaults()` / `getInstance()` debug pair |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Writing the deployable XML, the package.xml, the seed script, the test-data pattern, or the verification step |
| `references/gotchas.md` | Eleven platform behaviours with guide citations — merge semantics, cache vs SOQL, test isolation, visibility, SOAP exposure |
| `references/examples.md` | Working a feature-flag or per-profile-threshold scenario end to end, including what the first attempt got wrong |
| `references/well-architected.md` | Justifying the storage choice against Operational Excellence, Reliability, and Performance, or citing the official sources |
| `references/llm-anti-patterns.md` | Self-checking generated output for wrong accessors, invented governor costs, or unnecessary null guards |
| `templates/custom-metadata-types-and-settings-template.md` | Recording the decision, the seeding plan, and the review outcome for a specific request |
| `scripts/check_custom_metadata_types_and_settings.py` | Before every deploy — definition, field-type, Apex-accessor, and test-isolation checks over a manifest directory |

---

## Related Skills

- `admin/custom-metadata-types` — use when the decision is made (CMT) and the focus is type design, field modeling, protection, and packaging.
- `apex/custom-metadata-in-apex` — use when the storage decision is settled and Apex access and caching patterns are the remaining work.
- `apex/apex-test-setup-patterns` — use when the harder problem is seeding and isolating test data across `@TestSetup` and test methods.
- `admin/permission-set-architecture` — use when deciding how `customSettingAccesses` fits the org's permission-set design.
- `integration/named-credentials-setup` — use when the values are secrets, tokens, or credentials that should not live in CMT or Custom Settings.
- `admin/object-creation-and-design` — use when the records are business data, not configuration (frequent edits, reporting, CRUD by users).
