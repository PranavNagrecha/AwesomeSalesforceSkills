# Gotchas — Workflow Field Update Patterns

Non-obvious behaviors of Salesforce field-update automation.

---

## Gotcha 1: Before-save flows are governor-free for same-record updates

**What happens.** Many admin teams reflexively build same-record
stamps as after-save flows because that's how they learned. Each
stamp counts as a second DML, eats governor budget, and risks
recursion.

**When it occurs.** Default automation pattern across most orgs.

**How to avoid.** Use **before-save** flow for same-record stamps.
Modifies the in-flight record in place; no DML; no recursion. The
single highest-leverage admin-side performance improvement.

---

## Gotcha 2: After-save flow updating same record recurses without a guard

**What happens.** After-save flow on Account that updates an Account
field re-fires the Account trigger / flow on its own update. With no
guard, infinite loop until the platform's recursion detection cuts
it at 16 levels.

**When it occurs.** Default behavior; explicit guard required.

**How to avoid.**
- `ISCHANGED(Field__c)` in the entry condition — flow only fires
  if the field-being-updated changed.
- Decision branch: skip Update Records if the value already matches
  what we'd write.
- Migrate to before-save flow if same-record stamp doesn't need
  post-save context.

---

## Gotcha 3: Workflow Rule field updates are deprecated for new actions

**What happens.** Admin tries to add a new Field Update action to
an existing Workflow Rule. Setup blocks it: "Workflow Rule field
updates can no longer be created. Migrate to Flow."

**When it occurs.** Modernizing legacy automation; orgs created
before late-2022 still have the existing rules running.

**How to avoid.** Use the Migrate to Flow tool. Existing rules
continue to run; new automation must be flow.

---

## Gotcha 4: Formula fields are computed at read time, not stored

**What happens.** Admin builds a formula field; reports filter on
it; query performance is slower than expected. The formula
evaluates per row at query time.

**When it occurs.** High-volume objects with complex formulas in
filter / sort positions.

**How to avoid.** For very high-volume read paths, stamp the value
via before-save flow into a stored field. Formula for low-volume,
stamped for performance-critical paths. Trade is automation cost
vs query cost.

---

## Gotcha 5: Order of execution interleaves before-save flows with before-update triggers

**What happens.** Admin builds a before-save flow that depends on
a value stamped by a before-update trigger. The trigger fires AFTER
the flow on some saves and BEFORE on others. Behavior is
non-deterministic.

**When it occurs.** Mixing before-save flow with before-update
trigger on the same object.

**How to avoid.** Pick one tool for the same-record before-save
slot. Salesforce's documented order-of-execution explicitly does
not guarantee relative ordering between before-save flows and
before-update triggers.

---

## Gotcha 6: Cross-object update from a flow fires the target object's automation

**What happens.** Flow on Case updates the parent Account's
counter. Account's own automation fires (rollup recompute, audit
field, downstream notification). Side effects multiply across the
chain.

**When it occurs.** Cross-object updates on objects with rich
automation.

**How to avoid.** Document the chain. Each automation level adds
governor pressure; bulk operations against a Case object can
cascade through Account / Contact / Opportunity automation. Plan
the chain in design, not in production triage.

---

## Gotcha 7: Multiple flows on the same object fire in non-deterministic order

**What happens.** Admin team A builds a record-triggered flow on
Account. Team B builds another. Both fire on every save. Their
relative ordering is not guaranteed; one team's flow sometimes
sees the other team's results, sometimes doesn't.

**When it occurs.** Multi-team admin orgs with fragmented flow
ownership.

**How to avoid.** Consolidate into one flow per object per
save-time slot (one before-save, one after-save). Internal
decision branches handle per-team logic. Documented ownership;
predictable order.

---

## Gotcha 8: ISCHANGED() returns true on insert (the value "changed" from null)

**What happens.** Entry condition `ISCHANGED(Field__c) AND
ISPICKVAL(Field__c, 'Closed')` fires on insert of a record with
`Field__c = 'Closed'`, not just on the close transition. Admin
expected close-transition-only behavior.

**When it occurs.** Status-transition flows that should fire only
on update, not on insert.

**How to avoid.** Add `AND PRIORVALUE(Field__c) != null` or
explicit "Run when: A record is updated" trigger setting (not
"created or updated"). Be deliberate about insert-vs-update
behavior.

---

## Gotcha 9: Migrate-to-Flow tool produces drafts; doesn't auto-deactivate the source

**What happens.** Admin uses Migrate to Flow on a Workflow Rule.
Tool creates a draft flow. Admin activates the flow but doesn't
deactivate the WFR. Both fire on every save. Field gets stamped
twice — usually idempotent but sometimes not (if the value depends
on order or accumulates).

**When it occurs.** Migration runs that miss the deactivation step.

**How to avoid.** Migration sequence: activate flow → test in
sandbox → deactivate WFR → test again → deploy both as one change
set. Deactivation is the last step, gated on flow validation.
