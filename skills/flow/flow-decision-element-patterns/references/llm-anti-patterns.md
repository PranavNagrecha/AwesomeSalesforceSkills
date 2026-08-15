# LLM Anti-Patterns — Decision Element

Mistakes AI assistants reliably make when writing Flow decision logic.

---

## Anti-Pattern 1: Treating a Multi-Select Picklist as a Set

**What the LLM generates:** `Product_Interests__c EqualTo 'Platform'`, or a
condition using an `INCLUDES` / `EXCLUDES` operator borrowed from formula syntax.

**Why it happens:** multi-select picklists *are* sets conceptually, and
`INCLUDES` is genuinely the right operator in a validation-rule formula. The
model transfers formula vocabulary into Decision operators, which are a different
list.

**Correct pattern:** a multi-select picklist is one semicolon-delimited string to
Flow's condition operators — `red; blue; green` is a single value. `EqualTo`
matches only the whole string in that exact order. Use `Contains`, and know it is
a case-insensitive substring test that will also match a value which is a
substring of another. Where API values share a prefix, split the string into a
collection instead.

**Detection hint:** an `INCLUDES` or `EXCLUDES` operator in flow `<conditions>`,
or `EqualTo` against a single value on a multi-select field.

---

## Anti-Pattern 2: Case-Sensitive Reasoning About Text Comparisons

**What the LLM generates:** advice to normalise casing before comparison, or a
condition that relies on case to distinguish two values.

**Why it happens:** string comparison is case-sensitive in almost every language
the model knows, so normalising is a reflex.

**Correct pattern:** Decision, Wait, and Collection Filter comparisons are
case-insensitive for Text, Picklist, and Multi-Select Picklist values. Normalising
is wasted work, and distinguishing values by case does not work. The genuine trap
runs the other way: comparisons containing Salesforce Id values *are*
case-sensitive.

**Detection hint:** an `UPPER()` or `LOWER()` formula introduced solely to make a
Decision comparison work.

---

## Anti-Pattern 3: Leaving Null in the Default

**What the LLM generates:** `Field = 'Target'` as the only outcome, with null
expected to fall to the default and that being described as correct.

**Why it happens:** SQL's three-valued logic produces the same runtime behaviour,
so the model's mental model agrees with the outcome — it just does not surface
that two different populations are now sharing one branch.

**Correct pattern:** decide explicitly what null means and give it its own
outcome using `IsNull` with a `booleanValue` of `true`. Note the shape: the
operator takes a boolean right-hand value, not an empty string, so a generated
`EqualTo ''` is a different and usually wrong test.

**Detection hint:** an `EqualTo` against `''` in flow condition metadata, or a
decision design with no null branch on a nullable field.

---

## Anti-Pattern 4: Ordering Outcomes by Likelihood

**What the LLM generates:** the broadest condition first, justified as "covers
most records, so it short-circuits sooner."

**Why it happens:** a genuine optimisation instinct from languages where
condition order is a performance lever and all branches are mutually exclusive.

**Correct pattern:** outcomes evaluate top-down and first match wins, so a
superset listed first makes everything it subsumes unreachable. Most specific
first, widest last. Flow Builder does not warn about overlap.

**Detection hint:** an outcome whose conditions are a strict subset of an earlier
outcome's.

---

## Anti-Pattern 5: Comparing `$Record` to `$Record__Prior` by Hand

**What the LLM generates:** a two-condition outcome comparing
`$Record.StageName` to `$Record__Prior.StageName` with `NotEqualTo`, to express
"did it change."

**Why it happens:** it is the obvious construction from first principles, and the
prior-record resource is well known.

**Correct pattern:** operators exist specifically for evaluating `$Record` in a
record-triggered flow — including a changed test — and they handle the insert
case where there is no prior record. Across Decision, Wait, and Collection Filter
elements they are available **only in Decision elements**. They are *also*
available in Start-element entry conditions, on update-triggered flows only and
only under the "every time a record is updated" trigger option — so do not tell a
reader `Is Changed` cannot be used in entry criteria.

**Detection hint:** `$Record__Prior` in a `<conditions>` block that is expressing
a change test.

---

## Anti-Pattern 6: Mixed AND/OR Without Parentheses

**What the LLM generates:** `conditionLogic` of `1 AND 2 OR 3`, presented as
meaning `1 AND (2 OR 3)`.

**Why it happens:** the model applies C-family precedence, where AND binds tighter
than OR, and produces a string that reads correctly to a human skimming it.

**Correct pattern:** `conditionLogic` supports parentheses — write `1 AND (2 OR
3)`. Do this even if you are confident about precedence: the parentheses cost
nothing and remove a class of review error entirely. An expression with more than
about four terms should be extracted to a named Formula resource anyway.

**Detection hint:** a `<conditionLogic>` string containing both AND and OR and no
parentheses.

---

## Anti-Pattern 7: Picklist Labels Instead of API Values

**What the LLM generates:** `Status EqualTo 'In Progress'` where the API value is
`in_progress`.

**Why it happens:** the label is what appears in every screenshot, record page,
and requirements document the model has seen.

**Correct pattern:** comparisons use the stored API value. Labels are
translatable; API values are not, so a label comparison works in an English-only
org and fails for a translated user. Take the value from Setup → Object Manager →
the field's value set.

**Detection hint:** a picklist comparison value containing spaces or title case
where the org's API values are lower-snake.

---

## Anti-Pattern 8: A Hardcoded User Id or Last Name as the Rule

**What the LLM generates:** `CreatedById Equals 005...` or `Owner.LastName Equals
"Patel"` as a routing condition, often because the model was shown existing
metadata that does this.

**Why it happens:** copying working configuration looks like the safe move, and
an Id in metadata reads as a legitimate reference.

**Correct pattern:** it is configuration stored as a person. Deactivation, a name
change, and a sandbox refresh each break it with no error — the flow runs, that
outcome never fires, and records fall silently to the default. Route on a Custom
Permission, a Queue, a Public Group, or a Custom Metadata row holding the Id. And
note the Id case-sensitivity: unlike other text comparisons, Id comparisons are
case-sensitive, so a hand-copied 15-character Id can fail to match its
18-character form.

**Detection hint:** `<stringValue>005` inside a `<conditions>` block, or a
name-field equality used as access control.

---

## Anti-Pattern 9: Nested Decisions Mirroring the Requirement Narrative

**What the LLM generates:** three or four chained Decision elements
transcribing "if A, then if B, then if C" from the business description.

**Why it happens:** it is a faithful translation of the prompt, and each
individual step is defensible.

**Correct pattern:** the resulting tree has a default outcome at every level, and
the combinations that fall through them are exactly the ones nobody considered.
Flatten to one Decision with explicit outcomes covering the real combinations,
ordered most specific first. Cap nesting at two, and extract a subflow when
flattening produces more outcomes than fit comfortably.

**Detection hint:** a Decision whose outcome connector targets another Decision,
more than twice in a chain.

---

## Anti-Pattern 10: Encoding a Routing Table as Branches

**What the LLM generates:** one outcome per region, tier, or product family —
identical in shape, differing only in a literal — and a matching set of
downstream actions.

**Why it happens:** the requirement lists the values, so the model enumerates
them. It produces a flow that is obviously correct and expensive to own.

**Correct pattern:** outcomes that differ only in a literal are *data*, not logic.
Put the mapping in Custom Metadata, Get Records the matching row, and let the
Decision test whether a row was found. Adding a region becomes a data change with
no flow edit, no test, and no deploy.

**Detection hint:** three or more outcomes with structurally identical conditions
differing only in the `<stringValue>`.
