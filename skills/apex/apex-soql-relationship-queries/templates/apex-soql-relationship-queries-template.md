# SOQL Relationship Query — Work Template

Fill this in before writing the query. Every row maps to a question in
`SKILL.md` § *Questions to Ask Before Configuring*.

**Skill:** `apex-soql-relationship-queries`

## 1. Scope

| Field | Answer |
|---|---|
| Request summary | |
| Parent object | |
| Child object(s) | |
| Direction needed | child-to-parent / parent-to-child / both |
| Consuming class + layer | |

## 2. Relationship name resolution

Fill from Setup > Object Manager > Fields & Relationships, or from
`DescribeSObjectResult.getChildRelationships()` → `ChildRelationship.getRelationshipName()`.
The object API name is never the answer.

| Direction | Field | Relationship name to use | Source checked |
|---|---|---|---|
| child → parent | e.g. `Contact.AccountId` | e.g. `Account` | Object Reference / describe |
| parent → child | e.g. `Account` ← `Contact.AccountId` | e.g. `Contacts` | describe |
| polymorphic? | e.g. `Task.WhatId` | e.g. `What` | `isNamePointing()` = true/false |

## 3. Constraints from the answers

| Question | Answer | Consequence for the query |
|---|---|---|
| Children per busy parent | | `LIMIT` on the subquery? nested `for` instead of assignment? |
| Execution context | sync / Batch `start()` / Bulk API / ETL | subquery allowed at all? |
| Class `apiVersion` (from `-meta.xml`) | | `WITH USER_MODE`; never `WITH SECURITY_ENFORCED` at 67.0+ |
| Can a parent have zero children? | yes / no | guard + a test case for it |
| Parent fields projected, or only filtered? | | SELECT list width |

## 4. Shape chosen

Record which row of `SKILL.md` § *Decision Guidance* applies, and why the
alternatives were rejected.

- **Chosen:**
- **Rejected, and why:**

## 5. Query

```soql

```

## 6. Checklist

Copy from `SKILL.md` § *Review Checklist* and tick as you go.

- [ ] Relationship names verified against describe or Setup, not guessed
- [ ] Child access matches the query's type (typed vs `getSObjects`)
- [ ] Child collection guarded before iteration; zero-children case covered by a test
- [ ] No child set assigned or `.size()`-ed inside a SOQL for loop
- [ ] Batch `start()` locator carries no subquery
- [ ] Security clause matches the class `apiVersion`
- [ ] `python3 scripts/check_apex_soql_relationship_queries.py --manifest-dir <src>` exits 0

## 7. Notes

Record any deviation from the patterns in `references/code-examples.md` and the
reason, plus anything the checker flagged and you consciously accepted.
