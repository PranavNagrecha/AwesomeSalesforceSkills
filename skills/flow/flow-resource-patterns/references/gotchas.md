# Gotchas — Flow Resource Patterns

Resource-selection mistakes that pass `Run with Debug` but fail
under real usage. These compound the rules in `SKILL.md` and the
`llm-anti-patterns.md` set — they're the second-order issues that
only surface after the first wave of "looks-correct" patterns ship.

## Gotcha 1: Constants are static at design-time and cannot reference $Record or other resources

**What happens:** A practitioner tries to define a Constant whose
value is `{!$Record.OwnerId}` or `{!recAccount.Name}` and is
surprised when Flow Builder rejects the value with an error like
"Enter a literal value." Constants accept ONLY hardcoded literal
values — a number, a string, a boolean, a date, a `$Label` reference
in some cases, but never a reference to `$Record`, another flow
variable, or any merge field that resolves at runtime. They are
resolved when the flow is *activated*, not when it runs.

**When it occurs:** Practitioners migrating from Apex (where `static
final` constants can reference any compile-time expression) or from
LWC (where `const` can hold any expression result) reach for
Constants in Flow expecting the same flexibility. The first time
they need a "constant" that depends on the triggering record's
context — e.g., "the default Region for the Account's parent's
country" — they discover Constants don't work that way.

**How to avoid:** Use the right resource for the lifecycle:
- *Truly static* (e.g., a fixed record-type Id, a status string, a
  threshold number) → Constant.
- *Computed from $Record or other variables at run-time* → Formula.
- *Computed once at flow start and reused* → Variable populated by
  the first Assignment (or by a Formula referenced once and cached).

A common workaround for "constant per environment" (e.g., a
sandbox-vs-prod toggle) is Custom Metadata — see
`admin/custom-metadata-types`. Constants are NOT the right home for
environment-aware values.

---

## Gotcha 2: Formula resources re-evaluate on every reference and are NEVER cached

**What happens:** A practitioner writes a Formula resource with a
nested IF, three CASE branches, and a REGEX. They reference it from
six elements inside a Loop body. The Loop iterates 200 times. The
Formula evaluates 1,200 times — once per reference per iteration.
The flow runs fine on a 1-record debug test (6 evaluations) and
horrifically on a 200-record batch (1,200 evaluations). Apex CPU
time can spike enough to hit the 10,000-ms governor on
record-triggered flows.

**When it occurs:** Any Formula resource referenced more than once
inside a Loop, or any Decision element with a condition row that
references multiple Formula resources. The platform makes no
caching guarantee — Formula is a re-evaluation primitive, not a
memoization primitive. Flow Builder gives no warning about this
during save, and the debug log shows the formula's *result* but not
its *evaluation count*.

**How to avoid:** Inside a Loop where a non-trivial Formula is
referenced 2+ times, cache it. The canonical cache pattern:

```
Loop: loop_OnContacts
  Collection: {!col_Contacts}
  Variable: currentContact

  [Top of loop body]
  Assignment: assign_CacheFormula
    v_isVIPCached = {!f_isVIP}   ← evaluate the Formula once

  Decision: Decide_PathA
    Condition: {!v_isVIPCached} = TRUE   ← read the cached variable

  Decision: Decide_PathB
    Condition: {!v_isVIPCached} = TRUE
```

This collapses N references to 1 evaluation per iteration. For
trivial formulas (single field reference, single arithmetic) the
caching overhead isn't worth it — the cost is in the *body* of the
formula, not the reference mechanism. The skill at
`flow/flow-formula-and-expression-patterns` covers the cost-benefit
threshold in detail.

---

## Gotcha 3: "Available for Input/Output" toggle silently changes a flow's public contract

**What happens:** A Variable defined inside an Auto-launched flow
is initially scoped as "private to this flow" (neither Input nor
Output checked). The flow is invoked from a Process or another flow
with a single Input — `recordId`. Later, the practitioner enables
"Available for Output" on a second Variable (`output_NewRecordId`)
so a parent flow can read it. They save the flow. The next time the
parent flow runs, *if it was already constructed with no output
mapping*, nothing breaks — but the new output variable now appears
as an unmapped output in the parent's subflow element, easy to
silently leave on its default null.

The reverse is worse: unchecking "Available for Input/Output" on a
Variable already mapped from a parent flow leaves the parent's
mapping in place but the value now lands in a private variable that
nothing reads. Flow Builder shows the mapping in the parent as
green/valid because the variable still exists, just no longer
externally visible. The parent's reference falls through to null on
the subflow's side.

