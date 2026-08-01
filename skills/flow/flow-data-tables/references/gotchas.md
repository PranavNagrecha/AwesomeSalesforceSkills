# Gotchas — Flow Data Tables

Every item below is specific to the Data Table screen component's configuration and its
output contract. General screen-flow design belongs to the flow screen skills; this file
is about the component itself.

## Gotcha 1: Selection mode changes the output type, not just the interaction

**What happens:** downstream elements that referenced the table's output stop resolving,
and Flow Builder reports the reference as invalid — often several elements away from the
screen you actually edited.

**When it occurs:** switching between single-row and multi-row selection after the
downstream path has already been built. Single selection yields one record; multiple
selection yields a record collection. A Create Records element bound to a single record
cannot consume a collection, and a Loop cannot iterate a single record.

**How to avoid:** decide the selection mode before wiring anything downstream. If it has
to change, expect to rework every element that reads the output — and check the fault
paths too, which are the ones people forget to re-point.

---

## Gotcha 2: A lookup column renders the Id unless the source collection carries the name

**What happens:** the column shows an 18-character Id rather than the referenced record's
name, and users report the screen as broken.

**When it occurs:** the Get Records element that built the source collection selected the
lookup field itself (for example `AccountId`) but not the related record's name through
the relationship (`Account.Name`). The table can only render what the collection contains,
and the Id is what it was given.

**How to avoid:** include the relationship field in the source query, and bind the column
to that field rather than to the raw lookup. Verify with real data rather than a
single-record test — a collection assembled by hand in a debug run often has the related
fields populated when a live query does not.

---

## Gotcha 3: Column type is inferred, and the inference is not always what you want

**What happens:** currency renders without a symbol or grouping, dates render in an
unexpected format, and percentages appear as raw decimals. Nothing errors.

**When it occurs:** relying on the inferred type instead of setting it. Inference works
from the field's type, which is right for text and wrong often enough for the formatted
types to be worth checking every time.

**How to avoid:** set the type explicitly on every currency, date, date/time, percent and
checkbox column. Then verify with a user whose locale differs from yours, because
formatting is locale-sensitive and your own session is the one case guaranteed to look
correct.

---

## Gotcha 4: An empty source collection renders an empty table, not a message

**What happens:** the user reaches a screen with column headers, no rows and a Next
button, and has no idea whether the search failed or genuinely matched nothing.

**When it occurs:** whenever the Get Records element returns no records. The component
does not branch for you.

**How to avoid:** put a Decision immediately after Get Records, testing whether the
collection is null or empty, and route to a message screen that says what happened and
offers a way forward. This is the single most common review finding on flows that use this
component.

---

## Gotcha 5: The whole collection is materialised into one screen payload

**What happens:** the screen takes progressively longer to render as the underlying data
set grows, and the degradation is gradual enough that nobody attributes it to the table.

**When it occurs:** binding the table to a Get Records element with no filter or limit.
There is no server-side paging in the component — the rows it displays are the rows the
collection holds, all delivered in the request that renders the screen.

**How to avoid:** treat the source collection as something you bound deliberately, not
something you inherit. Filter to what the user actually needs to choose between, and add
an explicit record limit on the Get Records element. If the selection genuinely requires
searching a large set, the requirement is search-then-select rather than list-then-select,
and the flow should collect search criteria on an earlier screen. Note that a flow shares
the standard per-transaction limit of 50,000 records retrieved by SOQL queries, so an
unbounded Get Records has a hard ceiling that fails as an error rather than as slowness.

---

## Gotcha 6: Column labels are configured per column and do not follow field translations

**What happens:** the table's headers stay in the org's default language for users running
in another language, while the rest of the screen translates correctly.

**When it occurs:** typing a literal label into the column configuration instead of
leaving it to derive from the field, or hard-coding a label because the derived one was
too long.

**How to avoid:** prefer the derived label so the field's own translation applies. Where a
custom label is genuinely needed, source it from a translatable resource rather than a
literal, and add the table's headers to the translation checklist for the flow.
