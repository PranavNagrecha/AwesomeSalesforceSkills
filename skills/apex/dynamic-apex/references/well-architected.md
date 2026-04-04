# Well-Architected Notes — Dynamic Apex

## Relevant Pillars

### Security

Dynamic SOQL and dynamic field access are high-risk surfaces because they shift validation responsibility from the compiler to the developer. The platform cannot enforce type safety, query correctness, or permission boundaries when the query is a runtime string. Security is the most critical pillar for this skill:

- SOQL injection is the apex analog of SQL injection and is exclusively a developer responsibility.
- Field-level security is not automatically enforced on dynamic queries or on `record.get()` / `record.put()` calls. User-facing code must explicitly check `DescribeFieldResult.isAccessible()` and `isUpdateable()`.
- Object API names and field names sourced from external input or admin configuration must be allowlisted through Schema describe before use. `String.escapeSingleQuotes()` alone is not a sufficient defense for unquoted identifiers.

### Scalability

Describe calls are transactional resources. Governor limits cap describe operations at 100 per synchronous transaction. In batch, trigger, or multi-object utilities that touch many sObjects or many fields, naive implementations hit this limit and throw `LimitException`. Schema describe results do not change within a transaction — caching them in static maps is free and should always be done.

Dynamic SOQL also bypasses compile-time query binding, meaning selective filter analysis must be validated at design time rather than relying on the optimizer to do it. Poor filter selectivity in dynamic queries produces the same large-scan behavior as in static SOQL but is harder to detect in code review.

## Architectural Tradeoffs

### Flexibility vs. Compile-Time Safety

Dynamic SOQL enables admin-configurable field lists, generic utilities, and multi-object processors that would be impossible with static SOQL. The tradeoff is that every guarantee the compiler provides for static SOQL — field existence, type checking, query validity — must be replicated manually at runtime. Teams that choose dynamic patterns must compensate with thorough describe-based validation and comprehensive tests that cover schema-change scenarios.

### Graceful Degradation vs. Fail-Fast

`WITH SECURITY_ENFORCED` fails the entire query if any field is inaccessible. Pre-filtering with `isAccessible()` degrades gracefully by omitting inaccessible fields. The right choice depends on the context: a system utility that should never run without full access should fail fast; a user-facing component that should show what the user can see should degrade gracefully. This decision must be explicit and documented.

## Anti-Patterns

1. **Describe calls inside iteration loops** — calling `getGlobalDescribe()` or `getDescribe()` per record in a list multiplies describe-call cost by the record count. In any scenario with more than a handful of records this approaches or exceeds the 100-call limit. Cache describe results at the class level and access them inside loops.

2. **Trusting configuration or user input as a field name without Schema validation** — an admin-entered field name from custom metadata or a UI parameter that is concatenated into a query without validating it against `fields.getMap()` will throw a `QueryException` if the field does not exist (e.g., after a rename or deletion). All field names from external sources must be validated against the live schema before query construction.

3. **Skipping FLS enforcement under the assumption that sharing handles it** — `with sharing` enforces row visibility but says nothing about field-level security. A query run with sharing that includes fields the user cannot read will succeed without complaint unless explicit FLS checks are added. Dynamic queries in user-facing code must always filter or check field accessibility before including fields.

## Official Sources Used

- Apex Developer Guide — Dynamic SOQL, Schema namespace, Describe methods, SOQL injection guidance
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm

- Apex Reference Guide — Schema.DescribeSObjectResult, Schema.DescribeFieldResult, Database.query, String.escapeSingleQuotes
  https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_ref_guide.htm

- Secure Apex Classes — FLS enforcement patterns, dynamic field access security model
  https://developer.salesforce.com/docs/platform/lwc/guide/apex-security

- Salesforce Well-Architected Overview — Security and Scalability pillar framing
  https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
