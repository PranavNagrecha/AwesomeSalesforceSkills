# LLM Anti-Patterns — Picklist Data Integrity

Mistakes AI coding assistants commonly make when advising on
picklist hygiene.

---

## Anti-Pattern 1: "Just deactivate the value" without migration

**What the LLM generates.** "To remove the obsolete status,
deactivate the value in Setup."

**Why it happens.** Deactivation is the visible action; the LLM
doesn't surface that records still hold the value.

**Correct pattern.** Migrate records BEFORE deactivating. Pattern C
in SKILL.md.

**Detection hint.** Any "deactivate the value" recommendation that
doesn't include "migrate existing records first" leaves orphaned
data.

---

## Anti-Pattern 2: Validation rule duplicating restricted-picklist enforcement

**What the LLM generates.** Restricted picklist with values [A, B,
C] PLUS a validation rule that checks `ISPICKVAL(field, "A") ||
ISPICKVAL(field, "B") || ISPICKVAL(field, "C")`.

**Why it happens.** "Use a validation rule to enforce the picklist"
is a defaulting pattern from non-Salesforce mental models.

**Correct pattern.** Restricted picklist alone enforces value
membership. Validation rules are for cross-field constraints
("Status = Closed requires Closed_Date populated") that a picklist
can't express.

**Detection hint.** Validation rules that just recapitulate the
picklist's own value list are redundant.

---

## Anti-Pattern 3: Treating label rename as equivalent to API name rename

**What the LLM generates.** "Rename the picklist value from `Tech`
to `Technology`. Apex will continue to work because we're using the
API name." (When in fact the user wanted to rename only the label.)

**Why it happens.** "Rename" is ambiguous; the LLM picks one
interpretation without surfacing the distinction.

**Correct pattern.** Always disambiguate label rename (cosmetic, no
Apex impact) from API name rename (treated as a value migration —
old value retired, new value added, records migrated).

**Detection hint.** Any picklist-rename recommendation that doesn't
clarify "label or API name" is missing the central decision.

---

## Anti-Pattern 4: Picklist for everything

**What the LLM generates.** Defaulting to picklist for any
classification field, including ones that should be lookups or
custom metadata.

**Why it happens.** Picklist is the simplest classification
mechanism in Setup; the LLM picks the simplest answer.

**Correct pattern.** Picklist for small, admin-managed, stable
lists with no attributes. Lookup for relational data with
attributes (vendors, departments, products). Custom metadata for
admin-managed configuration that Apex consumes.

**Detection hint.** Any "use a picklist" recommendation for a list
that has additional attributes (a description, a code, an active
flag, a relationship) is suboptimal — that data wants a lookup or
custom metadata.

---

## Anti-Pattern 5: Recommending Unrestricted with no reconciliation

**What the LLM generates.** "Make the picklist Unrestricted so the
integration can write any value the source system has."

**Why it happens.** Integration flexibility is the user's stated
need; the LLM doesn't surface phantom-value risk.

**Correct pattern.** Unrestricted is acceptable WITH a periodic
reconciliation report (find records whose value isn't in the
current picklist) and a process to either add the missing values
or migrate the records. Without that, phantom values accumulate
silently.

**Detection hint.** Any Unrestricted-picklist recommendation that
doesn't mention reconciliation or value-list synchronization is
incomplete.

---

## Anti-Pattern 6: Deactivating dependent-picklist controller without migrating dependents

**What the LLM generates.** "Deactivate the obsolete Country value
in your country/state dependent picklist."

**Why it happens.** Dependent picklist's coupling isn't salient;
the LLM treats the controller deactivation as a single-value action.

**Correct pattern.** Pattern D in SKILL.md — migrate records'
controller AND dependent values atomically before deactivating the
controller. Records left with a deactivated controller have
unreachable dependent values.

**Detection hint.** Any "deactivate this picklist value"
recommendation on a controlling field that doesn't address
dependent records is going to orphan data.

---

## Anti-Pattern 7: Single-stakeholder Global Value Set rename

**What the LLM generates.** "Rename `Tech` to `Technology` in the
Industry Codes Global Value Set."

**Why it happens.** Looks like a single-field rename; the LLM
doesn't surface that Global Value Set ripples.

**Correct pattern.** Coordinate across every team consuming the
Global Value Set. Document affected fields. Rollout in a planned
window. Or use local picklists when one BU's evolution shouldn't
ripple to another's.

**Detection hint.** Any Global Value Set change advice that doesn't
include "notify consumers" / "coordinate with affected teams" is
missing the ripple impact.
