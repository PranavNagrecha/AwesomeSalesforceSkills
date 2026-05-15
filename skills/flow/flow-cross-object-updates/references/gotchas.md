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
