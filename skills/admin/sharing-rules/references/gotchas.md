# Gotchas — Sharing Rules

Non-obvious platform behaviour that turns a correct-looking sharing rule into a production incident.

---

## Gotcha 1: The Rule Saves Instantly and Grants Nothing for a While

**What happens:** An admin creates a sharing rule, the page returns without error, and the intended users report no change. The page that saved the rule says nothing further and does not link to the job it just started, so the admin assumes the rule is broken and goes to edit it — and finds the org-wide defaults and that object's other sharing rules locked against changes until the job finishes.

**Why:** Sharing rules are not evaluated when a user opens a record. Salesforce precomputes access: "Rather than applying every sharing rule, traversing all hierarchies, and analyzing record access inheritance in real time, Salesforce calculates record access data only when configuration changes occur. The calculated results persist in a way that facilitates rapid scanning and minimizes the number of database table joins necessary to determine record access at run time." Saving the rule is the *configuration change*; writing the access grants is a separate, asynchronous job whose duration scales with how many records match and how many users the target group resolves to. The same source is explicit that in large orgs "it can take some time to recalculate access for a large number of users, and adjust the tables that record their access rights."

The job is asynchronous but it is *not* invisible, and this is where most published advice on sharing rules is wrong. The Security Guide documents a progress view — "You can monitor the progress of your parallel sharing rule or organization-wide default recalculation on the Background Jobs page or view recent sharing operations on the View Setup Audit Trail page" — and a completion signal: "You receive an email notification when the recalculation is completed for all affected objects." It also documents share locks while the job runs: "You can't modify the org-wide defaults when a sharing rule recalculation for any object is in progress. Similarly, you can't modify sharing rules when recalculation for an org-wide default update is in progress."

**How to avoid:** Open Setup → Background Jobs and find the recalculation before concluding anything, then verify with SOQL against the object's share table rather than by asking a user to refresh. Rows appear as recalculation progresses, so a partial result is a normal intermediate state, not a defect.

```soql
SELECT COUNT(Id)
FROM AccountShare
WHERE RowCause = 'Rule' AND UserOrGroupId = '00GXX0000012345'
```

Re-run it a few minutes apart. A rising count means the job is working. Do not edit or delete the rule while the count is still climbing — for the object under recalculation the platform will refuse the change, and anywhere it does let an edit through you have queued more work, not less. Tell stakeholders "access will appear over the next while," never "it is live now."

