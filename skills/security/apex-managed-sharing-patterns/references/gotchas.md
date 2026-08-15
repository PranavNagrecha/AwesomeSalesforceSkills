# Gotchas — Apex Managed Sharing Patterns

Non-obvious platform behaviours that cause real production problems when granting
row access from Apex. Sourced from the Apex Developer Guide *Understanding Apex
Managed Sharing* chapter and the Salesforce Security Guide (Summer '26, API 67.0).

## Gotcha 1: There Is No Apex Managed Sharing on Standard Objects

**What happens:** A developer writes `Schema.OpportunityShare.RowCause.Deal_Team__c`
or `Schema.CaseShare.RowCause.Escalation__c` and the class refuses to save with a
compile error on the `RowCause` member. There is no Setup screen to fix it — the
Apex Sharing Reasons related list simply does not exist on standard objects.

The Apex Developer Guide states it twice in the same chapter:

> "Apex sharing reasons and Apex managed sharing recalculation are only available
> for custom objects."

**When it occurs:** Any time the requirement is phrased as "share this
Opportunity / Account / Case with the people named on it." Standard objects are
where the business data lives, so this is the *default* shape of the request.

**How to avoid:** Decide up front which of three things you actually have.

| You need | On a custom object | On a standard object |
|---|---|---|
| Access that survives owner change | Apex managed sharing with a custom sharing reason | Not available — use the built-in team (Account Team, Opportunity Team, Case Team) or accept manual-share semantics |
| Access that may be reclaimed on owner change | Manual share (`RowCause = 'Manual'`) | Manual share (`RowCause = 'Manual'`) |
| Access driven by field values, granted to a group | Criteria-based sharing rule | Criteria-based sharing rule |

You can still insert `OpportunityShare` rows from Apex. They are user managed
shares, and the Apex Developer Guide is explicit about the consequence: "Manual
shares written using Apex contains `RowCause="Manual"` by default. Only shares
with this condition are removed when ownership changes." Plan the re-grant.

---

## Gotcha 2: Apex Sharing Reasons Cannot Be Created in Lightning Experience

**What happens:** An admin opens Object Manager in Lightning, goes to the custom
object, and finds no **Apex Sharing Reasons** related list anywhere. They conclude
the feature is not licensed, or that the object needs some other setting first.
Neither is true.

> "Apex sharing reasons aren't available in Lightning Experience. Use Salesforce
> Classic to create sharing reasons within the UI."
> — Apex Developer Guide, *Creating Apex Managed Sharing*

The same applies to the **Apex Sharing Recalculation** related list used to
register the batch class.

**When it occurs:** On every org created in the last several years, because those
orgs never had Classic enabled for the admin's profile in the first place.

**How to avoid:** Do not create sharing reasons through the UI at all. Deploy them
as `SharingReason` metadata so they live in source control and survive sandbox
refresh:

```text
force-app/main/default/objects/Job__c/sharingReasons/Recruiter.sharingReason-meta.xml
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<SharingReason xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Recruiter</label>
</SharingReason>
```

If you must use the UI, switch the user to Salesforce Classic first
(**Setup → Users → [user] → Edit → uncheck Lightning Experience User**, or use the
Switch to Salesforce Classic link if it is still exposed).

---

## Gotcha 3: A Share Row That Is Not More Permissive Than the OWD Is Rejected

**What happens:** The insert fails with a `FIELD_FILTER_VALIDATION_EXCEPTION`
whose message mentions `AccessLevel`. Nothing about the message says "your OWD is
too permissive," so the usual reaction is to grant `All` — which fails differently.

The rule from the Apex Developer Guide's share-object property table:

> "This field must be set to an access level that's higher than the organization's
> default access level for the parent object."

and:

> "The object's organization-wide default access level must not be set to the most
> permissive access level. For custom objects, this level is Public Read/Write."

So on an object whose OWD is **Public Read Only**, an `AccessLevel = 'Read'` share
is redundant and rejected. On an object whose OWD is **Public Read/Write**, no
share row of any level is valid.

**When it occurs:** Most often after someone relaxes an OWD to unblock a report,
which quietly turns every managed-sharing insert in the org into an error.

**How to avoid:** Treat this specific error as expected, not exceptional, and
filter it out of your logging — that is exactly what the platform's own sample
code does:

```apex
Boolean trivialAccess =
    err.getStatusCode() == StatusCode.FIELD_FILTER_VALIDATION_EXCEPTION
    && err.getMessage().contains('AccessLevel');
if (!trivialAccess) {
    ApplicationLogger.error('JobShareService', err.getMessage());
}
```

Add an assertion to your deployment checks that the object's OWD is still Private
(or Public Read Only when you only ever grant Edit). An OWD change is a silent
functional regression for every managed-sharing class pointed at that object.

---

## Gotcha 4: `AccessLevel.USER_MODE` Breaks Apex Managed Sharing for Ordinary Users

**What happens:** A developer follows the current Apex Developer Guide sample
verbatim — it uses `Database.insert(shares, false, AccessLevel.USER_MODE)` — ships
it, and the share inserts succeed in their own admin sandbox and fail for every
sales user in production.

The reason is one sentence earlier in the same chapter:

> "Only users with 'Modify All Data' permission can add or change Apex managed
> sharing on a record."

A System Administrator has Modify All Data, so `USER_MODE` is fine in a dev org
and hides the problem entirely. A standard user does not, so the DML is rejected.

**When it occurs:** Predictably at UAT, and reported as "sharing works for admins
but not for reps" — which sends people hunting through profiles and permission
sets rather than at the DML access mode.

**How to avoid:** Run share DML in system mode deliberately, and say why in a
comment so the next reader does not "fix" it back:

```apex
// Apex managed sharing requires Modify All Data (Apex Developer Guide,
// "Creating Apex Managed Sharing"). Standard users do not have it, so this
// DML runs in system mode by design. The SELECTs that decide *who* gets a
// share still run in user mode.
Database.insert(shares, false, AccessLevel.SYSTEM_MODE);
```

Note the split. At API 67.0 database operations default to user mode and a bare
class defaults to `with sharing`, which is the behaviour you want for the queries
that read the driving data. Only the `__Share` DML needs the escape hatch.

---

## Gotcha 5: An Org-Wide Default Change Silently Wipes Your Shares

**What happens:** An admin changes the OWD on a custom object — say from Private
to Public Read Only to unblock a report — and every Apex-inserted share row
disappears. No warning, no email to the developer, no entry that names the
application.

> "Salesforce automatically recalculates sharing for all records on an object when
> its organization-wide sharing default access level changes. The recalculation
> adds managed sharing when appropriate. In addition, all types of sharing are
> removed if the access they grant is considered redundant."
> — Apex Developer Guide, *Recalculating Apex Managed Sharing*

**When it occurs:** Weeks or months after go-live, usually during an unrelated
reporting change, and the access loss is reported as a data problem.

**How to avoid:** Register a `Database.Batchable` recalculation class against the
object (**Object Manager → [object] → Apex Sharing Recalculation**, Classic only).
The platform then rebuilds your shares for you:

> "Every time a custom object's organization-wide sharing default access level is
> updated, any Apex recalculation classes defined for associated custom object are
> also executed."

and more broadly, from the Salesforce Security Guide:

> "When sharing is recalculated, Salesforce also runs all Apex sharing
> recalculations."

Treat the recalculation class as mandatory, not optional. Without it, your sharing
model is one admin click away from silent failure. Monitor execution under
**Setup → Apex Jobs**.

---

## Gotcha 6: Deleting Shares Without Filtering on `RowCause` Destroys Other Access

**What happens:** A "clean up stale shares" batch runs
`DELETE FROM Job__Share WHERE ParentId IN :ids` and removes rows the application
never created — sharing-rule rows (`RowCause = 'Rule'`), team rows
(`RowCause = 'Team'`), territory rows, and manual shares an end user set up by
hand. Those rows are rebuilt for rule-based causes on the next recalculation but
manual shares are gone for good.

**When it occurs:** In the revoke path, which is usually written last and tested
least. Also in "reset sharing" utilities written during an incident.

**How to avoid:** Every delete against a `__Share` object must be scoped to the
`RowCause` values your application owns:

```apex
delete as system [
    SELECT Id
    FROM Job__Share
    WHERE ParentId IN :jobIds
      AND RowCause IN (:Schema.Job__Share.RowCause.Recruiter__c,
                       :Schema.Job__Share.RowCause.Hiring_Manager__c)
];
```

Note that `RowCause` and `ParentId` are both documented as not updateable, so
there is no "change the reason" repair — a mis-scoped delete can only be recovered
by re-running the grant logic, and only for causes you can reconstruct.

---

## Gotcha 7: Detail Records in a Master-Detail Relationship Have No Share Object

**What happens:** `Line_Item__Share` does not exist. The developer assumes the
object is misconfigured or that sharing is disabled.

> "Objects on the detail side of a master-detail relationship don't have an
> associated sharing object. The detail record's access is determined by the
> master's sharing object and the relationship's sharing setting."
> — Apex Developer Guide, *Sharing a Record Using Apex*

**When it occurs:** Whenever a data model uses master-detail for referential
integrity and someone later needs per-record access on the child.

**How to avoid:** Decide this at data-model time, not at sharing time. If the child
needs independent row access, it must be a lookup relationship with its own OWD,
which costs you the roll-up summaries and cascade delete. That is a data-model
trade-off, and converting master-detail to lookup after go-live is a migration, not
a setting change.

---

## Gotcha 8: You Cannot Share to Unauthenticated Guest Users, and Experience Cloud Rewrites Your Groups

Two separate constraints that surface in the same Experience Cloud project.

**What happens (a):** An insert of a `__Share` row whose `UserOrGroupId` is the
site's guest user fails. The Apex Developer Guide's description of `UserOrGroupId`
ends with: "You can't grant access to unauthenticated guest users using Apex."

**What happens (b):** After digital experiences are enabled, access widens on its
own:

> "After enabling digital experiences, records accessible to Roles and Subordinates
> via Apex managed sharing are automatically made accessible to Roles, Internal,
> and Portal Subordinates. To secure external users' access, update your Apex code
> so that it creates shares to the Role and Internal Subordinates group."
> — Apex Developer Guide

So an existing, correct, internal-only sharing implementation becomes an external
data exposure the moment Experience Cloud is turned on, with no code change.

**How to avoid:** Before enabling digital experiences in any org that uses Apex
managed sharing, grep the codebase for group Ids resolved from `Group` where
`Type = 'RoleAndSubordinates'` and change them to
`RoleAndSubordinatesInternal`. The guide notes this is a large-scale operation and
recommends batch Apex for the conversion. For guest access, use the guest user
sharing rule mechanism instead of Apex.

Related, from the same chapter: share objects such as `AccountShare` and
`ContactShare` "aren't available to Customer Community Plus users," so a share
insert executed *in the context of* a community user fails even when the target of
the share is valid. Run that DML from a `without sharing` inner class or a
dedicated utility, which is what the guide recommends.

---

## Gotcha 9: 300 Sharing Rules per Object Is the Ceiling You Hit Before Apex

**What happens:** A team reaches for Apex managed sharing because "we ran out of
sharing rules," having never checked how many they actually have.

From the Salesforce Security Guide:

> "You can define up to 300 total sharing rules for each object, including up to 50
> criteria-based or guest user sharing rules."

**When it occurs:** In orgs that generate one sharing rule per region or per
business unit and grow past 50 criteria-based rules.

**How to avoid:** Count first. Hitting 50 criteria-based rules usually means the
criteria should be collapsed into a single formula-driven field that a smaller set
of rules keys off, which is far cheaper than an Apex sharing implementation you now
have to test, recalculate, and monitor forever. Reach for Apex managed sharing when
the *shape* of the policy cannot be expressed declaratively — access derived from a
child record, from a cross-object relationship, or from a value only code can
compute — not because of rule count alone. See
[`standards/decision-trees/sharing-selection.md`](../../../../standards/decision-trees/sharing-selection.md).
