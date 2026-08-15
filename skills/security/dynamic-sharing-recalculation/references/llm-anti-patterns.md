# LLM Anti-Patterns — Dynamic Sharing Recalculation

Mistakes AI assistants reliably make when asked to plan a large load, a role
reorg, or "why can't users see their records after the migration."

## Anti-Pattern 1: Treating Defer Sharing Calculations as a Setting the Admin Can Just Turn On

**What the LLM generates:** "Before the load, go to Setup → Defer Sharing
Calculations and check both suspend boxes."

**Why it happens:** The feature has a Setup page and a Quick Find entry, so it
looks like every other org preference. Nothing in the phrasing of most
documentation snippets signals that the page may not exist.

**Correct pattern:**

```
Defer Sharing Calculations is conditional. The Security Guide says
"If enabled in your org, you can temporarily defer sharing rule calculations."

The plan must therefore contain a verification step BEFORE it contains a
usage step:

  T-14d or earlier:
    Confirm the Setup -> Defer Sharing Calculations page renders in
    PRODUCTION. If it does not, open a Salesforce Support case and treat
    the enablement date as a schedule dependency.

Never write a migration plan whose critical path assumes an unverified
platform feature. Offer the fallback in the same breath: load in smaller
batches during a low-activity window, and sequence sharing configuration
per the LDV guide instead.
```

**Detection hint:** any plan that uses the deferral without a preceding
availability check, or that gives a timeline with no lead time for a Support case.

---

## Anti-Pattern 2: Ending the Runbook at "Resume Sharing Calculations"

**What the LLM generates:** a five-step runbook: defer → load → verify counts →
resume → done.

**Why it happens:** "Resume" reads as the natural inverse of "suspend," and in
most systems un-pausing a queue also drains it. Salesforce does not work that way.

**Correct pattern:**

```
Resuming stops suppressing FUTURE computations. It does not replay the
suppressed ones.

  "After this work is completed, you must resume sharing rule calculations
   and manually initiate a full sharing rule recalculation to prevent errors."

Required tail of every deferral runbook:

  resume group membership calculation
  resume sharing rule calculation
  Setup -> Sharing Settings -> [object] -> Sharing Rules -> Recalculate
  Setup -> Background Jobs -> wait until empty
  await the completion email
  run the access verification probe
  close the change record

Ordering matters: the Recalculate button is DISABLED while deferral is
active, so "recalculate then resume" is not executable.
```

**Detection hint:** search the generated runbook for the word "Recalculate" as a
distinct step after "resume." If it is absent, the plan leaves the org with stale
sharing.

---

## Anti-Pattern 3: Advising Users to "Wait a Few Minutes" for Access

**What the LLM generates:** "Sharing recalculation runs asynchronously; ask users
to wait a few minutes and refresh."

**Why it happens:** It is a safe-sounding non-answer that is true of many
asynchronous platform processes and is often correct for small orgs.

**Correct pattern:**

```
Never offer a duration you have not measured. Offer an instrument instead.

  Progress:      Setup -> Background Jobs
                 (subtypes: Account - Parent Access Grant,
                  Account - Extra Parent Access Removal,
                  Object - Access Cleanup)
  Apex portion:  Setup -> Apex Jobs
  Completion:    the email notification sent when recalculation finishes
                 for all affected objects
  Recent ops:    Setup -> View Setup Audit Trail
  Ground truth:  SELECT RecordId, HasReadAccess, HasEditAccess, MaxAccessLevel
                 FROM UserRecordAccess
                 WHERE UserId = :u AND RecordId IN :sample

The answer to "when will users see their records" is "when Background Jobs
is empty and the UserRecordAccess probe returns HasReadAccess = true for the
sample," not a number of minutes.
```

**Detection hint:** any time estimate in the output that is not tied to a measured
row count from the specific org. Also flag advice to "just refresh the page."

---

## Anti-Pattern 4: Scoping the Blast Radius to the Named Object

**What the LLM generates:** "This only affects Opportunity sharing, so the window
is short."

**Why it happens:** The user asked about one object, and object-scoped reasoning
is usually correct on the platform.

**Correct pattern:**

