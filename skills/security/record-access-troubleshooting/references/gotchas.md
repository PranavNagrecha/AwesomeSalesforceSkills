# Gotchas — Record Access Troubleshooting

Five second-order behaviors that mislead diagnosis. These compound
the basic sharing rules in `SKILL.md`'s gotchas list — they're the
things that make the diagnostic answer wrong even when the
`UserRecordAccess` query and `__Share` enumeration look correct.

## Gotcha 1: View All / Modify All silently bypass both sharing rules AND OWD

**What happens:** You diagnose a "user can see records they
shouldn't" ticket, query `AccountShare` for the records in question,
and find no share row for the user. You query the sharing rules and
none match. You conclude the OWD must be misconfigured — but OWD on
Account is `Private`. Nothing in the sharing model explains the
visibility. The actual cause: the user has a permission set with
`PermissionsViewAllData = true` (or the object-level
`PermissionsViewAllRecords` on `ObjectPermissions`), which makes
*every record of that object* visible regardless of any sharing
configuration. The `__Share` table is irrelevant for users with
these grants — Salesforce doesn't bother to materialize share rows
when the user has the bypass.

**When it occurs:** Any audit of "why does this user see X" where
the answer is "they have an admin-bypass permset." Particularly
common after a permset cleanup project that "consolidated" multiple
narrow permsets into a broad `Power_User` permset — the broad
permset usually picked up `View All` on objects the original narrow
permsets didn't grant. Also common when a permset *group* with
muting includes a member permset that has `View All`, because the
muting permset can mute *field*-level access but cannot mute
object-level `ViewAllRecords` / `ModifyAllRecords`.

**How to avoid:** Always include the admin-bypass check as Step 2
of any troubleshooting session — query
`PermissionSetAssignment` joined to `PermissionSet` for
`PermissionsViewAllData`, `PermissionsModifyAllData`, and join to
`ObjectPermissions` for object-level `PermissionsViewAllRecords` /
`PermissionsModifyAllRecords`. Salesforce's "Why can a user access
this record?" / Sharing Hierarchy view does *not* show admin-bypass
as the reason — it shows "owner" or "sharing rule" or whatever the
*nominal* reason would have been if the bypass weren't there, which
is actively misleading. Run the permission query yourself.

---

## Gotcha 2: Sharing recalculation runs async — the Share button doesn't appear immediately after OWD changes

**What happens:** An admin changes Account OWD from `Public Read Only`
to `Private` to support a new business unit's isolation requirement.
They immediately test by opening a record and looking for the
"Sharing" button (which only appears when an OWD is more restrictive
than Public Read/Write). The button isn't there. They conclude the
OWD change didn't take effect, re-save the OWD setting, the button
still doesn't appear, and they raise a "platform bug" with support.

