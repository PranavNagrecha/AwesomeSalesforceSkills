# Examples — Dynamic Sharing Recalculation

Sharing recalculation is the asynchronous process that rebuilds `__Share` rows
after something changes the inputs to the sharing model: an org-wide default, a
sharing rule, group membership, a role or territory, or a record owner. It is
platform-managed and mostly invisible — until it takes six hours during business
hours, or until it silently does not run.

Everything below is grounded in the Salesforce Security Guide (Summer '26, API
67.0) and *Best Practices for Deployments with Large Data Volumes*.

---

## Example 1: Initial load into a Private org — sequence the model, not just the data

**Context:** A greenfield implementation loads 1,200 users, a 6-level role
hierarchy, 40 public groups, 28 owner-based sharing rules, and 10M Opportunity
records. OWD on Opportunity is Private.

**Problem:** The team's first attempt loaded records first, then users, then roles,
then all 28 sharing rules in a single Metadata API deploy. Each rule triggered a
full recalculation over 10M rows; the deploy sat in `In Progress` for most of a
day and the org was effectively read-only for sharing changes the whole time —
because "You can't modify the org-wide defaults when a sharing rule recalculation
for any object is in progress."

**Solution:** the LDV guide prescribes an explicit order. Follow it literally.

```text
Phase 0  Set Opportunity OWD to Public Read/Write for the load window.
         LDV guide: "Use Public Read/Write security during initial load to
         avoid sharing calculation overhead."
         NOTE: no __Share row can be inserted while OWD is Public Read/Write,
         so any Apex managed sharing must be disabled for this phase too.

Phase 1  Load users into roles.
Phase 2  Load record data with owners, triggering calculations in the role
         hierarchy.
Phase 3  Configure public groups and queues; let those computations propagate.
Phase 4  Add sharing rules ONE AT A TIME, letting the computation for each
         rule finish before adding the next.
Phase 5  Set Opportunity OWD to Private. This triggers a full recalculation.
Phase 6  Verify (see Example 4), then reopen the org.
```

Phase 4 is the one teams skip. The LDV guide's wording is unambiguous: "Add
sharing rules one at a time, letting computations for each rule finish before
adding the next one." Batch-deploying 28 rules produces 28 overlapping
recalculations on the same object.

**Why it works:** each phase lets the platform finish one class of computation
before the next class depends on it. Loading records before roles exist means
every record is recalculated again when the role hierarchy lands.

**Monitoring between phases:**

```text
Setup → Background Jobs
```

Wait for the queue to drain before starting the next phase. You also receive an
email notification when recalculation completes for all affected objects.

---

## Example 2: A nightly ETL into a live org — Defer Sharing Calculations

**Context:** A live org ingests 400,000 Opportunity rows per night for two weeks
during a migration. Sales users are active from 07:00.

**Problem:** Each night's load triggers group-membership and sharing-rule
computation that has not finished by 07:00. Users open the pipeline report and
see a subset of their records. The next night's load starts before the previous
night's recalculation drains, and the backlog compounds.

**Solution:** use the Defer Sharing Calculations feature. From the LDV guide:

> "An organization's administrator can use a defer sharing calculation permission
> to suspend and resume sharing calculations, and to manage two processes: group
> membership calculation and sharing rule calculation. The administrator can
> suspend these calculations when performing a large number of configuration
> changes, which might lead to very long sharing rule evaluations or timeouts, and
> resume calculations during an organization's maintenance period."

The two processes are separate switches. Suspend both for a data-and-config
migration; suspend only group membership if you are only reorganising groups.

```text
Setup → Quick Find: "Defer Sharing Calculations" → Defer Sharing Calculations

    [ ] Suspend Group Membership Calculation
    [ ] Suspend Sharing Rule Calculation

The page is only present if the feature is enabled for your org — it is not
on by default. Raise the request with Salesforce Support well before the
migration window, not the week of it.
```

**Runbook shape:**

