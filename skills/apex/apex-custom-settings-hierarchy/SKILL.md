---
name: apex-custom-settings-hierarchy
description: "Use when reading or writing Hierarchy Custom Settings from Apex to resolve per-user/per-profile/org configuration. Covers `getInstance()` resolution order, DML cost, cache semantics, and when to prefer Custom Metadata Types instead. NOT for List Custom Settings, Custom Metadata Types deployment packaging, or the deprecated Setup UI for editing."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
  - Operational Excellence
triggers:
  - "read a tenant or feature flag configuration from Apex"
  - "override a setting per user or per profile in production"
  - "should this configuration live in Custom Settings or Custom Metadata"
  - "upsert a hierarchy custom setting without hitting DML limits"
  - "why does getInstance() return the wrong value for some users"
tags:
  - apex-custom-settings-hierarchy
  - configuration
  - feature-flags
  - custom-metadata
inputs:
  - "the name of the Hierarchy Custom Setting and its field(s) in play"
  - "the callers (trigger, batch, UI, integration) and their user context"
  - "whether the configuration changes at runtime (admins in Setup) or only at deploy"
outputs:
  - "correct `getInstance()` / `getOrgDefaults()` / `getValues()` usage with null handling"
  - "guidance on when to migrate to Custom Metadata Types"
  - "safe upsert patterns for mutable config"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-23
---

# Apex Custom Settings Hierarchy

Activates when Apex reads or writes Hierarchy Custom Settings — the cached, per-user/per-profile/per-org configuration store. Produces correct resolution, null-safe defaults, and guidance on when to pick Custom Metadata Types instead.

---

## Before Starting

- Is this configuration **mutable at runtime**? If admins never change it, prefer Custom Metadata Types (deploy-time only, packageable, no DML).
- Is this configuration **per-user/profile/org**? Only Hierarchy Custom Settings offer this automatically. List Custom Settings and CMDTs do not.
- Does the caller run as **System.RunAs or as a real user**? `getInstance()` with no argument returns the setting for the *running* user — tests often surprise.
- Does the setting need to be **visible to all profiles**? Without the `Privileged = true` flag (API field `Privileged`) or a CRUD grant, unprivileged users cannot read it.

---

## Core Concepts

### The Three Accessors Resolve Differently

Hierarchy Custom Settings have three distinct Apex accessors:

- `MySetting__c.getOrgDefaults()` — always returns the org-level record (or `null` if none exists).
- `MySetting__c.getInstance(userOrProfileId)` — returns the merged record for a specific User or Profile, falling back through Profile → Org.
- `MySetting__c.getInstance()` — equivalent to `getInstance(UserInfo.getUserId())`.

When the running user has no User-level override, Salesforce falls back to their Profile-level override, and if none exists, to the org default. **An empty record is returned, not `null`**, when no tier is configured — field values will be `null` but the record itself exists. This surprises practitioners who null-check the record.

### It's Cached, But Not Free

Reads are cached within a transaction, so repeated `getInstance()` calls in the same execution are cheap. But the cache is per-transaction — a long-running batch that calls `getInstance()` in every `execute()` re-reads. DML on the setting counts against governor DML limits; mass-upserting one record per user is the wrong shape.

### Custom Metadata Is Often The Better Fit

Hierarchy Custom Settings predate Custom Metadata Types (CMDTs). CMDTs are deployable (packageable, source-tracked, sandbox-migration-friendly) while Custom Settings values are **data, not metadata** — they don't move with deploys. If your "config" is actually static code-adjacent decisions (feature toggle per environment, integration endpoint URL, retry caps), CMDT is the right home. Reserve Custom Settings for values admins must change in production Setup UI.

---

## Common Patterns

### Pattern 1: Null-Safe Read With Org Default Fallback

**When to use:** Any feature-flag or threshold lookup in Apex.

**How it works:**

```apex
public with sharing class ApiRetryConfig {
    public static Integer maxRetries() {
        RetrySettings__c s = RetrySettings__c.getInstance();
        // s is never null for Hierarchy Settings, but field values can be null.
        return (s != null && s.MaxRetries__c != null)
            ? s.MaxRetries__c.intValue()
            : 3;
    }
}
```