**When it occurs:** Two contexts trip this:
1. **Screen Flows surfaced via Lightning App Builder / Quick Action
   / Flow Action.** The "Input" toggle controls what attributes the
   page/action exposes to admins for configuration. Toggling it on
   exposes the variable in the App Builder; toggling it off removes
   the attribute from any page/action that already references it,
   which can break the surface silently.
2. **Subflows.** Both "Input" and "Output" must be checked for the
   variable to participate in the subflow call's input/output
   mapping. Renaming or unchecking after the parent is built breaks
   the contract.

**How to avoid:** Treat the "Available for Input/Output" toggle as
a published contract. Once checked and referenced externally,
changes to the variable name, data type, or toggle state must be
coordinated with every consumer. The
`flow/flow-element-naming-conventions` skill recommends a naming
prefix (e.g., `input_` / `output_`) so the contract surface is
obvious at a glance and accidental toggling is caught in code
review. For auto-launched subflows specifically, document the
expected inputs and outputs in the Flow Description field and
treat any change to that contract as a breaking change.

---

## Gotcha 4: Collection Choice Set selections need a stored value variable to survive screen navigation

**What happens:** A Screen has a Multi-Select Picklist (or Checkbox
Group) component whose Choice is a Collection Choice Set fed by an
in-memory collection. The user picks two contacts on Screen 1,
clicks Next, lands on Screen 2, then clicks Previous to return to
Screen 1. Their selections are gone — the picklist resets to
nothing. Or they continue forward, the flow reaches a later element
that needs the selections, and the variable is empty.

**When it occurs:** Whenever a Choice or Choice Set is configured
on a screen component without an associated "stored value" variable
(also called the "default value" / "store output values" slot,
depending on the component). The Collection Choice Set itself just
*describes* what choices to render — it does NOT itself hold the
selection. The selection only persists if the screen component
writes it back into a Variable (for single-select) or Collection
Variable (for multi-select).

**How to avoid:** For every Screen component bound to a choice
resource, explicitly bind a flow Variable to its `value` /
`defaultValue` attribute (the name varies by component). For
multi-select pickers and Checkbox Groups, that variable must be a
Text Collection. For single-select Pickers and Radio Group, a
single Text variable. The same variable should also be referenced
in subsequent screens / Decisions / DML — and it must be marked
"Available for Input" if you want navigation back-and-forth to
remember the selection (otherwise the screen component re-initializes
on each render).

A telltale symptom of this bug: "the user complains the form
'forgot' their answer when they hit Previous." Verify by
inspecting the screen component's value-binding configuration in
Flow Builder; if the slot is empty, the selection is being thrown
away on every render.

---

## Gotcha 5: Picklist Choice Sets cache field metadata — adding picklist values requires flow reactivation

**What happens:** An admin adds three new picklist values to
`Opportunity.StageName`. A Screen Flow that uses a Picklist Choice
Set on `StageName` continues to show only the OLD set of values.
Users select from a stale list, never seeing "Closed-Lost-Competitive"
or whichever new values were added. The bug is hard to spot because
the field's own picklist editor and any record page show the new
values correctly — only the Flow's screen is stale.

**When it occurs:** Picklist Choice Sets in Flow are evaluated using
the metadata snapshot taken when the flow was last *activated*.
Changing the source picklist's values (adding, deactivating,
reordering, renaming labels) does NOT propagate to active flows
that reference the field as a Picklist Choice Set. The same applies
when the picklist is upgraded from a local picklist to a Global
Value Set, or when a record type's picklist value subset is changed.

This behavior is intentional — it prevents picklist changes from
silently breaking running flows — but it's surprising the first time
you hit it. Record Choice Sets do NOT have this problem (they
re-query the source object on each flow run), and Choice resources
hardcoded into the flow definition obviously don't either.

**How to avoid:** When changing picklist values on a field
referenced by a Picklist Choice Set in any active flow, **deactivate
the flow, save a new version, and reactivate**. The reactivation
forces Flow to take a fresh snapshot of the field's picklist
metadata. The Flow's "Version" panel will show a new active version
incorporating the latest picklist values.

Operational consequence: maintain an inventory of which flows
reference which picklist fields. The fastest source-of-truth is to
search the Flow XML / metadata for `<picklistObject>` and
`<picklistField>` elements in `dynamicChoiceSets` blocks — those
identify the Picklist Choice Set bindings. A small Apex or CLI
script can list every flow referencing a given object+field, which
becomes the "must reactivate" set when changing values. The skill
at `admin/picklist-data-integrity` covers the picklist-change
governance flow that this dependency feeds into.