```text
T-14d  Confirm the Defer Sharing Calculations page is visible in production.
       If it is not, the whole plan is invalid — replan or open the case now.
T-1d   Snapshot expected visibility for the verification users (Example 4).
T-0    Suspend group membership calculation AND sharing rule calculation.
       Record who suspended it and when, in the change record.
Load   Run the nightly loads. Do NOT change OWDs, roles, or sharing rules
       during the deferral unless that is the point of the window.
T+n    Resume BOTH calculations.
       Then manually recalculate: Setup → Sharing Settings → [object] →
       Sharing Rules related list → Recalculate.
       The Security Guide is explicit that this manual step is required:
       "After this work is completed, you must resume sharing rule
        calculations and manually initiate a full sharing rule recalculation
        to prevent errors."
T+n    Watch Setup → Background Jobs until the queue is empty.
       Await the completion email.
T+n    Run the verification queries. Only then reopen reports to users.
```

**Why it works:** one clean rebuild at a known time beats N partial rebuilds at
unpredictable times. The deferral converts an unbounded background cost into a
scheduled one.

**The trap:** while calculations are deferred, "The Recalculate button is disabled
when group membership or sharing rule calculations are deferred." If your runbook
says "recalculate, then resume," it is in the wrong order and the operator will
find a greyed-out button at 03:00.

---

## Example 3: Role hierarchy reorg for 1,200 users

**Context:** A regional realignment moves 1,200 users into a new role hierarchy
over a weekend.

**Problem:** Role changes cascade. Every object that grants access through the
hierarchy is affected, and on Account the cascade is wider than people expect:

> "If sharing rules are recalculated for accounts, cases, contacts, or
> opportunities, sharing rules are also recalculated for the other three objects.
> This behavior occurs because cases, contacts, and opportunities are child objects
> of accounts."
> — Salesforce Security Guide, *Automatic Recalculation of Org-Wide Defaults and
> Sharing Rules*

So a change scoped to "Accounts" recalculates four objects.

**Solution:**

```text
Saturday 02:00  Suspend group membership + sharing rule calculation.
Saturday 02:15  Apply the role hierarchy changes (Metadata API or Data Loader
                against User.UserRoleId).
Saturday 03:00  Resume both calculations.
Saturday 03:05  Manually recalculate sharing rules on Account.
                Because of the parent/child cascade above, this covers Case,
                Contact, and Opportunity as well.
Saturday 03:10  Monitor Background Jobs. Expect these subtypes:
                  Account — Parent Access Grant
                  Account — Extra Parent Access Removal
                  Object — Access Cleanup        (appears when a rule is deleted)
Sunday          Verify (Example 4). Reopen Monday.
```

**Why it works:** the deferral compresses 1,200 individual recalculation triggers
into one. Without it, "Sharing rule recalculation occurs automatically after adding
or removing individual users from a group, role, or territory, changing which role
a particular role reports to, changing which territory a particular territory is
subordinate to, or adding or removing a group from within another group" — that
is, every single user move fires its own recalculation.

**Watch for the share lock:** during the recalculation you cannot change org-wide
defaults on the affected objects, and you cannot change sharing rules while an OWD
recalculation is running. You *can* change OWDs and sharing rules for unrelated
objects. Plan any other sharing change for a different weekend.

---

## Example 4: Verifying that access actually landed

**Context:** Recalculation finished, the queue is empty, the email arrived. Before
reopening the org, prove that a real user sees what the policy says they should.

**Problem:** "The job completed" is not the same as "access is correct." A rule
that references an expired managed-package field is not recalculated at all, and
the platform does not surface that as a failure.

**Solution — a deterministic verification harness.** Pick one representative user
per persona, and one record each user should and should not see. Assert both.

The mechanism to reach for is **`UserRecordAccess`**, which answers "can this user
see this record right now" against the live sharing tables — no impersonation, no
test context, and therefore usable in the production window where the question
actually matters:

```sql
SELECT RecordId, HasReadAccess, HasEditAccess, MaxAccessLevel
FROM UserRecordAccess
WHERE UserId = '005xx0000012ABCAA2'
  AND RecordId IN ('006xx000001AAAA', '006xx000001BBBB')
```

Wrapped as a read-only probe you can run from anonymous Apex or a scheduled job
after every recalculation window:

> ⚠ **Run this as a user who can read every record in the probe set.** The Object
> Reference is explicit: "When the running user is querying a user's access to a
> set of records, records that the running user doesn't have read access to are
> filtered out of the results." A row missing from the result set therefore means
> *either* the probed user has no access *or* the operator running the probe has
> none — two very different findings. The probe below refuses to collapse them.

```apex
// Runs anywhere: anonymous Apex, a Queueable, or a scheduled sanity check.
// Read-only — it changes nothing.
public with sharing class SharingVerification {

    public class ProbeException extends Exception {}

    public static void probe(Id userId, Set<Id> shouldSee, Set<Id> shouldNotSee) {
        Set<Id> allIds = new Set<Id>();
        allIds.addAll(shouldSee);
        allIds.addAll(shouldNotSee);

        // "Up to 200 record IDs can be queried." Silently truncating would make
        // a green probe meaningless, so refuse instead.
        if (allIds.size() > 200) {
            throw new ProbeException(
                'UserRecordAccess accepts at most 200 record ids per query; got ' +
                allIds.size() + '. Split the probe set.');
        }

        Map<Id, Boolean> readable = new Map<Id, Boolean>();
        for (UserRecordAccess ura : [
            SELECT RecordId, HasReadAccess
            FROM UserRecordAccess
            WHERE UserId = :userId AND RecordId IN :allIds
        ]) {
            readable.put(ura.RecordId, ura.HasReadAccess);
        }

        for (Id recordId : allIds) {
            if (!readable.containsKey(recordId)) {
                // NOT a finding about the probed user. The row was filtered out
                // because the OPERATOR cannot read it. Treating this as
                // "no access" is how a probe reports a false failure — or, with
                // the comparison the other way round, a false pass.
                System.debug(LoggingLevel.ERROR,
                    'PROBE INVALID: operator cannot read ' + recordId +
                    ' — rerun as a user with full read on the probe set');
                continue;
            }
            Boolean canRead = readable.get(recordId);
            if (shouldSee.contains(recordId) && !canRead) {
                System.debug(LoggingLevel.ERROR,
                    'MISSING ACCESS: ' + userId + ' cannot see ' + recordId);
            }
            if (shouldNotSee.contains(recordId) && canRead) {
                System.debug(LoggingLevel.ERROR,
                    'OVER-GRANT: ' + userId + ' can see ' + recordId);
            }
        }
    }
}
```

One limit to record in the change ticket alongside the result: "This object doesn't
consider whether a user's access is blocked by a restriction rule." A green probe
means the *sharing* model grants access. If the object carries restriction rules,
the user's effective access can still be narrower, and that has to be checked
separately.

**Do not reach for `System.runAs` here.** It is test-only:

> "You can use `runAs` only in test methods."
> — Apex Developer Guide, *Using the runAs Method*

A probe built on `runAs` compiles, reads plausibly, and cannot be executed in the
production window it was written for. It has a second cost too: "Every call to
`runAs` counts against the total number of DML statements issued in the process,"
so a per-persona loop spends DML on impersonation. Use `runAs` where it belongs —
inside `@IsTest` classes that assert the sharing model's *design*, as distinct from
this probe, which verifies a *recalculation run*.

**Why it works:** it converts "recalculation finished" into "these 40
user × record assertions hold," which is a statement you can put in a change
record and hand to an auditor.

---

## Anti-Pattern: Deferring sharing calculations and forgetting to resume

**What practitioners do:** suspend both calculations before a migration, complete
the migration, and close the change ticket. The suspension is a checkbox with no
expiry and no alert.

**What goes wrong:** every subsequent group membership change, sharing rule edit,
role move, and record ownership change stops propagating. New records get owner
access only. The symptom arrives weeks later as scattered "I can't see my
colleague's records" tickets that look like a permissions problem, not a deferred
job. The Recalculate button is greyed out, which sends the admin down a
permissions rabbit hole rather than to the deferral page.

**Correct approach:** make resumption a distinct, separately-owned step in the
runbook with its own verification, not the tail of the load step. Add a standing
monitoring check that reads the Defer Sharing Calculations page state (or, at
minimum, a recurring calendar reminder for the change owner). Never close the
change record until Background Jobs is empty *and* the verification probe from
Example 4 passes.
