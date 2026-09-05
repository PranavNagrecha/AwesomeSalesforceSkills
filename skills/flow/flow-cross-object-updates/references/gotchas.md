# Gotchas — Flow Cross-Object Updates

Behaviors that catch even experienced Flow builders when a record-
triggered flow writes to a related record. These compound the rules
in `SKILL.md`'s gotchas section — these are the second-order issues
that only surface after the first round of fixes.

## Gotcha 1: "Update Records" with a filter (not an input collection) is NOT bulk-safe

**What happens:** The Update Records element accepts two modes:
"Specify conditions to identify records, and set fields individually"
(filter mode) and "Use the IDs and all field values from a record or
record collection" (collection mode). Practitioners often use filter
mode for cross-object writes — it reads more cleanly in Flow Builder.
What's not obvious: filter mode issues ONE underlying DML *per record
that triggered the flow*, even when the resulting filter matches the
same target each time.

**When it occurs:** A child-triggered flow uses Update Records with
filter `Id = {!$Record.AccountId}` to stamp a field on the parent.
For a bulk batch of 200 Contacts that all belong to ONE Account,
this issues... 200 DML against the same Account. The Flow engine
doesn't deduplicate filter conditions across batch members.

**How to avoid:** Use collection mode whenever you can. Build the
update records in an Assignment element (one per batch member),
add to a collection, deduplicate by Id (use a unique-ID collection-
processor invocable action or a Decision element checking
`contains`), then call Update Records once with the collection.
For the simple case of "stamp the same value on the parent of every
triggering record," accept the per-record DML — Flow's auto-
bulkification may also collapse identical filters in some
configurations, but don't rely on it for high-volume flows.

---

## Gotcha 2: `ISCHANGED()` returns `true` on insert for any non-null source field

**What happens:** An entry condition uses `ISCHANGED({!$Record.Status__c})`
intending to fire only when an *existing* record's Status changes.
The flow also fires on insert when the inserted record has a
non-null Status (which is most of them) — because in Flow's
ISCHANGED semantics, "changed from null/empty to the inserted
value" counts as a change.

**When it occurs:** Any record-triggered flow on update where the
intent was "only fire on real status transitions, not on new
records." Common pairings: status-cascade flows, audit-history
flows, notification flows.

**How to avoid:** Guard ISCHANGED with `NOT(ISNEW())` in the
entry condition. The combination `ISNEW() AND ISCHANGED(field)`
will never both be true on the same trigger — ISCHANGED is
INSERT-permissive in Flow, which is the opposite of its Apex
behavior. Practitioners coming from Apex find this consistently
surprising.

---

## Gotcha 3: A flow that updates the parent re-triggers a parent-side flow on the same transaction

**What happens:** A Contact-triggered flow updates the parent
Account's `Last_Contact_Date__c`. There's also an Account-triggered
flow that listens for `ISCHANGED(Account.Last_Contact_Date__c)`.
Both flows fire on every Contact insert/update — sometimes the
Account-side flow then writes back to the Contact (e.g., setting
`Account_Tier__c`), which re-triggers the Contact flow, which can
loop until the platform's recursion detection (16 levels) kicks in.

**When it occurs:** Bidirectional parent/child flows where each
side reacts to the other's changes. The classic ping-pong scenario:
parent-flow stamps child, child-flow stamps parent, parent-flow
notices stamp changed, child-flow stamps again.

**How to avoid:** Guard both sides with strict entry conditions
that won't fire on the *kind* of change the other side produces.
A safer pattern: have only ONE side write to a "calculated" field
on the other, and never read that calculated field back into a
trigger condition. If you absolutely need bidirectional updates,
use a transient flag (Custom Setting `Flow_Recursion_Guard__c =
TRUE` during the first pass) and skip the second-side flow when
the flag is set — clear the flag in a Decision element at the end.

---

## Gotcha 4: `Get Records` with no matches returns `null`, not an empty collection

**What happens:** A flow does Get Records to fetch related Contacts;
when no Contact exists, the resulting collection variable is
`null`. The next Loop element on that null collection throws
`The flow failed to access the value for variable's "current item"
because it hasn't been set or assigned`.

**When it occurs:** Edge cases where the relationship is empty —
new Accounts with no Contacts, freshly converted Leads with no
Opportunity yet, etc. Often only discovered when a real-world
edge case hits.

