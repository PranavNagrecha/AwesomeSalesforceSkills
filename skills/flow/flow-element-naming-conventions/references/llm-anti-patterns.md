## LLM Anti-Patterns — Flow Element Naming Conventions

Common mistakes AI coding assistants make when generating or advising on Flow
element / variable / outcome naming. The consuming agent should self-check
its own output against this list before returning the Flow XML or rename plan.

---

## Anti-Pattern 1: Generating cryptic numeric names like `Decision_1`, `Get_Records_2`

**What the LLM generates:**

```xml
<decisions>
  <name>Decision_1</name>
  <label>Decision 1</label>
</decisions>
<recordLookups>
  <name>Get_Records_2</name>
  <label>Get Records 2</label>
</recordLookups>
```

**Why it happens:** Flow Builder defaults element API Names to
`<Type>_<n>` and the model treats the Salesforce default as canonical
when generating XML from scratch. Training data also includes many
real-world flows that shipped with these auto-names.

**Correct pattern:**

```xml
<decisions>
  <name>Decision_HasActiveContract</name>
  <label>Has active contract?</label>
</decisions>
<recordLookups>
  <name>Get_OpenCasesByOwner</name>
  <label>Get open cases owned by current user</label>
</recordLookups>
```

**Detection hint:** regex `<name>(Decision|Get_Records|Update|Create|Loop|Assignment|Screen|Action)_\d+</name>`
in the Flow XML, or any element API Name ending in `_<digits>`.

---

## Anti-Pattern 2: Using camelCase or spaces in API Names that auto-convert

**What the LLM generates:**

```xml
<variables>
  <name>get open cases</name>
</variables>
<variables>
  <name>getOpenCases</name>
</variables>
```

**Why it happens:** the model conflates Label (human text, allows spaces)
with API Name (technical identifier, alphanumeric + underscore only).
JavaScript / TypeScript training-data bleed pushes camelCase as the default
identifier shape.

**Correct pattern:**

```xml
<variables>
  <name>collOpenCases</name>     <!-- type-prefixed, no spaces -->
</variables>
```

PascalCase or snake_case is fine for elements (`Get_OpenCasesByOwner`);
camelCase with a type prefix is the convention for variables
(`varAccountId`, `collOpenCases`). Never spaces, never hyphens, never
special characters.

**Detection hint:** any `<name>` value containing a space, a hyphen, or
ending with an underscore-numeric collision suffix (`_1`, `_2` after
auto-replacement).

---

## Anti-Pattern 3: Generating bare `Yes` / `No` Decision outcomes with a blank Default

**What the LLM generates:**

```xml
<decisions>
  <name>Decision_HasContract</name>
  <rules>
    <name>Yes</name>
    <conditions>...</conditions>
  </rules>
  <rules>
    <name>No</name>
    <conditions>...</conditions>
  </rules>
  <defaultConnectorLabel></defaultConnectorLabel>   <!-- BLANK -->
</decisions>
```

**Why it happens:** the model mirrors how decisions are described in
natural language ("if yes, do A; if no, do B") and forgets that Flow
outcomes show up in fault diagnostics and metadata diffs detached from
their parent Decision.

**Correct pattern:**

```xml
<decisions>
  <name>Decision_HasActiveContract</name>
  <rules>
    <name>HasActiveContract</name>
    <conditions>...</conditions>
  </rules>
  <defaultConnectorLabel>NoActiveContract_Default</defaultConnectorLabel>
</decisions>
```

Affirmative business condition for the matched outcome; explicit name for
the default outcome.

**Detection hint:** any `<rules><name>(Yes|No|Match\d*|Outcome\d+)</name>`
inside `<decisions>`, or any `<defaultConnectorLabel></defaultConnectorLabel>`
that is empty.

---

## Anti-Pattern 4: Generating two elements with the same Label causing fault-email confusion

**What the LLM generates:**

```xml
<recordUpdates>
  <name>Update_Account</name>
  <label>Update Account</label>     <!-- same label -->
</recordUpdates>
<recordUpdates>
  <name>Update_Account_2</name>
  <label>Update Account</label>     <!-- duplicate label -->
</recordUpdates>
```

**Why it happens:** the model generates element-by-element without checking
that earlier siblings already exist with the same Label. Flow Builder
allows duplicate Labels (only API Names must be unique).

**Correct pattern:**

```xml
<recordUpdates>
  <name>Update_AccountTier</name>
  <label>Update Account tier based on revenue</label>
</recordUpdates>
<recordUpdates>
  <name>Update_AccountOwner</name>
  <label>Reassign Account owner to regional director</label>
</recordUpdates>
```

Distinct API Names AND distinct Labels — the qualifier in the API Name
should map to a clarifying phrase in the Label.

**Detection hint:** group elements by `<label>` and flag any group with
size > 1.

---

## Anti-Pattern 5: Suggesting renames of Subflow input/output variables without warning about parent-flow impact

**What the LLM generates (in advice mode):**

> "Sure, you can rename `inputAccountId` to `inputAcctId` for brevity.
> Just edit the variable in the subflow and save."

**Why it happens:** the model treats variable rename as a local refactor
and does not model the cross-flow contract surface. Salesforce does not
provide a "find references" warning for cross-flow variable references, so
the model has no platform feedback to learn from.

**Correct pattern:**

> "Renaming `inputAccountId` on an active Subflow is a breaking contract
> change. Salesforce will allow the rename to save with no warning, but
> every parent flow calling this Subflow will fail at the next interview
> with `The flow couldn't find a referenced variable inputAccountId.`
> Recommended approach:
> 1. Bump the Flow version per `flow-versioning-strategy`.
> 2. In the new version, add `inputAcctId` alongside `inputAccountId`.
> 3. Update every parent flow's Subflow element to pass `inputAcctId`.
> 4. Activate the new version. Retire the old version after all parents
>    are migrated."

**Detection hint:** any LLM output containing the phrase "rename ... input"
or "rename ... output" in the context of a Subflow without a corresponding
"version bump" / "parent flow update" warning.

---

## Anti-Pattern 6: Skipping resource type prefixes (`var`, `coll`, `map`, `formula`)

**What the LLM generates:**

```xml
<variables>
  <name>accountId</name>
  <dataType>String</dataType>
</variables>
<variables>
  <name>cases</name>
  <dataType>SObject</dataType>
  <isCollection>true</isCollection>
</variables>
```

**Why it happens:** model uses generic programming-language conventions
where the type is inferable from declaration context. In Flow formulas and
Assignment elements, the type is NOT visible at the call site —
`{!cases}` could be a single record or a collection, and the formula
author has to flip back to the variable list to check.

**Correct pattern:**

```xml
<variables>
  <name>varAccountId</name>
  <dataType>String</dataType>
</variables>
<variables>
  <name>collOpenCases</name>
  <dataType>SObject</dataType>
  <isCollection>true</isCollection>
</variables>
```

**Detection hint:** any `<variables><name>` whose value does not start
with one of `var`, `coll`, `map`, `formula`, `choice`, `constant`, `stage`,
`screen`, `decisionOutcome`, `input`, `output`.
