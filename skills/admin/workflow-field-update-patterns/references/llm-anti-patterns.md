# LLM Anti-Patterns — Workflow Field Update Patterns

Mistakes AI coding assistants commonly make when advising on
field-update automation.

---

## Anti-Pattern 1: Recommending after-save flow for same-record stamp

**What the LLM generates.** "Use a record-triggered after-save flow
to set the field on save."

**Why it happens.** "Record-triggered flow" is the modern primary
recommendation; the LLM doesn't differentiate before-save vs
after-save in its advice.

**Correct pattern.** For same-record stamps, **before-save** flow.
Free (no DML), no recursion possible. After-save is for
cross-object updates and post-save context (record Id on insert,
related-record join).

**Detection hint.** Any "stamp this same-record field on save"
recommendation that doesn't specify before-save is suspect.

---

## Anti-Pattern 2: Reaching for flow when a formula fits

**What the LLM generates.** Detailed flow design for a value that's
purely derivable from same-record fields.

**Why it happens.** "Use Salesforce flow" is the modern automation
default; the LLM doesn't pause to ask if no automation is the
right answer.

**Correct pattern.** Formula field is the right answer when the
value is a function of other same-record fields. No automation,
no recursion, no governor cost. Flow only when formula can't
express it.

**Detection hint.** Any flow recommendation for a "stamp X = f(Y, Z)
where Y, Z are same-record fields" use case is over-engineering.

---

## Anti-Pattern 3: Recommending Workflow Rule for new field-update automation

**What the LLM generates.** "Create a Workflow Rule with a Field
Update action."

**Why it happens.** Workflow Rules are heavily represented in older
training data. The deprecation (late 2022, no new field-update
actions) is recent.

**Correct pattern.** Record-triggered flow. Workflow Rule field
updates can no longer be created in any org. Existing rules still
run; new automation must be flow.

**Detection hint.** Any "create a Workflow Rule" recommendation
for new field-update automation is dated.

---

## Anti-Pattern 4: After-save flow update with no recursion guard

**What the LLM generates.** After-save flow on Account that updates
an Account field, with no `ISCHANGED` entry condition or decision
branch checking the value.

**Why it happens.** Default flow behavior; the LLM doesn't surface
the recursion risk.

**Correct pattern.** Either move to before-save (preferred), or add
explicit guard:
- `ISCHANGED(Field__c)` in entry condition.
- Decision branch: skip update if value already matches.

**Detection hint.** Any after-save flow doing same-object DML
without an `ISCHANGED` guard or decision-branch sentinel will
recurse.

---

## Anti-Pattern 5: Migrating WFR by deactivating the source first

**What the LLM generates.** "First, deactivate the existing
Workflow Rule. Then build the equivalent flow."

**Why it happens.** "Out with the old, in with the new" feels like
the right order.

**Correct pattern.** Activate the new flow FIRST, test, then
deactivate the WFR. The reverse order leaves a gap where neither
runs and the field is unstamped on records saved during the gap.

**Detection hint.** Any migration plan whose first step is
"deactivate the WFR" is going to produce a coverage gap.

---

## Anti-Pattern 6: Apex trigger when a flow would do

**What the LLM generates.** Apex `before update` trigger for a
same-record stamp.

**Why it happens.** Apex is the canonical "trigger" mental model.
The LLM doesn't surface that admin-editable flow is the modern
preferred path.

**Correct pattern.** Before-save flow for the standard cases. Apex
trigger only when:
- Logic requires Schema describe / dynamic types.
- Logic requires synchronous callout.
- Logic requires complex transactional rollback.
- Logic requires functions flow doesn't expose (cryptography, regex
  with backreferences in replacement).

**Detection hint.** Any "use an Apex trigger" recommendation for a
simple stamp is over-engineering.

---

## Anti-Pattern 7: ISCHANGED() on insert assumed to be false

**What the LLM generates.** Entry condition `ISCHANGED(Status) AND
ISPICKVAL(Status, 'Closed')` expecting it to fire only on the
update transition.

**Why it happens.** "Changed" reads as "transitioned". On insert,
the value goes from null to the new value, which Salesforce
classifies as a change.

**Correct pattern.** Use the trigger's "Run when" setting to
restrict to "A record is updated" only. Or add explicit `AND
PRIORVALUE(Status) != null` check.

**Detection hint.** Any flow with `ISCHANGED()` and a "Run when"
of "Created or Updated" is going to fire on insert too. Be
deliberate.

---

## Anti-Pattern 8: Recommending one flow per BU when one flow per object scales better

**What the LLM generates.** Per-BU record-triggered flows with
shared object scope.

**Why it happens.** "Each team owns their own automation" is a
team-organization pattern bleeding into platform design.

**Correct pattern.** One flow per object per save-time slot
(one before-save, one after-save). Internal decision branches per
BU's logic. The flow is shared infrastructure with documented
ownership for each branch.

**Detection hint.** Any "build per-BU flows" recommendation on a
shared object is going to produce non-deterministic ordering and
multi-team debugging headaches.
