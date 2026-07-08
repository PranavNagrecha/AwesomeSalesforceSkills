# SOQL Object Limits and Restrictions — Work Template

Use this template when a SOQL query fails or must be shaped around a specific object's own
limit — not the generic governor limits.

## Scope

**Skill:** `soql-object-limits-and-restrictions`

**Request summary:** (fill in the query / failure the user reported)

## Context Gathered

- Target object (from the `FROM` clause): (e.g. `ContentDocumentLink`, `Attachment`, a `__b` big object)
- Restriction shape: hard row cap | mandatory filter | required LIMIT | restricted filter surface
- Running user holds View All Data? (yes / no / unknown)
- Runs in user mode or system mode?
- Expected result volume (does it approach a cap?):

## Per-Object Restriction Reference

Match the target object to its rule (source: SOQL and SOSL Reference — SOQL Object Limits and
Restrictions). These sit *on top of* the generic governor limits.

| Object / situation | Restriction |
|---|---|
| `Attachment` | Fails past **100,000** records; scope with WHERE + LIMIT, or use View All Data (avoid) |
| `ContentDocumentLink` | Must filter on one of `Id`, `ContentDocumentId`, `LinkedEntityId` |
| `ContentHubItem` | Must filter on one of `Id`, `ExternalId`, `ContentHubRepositoryId` |
| `Vote` | Must filter on `ParentId` (single ID), `Parent.Type` (single type), or `Id` (single/list) |
| `UserRecordAccess` | Max **200** rows; `ORDER BY HasAccess` required when `HasAccess` is selected |
| `TopicAssignment` | `LIMIT` **1,100** or fewer unless View All Data |
| `NewsFeed` / `UserProfileFeed` | `LIMIT` **1,000** or fewer unless View All Data |
| Big objects (`__b`) | Filter only on index fields, in order, no gaps; `=` on all but last field; last field `=,<,>,<=,>=,IN`; no `!=`,`LIKE`,`NOT IN`,`EXCLUDES`,`INCLUDES` |
| External objects | Up to **4** joins; subqueries fetch up to **1,000** rows; no `AVG/COUNT(field)/HAVING/GROUP BY/MAX/MIN/SUM` |
| `KnowledgeArticleVersion` | No inline Apex bind variables — use dynamic SOQL |
| `RecentlyViewed` | Retained **90 days**, truncated to ~200 records per object — not a history table |

> Maturity note: these are standard, unversioned platform reference limits. The docs do not
> stamp them GA/Beta and the exact numbers can change — re-check the reference for edge cases.

## Approach

- Which pattern from SKILL.md applies (mandatory filter / bounded Attachment / big-object index)?
- The fix (add filter / add LIMIT / batch to stay under cap / reshape to index):
- Confirm you are **not** relying on View All Data or system mode just to make the query pass:

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] Mandatory-filter objects filter on an allowed field
- [ ] `Attachment` bounded (WHERE + LIMIT) or migrated to `ContentVersion`
- [ ] Required `LIMIT` present on feed / topic objects
- [ ] `UserRecordAccess` within 200 rows with `ORDER BY HasAccess`
- [ ] Big-object filter uses only index fields, in order
- [ ] External-object query within join/subquery caps
- [ ] `KnowledgeArticleVersion` uses dynamic SOQL
- [ ] No per-object failure resolved by widening access

## Validation

Run the skill checker against your metadata tree:

```bash
python3 scripts/check_soql_object_limits_and_restrictions.py --manifest-dir force-app/main/default
# enable big-object operator checks:
python3 scripts/check_soql_object_limits_and_restrictions.py --manifest-dir force-app --big-objects Interaction__b
```

## Notes

(Record which restriction applied, the fix chosen, and why View All Data was not used.)
