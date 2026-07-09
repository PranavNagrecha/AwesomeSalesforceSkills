# Well-Architected Notes — SOQL Object Limits and Restrictions

## Relevant Pillars

- **Reliability** — this is the primary pillar. A query that ignores a per-object rule does not
  degrade gracefully; it throws. An unfiltered `ContentDocumentLink`, an `Attachment` query past
  100,000 records, a big-object filter with a gap, or a `TopicAssignment` query with no `LIMIT`
  fails at runtime. Designing to the object's rule up front is what makes the query reliable at
  scale, not just in a small sandbox.
- **Performance** — several of these rules exist because the object cannot be scanned like a
  normal table. Big objects filter only on their index (so a compliant filter is also the *fast*
  filter), and external objects cap joins and subqueries because each hop is a remote OData call.
  Respecting the rule and shaping the query to the index or the join budget is the performant path.
- **Security** — the escape hatch for the Attachment cap and the feed `LIMIT` requirements is
  View All Data. Leaning on it to make a query pass bypasses sharing for the entire transaction.
  Keeping queries in user mode and scoping them to comply — rather than widening access — keeps
  the least-privilege posture intact.

## Architectural Tradeoffs

- **Scope the query vs. widen access.** The fastest way to make a limited query "work" is often
  View All Data or system mode. The durable, secure choice is to add the mandatory filter or
  `LIMIT` and keep the running user's real access. Prefer scoping every time; reserve elevated
  context for genuinely system-level jobs, and document why.
- **Legacy Attachment vs. modern ContentVersion.** For a large or growing file workload, working
  around the 100,000-record `Attachment` cap with ever-tighter filters is a treadmill. Migrating
  to `ContentVersion` / `ContentDocument` removes the cap-driven design constraint at the cost of
  a data migration — usually worth it for anything that will grow.
- **Big-object index design vs. query flexibility.** A big object's index dictates what you can
  filter on. Designing the index around the queries you need trades one-time modelling effort for
  every future query being both legal and fast; a poorly chosen index leaves whole access paths
  simply unavailable.

## Anti-Patterns

1. **Widening access to dodge a limit** — granting View All Data or switching to system mode so a
   capped or `LIMIT`-required query compiles. It bypasses sharing org-wide; scope the query instead.
2. **Treating restricted objects like normal sObjects** — filterless `ContentDocumentLink`
   queries, `LIKE`/`!=` on big objects, inline binds on `KnowledgeArticleVersion`, or `OFFSET`
   paging on `Attachment`. Each fails; encode the object's rule in a selector so it is written once.
3. **Blaming the generic governor limits** — diagnosing a per-object failure as the 50,000-row or
   100-query limit and "optimizing" the wrong thing, leaving the actual restriction unaddressed.

## Official Sources Used

- SOQL Object Limits and Restrictions (SOQL and SOSL Reference) — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_limits.htm
- Salesforce Platform Limits Cheat Sheet — SOSL and SOQL — https://developer.salesforce.com/docs/atlas.en-us.salesforce_app_limits_cheatsheet.meta/salesforce_app_limits_cheatsheet/salesforce_app_limits_platform_soslsoql.htm
- Apex Developer Guide — Execution Governors and Limits — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