**Source:** [T1] Record-Level Access: Under the Hood (Spring '26) — https://architect.salesforce.com/fundamentals/record-level-access-under-hood, local copy `knowledge/imports/salesforce-record-access-under-the-hood.md`. [T1] Salesforce Security Guide (v262) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_security_impl_guide.pdf — Recalculate Sharing Rules Manually / Automatic Recalculation of Org-Wide Defaults and Sharing Rules (Background Jobs, completion email, share locks).

---

## Gotcha 2: Changing a Record's Owner Silently Rewrites Its Access

**What happens:** A deal is transferred between reps as part of routine pipeline hygiene. Nobody touched a sharing rule. The next day a whole team has lost sight of the record, and a different team has gained it.

**Why:** Owner-based rules key off the *current* owner's group membership, so a transfer moves the record out of one rule's scope and into another's. Worse, manual shares do not survive the move at all: "When a record owner changes, Salesforce deletes its associated sharing rows with Manual row causes." The documented scenario continues: "because Maria, the Sales Executive, no longer owns the record, the rule from Scenario 3 no longer applies. Under the hood, Salesforce deletes the sharing row for the Services Exec RoleAndSubordinates group … causing Frank and Sam to lose access to the Acme record."

**How to avoid:** Treat ownership transfer as a sharing event. Before any mass transfer, list which owner-based rules reference the source and destination groups, and be explicit with the business that anyone who was holding access through a manual share will lose it. If the access must survive transfers, it cannot be a manual share — either an owner-based rule whose target group covers both populations, or `apex/apex-managed-sharing` with a custom sharing reason, which the Apex Developer Guide describes as "maintained when the record owner changes or is deactivated."

**Source:** [T1] Record-Level Access: Under the Hood, Scenario 4 (Ownership Change); Apex Developer Guide — Creating Apex Managed Sharing — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_bulk_sharing_creating_with_apex.htm.

---

## Gotcha 3: `includeRecordsOwnedByAll` Is Write-Once and Its Label Hides What It Does

**What happens:** A criteria-based rule is created, works for months, and then someone notices that records owned by the integration user, or by a portal-adjacent account, never appear for the target team. The admin opens the rule to flip the setting and finds it greyed out.

**Why:** The Metadata API reference is unambiguous on both halves. The field "indicates whether records owned by users who can't have an assigned role are included in the records shared (true) or not (false)", and "you can't edit this field after the sharing rule is created." Users who can't have an assigned role are a real and growing population in most orgs — integration users, some external identity types, and accounts provisioned outside the role hierarchy. The same write-once constraint applies to the guest-rule equivalent, `includeHVUOwnedRecords`, which controls "whether records owned by high-volume community or site users are included."

**How to avoid:** Decide the value during design, not in the Setup form. Write it into the rule design record alongside the access level. If it turns out wrong, the only remedy is to delete and recreate the rule — and that is a full recalculation on the object twice over, so schedule it rather than doing it in the middle of a business day.

**Source:** [T1] Metadata API Developer Guide — SharingRules (`SharingCriteriaRule`, `SharingGuestRule`) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_sharingrules.htm.

---

## Gotcha 4: Criteria on a Churning Field Makes Every Record Edit a Sharing Job

**What happens:** A criteria-based rule keys on `Status`, `StageName`, `Priority`, or a similar workflow field. The rule is logically perfect. Six months later the org is slow on bulk updates, Data Loader jobs that used to take minutes take hours, and nobody connects it to sharing.

**Why:** Criteria-based rules are re-evaluated whenever a criteria field changes, because that change can move the record in or out of the rule's match set — which means adding or deleting share rows. A field that changes on most records regularly converts routine data maintenance into continuous sharing-table maintenance. This compounds with group complexity: "the size and complexity of an organization's queues and hierarchies directly affect the duration of record access calculations," so the same rule that is cheap in a flat org is expensive in a deep one.

**How to avoid:** Prefer criteria fields that are set once and rarely revisited — record type, a classification picklist, a country, an ownership flag. If the requirement genuinely follows a workflow field, ask whether the access actually needs to follow it, or whether an owner-based rule on the team that handles that stage expresses the same intent without the churn. When a bulk update to a criteria field is unavoidable, batch it into a deferral window (Gotcha 7).

**Source:** [T1] Record-Level Access: Under the Hood — Group Maintenance Tables and recalculation cost.

---

## Gotcha 5: One Account Rule Is Really Four

**What happens:** The business asks for "read access to partner accounts." An admin creates the Account rule, accepts the defaults on the three extra pickers, and inadvertently exposes the partner pipeline, every partner contact, and every partner case to a team that was only supposed to see company names.

**Why:** Account sharing rules carry a nested `accountSettings` block, and the Metadata API marks all three of its members required: `caseAccessLevel`, `contactAccessLevel`, and `opportunityAccessLevel`, each taking `None`, `Read`, or `Edit`. There is no "leave it alone" value — every Account rule makes an explicit statement about the account's children whether the admin thought about it or not. The blast radius is wider than the one object, too: "If sharing rules are recalculated for accounts, cases, contacts, or opportunities, sharing rules are also recalculated for the other three objects."

**How to avoid:** Write all four access levels into the design before opening Setup, and set the child levels to `None` unless the requirement names those children. In review, read the deployed XML rather than the Setup page — the block is unambiguous in metadata and easy to skim past in the UI.

```xml
<accountSettings>
    <caseAccessLevel>None</caseAccessLevel>
    <contactAccessLevel>Read</contactAccessLevel>
    <opportunityAccessLevel>None</opportunityAccessLevel>
</accountSettings>
```

**Source:** [T1] Metadata API Developer Guide — SharingBaseRule / AccountSharingRuleSettings — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_sharingbaserule.htm. [T1] Salesforce Security Guide (v262) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_security_impl_guide.pdf — Automatic Recalculation of Org-Wide Defaults and Sharing Rules (four-object recalculation).

---

## Gotcha 6: You Cannot Revoke Rule Access by Deleting the Share Row

**What happens:** An auditor finds an unwanted grant. Someone queries the share object, finds the offending row, and deletes it — through Data Loader, through anonymous Apex, or through a script. The access comes back.

**Why:** The share row is an output of the rule, not the rule itself. `RowCause` records which mechanism produced the grant, and the Apex Developer Guide states plainly that "the reason determines the type of sharing, which controls who can alter the sharing record", and that `RowCause` and `ParentId` both "can't be updated." Rows with `RowCause = 'Rule'` belong to the platform's managed sharing; the next recalculation touching that record recreates them. Only manual shares (`RowCause = 'Manual'`) and Apex managed shares with custom reasons are yours to delete.

**How to avoid:** Revoke by changing the cause — narrow the criteria, change the target group's membership, or delete the rule. Use the share table for diagnosis, never for remediation. When an audit turns up a grant nobody can explain, the query that answers "why" is a `RowCause` breakdown, not a row hunt:

```soql
SELECT RowCause, COUNT(Id)
FROM AccountShare
WHERE AccountId = '001XX000003DHPh'
GROUP BY RowCause
```

**Source:** [T1] Apex Developer Guide — Understanding Sharing / Creating Apex Managed Sharing — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_bulk_sharing_understanding.htm.

---

## Gotcha 7: Deferral Does Not Reduce the Work — It Concentrates It

**What happens:** A team enables defer sharing calculation for a big data load, loads everything, resumes, and is surprised when the resume itself runs long enough to be an incident.

**Why:** The feature "allows users to defer the processing of sharing rules until after new users, rules, and other content have been loaded", and an administrator "can use a defer sharing calculation permission to suspend and resume sharing calculations, and to manage two processes: group membership calculation and sharing rule calculation." Suspension does not cancel anything. Every deferred change accumulates and is settled on resume, in one job, on an org that by then has more records in it than when the work was deferred.

**How to avoid:** Treat the resume as the maintenance window, not the load. Sequence structural changes so the deferred set is as small as it can be — the documented load order is to load users into roles first, then record data with owners, then public groups and queues, then add sharing rules one at a time. Resuming is one step of two, not the end: "After this work is completed, you must resume sharing rule calculations and manually initiate a full sharing rule recalculation to prevent errors." Budget for that full recalculation inside the window. Note also that deferral costs you the manual escape hatch while it is on — "The Recalculate button is disabled when group membership or sharing rule calculations are deferred" — so a rule that misbehaves mid-load cannot be recalculated on demand until you resume.

**Source:** [T1] Salesforce Large Data Volumes Best Practices — Defer Sharing Calculation; local copy `knowledge/imports/salesforce-large-data-volumes-best-practices.md`. [T1] Salesforce Security Guide (v262) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_security_impl_guide.pdf — Recalculate Sharing Rules Manually (mandatory full recalculation after resume; Recalculate button disabled while deferred).

---

## Gotcha 8: Sharing to a Queue Only Works on Three Object Families

**What happens:** A design shares Opportunity records to a queue so the desk that owns the queue can see them. The rule cannot be built, or it is built against a public group whose name resembles the queue and quietly grants a different population.

**Why:** The Metadata API `SharedTo` reference constrains the `queue` recipient: "A list of queues with sharing access. Applies only to lead, case, and CustomObject sharing rules." Public groups have no such restriction, which is why the two get conflated — the group workaround succeeds where the queue does not, and its membership is not the same thing.

**How to avoid:** Share to a public group and, if the same people also work a queue, make the group the queue's member rather than duplicating the roster. See `admin/queues-and-public-groups` for the queue-versus-group distinction, and its Gotcha 6 for the `roleAndSubordinates` → `roleAndSubordinatesInternal` rename that affects every `sharedTo` element written before Secure Roles.

**Source:** [T1] Metadata API Developer Guide — SharedTo — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_sharedto.htm.

---

## Gotcha 9: Guest Sharing Rules Are a Different Type With a Locked Access Level

**What happens:** A public-facing site needs an object exposed. Someone builds an ordinary criteria-based rule pointing at a group that contains the guest user, sets it to Read/Write because the site has a form, and ships it.

**Why:** `SharingGuestRule` is its own array under `SharingRules`, introduced in API version 47.0, and it is the mechanism for guest access. Its access ceiling is fixed: "For `SharingGuestRule`, the `accessLevel` field can be set only to `Read`." Criteria support on guest rules arrived later, in API version 48.0. A rule built as a normal criteria-based rule is a different metadata type with different constraints and is not the supported path for unauthenticated access.

**How to avoid:** Build guest access as `SharingGuestRule` with `sharedTo` → `guestUser` and `accessLevel` of `Read`. If the site needs to write, the write path is not a sharing rule — it is an Apex controller or a flow running in a context that can perform the DML. Everything about the guest profile, the site's object permissions, and what the page can render belongs to `admin/experience-cloud-guest-access` and `security/guest-user-security`.

**Source:** [T1] Metadata API Developer Guide — SharingRules (`SharingGuestRule`) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_sharingrules.htm.

---

## Gotcha 10: A Rule on a Public Read/Write Object Is Dead Weight

**What happens:** An org loosens an OWD to Public Read/Write to solve a visibility complaint and leaves the object's existing sharing rules in place. Later the OWD is tightened again during a security review and the old rules — written for a different org shape, targeting groups that have since drifted — snap back into effect all at once.

**Why:** Access grants are the mechanism only under a restrictive baseline: "When an object has its organization-wide default set to Private or Public Read Only, Salesforce uses access grants to define how much access a user or group has to that object's records." Under Public Read/Write the grants are redundant, so the rules appear harmless and stop being reviewed — but they are still definitions, still counted against the object's rule budget, and still deployed to every sandbox.

**How to avoid:** When an OWD is relaxed, delete the rules that the relaxation made redundant rather than leaving them dormant. When an OWD is tightened, audit every existing rule on that object *before* the change lands, because the recalculation that follows will write every grant those rules describe. Record the object's current rule inventory in the design doc so the next admin inherits the list rather than rediscovering it.

**Source:** [T1] Record-Level Access: Under the Hood — Access Grants.

---

## Gotcha 11: The Rule-Count Cap Is 300, and the 50 Is Inside It — Not Next to It

**What happens:** A design review budgets "300 sharing rules plus 50 criteria-based ones" on an object, or reserves the 50 for criteria-based rules and then discovers guest user rules have been eating the same allowance. Later, a rule fails to save on an object nobody thought was near a ceiling.

**Why:** The Salesforce Security Guide states it in one sentence: "You can define up to 300 total sharing rules for each object, including up to 50 criteria-based or guest user sharing rules, if available for the object." Three things in that sentence get lost in retelling:

| Reading | Correct? |
|---|---|
| 300 total per object, all rule types combined | Yes |
| 50 is a sub-limit **inside** the 300 | Yes — "including up to 50" |
| 350 rules are available if 50 are criteria-based | No |
| The 50 is reserved for criteria-based rules | No — criteria-based **or guest user** rules share it |
| The numbers change by edition | No — see below |

The edition dependency is real but attaches to a different dimension: which *objects* support sharing rules, not how many rules an object gets. "The objects available for sharing rules depend on which Salesforce editions and features you have," and "Only account, asset, campaign, and contact sharing rules are available in Professional Edition."

**How to avoid:** Record the object's current count against 300/50 in the design record before adding a rule, and count guest rules against the 50. Treat a count that climbs every quarter as evidence that the OWD or the role hierarchy is wrong rather than as a number to optimise against — the cap is a ceiling, not a target. `data/sharing-recalculation-performance` and `admin/data-skew-and-sharing-performance` carry the volume-side analysis.

**Source:** [T1] Salesforce Security Guide (v262) — Sharing Rules; Sharing Rule Considerations — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_security_impl_guide.pdf