**How to avoid:** Before every Loop on a Get Records output, add
a Decision element with the condition
`{!getRecordsOutput} IS NULL` → bypass the loop, route to a
sensible default (do nothing, set a "no matches" flag, or stamp
the parent with a zero count). Or, switch to the "Get just the
first record" mode of Get Records — its output is a single record
variable that's null-safe in subsequent assignments without
the collection-iteration step.

---

## Gotcha 5: Cross-object writes don't respect the running user's CRUD/FLS by default

**What happens:** A Customer Community user triggers an action
that runs a record-triggered flow which writes to an Account
field they don't have edit access to. The write succeeds because
flows run in **system context** by default — bypassing the user's
profile-level CRUD and FLS. The same write done by the user via
the standard UI would be denied.

**When it occurs:** Any flow not explicitly configured to enforce
sharing. Spring '21 introduced the `RunInMode` property on
records-triggered flows (System Context with Sharing / Without
Sharing / User Context); Auto-launched flows have similar
settings. Default for newly created flows varies by Salesforce
release — older flows tend to be "Without Sharing"; newer ones
"With Sharing"; neither enforces FLS automatically.

**How to avoid:** Explicitly choose the flow's mode on the
Properties panel. For flows triggered by community/portal users,
set "How to Run the Flow" to `System Context with Sharing` and
add explicit `IsAccessible()` / `IsUpdatable()` checks via a
Decision element when writing sensitive fields. The wrong default
is a real security gap — many orgs have an open finding from
Security Health Check pointing at this exact issue, with a list
of flows that bypass user permissions.

---

## Audit of Gotchas 1–5 against the official guides (2026-09-05)

The five gotchas above predate this package's grounding pass. Each was re-checked
line-by-line against the Metadata API Developer Guide (`api_meta.txt`), the Apex
Developer Guide (`apexdev.txt`), the Bulk API guide (`api_asynch.txt`) and the App
Limits Cheat Sheet. Read the verdicts before you cite any of them.

| # | Claim | Verdict |
|---|---|---|
| 1 | Filter-mode Update Records issues one DML **per triggering record** | **UNVERIFIED (2026-09-05)** — `FlowRecordUpdate` (`api_meta.txt` L71264–71292) documents the two modes and says nothing about how the engine batches either one. It also sits in direct tension with the "Flow bulkifies automatically" claim elsewhere in this package. Treat the per-record cost as a *hypothesis to test in your org's debug log*, not a fact. The mitigation (deduplicate, use collection mode) is sound regardless of which way the test lands |
| 2 | `ISCHANGED()` in a Flow entry condition returns `true` on insert | **UNVERIFIED (2026-09-05)** — not stated in any fetchable guide, and it inverts the documented behaviour of the same function in validation rules. What *is* grounded, and makes the question moot: set `<recordTriggerType>Update</recordTriggerType>` (`api_meta.txt` L72448–72461) so the flow never runs on insert, and `<doesRequireRecordChangedToMeetCriteria>true</doesRequireRecordChangedToMeetCriteria>` (L72322–72326) so it fires only on a transition into the criteria. Both are declarative and neither depends on how `ISCHANGED` behaves |
| 3 | Bidirectional flows loop until recursion detection at 16 levels | **GROUNDED** on the number — "total stack depth for any Apex invocation that recursively fires triggers due to insert, update, or delete statements: 16" (`apexdev.txt` L19559). The re-entry mechanism is grounded too: "when a process or flow executes a DML operation, the affected record goes through the save procedure" (`apexdev.txt` L15468) |
| 4 | Get Records with no matches yields `null`, not an empty collection | **PARTIALLY GROUNDED** — `assignNullValuesIfNoRecordsFound` "specifies that all values are set to null when no record is found" and is "supported only when `storeOutputAutomatically` is false" (`api_meta.txt` L71100–71110). That documents the null semantics for the *variable-output* form. UNVERIFIED (2026-09-05): the exact runtime error text quoted in Gotcha 4 is from Flow Builder, not from any guide |
| 5 | Flows run in system context by default | **CONTRADICTED as worded.** `runInMode` `DefaultMode` means "how the flow is launched determines whether the flow runs in user context or in system context" (`api_meta.txt` L68374–68378) — not "system". The rest of the gotcha is grounded: `SystemModeWithSharing` "respects org-wide default settings, role hierarchies, sharing rules, manual sharing, teams, and territories. The flow doesn't respect object permissions, field-level access, or other permissions of the running user" (L68379–68386). Also **CONTRADICTED**: `runInMode` is available in API version 48.0 and later, with `SystemModeWithoutSharing` added at 49.0 (L68386–68390) — not introduced in Spring '21. The advice (set the mode explicitly) stands |

