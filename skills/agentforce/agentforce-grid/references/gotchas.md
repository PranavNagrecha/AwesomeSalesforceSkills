# Gotchas — Agentforce Grid

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Cost multiplies by rows × AI/action columns

**What happens:** a worksheet that felt cheap on a 5-row preview burns a surprising number of
Flex Credits when run against the full record set.

**When it occurs:** every AI column and action column is marked **Run For Each Row**, so the
metered work is `rows × (number of AI/action columns)`. A 4-column, 2,000-row worksheet runs
thousands of model/action invocations.

**How to avoid:** bound the data column with a filter and **Max Results**, review the Flex
Credit / Billing Calculator estimate for the *actual* row count before running, and drop AI
columns you don't need.

---

## Gotcha 2: Metered in every lifecycle phase, not just testing

**What happens:** a team assumes exploratory runs are free and iterates loosely, then sees
credit consumption they didn't budget for.

**When it occurs:** "Agentforce Grid usage is metered regardless of the AI lifecycle phase in
which it's used." Even "testing" runs draw compute — there is no free experimentation tier.

**How to avoid:** treat every run (test, build, or scale) as a spend. Preview a few rows to
validate the chain before running the full worksheet.

---

## Gotcha 3: Left-to-right references break silently when columns move

**What happens:** you insert or reorder a column and a downstream AI/action column stops
producing the value it used to.

**When it occurs:** columns process left to right and can only reference columns to their left.
Moving a referenced column to the right of the column that consumes it makes the reference
unresolvable.

**How to avoid:** keep data columns leftmost, then AI, then action; after any reorder, verify
every `@` reference still points to a column to its left. `scripts/check_agentforce_grid.py`
catches forward and unknown references.

---

## Gotcha 4: Action columns mutate live production data at scale

**What happens:** an Update Record run overwrites the wrong field on thousands of records, or
writes to more records than intended.

**When it occurs:** the action column maps AI output to a real Salesforce field and writes for
each row under the operating user's permissions. A wrong field mapping or an over-broad data
filter propagates the mistake across the whole row set.

**How to avoid:** double-check the object/field mapping, tighten the data-column filter, preview
the output, and confirm the running user's FLS actually permits the write before running.

---

## Gotcha 5: It's a no-code Studio tool, not a deployable artifact

**What happens:** someone tries to put a Grid worksheet in a change set, package, or `sf project
deploy`, and can't find a metadata type for it.

**When it occurs:** Grid worksheets are built and run inside Agentforce Studio; they are not a
Metadata API type like Flow or Apex. Treating a worksheet as source-controlled deployable
metadata leads nowhere.

**How to avoid:** for repeatable, deployable production automation use Flow or Apex. Use Grid
for bulk, interactive, human-in-the-loop data and AI operations — and capture the *design*
(column plan) as documentation, not as deployable metadata.

---

## Gotcha 6: Beta surface — behavior and limits can change

**What happens:** guidance or a saved worksheet assumes a limit or UI that shifts in a later
release.

**When it occurs:** Grid's setup is documented as **Beta** and it was introduced in Winter '26.
Beta features can change behavior, limits, and availability without the stability guarantees of
a GA feature.

**How to avoid:** don't hard-code assumptions about limits or claim GA; re-check the Beta
documentation before relying on a specific behavior in a production process.
