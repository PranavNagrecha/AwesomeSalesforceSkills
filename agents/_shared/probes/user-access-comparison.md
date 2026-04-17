# Probe: user-access-comparison

## Purpose

Produce a structured, symmetric comparison of two Users' access surface in a live org. Used by the `user-access-diff` agent to answer "what does User A have that User B doesn't, and vice versa."

Scope covers the permission surface a single Apex runtime check would honor: profile + active Permission Sets + active Permission Set Groups (flattened through component membership), plus role hierarchy placement, public-group membership, queue membership, and territory membership where present.

This probe is read-only. It does not compute sharing-rule outcomes — two users with identical PSes can still see different records when OWD + sharing rules + role hierarchy interact. Use `sharing-audit-agent` for that layer.

---

## Arguments

| Arg | Type | Required | Notes |
|---|---|---|---|
| `user_a` | string | yes | Username OR 15/18-char `User.Id` |
| `user_b` | string | yes | Username OR 15/18-char `User.Id` |
| `dimensions` | array | no (default `all`) | Any of: `profile`, `permission-sets`, `object-crud`, `fls`, `system-perms`, `apex-classes`, `vf-pages`, `tabs`, `apps`, `record-types`, `custom-perms`, `groups`, `queues`, `territories`, `all` |
| `include_field_permissions` | boolean | no (default `false`) | Off by default — FLS rows explode across broad PSes |

---

## Queries

### 1. User shape (both users, one query each)

```sql
SELECT Id, Username, Name, IsActive, UserType, ProfileId, Profile.Name,
       UserRoleId, UserRole.Name, ManagerId, Manager.Username,
       DefaultCurrencyIsoCode, LanguageLocaleKey, TimeZoneSidKey
FROM User
WHERE Id = '<user_a_id>'
LIMIT 1
```

Run twice — once per user.

### 2. Active Permission Set + PSG assignments (excludes any expired via `ExpirationDate`)

```sql
SELECT PermissionSetId, PermissionSet.Name, PermissionSet.Label,
       PermissionSet.IsCustom, PermissionSet.Type,
       PermissionSetGroupId, PermissionSetGroup.DeveloperName,
       ExpirationDate
FROM PermissionSetAssignment
WHERE AssigneeId = '<user_a_id>'
  AND (ExpirationDate = null OR ExpirationDate > TODAY)
LIMIT 200
```

Note: `PermissionSet.Type = 'Group'` rows are the PSG's internal permission set — filter to `Type != 'Group'` when listing human-facing PSes, and follow the `PermissionSetGroupId` link separately.

### 3. PSG components (flatten each PSG the user has)

```sql
SELECT PermissionSetGroupId, PermissionSetId, PermissionSet.Name, PermissionSet.Label
FROM PermissionSetGroupComponent
WHERE PermissionSetGroupId IN (<list-of-psg-ids-from-query-2>)
LIMIT 500
```

The effective PS set for a user = (direct PS assignments) ∪ (components of assigned PSGs).

### 4. Object CRUD (for each dimension PS in either user's effective set)

```sql
SELECT ParentId, Parent.Label, Parent.Type,
       SObjectType, PermissionsRead, PermissionsCreate, PermissionsEdit,
       PermissionsDelete, PermissionsViewAllRecords, PermissionsModifyAllRecords
FROM ObjectPermissions
WHERE ParentId IN (<effective-ps-ids>)
LIMIT 2000
```

### 5. Field-level security (only if `include_field_permissions = true`)

```sql
SELECT ParentId, SObjectType, Field, PermissionsRead, PermissionsEdit
FROM FieldPermissions
WHERE ParentId IN (<effective-ps-ids>)
LIMIT 5000
```

### 6. System permissions (boolean flags on the PS itself)

```sql
SELECT Id, Name, PermissionsModifyAllData, PermissionsViewAllData,
       PermissionsManageUsers, PermissionsApiEnabled, PermissionsAuthorApex,
       PermissionsCustomizeApplication, PermissionsManageDataCategories,
       PermissionsEditPublicReports, PermissionsManageSharing,
       PermissionsViewSetup, PermissionsViewAllUsers,
       PermissionsViewEventLogFiles, PermissionsPasswordNeverExpires,
       PermissionsManagePasswordPolicies
FROM PermissionSet
WHERE Id IN (<effective-ps-ids>)
LIMIT 500
```

### 7. Setup Entity Access (Apex classes, VF pages, Flows, Custom Permissions, Named Credentials)

```sql
SELECT ParentId, SetupEntityId, SetupEntityType
FROM SetupEntityAccess
WHERE ParentId IN (<effective-ps-ids>)
LIMIT 5000
```

