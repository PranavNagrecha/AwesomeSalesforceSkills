# Probe: matching-and-duplicate-rules

## Purpose

Enumerate Matching Rules and Duplicate Rules for an sObject, with active state, bypass-permission linkage, and overlap detection hints. Consumed by any agent that designs, audits, or must reason around duplicate-management semantics.

## Arguments

| Arg | Type | Required | Notes |
|---|---|---|---|
| `object` | string | yes | sObject API name |
| `active_only` | boolean | no (default `false`) | Skip inactive rules |

## Query

```sql
SELECT Id, DeveloperName, MasterLabel, RuleStatus, SobjectType
FROM MatchingRule
WHERE SobjectType = '<object>'
LIMIT 200
```

Active-rule filter: `MatchingRule` uses `RuleStatus` (picklist values include `Active`, `Inactive`, `Activating`, `Deactivating`), NOT a boolean `IsActive`. Post-filter client-side when `active_only=true`.

```sql
SELECT Id, DeveloperName, MasterLabel, IsActive, SobjectType, SobjectSubtype
FROM DuplicateRule
WHERE SobjectType = '<object>'
LIMIT 200
```

`DuplicateRule` has a boolean `IsActive` (unlike MatchingRule). It does NOT have a `ParentId` field on the standard object — the parent-rule relationship is stored in the rule's `Metadata` body (see below).

For each MatchingRule id, fetch the items:

```sql
SELECT MatchingRuleId, Field, MatchingMethod, BlankValueBehavior, SortOrder
FROM MatchingRuleItem
WHERE MatchingRuleId IN (<ids>)
LIMIT 2000
```

`MatchingRuleItem.Field` (not `FieldName`) — the column name is just `Field`.

For each DuplicateRule, read the rule body from `Metadata` and parse it for:

- `<actionOnInsert>` / `<actionOnUpdate>` — Allow or Block
- `<securityOption>` — `EnforceSharingRules` or `BypassSharingRules`. Consumers care: under `EnforceSharingRules` a duplicate the running user cannot see does not stop the save, so the same rule behaves differently for a restricted integration user than for an admin.
- `<duplicateRuleFilter>` → `<duplicateRuleFilterItems>` — **this is where a bypass lives.** Filter items whose `table` is `$User` are how a rule is made not to apply to a loader or integration principal.

**There is no `operationsOnBypass` element and no Custom-Permission bypass.** The documented DuplicateRule fields are `actionOnInsert`, `actionOnUpdate`, `alertText`, `description`, `duplicateRuleFilter`, `duplicateRuleMatchRules`, `isActive`, `masterLabel`, `operationsOnInsert`, `operationsOnUpdate`, `securityOption`, `sortOrder`. A probe that looks for `operationsOnBypass` finds nothing on every org and, worse, invites the consuming agent to report "no bypass configured" as a finding when the org's real bypass is sitting in `duplicateRuleFilter` or in an Apex `Database.DMLOptions.DuplicateRuleHeader.allowSave` call the probe never sees. Report the Apex path as unobservable from this probe rather than as absent.

Official source: *DuplicateRule*, Metadata API Developer Guide.

## Post-processing — overlap detection

Two active rules on the same sObject with overlapping match-field sets is a P0 finding. Compute overlap:

1. Reduce each MatchingRule to a `Set<FieldName>`.
2. Two rules overlap iff `|A ∩ B| >= 1` AND both are active.
3. Two rules **conflict** (stronger) iff `A == B` and both are active.

Surface overlaps in the probe output under `overlaps[]`.

## Returns

```json
{
  "matching_rules": [
    {
      "id": "0M0...",
      "developer_name": "MR_Lead_Email",
      "active": true,
      "fields": [
        { "field": "Email", "method": "Exact", "blank_behavior": "NullNotAllowed", "sort_order": 1 }
      ]
    }
  ],
  "duplicate_rules": [
    {
      "id": "0Bm...",
      "developer_name": "DR_Lead_Email",
      "active": true,
      "action_on_insert": "Block",
      "action_on_update": "Allow",
      "bypass_permissions": ["Bypass_Duplicate_Rule_Lead"]
    }
  ],
  "overlaps": [
    { "left": "MR_Lead_Email", "right": "MR_Lead_Contact", "shared_fields": ["Email"] }
  ]
}
```

## Consumed by

- `duplicate-rule-designer` — primary consumer; uses overlap detection for P0 refusal
- `data-loader-pre-flight` — checks that the integration user has a bypass Custom Permission assigned
- `lead-routing-rules-designer` — duplicate rules and lead-routing-rule semantics interact at convert time
