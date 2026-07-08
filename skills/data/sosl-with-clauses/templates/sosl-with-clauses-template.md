# SOSL WITH Clauses — Query Builder Worksheet

Use this worksheet to assemble a SOSL `FIND` query with the right WITH clauses, in the fixed
canonical order, with the object/field/API-version rules checked. Delete the clauses you don't
need — but keep the ones you keep in this order.

## 1. Scope

**Skill:** `sosl-with-clauses`

**Request summary:** (what should the search return, and how should it look?)

**Issuing context + API version:** (Apex class / LWC / REST call, and its `apiVersion`)

## 2. Decide which clauses you need

| Clause | Need it? | Target object(s) supported? | API floor met? |
|---|---|---|---|
| `WITH DivisionFilter` (Divisions orgs) | ☐ | orgs using Divisions | — |
| `WITH DATA CATEGORY` (Knowledge/Question) | ☐ | `KnowledgeArticleVersion` / `__kav`, `Question` | 18.0 |
| `WITH SNIPPET (target_length=n)` | ☐ | Case, CaseComment, FeedItem, FeedComment, Idea, IdeaComment, KnowledgeArticleVersion | 32.0 |
| `WITH NETWORK` (Experience Cloud) | ☐ | `User` and feeds only | — |
| `WITH PricebookId` | ☐ | `Product2` only | — |
| `WITH METADATA` | ☐ | response envelope | — |
| `WITH HIGHLIGHT` | ☐ | auto number, email, text, text area, long text area | 39.0 (40.0 custom) |
| `WITH SPELL_CORRECTION = true\|false` | ☐ | supported searches | 40.0 |

## 3. Ordered clause skeleton

Fill in and delete unused lines. The order below is the required canonical order.

```sql
FIND {SEARCH_TERM}                      -- no wildcard (*/?) if you need SNIPPET/HIGHLIGHT
  IN ALL FIELDS                          -- or NAME/EMAIL/PHONE/SIDEBAR FIELDS
  RETURNING OBJECT_API_NAME (
    FIELD_LIST
    WHERE PublishStatus = 'online'       -- REQUIRED when using WITH DATA CATEGORY
    -- ORDER BY ... LIMIT n OFFSET m      -- per-object sort/paging lives inside RETURNING
  )
  WITH DivisionFilter                    -- 1. division name or ID
  WITH DATA CATEGORY GROUP__c AT VALUE__c -- 2. AT | ABOVE | BELOW | ABOVE_OR_BELOW; join specs with AND only
  WITH SNIPPET (target_length=200)       -- 3. 50-1,000 chars (default 300); no snippet on wildcards
  WITH NETWORK = 'NETWORK_ID'            -- 4. or IN ('id1','id2'); '000...0' for internal
  WITH PricebookId                       -- 5. Product2 only
  WITH METADATA = 'LABELS'               -- 6. omit to return no metadata
  WITH HIGHLIGHT                          -- 7. <mark> markup; max 25 records/entity; no highlight on wildcards
  WITH SPELL_CORRECTION = false          -- 8. default true; set false for exact match
  LIMIT 20                                -- snippets only render at <=20 results per page
```

## 4. Pre-flight checklist

- [ ] Kept WITH clauses in the canonical order above; `LIMIT`/`UPDATE` after them
- [ ] Each clause's target objects actually support it
- [ ] API version meets every clause's floor
- [ ] `SNIPPET target_length` within 50–1,000
- [ ] `HIGHLIGHT` only on auto number / email / text / text area / long text area fields
- [ ] `DATA CATEGORY`: `RETURNING` + `WHERE PublishStatus` present; specs joined with `AND` only
- [ ] `NETWORK`: no scoped + unscoped mix; only `User`/feeds relied on for scoping
- [ ] No wildcard term paired with a `SNIPPET`/`HIGHLIGHT` expectation

## 5. Lint it

```bash
python3 ../scripts/check_sosl_with_clauses.py --query "PASTE_YOUR_QUERY_HERE"
```

## 6. Notes

(Record any object that silently dropped a clause, or any API-version bump you made.)
