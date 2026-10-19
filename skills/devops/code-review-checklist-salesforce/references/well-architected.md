# Well-Architected Notes — Code Review Checklist Salesforce

## Relevant Pillars

- **Security** — Code review is where implicit `without sharing`, missing FLS enforcement, and unsafe dynamic SOQL are caught before ship. Tying findings to explicit sharing and access patterns keeps reviews objective.
- **Performance** — Governor-efficient code reduces latency, queue backlog, and surprise production failures under real batch sizes.
- **Scalability** — Bulk-safe patterns are the difference between a feature that works for pilot data and one that survives enterprise row volumes.
- **Reliability** — Meaningful tests and clear error handling reduce escaped defects and shorten incident response.
- **Operational Excellence** — Repeatable checklists and PR artifacts make reviews teachable and auditable across teams and releases.

## Architectural Tradeoffs

Strict user-mode SOQL everywhere improves safety but can increase `QueryException` noise if UX does not surface field access errors — reviewers should confirm the UI handles those failures. Partial success DML improves throughput for integrations but complicates transactional semantics; the checklist should flag whether the business really needs per-row success. Thin triggers with indirection add files and indirection cost but simplify testing and governor reasoning versus monolithic trigger bodies.

## Anti-Patterns

1. **Coverage-driven tests** — High percentage with no assertions; replace with behavior-focused cases.
2. **“Works on my sample” bulk** — Only testing with small lists; require 200-row paths for trigger code.
3. **Undocumented system mode** — Elevated access without comment in code or PR; treat as blocking until rationale and scope are documented.

## Official Sources Used

Corpus: Summer '26 (API 67.0) PDFs; line numbers are `grep -n` positions in the `pdftotext -layout` text.

- Apex Developer Guide (`salesforce_apex_developer_guide.txt`) L11742–11753 — `WITH SECURITY_ENFORCED` unusable at 67.0+, user context by default at 67.0+, undeclared classes run `with sharing` at 67.0+, and the 66.0-and-earlier inheritance/caller rules (gotcha 4, SKILL.md "Version-gated defaults").
- Apex Developer Guide L4881–4885 and L4886–4905 — triggers can't have a sharing declaration and run without sharing; database operations in trigger bodies run in user mode unless system mode is specified (`AccountUpdateTrigger` example, API 67.0) (gotcha 5).
- Apex Developer Guide L4873–4875 — recommendation to always include an explicit sharing declaration on classes with database operations or SOQL (gotcha 4 avoidance).
- Apex Developer Guide L11964–11973 — `WITH USER_MODE` clause, `getInaccessibleFields()` on `QueryException`; L12095–12096 — `stripInaccessible` strips inaccessible fields (SKILL.md "CRUD, FLS, and sharing").
- Apex Developer Guide L19544 and L19554 — 100 sync / 200 async SOQL queries, 150 DML statements per transaction; L19573 — `System.enqueueJob` 50 sync / 1 async; L15972 — default chained-queueable stack depth of five in Developer and Trial Edition (gotcha 3).
- Apex Developer Guide L14906–14908 and L15851–15884 — Bulk API triggers fire on chunks of 200 with limits reset between invocations; trigger and bulk request best practices (gotcha 6, example 1).
- Apex Developer Guide L15502 — order of multiple triggers on the same object and event isn't guaranteed (SKILL.md "Architectural compliance").
- Apex Developer Guide L6615–6617 — Java naming standards recommendation (SKILL.md "Naming and structure").
- Apex Developer Guide L728 and L733 — 75% coverage requirement and the advice not to focus on the percentage (SKILL.md "Tests as contract").
- Apex Developer Guide L9061–9062 — `allOrNone=false` requires iterating results (gotcha 1).
- Apex Reference Guide (`salesforce_apex_reference_guide.txt`) L240541–240544 — `Test.getStandardPricebookId()` works without `SeeAllData=true`; L241071 — code between `startTest` and `stopTest` gets a new set of governor limits (anti-pattern 4, examples).
- Metadata API Developer Guide (`api_meta.txt`) L22218–22221 — Apex class updates are blocked by active jobs unless cancelled or the Deployment Settings option is enabled (gotcha 7); L22231 and L22243 — `ClassName.cls-meta.xml` and its `apiVersion` field (SKILL.md XML fence).
- Salesforce Well-Architected Overview — quality framing for what “done” means beyond syntax: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
