# Examples — Record Access Troubleshooting

Two worked diagnostic scenarios plus the most common anti-pattern.
Each scenario walks the actual SOQL (against `UserRecordAccess` and
the relevant `__Share` table) and admin click-path you would run in
the org. The point is to make the diagnosis deterministic so two
different practitioners produce the same root cause from the same
inputs.

---

## Example 1: "I can't open Opportunity 006XXXXXXXXXXXXXXX" — pinpoint with UserRecordAccess

**Context:** A sales rep (UserId `005gK000003xQVuQAM`) reports they
clicked a deep link to Opportunity `0061h00000ABCDEAAY` and got
"Insufficient Privileges. You do not have the level of access
necessary to perform the operation you requested." The Opportunity
exists — another rep can open it. OWD on Opportunity is **Private**.
You have ~2 minutes to confirm whether this is a sharing gap or a
permission bug before the rep pages their manager.

**Problem:** Practitioners jump straight to "add them to an
Opportunity team" or "give them View All on the object" without
first proving the access state. Both fix the symptom and obscure the
root cause — six months later nobody knows why that team exists, and
the View All permset has now propagated to 14 people who shouldn't
have it.

**Solution:** Run the canonical `UserRecordAccess` diagnostic first.
It's the only Salesforce-supplied query that tells you the
*effective* access for a (user, record) pair — joining across every
grant source — and it costs zero modification to the org.

Step 1 — Confirm the access state. In the Developer Console (or any
SOQL runner) run as a System Administrator:

```sql
SELECT RecordId,
       HasReadAccess,
       HasEditAccess,
       HasDeleteAccess,
       HasTransferAccess,
       HasAllAccess,
       MaxAccessLevel
FROM   UserRecordAccess
WHERE  UserId   = '005gK000003xQVuQAM'
  AND  RecordId = '0061h00000ABCDEAAY'
```

Expected result for the failing case: `HasReadAccess = false`,
`MaxAccessLevel = 'None'`. If the row *isn't returned at all*, the
RecordId is invalid for that object — you've been chasing a wrong
input.

Step 2 — Rule out the admin-bypass permissions. If the user has
`PermissionsViewAllData` or `PermissionsModifyAllData` (via a profile
or any assigned permission set), sharing is irrelevant. Run:

```sql
SELECT AssigneeId, PermissionSet.Name,
       PermissionSet.PermissionsViewAllData,
       PermissionSet.PermissionsModifyAllData,
       PermissionSet.IsOwnedByProfile,
       PermissionSet.Profile.Name
FROM   PermissionSetAssignment
WHERE  AssigneeId = '005gK000003xQVuQAM'
  AND  (PermissionSet.PermissionsViewAllData = true
        OR PermissionSet.PermissionsModifyAllData = true)
```

The `PermissionSet` row that backs a Profile has `IsOwnedByProfile =
true`, so this query also surfaces profile grants without a second
query. The object-level `View All` / `Modify All` (stored on
`ObjectPermissions.PermissionsViewAllRecords` /
`PermissionsModifyAllRecords`) are the more common bypass — they're
easier to grant than the tenant-wide `View All Data`, and they're
frequently the silent reason an access-control test fails. Check
those with a second query:

```sql
SELECT Parent.Name, SObjectType,
       PermissionsViewAllRecords, PermissionsModifyAllRecords
FROM   ObjectPermissions
WHERE  ParentId IN (SELECT PermissionSetId FROM PermissionSetAssignment
                    WHERE AssigneeId = '005gK000003xQVuQAM')
  AND  SObjectType = 'Opportunity'
  AND  (PermissionsViewAllRecords = true OR PermissionsModifyAllRecords = true)
```

Step 3 — Click "Sharing" on the record. In Lightning, open the
Opportunity → click the gear icon (top-right of the record page) →
**Sharing**. Salesforce shows every grant for the running user
context; switch to "Why can a user access this record?" (Classic
button text) or use the equivalent **Sharing Hierarchy** view to
search for the failing user. If no row appears for that user, you've
confirmed: no grant exists, period.

**Why it works:** `UserRecordAccess` is computed by the same engine
that gates the UI. If `HasReadAccess = false` there, the UI will
deny — there is no scenario in which `UserRecordAccess` lies and the
UI permits, or vice versa, unless `Restriction Rules` are in play
(Restriction Rules filter *down* after sharing; they reduce what's
queryable but don't show in `UserRecordAccess` because that object
reports the granted access, not the filtered visible set). Combining
the admin-bypass check with `UserRecordAccess` resolves the majority
of "I can't see this record" tickets in under 5 minutes, and produces
a clear audit trail: the SOQL output is the evidence that the access
gap is real, not a browser-cache artifact or a wrong RecordId.

