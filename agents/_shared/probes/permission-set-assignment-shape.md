# Probe: permission-set-assignment-shape

## Purpose

Produce a structured summary of how a Permission Set or Permission Set Group is shaped in the live org — composition, assignment volume, and concentration risk. Consumed by agents that reason about security surface.

## Arguments

| Arg | Type | Required | Notes |
|---|---|---|---|
| `scope` | string | yes | `org` \| `psg:<name>` \| `ps:<name>` \| `user:<username>` |
| `include_field_permissions` | boolean | no (default `false`) | Off by default — field-perm rows explode on broad PSes |

## Query

Composition of a PSG:

```sql
SELECT PermissionSetGroupId, PermissionSetId, PermissionSet.Name, PermissionSet.Label
FROM PermissionSetGroupComponent
WHERE PermissionSetGroup.DeveloperName = '<psg_name>'
LIMIT 200
```

Assignment concentration:

```sql
SELECT PermissionSetGroup.DeveloperName, COUNT(Id)
FROM PermissionSetAssignment
WHERE PermissionSetGroupId != null
GROUP BY PermissionSetGroup.DeveloperName
ORDER BY COUNT(Id) DESC
LIMIT 50
```

Post-processing: the second column appears as `expr0` in the result set — SOQL aggregate queries don't accept `AS alias` syntax. Map to a named field client-side.

Per-user assignment shape:

```sql
SELECT PermissionSet.Name, PermissionSet.Label, PermissionSetGroup.DeveloperName
FROM PermissionSetAssignment
WHERE Assignee.Username = '<username>'
LIMIT 200
```

Active-user totals (for concentration ratios):

```sql
SELECT COUNT(Id) FROM User WHERE IsActive = true AND UserType = 'Standard'
```

## Post-processing — concentration risk

- A single PSG with `assignees > active_users / 3` = "super" PSG smell (P2).
- A PS assigned only to one user = candidate for removal or promotion (P1).
- An active PSG whose components include `Modify All Data` = P0 (agent should not wait for `permission-set-architect` to flag this).

## Returns

```json
{
  "scope": "psg:Sales_Operations_Bundle",
  "active_user_count": 1200,
  "components": [
    { "permission_set": "Obj_Opportunity_ReadWrite", "category_guess": "Object" },
    { "permission_set": "Feat_Forecasts", "category_guess": "Feature" }
  ],
  "assignees": 420,
  "concentration_ratio": 0.35,
  "risk_flags": [
    { "severity": "P2", "reason": "concentration_ratio > 0.33 — \"super\" PSG smell" }
  ]
}
```

## Consumed by

- `permission-set-architect` — primary consumer
- `sharing-audit-agent` — ties PSG assignment to sharing model concerns
- `security-scanner` — flags `Modify All Data` in persona PSGs
