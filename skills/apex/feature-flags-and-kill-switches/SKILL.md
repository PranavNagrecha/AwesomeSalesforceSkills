---
name: feature-flags-and-kill-switches
description: "Use when implementing runtime feature toggles, emergency kill switches, or gradual rollout controls in Apex using Custom Metadata Types, Custom Permissions, or Hierarchical Custom Settings. NOT for Custom Metadata Type fundamentals — see custom-metadata-types skill for CMDT basics."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "how do I toggle a feature on or off without deploying code"
  - "emergency kill switch to disable a feature in production instantly"
  - "gradual rollout of new functionality to specific users or profiles"
  - "runtime feature flags in Apex using Custom Metadata Types"
tags:
  - feature-flags-and-kill-switches
  - custom-metadata-types
  - custom-permissions
  - hierarchical-custom-settings
  - kill-switch
  - runtime-toggle
inputs:
  - "Name of the feature or behavior to control"
  - "Scope of the toggle: org-wide, profile-level, or user-level"
  - "Whether the flag needs to be packageable or sandbox-portable"
outputs:
  - "Feature flag CMDT object and field definitions"
  - "Apex utility class for flag evaluation"
  - "Kill switch pattern with test coverage"
  - "Decision on which mechanism to use (CMDT vs Custom Permission vs Custom Setting)"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# Feature Flags And Kill Switches

This skill activates when a practitioner needs to control feature availability at runtime without deploying code. It covers the three primary Salesforce-native mechanisms for feature flags: Custom Metadata Types with boolean fields, Custom Permissions checked via `FeatureManagement.checkPermission()`, and Hierarchical Custom Settings for user/profile/org-level overrides.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Determine the toggle scope.** Is the flag org-wide (all users on or off), user-scoped (different users see different behavior), or profile-scoped? This determines which mechanism to use.
- **Clarify deployment constraints.** Custom Metadata records are deployable via metadata API and change sets, but Hierarchical Custom Settings values are data — they do not travel with deployments unless scripted.
- **Understand the caching model.** Custom Metadata and Custom Settings are cached in the application server and do not count against SOQL limits when accessed via `getInstance()` or `getAll()`. However, changes to CMDT records require a metadata deployment, not a DML statement, which means they cannot be changed from anonymous Apex or triggers.

---

## Core Concepts

### Custom Metadata Types as Feature Flags

Custom Metadata Types (CMDT) are the recommended mechanism for org-wide feature flags. Define a `FeatureFlag__mdt` object with an `IsEnabled__c` checkbox field and a `Description__c` text field. Each feature gets a record: `FeatureFlag__mdt.getInstance('My_Feature').IsEnabled__c`. CMDT records are metadata, not data, so they deploy across sandboxes and can be packaged. They are cached and do not consume SOQL queries. The tradeoff is that changing a CMDT record requires a metadata deployment (via Setup UI, change set, or metadata API), which takes seconds but is not instantaneous DML.

### Custom Permissions for User-Scoped Flags

Custom Permissions provide user-level feature gating. Create a Custom Permission, assign it to a Permission Set, and check it in Apex with `FeatureManagement.checkPermission('My_Permission')`. This returns `true` if the running user has the permission via any assigned permission set. This is ideal for beta rollouts — assign the permission set to pilot users, then broaden. Revoking the permission set immediately revokes access with no code change. Custom Permissions are also available in Validation Rules and Flows via `$Permission.My_Permission`.

### Hierarchical Custom Settings for Layered Overrides

Hierarchical Custom Settings evaluate at three levels: org-wide default, profile-level override, and user-level override. Access them via `MyFlag__c.getInstance()` which returns the most specific value for the running user. Unlike CMDT, Custom Setting values are data and can be changed via DML — enabling true instant toggling from scripts, anonymous Apex, or even triggers. The downside is that they do not deploy as metadata, so you must script value population per environment, and they are not packageable as data.

---

## Common Patterns

### Org-Wide Kill Switch via CMDT

**When to use:** You need an emergency off-switch for a feature that affects all users identically — callout integrations, complex trigger logic, or batch processes.

**How it works:**

1. Create `FeatureFlag__mdt` with `IsEnabled__c` (checkbox) and `Description__c` (text).
2. Create a record named `My_Integration` with `IsEnabled__c = true`.
3. In Apex, gate the feature:

```apex
public class FeatureFlags {
    public static Boolean isEnabled(String featureName) {
        FeatureFlag__mdt flag = FeatureFlag__mdt.getInstance(featureName);
        return flag != null && flag.IsEnabled__c;
    }
}

// Usage in a trigger handler:
if (FeatureFlags.isEnabled('My_Integration')) {
    IntegrationService.syncToExternal(records);
}
```

4. To kill the feature: edit the CMDT record in Setup and set `IsEnabled__c = false`. No code deploy needed.

**Why not the alternative:** Using a Custom Setting would work, but CMDT records travel with deployments and change sets, keeping environments in sync. A hard-coded boolean requires a code deploy to flip.

### User-Scoped Beta Rollout via Custom Permission

**When to use:** You are rolling out a new UI feature, Lightning component behavior, or Apex logic path to a subset of users before going org-wide.

**How it works:**

1. Create a Custom Permission: `BetaNewCheckout`.
2. Create a Permission Set: `Beta - New Checkout Experience`.
3. Assign the Permission Set to pilot users.
4. Gate the feature:

