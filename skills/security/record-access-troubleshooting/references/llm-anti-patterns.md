# LLM Anti-Patterns — Record Access Troubleshooting

Common mistakes AI coding assistants make when diagnosing record-access issues.

## Anti-Pattern 1: Guessing sharing cause without UserRecordAccess

**What the LLM generates:** Long narrative about "probably the role hierarchy" or "maybe a sharing rule" without querying.

**Why it happens:** Model defaults to plausible-sounding explanations.

**Correct pattern:**

```
Start every diagnosis with a deterministic query:

SELECT RecordId, HasReadAccess, HasEditAccess, HasDeleteAccess,
       MaxAccessLevel
FROM UserRecordAccess
WHERE UserId = '005...' AND RecordId = '001...'

Then open the record's Sharing detail page → "Why can this user
access this record?" for the explicit reason. Guessing wastes time
and produces wrong remediation.
```

**Detection hint:** Troubleshooting narrative that does not reference `UserRecordAccess` or the Sharing detail page.

---

## Anti-Pattern 2: Forgetting admin-bypass permissions

**What the LLM generates:** "Add a sharing rule for this user" when the user already has `View All Data`.

**Why it happens:** Model focuses on sharing-layer mechanics and misses the profile/permset layer.

**Correct pattern:**

```
Sharing is irrelevant when the user has:
- View All Data / Modify All Data (org-wide)
- View All / Modify All on the object
- "Delegated Admin" for the user's role

Always check first:

SELECT PermissionsViewAllData, PermissionsModifyAllData
FROM PermissionSetAssignment
WHERE AssigneeId = :uid

If true, the fix is at the permission layer — removing a sharing rule
won't stop access; remove the permission or assign to fewer users.
```

**Detection hint:** Remediation suggests "add sharing rule" or "remove sharing rule" without checking admin-level permissions.

---

## Anti-Pattern 3: Ignoring restriction rules

**What the LLM generates:** "User has a __Share row, so they have access" — then user reports zero visible records.

**Why it happens:** Restriction rules are newer (2022+) and not in model's default mental model.

**Correct pattern:**

```
Restriction rules filter DOWN the result set AFTER sharing grants.
A user can have read access via a share row yet still see zero
records because a restriction rule's filter excludes them.

Check: Setup → Object Manager → Restriction Rules. If active,
trace the filter against the user's context fields.

The diagnostic order is:
1. Admin bypass?
2. Sharing chain (ownership/role/rules/teams/manual/apex/implicit)
3. Restriction rule filter
```

**Detection hint:** Sharing trace that confirms `__Share` row but fails to explain why user sees 0 records.

---

## Anti-Pattern 4: Assuming role hierarchy grants access on all objects

**What the LLM generates:** "User is above owner in role hierarchy, so they have read access."

**Why it happens:** Model doesn't know "Grant Access Using Hierarchies" is a per-object toggle.

**Correct pattern:**

```
For custom objects with Private OWD, "Grant Access Using Hierarchies"
can be disabled. When off, even the CEO doesn't inherit access from
subordinates.

Check: Setup → Sharing Settings → OWD → scroll to Default Internal
Access column and the "Grant Access Using Hierarchies" checkbox.

Standard objects: always on, cannot disable.
Custom objects: on by default, can be disabled.
```

**Detection hint:** Hierarchy-based explanation for a custom object without verifying the toggle state.

---

## Anti-Pattern 5: Using a manual share that won't survive ownership change

**What the LLM generates:** "Insert a AccountShare row with RowCause='Manual' and AccessLevel='Edit'."

**Why it happens:** Model picks the simplest Share row.

**Correct pattern:**

```
RowCause='Manual' shares are deleted when the record's owner changes.
For persistent Apex-managed sharing, declare a custom Apex Sharing
Reason (per-object) and use its RowCause:

Account__Share s = new Account__Share(
    ParentId = acc.Id,
    UserOrGroupId = uid,
    AccessLevel = 'Edit',
    RowCause = Schema.Account__Share.RowCause.SalesOps__c
);
insert s;

Shares with a custom RowCause survive ownership transfers.
```

**Detection hint:** Apex code inserting a `__Share` row with `RowCause = 'Manual'` in a context where the record owner may change.
