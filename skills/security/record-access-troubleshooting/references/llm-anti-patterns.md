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
Custom Apex sharing reasons survive ownership transfer — but they are
available ONLY on custom objects. There is no way to declare one on
Account, Opportunity, Case or any other standard object.

// CUSTOM object — custom Apex sharing reason is available
Project__Share s = new Project__Share(
    ParentId       = proj.Id,                              // ParentId
    UserOrGroupId  = uid,
    AccessLevel    = 'Edit',                               // AccessLevel
    RowCause       = Schema.Project__Share.RowCause.SalesOps__c
);
insert s;

// STANDARD object — different object name AND different field names.
// Only built-in RowCause values are available; to survive an owner
// change, re-create the share in an after-update trigger on OwnerId,
// or move the requirement to a sharing rule / account team.
AccountShare a = new AccountShare(
    AccountId          = acc.Id,                           // NOT ParentId
    UserOrGroupId      = uid,
    AccountAccessLevel = 'Edit',                           // NOT AccessLevel
    RowCause           = Schema.AccountShare.RowCause.Manual
);
insert a;
```

**Detection hint:** Apex code inserting a `__Share` row with `RowCause = 'Manual'` in a context where the record owner may change.

---

## Anti-Pattern 6: Applying the Custom-Object `__Share` Naming Convention to Standard Objects

**What the LLM generates:**
```apex
Account__Share s = new Account__Share(
    ParentId    = acc.Id,
    UserOrGroupId = uid,
    AccessLevel = 'Edit',
    RowCause    = Schema.Account__Share.RowCause.SalesOps__c
);
```
Also as SOQL: `SELECT ... FROM Account__Share WHERE ParentId = '001...'`, and as prose: "query `<Object>__Share` for any object with a restrictive OWD."

**Why it happens:** `MyObject__c → MyObject__Share` is the pattern that appears in every Apex managed sharing tutorial, because those tutorials are all built on the custom `Job__c` example in the Apex Developer Guide. The model generalises the rule to all objects, and the double-underscore suffix *looks* like a platform convention rather than a custom-object marker. The `__Share` form is genuinely a rule — it is just a rule about custom objects only.

**Three errors compound in the generated block:**
1. `Account__Share` does not exist. Standard objects append `Share` with no underscores: `AccountShare`, `OpportunityShare`, `CaseShare`, `ContactShare`.
2. Standard object shares do not have `ParentId` or `AccessLevel`. They use `<Object>Id` and `<Object>AccessLevel` — `AccountShare.AccountId` and `AccountShare.AccountAccessLevel`.
3. `Schema.AccountShare.RowCause.SalesOps__c` cannot exist under any spelling. The Apex Developer Guide: "Apex sharing reasons and Apex managed sharing recalculation are only available for custom objects."

**Correct pattern:**
```
                     Standard object          Custom object
Share object         AccountShare             Project__Share
Parent lookup        AccountId                ParentId
Access level field   AccountAccessLevel       AccessLevel
Custom Apex reason   NOT AVAILABLE            Schema.Project__Share.RowCause.X__c

To make a standard-object share survive an owner change, you cannot use a
custom RowCause. Re-create the share from an after-update trigger on OwnerId,
or express the requirement as a sharing rule / account team instead.
```

**Detection hint:** the string `__Share` preceded by a standard object name is always wrong — mechanically, `__Share` on any token that does not end in `__c` before substitution. Second checkable tell: `ParentId` or a bare `AccessLevel` assigned on a share object whose name lacks `__`. Third: `Schema.<Anything>Share.RowCause.<Anything>__c` where the object is standard — a custom RowCause with no `__Share` in the type name cannot compile.

---

## Anti-Pattern 7: Owner-based remediation on the detail side of a master-detail

**What the LLM generates:** asked to "route `Inspection__c` records to the Field
Ops queue," it produces a queue design plus

```apex
Inspection__c i = [SELECT Id, OwnerId FROM Inspection__c WHERE Id = :recId];
i.OwnerId = fieldOpsQueueId;
update i;
```

— or an owner-based sharing rule, or a manual share, on the same object.

**Why it happens:** the model treats `OwnerId` as universally present on every
sObject, because it is present on every object it has seen in a tutorial. That
`Inspection__c` is the *detail* side of a master-detail to `Account` is invisible
in the prompt and never checked.

**Correct pattern:**

```
The Object Reference: "The Owner field on the detail object isn't available and
is automatically set to the owner of its associated master record," and "Custom
objects on the detail side of a master-detail relationship can't have sharing
rules, manual sharing, or queues, because these elements require the Owner
field." There is nothing to grant at the child level — "The detail record
inherits the sharing and security settings of its master record," so fix access
on the MASTER. If the child genuinely needs its own owner, sharing rules or
queues, the relationship is the wrong shape: it has to be a Lookup, which is a
data-model change, not a sharing change.

Confirm before recommending anything owner-based:
  SELECT QualifiedApiName FROM FieldDefinition
  WHERE  EntityDefinition.QualifiedApiName = 'Inspection__c'
    AND  QualifiedApiName = 'OwnerId'
Zero rows on a custom object = it is the detail side of a master-detail.
```

**Detection hint:** any `OwnerId` read or write, `__Share` insert, queue
assignment, or owner-based sharing rule proposed for a custom object that
carries a master-detail relationship field to a parent — Apex or SOQL naming
`OwnerId` there does not compile, because the field does not exist. OWD
`Controlled by Parent` is *not* the tell: Contact carries that OWD and still has
an Owner (see `gotchas.md` Gotcha 3).