---

## Gotcha 6: Changing the relationship between MasterDetail and Lookup is a data-loss operation inside a metadata deploy

**What happens:** A deploy that flips `Subscription_Line__c.Subscription__c` from
`Lookup` to `MasterDetail` — or back — behaves unlike any other field change.
The guide states three separate consequences. First, the change "isn't
supported when using the `checkOnly` option to test a deployment. This change
isn't supported for test deployments to avoid permanently altering your data.
If a change that isn't supported for test deployments is included in a
deployment package, the test deployment fails and issues an error"
(`api_meta.txt` L4177–4183). Second, "for a deployment with a new
Master-Detail field, soft delete (send to the Recycle Bin) all detail records
before proceeding to deploy the Master-Detail field, or the deployment fails.
During the deployment, detail records are permanently deleted from the Recycle
Bin and can't be recovered" (L4202–4206). Third, converting a Lookup to a
Master-Detail requires that "detail records must reference a master record or
be soft-deleted (sent to the Recycle Bin) for the deployment to succeed.
However, a successful deployment permanently deletes any detail records in the
Recycle Bin" (L4207–4213).

**When it occurs:** Late in a project, when someone realises the roll-up
summary they want needs master-detail and adds the field-type change to the
next release's manifest. The pipeline's standard `deploy validate` step fails
with an error nobody recognises, so the change gets pushed straight to a real
deploy — which is exactly the path the guide is trying to prevent.

**How to avoid:** Take the relationship-type change out of the release
manifest and run it as its own deploy against a *full* sandbox first, which
"includes a validation of the changes as part of the deployment process"
(L4185–4189). Before that deploy, empty the Recycle Bin deliberately rather
than discovering it was emptied for you. And check the orphan population
first — `SELECT COUNT() FROM Subscription_Line__c WHERE Subscription__c = NULL`
— because those rows are what the guide is describing when it says detail
records must reference a master.

---

## Gotcha 7: Bulk child inserts serialise on the parent record's lock

**What happens:** A cross-object flow is blamed for a load that fails with
lock timeouts, when the locking is a property of the *relationship*, not of
the flow. The Bulk API guide is explicit about the mechanism: "when an
AccountTeamMember record is created or updated, the corresponding Account for
this record is locked during the transaction. If you upload different jobs
that include AccountTeamMember records, and they all contain references to the
same account, they all try to lock the same account, and it's likely that you
experience a lock timeout" (`api_asynch.txt` L2701–2707). The remedy is a
data-organisation one: "for large data loads, sort main records based on their
parent record to avoid having different child records (with the same parent)
in different jobs" (L2700–2702).

**When it occurs:** Any high-volume child load into a relationship where many
children share one parent — which is the shape every cross-object flow in this
skill is built for. It compounds when a child-triggered flow *also* writes the
parent: now each child's own transaction takes the same parent lock the loader
is contending for.

**How to avoid:** Sort the load file by parent Id so one job holds one parent's
children (`api_asynch.txt` L2700–2707; the classic Bulk API 1.0 wording is at
L4997–5003). Know the retry behaviour before you tune anything: "the Bulk API
doesn't generate an error immediately when encountering a lock. It waits a few
seconds for its release and, if it doesn't happen, the record is marked as
failed. If there are problems acquiring locks for more than 100 records in a
batch, the Bulk API places the remainder of the batch back in the queue for
later processing" (L5003–5008). If it persists, serial mode "ensures that only
one batch is processed at a time" (L5008–5010). `flow/flow-record-locking-and-contention`
owns the in-transaction side of this.

---

## Gotcha 8: A recursive save skips the roll-up steps, so a flow inside one cannot trust the roll-up value

**What happens:** A parent-side flow reads `Active_Line_Count__c` to decide
something, and the number is right when a human edits a line and wrong when
the same line is edited by another automation. The save order explains it. Roll-up
recalculation is step 16 — "if the record contains a roll-up summary field or is
part of a cross-object workflow, performs calculations and updates the roll-up
summary field in the parent record. Parent record goes through save procedure"
(`apexdev.txt` L15471–15473) — and step 17 does the same for a grandparent.
But: "during a recursive save, Salesforce skips steps 9 (assignment rules)
through 17 (roll-up summary field in the grandparent record)"
(`apexdev.txt` L15414–15415). Step 16 is inside that skipped range.

