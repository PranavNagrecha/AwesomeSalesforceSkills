# LLM Anti-Patterns — Report Type Strategy

Common mistakes AI coding assistants make when designing CRTs.

---

## Anti-Pattern 1: Recommending a CRT when a standard exists

**What the LLM generates.** "Create a custom report type for
Opportunities and Products."

**Correct pattern.** Check Setup → Report Types first. The
"Opportunities with Products" standard report type ships with
the platform. CRTs are for shapes that do not exist as standards.

**Detection hint.** Any recommendation to create a CRT for the
named shape "<Standard Object> with <Standard Object>" should be
verified against the Standard Report Types list first.

---

## Anti-Pattern 2: Using "must have at least one" for "with or without"

**What the LLM generates.** A CRT design where the user wants
every Account (with or without Cases), but the join is set to
"each A record must have at least one related B record".

**Correct pattern.** "Each A record may or may not have related
B records" — this is the outer join. Inner-join CRTs silently
drop the rows the user expects to see.

**Detection hint.** Any CRT design where the requirement says
"every record" / "all records, with details when available" but
the join is "must have".

---

## Anti-Pattern 3: Modeling "without" as a CRT join

**What the LLM generates.** "Create a CRT for Accounts where the
join is 'must NOT have related Opportunities'."

**Correct pattern.** CRTs do not support negation joins. Use a
Cross Filter on a single CRT, or build a joined report.

**Detection hint.** Any CRT recommendation phrased "Accounts
without Opportunities", "Cases not having Tasks", etc.

---

## Anti-Pattern 4: Adding all object fields to the CRT layout

**What the LLM generates.** A CRT layout with every field on
every object, no grouping, no curation.

**Correct pattern.** Curate to the ~30-50 fields users actually
need, grouped into 3-5 sections by purpose. Past 60 fields the
report builder gates them behind search; users miss them.

**Detection hint.** Any CRT design that "exposes all fields" or
references the full object schema.

---

## Anti-Pattern 5: Recommending a joined report for shapes a single CRT can model

**What the LLM generates.** "Use a joined report to combine
Accounts and Contacts."

**Correct pattern.** That shape is the standard "Accounts with
Contacts" report type. Joined reports are the last resort for
shapes a single CRT (or a single CRT + Cross Filter) cannot
model.

**Detection hint.** Any joined-report recommendation for a join
that is a single primary-secondary relationship.

---

## Anti-Pattern 6: Promising 4+ levels of object joins

**What the LLM generates.** "The CRT will join Case → Account →
Contact → User → Profile."

**Correct pattern.** CRTs allow primary + secondary + tertiary
(via lookup), so 3 levels max. Going deeper requires denormalizing
fields up via formula or Flow, then reporting against the
flattened representation.

**Detection hint.** Any CRT design that names 4+ joined objects.

---

## Anti-Pattern 7: Recommending CRT changes that break existing reports

**What the LLM generates.** "Change the CRT join to 'must have at
least one' to filter the unwanted rows."

**Correct pattern.** Once saved, a CRT's join cannot be edited.
Filtering must happen in the report itself or in a Cross Filter.
Recommending a join change is recommending CRT recreation, which
breaks every report on the CRT.

**Detection hint.** Any "edit the CRT join semantics" suggestion
without acknowledging the recreation cost.
