# Well-Architected Notes — CRM Analytics Security Predicates

## Relevant Pillars

- **Security** — Predicates are the primary control for row-level
  access in CRM Analytics. The most common security failure is
  testing only with admins (who bypass predicates). Test matrix that
  includes a non-admin user who SHOULD have access AND a non-admin
  user who SHOULD NOT is the highest-yield security investment.
- **Reliability** — `$User.<CustomField>` resolving to null silently
  blocks visibility. Surface this in user provisioning so a new user
  doesn't open the dashboard and see "no data" with no clear cause.
- **Operational Excellence** — Single ownership of predicates (source
  control OR Setup, not both) prevents drift. Predicates edited in
  Setup that aren't reflected in source-controlled metadata become
  invisible to deployments.

## Architectural Tradeoffs

- **Single dataset with a per-user predicate vs separate datasets
  per audience.** Single dataset + predicate is simpler to operate;
  one dataset to refresh, one set of dashboards. Separate datasets
  per audience eliminates predicate cost and gives audience-specific
  schemas. Use single + predicate unless predicate cost or
  audience-specific transforms justify the duplication.
- **Predicate-only vs predicate + sharing rules.** Predicate-only
  protects only the CRM Analytics surface. Source-record sharing
  rules also apply on Salesforce Core. For full parity, both layers
  must encode the same access rules — which means dual maintenance.
  Some orgs accept the asymmetry (CRM Analytics shows what the
  predicate allows, regardless of Core sharing); others enforce
  parity by deriving the predicate from the sharing model.
- **`matches` regex vs precomputed enumerations.** `matches` is
  flexible but per-row expensive. Precomputing per-row access lists
  in the dataflow trades dataset size + dataflow time for query-time
  speed.
- **Custom User fields vs role-hierarchy traversal.** Custom User
  fields are simple to populate but require user provisioning
  discipline. Role-hierarchy traversal is automatic but requires
  dataflow support and careful column shape.

## Anti-Patterns

1. **Testing predicates only with admins.** Admins bypass; tests
   pass; non-admins discover the real behavior in production.
2. **Predicate at dashboard level instead of dataset level.**
   Dashboards aren't the right enforcement point. SAQL Studio or API
   access bypasses them entirely.
3. **Confusing predicates with sharing rules.** Predicates do not
   replace SObject-level sharing on source records; both can apply.
4. **Hardcoding service-account User Ids.** Brittle on account
   recreation; use `Manage Analytics` permission for bypass instead.
5. **`matches` against high-volume multi-value columns without
   profiling.** Per-row regex cost can dominate dashboard load.
6. **Test matrix missing the "no access" user.** Catches
   over-permissive predicates that grant access to users who
   shouldn't have it.

## Official Sources Used

- Analytics Security Implementation Guide — https://help.salesforce.com/s/articleView?id=sf.bi_security_implementation_guide.htm&type=5
- Add Row-Level Security with a Security Predicate — https://help.salesforce.com/s/articleView?id=sf.bi_security_datasets_predicate_considerations.htm&type=5
- Predicate Expression Syntax for Datasets — https://help.salesforce.com/s/articleView?id=sf.bi_security_datasets_predicate_syntax.htm&type=5
- Sample Predicate Expressions — https://help.salesforce.com/s/articleView?id=sf.bi_security_datasets_predicate_sampleexpressions.htm&type=5
- Values in a Predicate Expression — https://help.salesforce.com/s/articleView?id=sf.bi_security_datasets_predicate_values.htm&type=5
- CRM Analytics SAQL Reference — https://developer.salesforce.com/docs/atlas.en-us.bi_dev_guide_saql.meta/bi_dev_guide_saql/
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