```
Two cascades break object-scoped reasoning:

1. The Account family. "If sharing rules are recalculated for accounts, cases,
   contacts, or opportunities, sharing rules are also recalculated for the other
   three objects." Touch one, size the window for four.

2. Role and group changes. Sharing rule recalculation fires automatically on:
     - adding/removing individual users from a group, role, or territory
     - changing which role a role reports to
     - changing which territory a territory is subordinate to
     - adding/removing a group from within another group
   A role reorg therefore recalculates every object that shares through the
   hierarchy, not just the one in the ticket.

3. Apex rides along. "When sharing is recalculated, Salesforce also runs all
   Apex sharing recalculations." Inventory registered Database.Batchable
   recalculation classes and add their runtime to the estimate.
```

**Detection hint:** a window estimate that names exactly one object, or that omits
Apex sharing recalculation classes from the inventory.

---

## Anti-Pattern 5: Believing Deferral Suppresses Application Triggers

**What the LLM generates:** "Defer sharing calculations before the load so that no
sharing work happens during the ingest."

**Why it happens:** The feature name generalises. "Sharing calculations" sounds
like it covers everything that writes to `__Share`.

**Correct pattern:**

```
Deferral covers exactly two platform processes:
  - group membership calculation
  - sharing rule calculation

It does not touch:
  - Apex triggers that insert __Share rows
  - Flows or Apex that change record ownership
  - Apex managed sharing recalculation classes you invoke yourself

For a bulk load, disable application triggers separately (see
templates/apex/TriggerControl.cls) and rebuild application shares afterwards
by invoking the object's recalculation batch explicitly. The LDV guide's own
advice: "Disable Apex triggers, workflow rules, and validations during loads;
investigate the use of batch Apex to process records after the load is
complete."
```

**Detection hint:** a load plan that defers sharing but says nothing about
application triggers, or that assumes `__Share` inserts stop during the deferral.

---

## Anti-Pattern 6: Deploying All Sharing Rules in One Change

**What the LLM generates:** "Deploy the sharing rules via Metadata API in a single
package for consistency."

**Why it happens:** Single-deploy is correct engineering advice for almost every
other metadata type, and atomicity is normally a virtue.

**Correct pattern:**

```
The LDV guide prescribes serialisation for sharing rules specifically:

  "Add sharing rules one at a time, letting computations for each rule finish
   before adding the next one."

and gives the full initial-load ordering:

  1. Load users into roles.
  2. Load record data with owners, triggering calculations in the role hierarchy.
  3. Configure public groups and queues, and let those computations propagate.
  4. Add sharing rules one at a time, letting computations for each rule finish.

For an initial load it also suggests "Use Public Read/Write security during
initial load to avoid sharing calculation overhead" - but note two constraints:
no __Share row can be inserted while OWD is Public Read/Write, and a custom
object's OWD cannot be changed from private to public at all if Apex code
references its sharing entries.
```

**Detection hint:** a deployment plan with more than one `SharingRules` member in
a single `package.xml` for a high-volume object, with no note about serialisation.

---

## Anti-Pattern 7: Reporting "Recalculation Complete" as Proof of Correct Access

**What the LLM generates:** "The Background Jobs queue is empty and the completion
email arrived, so sharing is correct — you can reopen the org."

**Why it happens:** Job completion is the only signal the platform pushes, so it
becomes the de facto success criterion.

**Correct pattern:**

```
Job completion means the platform finished the work it decided to do. It says
nothing about whether the work produced the intended access. Two documented
ways it can complete and still be wrong:

  - Criteria-based sharing rules that reference a field from a managed package
    with an expired license "aren't recalculated, and new records aren't shared
    based on those rules." Historical sharing is preserved, so the rule looks
    alive and only NEW records are missing.
  - Restriction rules subtract access after sharing grants it, and
    UserRecordAccess "doesn't consider whether a user's access is blocked by a
    restriction rule."

Gate on assertions, not on job status:
  for each persona: one record they must see, one they must not, both asserted.
```

**Detection hint:** a sign-off criterion that mentions only Background Jobs, the
completion email, or record counts — and no per-user, per-record access assertion.