**When it occurs:** Whenever the child DML originates from automation that is
itself running inside a save — a flow's Update Records, an Apex trigger's
`update`, a roll-up's own parent re-save. The first, human-initiated save gets
a fresh roll-up; the nested ones do not.

**How to avoid:** Never branch a flow on a roll-up summary field that the same
transaction just caused to change. If the decision needs a current count, compute
it from the collection you already hold — see `flow/flow-collection-processing`
— rather than reading the stored field. If the decision genuinely needs the
committed value, move it to an asynchronous path so it runs after the transaction
settles. `flow/flow-record-save-order-interaction` owns the full step-by-step.

---

## Gotcha 9: On master-detail, writing the child requires access to the parent — and the default is the restrictive one

**What happens:** A parent→child fan-out flow that works for admins fails for
ordinary users with an access error on the *child* write, even though the
users have edit access to the child object. The controlling field is on the
relationship, not on either object's permissions: `writeRequiresMasterRead`
"sets the minimum sharing access level required on the primary record to
create, edit, or delete child records… `true` — allows users with Read access
to the primary record permission to create, edit, or delete child records.
This setting makes sharing less restrictive. `false` — allows users with
Read/Write access to the primary record permission to create, edit, or delete
child records. This setting is more restrictive than `true`, and is the
default value" (`api_meta.txt` L43724–43734).

**When it occurs:** Any flow whose `runInMode` leaves record access to the
running user, on a master-detail relationship where the user's access to the
parent is read-only — a common shape when the parent is owned by a different
team. On junction objects it gets stricter still: "for junction objects, the
most restrictive access from the two parents is enforced" (L43735–43738).

**How to avoid:** Decide the flow's `runInMode` explicitly and record why.
`SystemModeWithSharing` "respects org-wide default settings, role hierarchies,
sharing rules, manual sharing, teams, and territories" (`api_meta.txt`
L68379–68383), so it does not escape this constraint — it enforces it. If the
flow must write children for users who only read the parent, the fix is
`writeRequiresMasterRead` set to `true` on the relationship field, which is a
sharing-model decision to take with whoever owns the parent object, not a flow
setting.

---

## Gotcha 10: `limit`, `getFirstRecordOnly` and `assignNullValuesIfNoRecordsFound` are mutually gated, and a wrong combination fails at deploy

**What happens:** A Get Records on the child collection is hardened with all
three settings at once and the flow will not deploy, or deploys and ignores
one of them. Each has a documented precondition and they do not overlap:

| Field | Precondition | Guide |
|---|---|---|
| `limit` | "Supported only when `getFirstRecordOnly` is `false`". Valid values 2 to 20,000. API 63.0+ | `api_meta.txt` L71177–71185 |
| `getFirstRecordOnly` | "Supported only when `storeOutputAutomatically` is `true`". API 47.0+ | L71153–71163 |
| `assignNullValuesIfNoRecordsFound` | "Supported only when `storeOutputAutomatically` is `false`". API 30.0+ | L71100–71110 |
| `outputAssignments`, `outputReference` | Both "supported only when `storeOutputAutomatically` is `false`" | L71188–71199 |

So `getFirstRecordOnly` and `assignNullValuesIfNoRecordsFound` require
*opposite* values of `storeOutputAutomatically` and can never both apply to
one element.

**When it occurs:** Hand-editing flow XML, or an assistant generating it from
a field list without reading the precondition column. Also when a flow built
in an older org is redeployed after the `apiVersion` is raised — `limit` did
not exist before 63.0 and the element silently had no ceiling.

**How to avoid:** Pick the output style first. Automatic output
(`storeOutputAutomatically` true) gives you `getFirstRecordOnly` and `limit`;
that is the combination the parent→child fan-out in
`references/metadata-examples.md` § 3 uses, and it is the right default for a
child collection. Manual output (false) gives you `outputReference` and
`assignNullValuesIfNoRecordsFound`, which is what you want only when a
downstream element needs a named variable. Setting `apiVersion` below 63.0
silently drops `limit`, so treat an unbounded child Get as an `apiVersion`
question as well as a design one.