```apex
if (FeatureManagement.checkPermission('BetaNewCheckout')) {
    // New checkout logic
} else {
    // Legacy checkout logic
}
```

5. When ready for GA, either assign the permission set to all users or remove the gate entirely.

**Why not the alternative:** CMDT is all-or-nothing at the org level. Custom Permissions allow per-user control with no code changes — just permission set assignment.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Org-wide on/off for integrations or batch jobs | Custom Metadata Type | Deploys across environments, cached, no SOQL cost |
| Per-user or per-profile feature rollout | Custom Permission + Permission Set | Immediate grant/revoke via permission set assignment |
| Need to flip a flag instantly via DML or script | Hierarchical Custom Setting | Only mechanism supporting DML-based changes |
| Flag value needed in formula fields or validation rules | Custom Permission (`$Permission`) | CMDT is not available in formula context |
| Packageable flag for ISV distribution | Custom Metadata Type | CMDT records can be included in managed packages |
| Temporary debug flag for a single user | Hierarchical Custom Setting (user-level) | User-level override without affecting anyone else |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner implementing feature flags:

1. **Identify the scope and lifecycle.** Determine whether the flag is org-wide, user-scoped, or profile-scoped. Decide whether the flag is temporary (removed after full rollout) or permanent (long-lived operational control like a kill switch).
2. **Select the mechanism.** Use the Decision Guidance table above. Default to CMDT for org-wide flags and Custom Permissions for user-scoped flags. Only use Hierarchical Custom Settings when DML-based instant toggling is a hard requirement.
3. **Create the metadata.** For CMDT: define the `FeatureFlag__mdt` object (if not already present) with `IsEnabled__c` and `Description__c`. For Custom Permissions: create the permission and a dedicated permission set. For Custom Settings: define the setting with a boolean field.
4. **Build the Apex gate.** Create a centralized `FeatureFlags` utility class that encapsulates the check. Never scatter raw `getInstance()` calls across the codebase — always route through the utility so flags can be mocked in tests and found via a single search.
5. **Write unit tests.** For CMDT flags, use `@IsTest` methods that construct `FeatureFlag__mdt` records via `JSON.deserialize` or use a wrapper that can be overridden in tests. For Custom Permissions, use `System.runAs()` with a user assigned the permission set. For Custom Settings, insert test data via DML.
6. **Validate the kill path.** Before deploying, verify the "off" path works correctly: set the flag to false and confirm the feature is fully bypassed with no partial execution or null pointer exceptions.
7. **Document the flag.** Add the flag name, purpose, mechanism, owner, and expected removal date (if temporary) to the team's feature flag registry or wiki.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Feature flag utility class centralizes all flag reads — no raw `getInstance()` scattered in code
- [ ] Kill switch "off" path is tested and does not throw exceptions or leave partial state
- [ ] Unit tests cover both the enabled and disabled paths for every flag
- [ ] CMDT records are included in the deployment package or change set
- [ ] Temporary flags have a documented removal date and a backlog item to clean them up
- [ ] Custom Permission flags have a dedicated Permission Set (not added to an existing broad set)
- [ ] Flag names follow a consistent naming convention (`Feature_Name`, not `flag1`)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **CMDT records cannot be modified via DML** — Unlike Custom Settings, you cannot insert, update, or delete CMDT records in Apex. Attempting `insert new FeatureFlag__mdt(...)` throws a runtime error. Changes must go through the Metadata API or Setup UI. This means you cannot programmatically flip a CMDT flag from a trigger or scheduled job.
2. **CMDT getInstance returns null for missing records** — If you call `FeatureFlag__mdt.getInstance('Nonexistent')` it returns `null`, not an exception. Unchecked null access on `.IsEnabled__c` causes a `NullPointerException` in production. Always null-check or default to `false`.
3. **Custom Settings values do not deploy** — Hierarchical Custom Setting field definitions deploy, but the actual data values (org-default, profile overrides, user overrides) are data rows. After refreshing a sandbox, your flags may have stale or missing values unless you script their population.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `FeatureFlag__mdt` object + fields | Custom Metadata Type definition with `IsEnabled__c` checkbox and `Description__c` text |
| `FeatureFlags.cls` utility class | Centralized Apex class exposing `isEnabled(String)` for CMDT and `isPermitted(String)` for Custom Permissions |
| `FeatureFlags_Test.cls` | Unit tests covering enabled, disabled, and null-record paths |
| Feature flag CMDT records | One record per controlled feature, deployable via change set or metadata API |

---

## Related Skills

- `custom-metadata-types` — Covers CMDT fundamentals (object creation, field types, deployment). Use this skill when you need to go deeper on CMDT design beyond the flag pattern.
- `permission-set-design` — Covers permission set strategy and assignment patterns. Use when the feature flag approach involves Custom Permissions and you need to design the permission set hierarchy.
- `callout-limits-and-async-patterns` — Feature flags often gate integration callouts. Use when the flagged feature involves HTTP callouts and you need to handle limits.

## Official Sources Used

- FeatureManagement Class — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_System_FeatureManagement.htm
- CustomPermission Metadata Type — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_custompermission.htm
- Custom Metadata Type Methods — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_methods_system_custom_metadata_types.htm
