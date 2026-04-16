# Subflow pattern

Use a subflow when the same logic needs to run from:

- multiple parent flows,
- both a record-triggered and a screen-triggered context,
- Apex (via `Flow.Interview`) and a flow.

## Interface contract

Every subflow has exactly three parts of its "public API":

| Part | Declared in subflow | Seen by callers |
|---|---|---|
| Inputs | Variables with `Available for input = true` | Passed via `<inputAssignments>` |
| Outputs | Variables with `Available for output = true` | Read via `<outputAssignments>` |
| Side effects | DML + callouts + async dispatch | Invisible to caller — document them |

**Rule:** a subflow with `Available for input/output` not set on any variable
cannot be refactored later without renaming because every call site already
hardcodes positional state. Turn both flags on explicitly, always.

## Canonical subflow shape

```
Inputs (marked Available for input):
  - recordId (Text)
  - action   (Text: 'create' | 'update' | 'delete')

Outputs (marked Available for output):
  - success (Boolean)
  - errorMessage (Text)

Body:
  - [Decision: Route by action]
    ├── create → [Create Records] → Fault path → set success=false, errorMessage
    ├── update → [Update Records] → Fault path → set success=false, errorMessage
    └── delete → [Delete Records] → Fault path → set success=false, errorMessage
  - [Assignment: success = true] (on happy path)
  - End
```

## Calling the subflow

```xml
<subflows>
    <name>Call_Record_Writer</name>
    <flowName>Record_Writer_Subflow</flowName>
    <inputAssignments>
        <name>recordId</name>
        <value><elementReference>$Record.Id</elementReference></value>
    </inputAssignments>
    <inputAssignments>
        <name>action</name>
        <value><stringValue>update</stringValue></value>
    </inputAssignments>
    <outputAssignments>
        <assignToReference>writeSucceeded</assignToReference>
        <name>success</name>
    </outputAssignments>
</subflows>
```

## Versioning rules

- Never remove an input variable once published — callers break.
- Add new inputs as optional (with a default value) — callers don't have to change.
- Rename inputs only by adding a new name and keeping the old one for one release.
- Track the contract in a comment at the top of the `.flow-meta.xml`.
