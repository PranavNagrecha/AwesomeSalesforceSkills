# LLM Anti-Patterns — Flow Data Tables

Scope: configuring the Data Table screen component and consuming what it outputs. Screen
flow structure generally belongs to `flow/screen-flows`; building a custom screen
component belongs to `flow/flow-screen-lwc-components`.

## Anti-Pattern 1: Reaching for a custom screen component by reflex

Asked for "a table in a screen flow where the user picks rows", assistants generate a
custom component bundle — controller, template, wire adapter, an `@api` output and a
`FlowAttributeChangeEvent` dispatch. That is roughly two hundred lines and a permanent
maintenance obligation for something the standard component does declaratively.

❌ Generate a bundle for display-and-select.
✅ Use the Data Table component. Write a custom one only when you need something it
genuinely does not do — inline editing, server-side paging over a large set, or a cell
renderer with custom markup. Those are real reasons; "a table" is not one.

## Anti-Pattern 2: Binding the table to an unfiltered Get Records

The generated flow gets every record of the object and hands the whole collection to the
table. It reads as complete, and it makes the screen's cost a function of how big the
object gets rather than of what the user is choosing between.

**Wrong** — no filter, no limit, the source grows without bound:

```xml
<recordLookups>
    <name>Get_All_Contacts</name>
    <object>Contact</object>
    <getFirstRecordOnly>false</getFirstRecordOnly>
    <storeOutputAutomatically>true</storeOutputAutomatically>
</recordLookups>
```

**Right** — filtered to the decision the user is actually making, and explicitly bounded:

```xml
<recordLookups>
    <name>Get_Account_Contacts</name>
    <object>Contact</object>
    <filterLogic>and</filterLogic>
    <filters>
        <field>AccountId</field>
        <operator>EqualTo</operator>
        <value><elementReference>recordId</elementReference></value>
    </filters>
    <filters>
        <field>IsActive__c</field>
        <operator>EqualTo</operator>
        <value><booleanValue>true</booleanValue></value>
    </filters>
    <sortField>LastName</sortField>
    <sortOrder>Asc</sortOrder>
    <getFirstRecordOnly>false</getFirstRecordOnly>
    <storeOutputAutomatically>true</storeOutputAutomatically>
</recordLookups>
```

There is no server-side paging in the component: the rows it shows are the rows the
collection holds. Bound the collection or the screen has no bound either.

## Anti-Pattern 3: Wiring the downstream path before choosing the selection mode

Single selection produces one record; multiple selection produces a record collection.
Assistants pick one, build the whole downstream path, and then switch the mode when the
requirement is clarified — at which point every reference breaks, including the ones on
fault paths that nobody re-tests.

❌ Build the Update Records element first and decide the selection mode later.
✅ Fix the selection mode before anything consumes the output. Single feeds an element
that takes a record; multiple feeds a Loop or a collection-aware element. These are
different flows, not a toggle.

## Anti-Pattern 4: No empty-state branch

The most common review finding on flows that use this component. Assistants produce Get
Records → Data Table → Next, and when the query matches nothing the user gets column
headers, no rows and no explanation. It looks like a broken screen rather than a
legitimate result.

❌ Route straight from Get Records into the screen.
✅ Decision immediately after Get Records testing whether the collection is empty, routing
to a message screen that names what was searched and offers the next step. Assume the
empty case will happen, because it is the case the flow was never demonstrated with.

## Anti-Pattern 5: Binding a lookup column to the lookup field

The column is bound to `AccountId` and renders an 18-character Id. Users report the table
as broken, and the fix gets applied to the column configuration when the defect is
actually upstream in the query.

❌ Select `AccountId` in Get Records and bind the column to it.
✅ Select the related field through the relationship — `Account.Name` — and bind the
column to that. The table can only render what the collection contains.

## Anti-Pattern 6: Leaving formatted column types to inference

Currency renders without its symbol, dates in an unexpected order, percentages as raw
decimals. Nothing errors, so it survives review and surfaces as a user complaint.

❌ Accept the inferred type for every column.
✅ Set the type explicitly for currency, date, date/time, percent and checkbox columns,
then check the screen as a user whose locale differs from your own. Your own session is
the one case guaranteed to look right.

## Anti-Pattern 7: Using the component for editing

Assistants suggest it whenever a grid appears in the requirement, including "let users
update the amounts". The component displays and selects; it does not save cell edits.

❌ Configure it as an editable grid and add an Update Records element expecting changed
values.
✅ Select in the table, then edit the selection on a following screen — or build a custom
screen component if genuine inline editing is a hard requirement. Selection and editing
are different interactions and conflating them produces a flow that appears to save and
does not.
