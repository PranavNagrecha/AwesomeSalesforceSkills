# AMPscript Development — Work Template

Use this template when designing, writing, or reviewing AMPscript for a Marketing Cloud content area.

## Scope

**Skill:** `ampscript-development`

**Request summary:** (fill in what the user asked for — e.g., "personalize email body with top 3 product recommendations from ProductRecs_DE")

**Channel:** [ ] Email body  [ ] Subject line  [ ] Preheader  [ ] SMS  [ ] Push  [ ] Cloud Page

---

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md before writing any code.

| Question | Answer |
|---|---|
| Channel and content area | |
| Data Extension name(s) | |
| Primary key field(s) of each DE | |
| Lookup field (PK or non-PK?) | |
| Expected row count per subscriber | |
| Subscriber identifier field in sendable DE | |
| Fallback content when no data matches | |

---

## Data Flow

Describe the data retrieval path for this personalization:

```
Sendable DE / All Subscribers
  └── _subscriberkey
        └── Lookup("DE_Name", "ReturnField", "MatchField", _subscriberkey)
              └── Output: @variable → rendered inline with %%=v(@variable)=%%
```

Fill in the actual DE names, field names, and variable names for this use case.

---

## AMPscript Block

```
%%[
/* --- Variable declarations --- */
SET @subKey = _subscriberkey

/* --- Data retrieval --- */
/* Single value: */
SET @fieldValue = Lookup("DE_Name", "ReturnField", "MatchField", @subKey)

/* Multi-row: */
/* SET @rows = LookupOrderedRows("DE_Name", 5, "SortField", "DESC", "MatchField", @subKey) */
/* SET @rowCount = RowCount(@rows) */

/* --- Conditional logic --- */
IF @fieldValue == "Value1" THEN
  SET @output = "Content for Value1"
ELSEIF @fieldValue == "Value2" THEN
  SET @output = "Content for Value2"
ELSE
  SET @output = "Default fallback content"
ENDIF
]%%
```

Replace placeholders with real DE names, field names, and business logic.

---

## FOR Loop Block (if multi-row rendering required)

```
%%[ IF @rowCount > 0 THEN ]%%
<ul>
%%[ FOR @i = 1 TO @rowCount DO ]%%
  %%[ SET @row = Row(@rows, @i) ]%%
  <li>%%=Field(@row, "FieldName1")=%% — %%=Field(@row, "FieldName2")=%%</li>
%%[ NEXT @i ]%%
</ul>
%%[ ELSE ]%%
<p>No records found. [Fallback message]</p>
%%[ ENDIF ]%%
```

---

## Subject Line / Preheader (inline only)

```
Your %%=AttributeValue("FieldName")=%% — [static subject text]
```

Note: NO block syntax (%%[ ... ]%%) allowed in subject or preheader fields.

---

## Checklist

Copy from SKILL.md review checklist and tick items as you complete them:

- [ ] All variables declared with SET before first use
- [ ] LookupRows() results guarded with IF RowCount(@rows) > 0 before FOR loop
- [ ] FOR loop uses Row(@rows, @i) and Field(@row, "FieldName") — not array notation
- [ ] Subject line and preheader use only inline %%=...=%% syntax
- [ ] Lookup field is the DE primary key or has a documented performance note if non-PK
- [ ] All string literals use straight ASCII quotes — no smart/curly quotes
- [ ] Fallback ELSE content is present and renders correctly when no data matches
- [ ] Tested with a real subscriber via preview or test send — not generic preview only

---

## Decision: AMPscript vs SSJS

| Requirement | AMPscript | SSJS |
|---|---|---|
| Single DE field lookup | Preferred | Overkill |
| Multi-row iteration | Preferred | Overkill |
| HTTP REST/SOAP API call | Not available | Required |
| Complex string manipulation | Built-in functions usually sufficient | Use if AMPscript functions don't cover |
| SMS / Push channel | Supported | Not supported |

**Decision for this use case:** (record which language was chosen and why)

---

## Notes

Record any deviations from the standard AMPscript pattern and the reason:

- Deviation 1:
- Deviation 2:

---

## Test Evidence

| Test Subscriber | Tier / Segment | Expected Output | Actual Output | Pass? |
|---|---|---|---|---|
| subscriber_key_1 | [e.g., Gold] | [e.g., GOLD20 code] | | |
| subscriber_key_2 | [e.g., no match] | [e.g., fallback content] | | |
| subscriber_key_3 | [e.g., 3 orders] | [e.g., 3-item list] | | |