---

## Example 2: Trace the full sharing-cause chain via AccountShare

**Context:** Finance asks: "Why can the regional VP edit the
'Acme Industries' Account? She's not the owner, she's not in the
account team, and there's no role hierarchy above her that owns it."
You need to enumerate every grant for that Account and explain each
one — finance is preparing a SOX walkthrough and needs the access
chain documented for an auditor.

**Problem:** Practitioners look only at the "Sharing" button on the
record and report what it says. The button surfaces the *winning*
grant per user, not every grant — so when an Account is shared via
both a sharing rule AND an Apex managed share, only one is shown.
For a SOX walkthrough, the auditor wants every grant enumerated and
classified by `RowCause`. The button can't produce that.

**Solution:** Query `AccountShare` directly, enumerate every row for
the ParentId, and join the grantee to resolve User vs Group vs Role
vs Territory. The `RowCause` field is the canonical reason code.

Step 1 — Walk the canonical hierarchy in order. Salesforce evaluates
sharing in this priority sequence — checking each before moving on:

1. **Ownership** — `Account.OwnerId` always wins; full access.
2. **Role hierarchy** — if "Grant Access Using Hierarchies" is on
   for the object (always on for standard, optional for custom),
   every user *above* the owner in the role tree inherits the owner's
   access.
3. **Sharing rules** — owner-based (records owned by group X go to
   group Y) and criteria-based (records matching field criteria go
   to group Y), both materialize as `RowCause = 'Rule'` rows.
4. **Teams** — `AccountTeamMember`, `OpportunityTeamMember`,
   `CaseTeamMember` rows produce `RowCause = 'Team'` shares.
5. **Manual shares** — created via the Share button or the
   `Sharing` REST endpoint; `RowCause = 'Manual'`.
6. **Apex managed shares** — created by Apex code with a custom
   `RowCause` (the API name of an Apex Sharing Reason metadata
   record, ending in `__c`).
7. **Implicit parent/child shares** — Contact/Opportunity/Case access
   *implies* parent Account access (`RowCause = 'ImplicitChild'`);
   master-detail children inherit parent access
   (`RowCause = 'ImplicitParent'`).

Step 2 — Enumerate every grant on the Account:

```sql
SELECT Id,
       UserOrGroupId,
       AccessLevel,            -- Read | Edit | All
       RowCause,               -- Owner | Manual | Rule | Team |
                               -- ImplicitChild | ImplicitParent |
                               -- TerritoryManual | TerritoryRule |
                               -- TerritoryRule2 | <ApexRowCause>
       ParentId,
       LastModifiedDate
FROM   AccountShare
WHERE  ParentId = '0011h00000XYZWXAA0'
ORDER  BY RowCause, AccessLevel DESC
```

Step 3 — Resolve each `UserOrGroupId`. `UserOrGroupId` can be a
User (005), a public Group (00G), a Role group (00G with
`DeveloperName` prefixed `Role` / `RoleAndSubordinates` /
`RoleAndSubordinatesInternal`), a Territory group, or a Queue. Run:

```sql
SELECT Id, Type, DeveloperName, RelatedId, Name
FROM   Group
WHERE  Id IN ('00Ggk000001abcdEAQ', '00Ggk000001efghIAQ')
```

`Group.Type` resolves to values like `Role`, `RoleAndSubordinates`,
`Territory`, `Queue`, `Regular` (a Public Group), or
`SharingRuleHeader`. The naming convention for hierarchy groups is
the giveaway: `Role` = just users in that role; `RoleAndSubordinates`
= that role *plus everyone below*; `RoleAndSubordinatesInternal`
excludes Partner/Customer users.

Step 4 — Map each `RowCause` to the configuration that created it.
The canonical mapping:

| `RowCause` | What created it | Where to find it in Setup |
|---|---|---|
| `Owner` | Record owner | Owner field on the record |
| `Manual` | "Share" button click (or `Sharing` REST API) | Sharing detail page |
| `Rule` | Owner-based or criteria-based sharing rule | Setup → Sharing Settings → Sharing Rules |
| `Team` | Account / Opportunity / Case Team membership | Team-related list on record |
| `ImplicitChild` | Contact/Opportunity/Case share implies parent Account access | Implicit by platform; not configurable |
| `ImplicitParent` | Master-detail child inherits parent access | Implicit by platform |
| `TerritoryManual` / `TerritoryRule` / `TerritoryRule2` | Enterprise Territory Management assignment | Setup → Territories |
| `<DeveloperName>__c` | Apex Managed Sharing reason | The `<Object>` Sharing Reason metadata + Apex `insert` |