`SetupEntityType` values: `ApexClass`, `ApexPage`, `FlowDefinition`, `CustomPermission`, `NamedCredential`, `ExternalDataSource`, `TabSet`, `ConnectedApplication`.

### 8. Group / queue / territory membership

```sql
SELECT GroupId, Group.Name, Group.Type, Group.DeveloperName
FROM GroupMember
WHERE UserOrGroupId = '<user_a_id>'
LIMIT 500
```

`Group.Type` values include `Regular` (public group), `Queue`, `Role`, `RoleAndSubordinates`, `Territory`, `TerritoryAndSubordinates`.

### 9. Territory2 assignment (if Enterprise Territory Management is enabled)

```sql
SELECT Territory2Id, Territory2.Name, Territory2.Territory2ModelId
FROM UserTerritory2Association
WHERE UserId = '<user_a_id>'
LIMIT 100
```

---

## Post-processing — diff shape

For each dimension, produce three sets:

- `identical` — rows present in both users with the same grant state
- `only_a` — present in A, absent in B
- `only_b` — present in B, absent in A

Key for diffing object CRUD: `(SObjectType, specific-crud-flag)` — not just SObjectType. A and B may both have Account rows but only A has `PermissionsDelete = true`.

Key for FLS: `(SObjectType, FieldName, permission-type)`.

Key for SetupEntityAccess: `(SetupEntityType, SetupEntityId)`.

Key for GroupMember: `Group.DeveloperName` (or `GroupId` when DeveloperName is null, which happens for role-derived groups).

### Risk flags the probe can surface

- `P0` — one user has `ModifyAllData` and the other does not (huge blast-radius delta; verify intentional)
- `P0` — one user has `ViewAllUsers` and the other does not (privacy implication)
- `P1` — one user has `AuthorApex` and the other does not
- `P1` — delta in `PermissionsManageSharing` or `PermissionsManageUsers`
- `P2` — > 20-object CRUD delta (suggests role divergence; not necessarily wrong)
- `P2` — PSG components differ but direct PS assignments are identical (silent drift via PSG re-composition)

---

## Returns

```json
{
  "user_a": {
    "id": "005XX0000012abc",
    "username": "alice@acme.com",
    "profile": "Standard User",
    "role": "NA Sales Manager",
    "active": true
  },
  "user_b": {
    "id": "005XX0000034def",
    "username": "bob@acme.com",
    "profile": "Standard User",
    "role": "NA Sales Rep",
    "active": true
  },
  "dimensions_compared": ["profile", "permission-sets", "object-crud", "system-perms", "groups"],
  "summary": {
    "identical_count": 87,
    "only_a_count": 14,
    "only_b_count": 3,
    "highest_severity": "P0"
  },
  "by_dimension": {
    "permission-sets": {
      "identical": ["Sales_Core", "Forecast_Viewer"],
      "only_a": ["Sales_Ops_PSG (Group)"],
      "only_b": []
    },
    "object-crud": {
      "identical": [
        {"object": "Account", "flags": ["Read", "Create", "Edit"]},
        ...
      ],
      "only_a": [
        {"object": "Quote", "flags": ["Read", "Create", "Edit", "Delete"]},
        ...
      ],
      "only_b": []
    },
    "system-perms": {
      "identical": ["ApiEnabled"],
      "only_a": ["ModifyAllData", "ViewAllUsers"],
      "only_b": []
    },
    "groups": {
      "identical": ["NA_Sales_All"],
      "only_a": ["Sales_Leadership"],
      "only_b": []
    }
  },
  "risk_flags": [
    {"severity": "P0", "dimension": "system-perms", "delta": "only_a has ModifyAllData"},
    {"severity": "P0", "dimension": "system-perms", "delta": "only_a has ViewAllUsers"}
  ]
}
```

---

## Governor-limit considerations

- Query 2 is cheap — PSAs per user rarely exceed 30.
- Query 4 (ObjectPermissions) can return thousands of rows across broad PSes. Batch by chunks of 100 PS Ids per query if effective set is large.
- Query 5 (FieldPermissions) is opt-in specifically because a single `Administrator` PSG can return 50k+ FLS rows. Enable only when the user explicitly asks for FLS diff.
- `SetupEntityAccess` is the longest single query in practice; tune with `LIMIT` + pagination if the org has > 1000 Apex classes + > 500 Custom Permissions.

---

## Consumed by

- `user-access-diff` — primary consumer
- `permission-set-architect` — when designing a new PS to match an existing user's access
- `profile-to-permset-migrator` — to verify post-migration access parity with pre-migration users

---

## See also

- `agents/_shared/probes/permission-set-assignment-shape.md` — single-user access shape
- `skills/admin/permission-set-architecture`
- `skills/admin/user-management`