**Why not the alternative:** `getOrgDefaults()` misses per-user overrides. `getInstance()` with a nested null-check is the universal safe shape.

### Pattern 2: Bulk-Safe Upsert Of Per-User Overrides

**When to use:** A one-time job seeds per-user settings during onboarding.

**How it works:**

```apex
List<PerUserFlag__c> rows = new List<PerUserFlag__c>();
for (Id userId : userIds) {
    rows.add(new PerUserFlag__c(SetupOwnerId = userId, Enabled__c = true));
}
upsert rows SetupOwnerId;
```

**Why not the alternative:** `insert` row-by-row burns DML statements. Batch upsert by the `SetupOwnerId` external-ID-like key inserts new and updates existing in one DML.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Static config that changes at deploy only | Custom Metadata Type | Packageable, deploys with source, no DML |
| Admin-editable per-user or per-profile config | Hierarchy Custom Setting | Only CS offers hierarchy fallback |
| Feature flag changed during an incident | Hierarchy Custom Setting at Org tier | Admins can flip in Setup without deploy |
| Lookup table (e.g., country → currency) | Custom Metadata Type with custom fields | Relationships and SOQL; better than List CS |
| Per-transaction cache of computed values | Platform Cache (`Cache.Org` / `Cache.Session`) | Custom Settings are not a computation cache |

---

## Recommended Workflow

1. Classify the data: runtime-mutable admin config, deploy-time code config, or derived/cached compute? Only the first belongs in Hierarchy Custom Settings.
2. Confirm the object's `Privileged` flag matches the security posture — set it if end users should not write.
3. Read through `getInstance()` for per-user fallback; document why if you pick `getOrgDefaults()` explicitly.
4. Null-check the **field** (not the record), with a sane code default for missing fields.
5. For writes, batch by `SetupOwnerId` and use `upsert ... SetupOwnerId`; never loop-inserting.
6. Write a test with `System.runAs(user)` to confirm the hierarchy resolves as expected.
7. Document in the setting's Description field who edits this in production and when.

---

## Review Checklist

- [ ] The object is actually mutable at runtime; otherwise migrate to CMDT.
- [ ] `Privileged` is set correctly for the security posture.
- [ ] Apex uses `getInstance()` with a null-safe field read AND a code default.
- [ ] Tests cover the hierarchy: org default, profile override, user override.
- [ ] Writes are batched with `upsert ... SetupOwnerId`; no DML in loops.
- [ ] The README / setting description lists the intended editors and change cadence.

---

## Salesforce-Specific Gotchas

See `references/gotchas.md` for the full list.

1. **`getInstance()` never returns `null`** for Hierarchy Settings — it returns an empty record with `null` fields. Null-check fields, not the record.
2. **`getOrgDefaults()` CAN return `null`** if no org-default row exists. Different semantics than `getInstance()`.
3. **CS values do not deploy with metadata** — seeding production after a sandbox deploy is manual or requires a data loader.
4. **`Privileged` checkbox on the object** controls whether non-admins can write. Without it, a user trigger calling `insert newCSRecord` can fail for low-privilege users.
5. **`SetupOwnerId` is polymorphic** — it accepts User or Profile IDs. The wrong type inserts as the wrong hierarchy tier silently.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `references/examples.md` | Realistic read/write patterns and a List-CS to CMDT migration |
| `references/gotchas.md` | Hierarchy resolution surprises and packaging warnings |
| `references/llm-anti-patterns.md` | Common LLM mistakes: null-checking the record, `getOrgDefaults` drift |
| `references/well-architected.md` | OpEx / Reliability framing and CMDT vs CS tradeoffs |
| `scripts/check_apex_custom_settings_hierarchy.py` | Stdlib lint for anti-pattern usage |

---

## Related Skills

- **apex-custom-metadata-types** — when to migrate config from CS to CMDT
- **apex-platform-cache** — for runtime caches, not configuration
- **apex-user-and-permission-checks** — resolving the running user before `getInstance(userId)`