Step 5 — For each row, decide if the grant is justified. The
auditable output is a table: one row per `RowCause`, with the
configuration source named, the business owner who approved it, and
the review cadence. The regional VP's edit access typically resolves
to `RowCause = 'Rule'` (a criteria-based sharing rule like "Industry
= Manufacturing → Western Region Public Group, Read/Write") — name
the rule, screenshot it, attach to the SOX evidence.

**Why it works:** Every record-level access on any non-Public-Read/Write
object is materialized as a `__Share` row at the moment it's granted.
`__Share` is the source of truth — the "Sharing" button is a UI
that filters and groups rows for human reading. By querying
`<Object>Share` directly you bypass any UI filtering and see the
raw grant set. Pairing this with `UserRecordAccess` lets you
answer both "what access does this user have?" (UserRecordAccess)
and "why do they have it?" (`__Share` + `RowCause` mapping) —
together they cover every diagnostic question short of
restriction-rule subtraction.

For standard objects the share table name follows the pattern
`<Object>Share` (e.g., `AccountShare`, `OpportunityShare`,
`CaseShare`, `LeadShare`). For custom objects it's `<API_Name>__Share`
(double-underscore-Share, e.g., `Project__c` → `Project__Share`).
Standard objects that are always Public Read/Write (e.g., `User`) and
objects with OWD `Controlled by Parent` have no separately-queryable
share table.

---

## Anti-Pattern: "Just grant Modify All to fix the ticket"

**What practitioners do:** A frustrated practitioner triages 11
access tickets in one afternoon and copies the same "fix" into each
one: assign the `Sales_Power_User` permission set, which has
`PermissionsModifyAllData = true` (tenant-wide Modify All Data). The
tickets all close as resolved. Ops moves on.

**What goes wrong:** Three failure modes compound. **First, the
underlying configuration bug is now invisible** — the sharing rule
that should have matched these records is still broken, but nobody
will discover it until a different user (not in the permset) hits
the same gap. **Second, `Modify All Data` bypasses every Field-Level
Security restriction, every Restriction Rule, every Apex `with
sharing` check, and every encrypted-field probabilistic-match
constraint** — the permset user can now read PII fields, financial
exports, and historical records they were specifically gated from.
**Third, Security Health Check flags `ModifyAllData` assignments as
a critical risk** — the org's health score drops, and on the next
audit the answer to "why does this user have ModifyAllData?" is "to
fix a ticket six months ago" — which is the *exact* finding that
triggers a mandatory access review cycle.

The deeper problem: `ModifyAllData` is not a sharing tool — it's an
*administrative* permission, intended for the system administrators
who maintain the org itself (data migrations, mass cleanups,
metadata deployments). Routing it through ticket-resolution is a
category error.

**Correct approach:** Use `UserRecordAccess` to confirm the gap, then
fix the *configuration* at the lowest-permission tier that resolves
it. The hierarchy of fixes, from least to most invasive:

1. **Add the user to the right Role / Public Group** if a sharing
   rule grants on that group. Zero new sharing configuration; the
   existing rule does the work.
2. **Add a manual share or Apex managed share** on just this record
   if access should be narrow. Manual shares disappear on ownership
   change; Apex shares with a `RowCause` survive transfer.
3. **Add the user to an Account / Opportunity / Case Team** if the
   record uses teams. Team membership is the auditable, role-named
   alternative to manual shares.
4. **Add an owner-based or criteria-based sharing rule** if a
   *class* of records needs to grant to a *class* of users. Sharing
   rules recalculate async — wait for completion before testing.
5. **Change OWD only as a last resort.** Loosening OWD from
   `Private` to `Public Read Only` is a tenant-wide change that
   triggers a full sharing recalculation (can take hours on a large
   org) and changes the security posture for every record on that
   object.

`ModifyAllData` and the object-level `ModifyAllRecords` belong on
integration users (one user, narrow scope, audited via Setup Audit
Trail) and on dedicated system-administrator accounts — never as a
ticket-resolution shortcut. The rule of thumb: if your fix involves
`Modify All`, you've stopped diagnosing and started covering up.