**When it occurs:** Any OWD tightening (Public Read/Write →
Public Read Only, Public Read Only → Private, etc.) triggers an
async sharing recalculation job. On a large org (millions of
records), this can take *hours*. The UI elements that depend on the
new OWD (the Sharing button, the AccountShare table's existence,
the sharing rule editor's "Default" picklist values) only become
fully consistent after the recalculation completes. Loosening OWD
(Private → Public Read Only) is faster because Salesforce just stops
enforcing sharing on that object — but tightening requires
materializing every previously-implicit grant as a row.

**How to avoid:** Set expectations before the OWD change. In Setup
→ Sharing Settings, after submitting an OWD change, Salesforce
shows a banner like "Your settings have been queued for processing.
You'll receive an email when the recalculation is complete." Watch
for that email before testing. In sandbox, you can monitor progress
via Setup → Background Jobs (look for "Sharing Recalculation" or
"Parallel Sharing Recalculation" job types). For diagnostic queries
during the window, `UserRecordAccess` reports the *current*
materialized state — so a user might genuinely have read access via
implicit grants that will be revoked once recalculation finishes.
Don't make sharing-design decisions on data captured mid-recalc.

---

## Gotcha 3: Implicit Account ↔ Contact/Opportunity sharing does NOT extend to custom child objects

**What happens:** A practitioner builds a custom `Site_Visit__c`
object as a child of Account via a Lookup relationship. They set
OWD to `Controlled by Parent`, expecting that anyone with Account
access automatically gets Site_Visit access. Users who can see the
parent Account get "Insufficient Privileges" on the child Site
Visit. The practitioner adds `Controlled by Parent` again, redeploys,
same result. The actual cause: `Controlled by Parent` requires a
**master-detail** relationship, not a Lookup. A Lookup-child custom
object has its own OWD (Private/Public Read Only/Public Read/Write)
and must be shared independently. The implicit-parent-share behavior
(`RowCause = 'ImplicitParent'`) only fires for master-detail.

The reverse asymmetry also bites: implicit *child-to-parent* shares
(`RowCause = 'ImplicitChild'`) only exist between the four
hardcoded pairs — Contact→Account, Opportunity→Account, Case→Account,
and Order→Account — and they grant Read on the Account when the user
has access to the child. This does **not** extend to custom
relationships, regardless of whether they're master-detail or Lookup.
A custom `Project__c` that's a child of `Account` does not implicitly
grant Account read access when a user is granted Project access.

**When it occurs:** Any custom-child-of-standard data model where
the architect assumed parent-child implicit sharing would propagate.
The Service Cloud expansion case is the textbook example: teams add
a custom `Service_Visit__c` related to Account, configure
"Controlled by Parent" expecting the standard Contact-like behavior,
and find that field service technicians (who have Account access
via a sharing rule) can't see the visits assigned to their accounts.

**How to avoid:** Decide upfront whether the relationship needs to be
master-detail (loses ability to reparent, child inherits parent OWD,
parent cannot be deleted while children exist) or Lookup (independent
sharing). For Lookup-child objects, either share them explicitly
(sharing rule on the child) or write Apex managed sharing that
mirrors the parent's grants. Don't assume the four-object implicit
sharing extends — those four pairs are hardcoded in the platform
and the list has not expanded.

---

## Gotcha 4: Apex Managed Sharing requires the Sharing Reason metadata to exist AND be active — deleting it orphans existing shares

**What happens:** An Apex trigger has been inserting `Project__Share`
rows with `RowCause = 'Project_Manager_Access__c'` for two years.
A developer cleans up "unused metadata" and deletes the
`Project_Manager_Access` Apex Sharing Reason because they don't see
any code referencing it (they missed the trigger's hardcoded string).
The deployment succeeds. Two days later, all 47,000 existing
`Project__Share` rows with that `RowCause` are gone — Salesforce
cascades the deletion of the Sharing Reason to every share row
that used it. Project Managers lose access en masse. Restoring the
Sharing Reason metadata does not restore the share rows — they have
to be re-inserted by re-running the trigger logic over every
in-scope Project.

**When it occurs:** Two pathways. (1) Metadata cleanup where an
Apex Sharing Reason looks orphaned because its grep-able name only
appears in a trigger as a string literal, not in any other metadata.
(2) Refactoring an Apex Sharing class to use a different reason name
without backfilling the old shares — same effect, but in slow
motion as old shares decay (sharing recalculation removes them as
records are touched).

The naming rule for Apex Sharing Reasons: they live as child metadata
of the parent object (Setup → Custom Objects → `<Object>` → Apex
Sharing Reasons), with a `Label` and a `DeveloperName`. When you
insert a `__Share` row from Apex, you set `RowCause =
Schema.<Object>Share.RowCause.<DeveloperName>__c` — Salesforce
appends the `__c` automatically. Querying back, the `RowCause`
field returns the full `<DeveloperName>__c` string.

**How to avoid:** Before deleting an Apex Sharing Reason, query the
share table for any rows that use it:

```sql
SELECT COUNT() FROM Project__Share
WHERE  RowCause = 'Project_Manager_Access__c'
```

If the count is non-zero, you must (1) re-route the Apex to use a
new RowCause and backfill the existing shares first, or (2) accept
that deletion will revoke those grants. Document Apex Sharing
Reasons in the same place you document trigger handlers — the
coupling between the metadata name and the hardcoded string in
Apex is invisible to most static-analysis tools (PMD, Code
Analyzer) and only surfaces under runtime testing.

---

## Gotcha 5: Restriction Rules subtract access AFTER sharing computes — and don't show up in "Why can this user access this record?"

**What happens:** A user reports they used to see 1,200 records in
the `Highly_Sensitive_Case__c` list view and now see 73. Owner has
not changed. Their permset assignments have not changed. Sharing
rules have not changed. The "Why can a user access this record?"
explanation for one of the *missing* records, when run from an
admin context, returns nothing — there's no share row for the user,
but the user *did* have access yesterday. The actual cause: a
Restriction Rule was activated on `Highly_Sensitive_Case__c`
yesterday. Restriction Rules (GA in Spring '22) are a *filter-down*
mechanism — they take the records the user would otherwise see
through sharing and subtract the records that don't match the
restriction rule's criteria.

The diagnostic challenge: Restriction Rules don't remove `__Share`
rows. They don't appear in the "Sharing" UI. `UserRecordAccess`
still reports `HasReadAccess = true` for the user/record pair (the
*grant* is still there). But the record is invisible in list views,
search, reports, and SOQL run as that user — because the Restriction
Rule filter is applied *after* sharing computes, at query time.

**When it occurs:** Any object that has Restriction Rules enabled
(introduced as a separate metadata type — Setup → Object Manager →
`<Object>` → Restriction Rules). Common in highly-regulated industries
(financial services, healthcare) where access to sensitive records
must be tightened beyond what OWD + sharing can express. Also
appears as a "scoping rule" on certain standard objects (User, Lead,
Case) — Scoping Rules are similar mechanism but default-filter
records out of list views without preventing direct-link access,
whereas Restriction Rules actually prevent the access.

**How to avoid:** Add Restriction Rules to the diagnostic checklist.
For every troubleshooting session, run:

```sql
SELECT Id, DeveloperName, Active, IsActive,
       UserCriteria, RecordCriteria
FROM   RestrictionRule
WHERE  TargetEntity = 'Highly_Sensitive_Case__c'
```

(The exact field names depend on API version; verify against the
current Object Reference.) If any active rule exists, check whether
the troubled user matches its `UserCriteria` (or fails to, depending
on whether the rule is inclusive or exclusive). The other diagnostic
tell: run the same SOQL once as the user (via "Login As") and once
as a system admin. If the admin sees the record and the user
doesn't, but `UserRecordAccess` returns `HasReadAccess = true` for
the user, you're looking at a Restriction Rule. Document the rule
as the root cause; don't try to "fix" it by adding more sharing
(the rule will still subtract).

**The exemption that makes this a security finding, not just a
diagnostic one:** per Restriction Rule Considerations, *"Restriction
rules aren't applied for code executed in System Mode."* Any
`@AuraEnabled` controller, any `without sharing` class, any
system-context Flow, any Apex invoked from a trigger or a REST
service in system mode returns **exactly the records the restriction
rule was written to hide**. A restriction rule is a UI-and-user-mode
filter, not a security boundary for code. Two more overrides worth
stating on the same page: *"Users with the View All Records or View
All Data permissions can view all records regardless of restriction
rules. Users with the Modify All Records or Modify All Data
permissions can view, edit, and delete all records regardless of
restriction rules."*

So when a restriction rule is the intended control, the audit is not
"is the rule active" but "does every code path to this object run in
user mode" — `WITH USER_MODE`, `with sharing` plus explicit FLS/CRUD,
or `Security.stripInaccessible`. And note the edition ceiling while
you are there: *"You can create up to two active restriction rules
per object in Enterprise and Developer Editions and up to five active
restriction rules per object in Performance and Unlimited Editions."*
