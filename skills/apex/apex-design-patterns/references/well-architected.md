# Well-Architected Notes — Apex Design Patterns

## Relevant Pillars

### Scalability

Good layering prevents each new requirement from increasing coupling exponentially. Query centralization and reusable service boundaries make the codebase safer to expand.

Tag findings as Scalability when:
- the same logic is duplicated across many entry points
- query sprawl makes tuning and limit management harder
- one class becomes a central bottleneck for every change

### Reliability

Patterns improve reliability when business rules live in one place and dependencies are easier to isolate in tests.

Tag findings as Reliability when:
- duplicated rules can drift between trigger, Flow, and API paths
- tests cannot isolate integrations or collaborators
- entry points directly mutate data with no service boundary

### Operational Excellence

Operational Excellence improves when the structure is easy to review, easy to onboard into, and predictable under change.

Tag findings as Operational Excellence when:
- class responsibilities are ambiguous
- layer names are present but not meaningful
- refactors require touching too many unrelated classes

## Architectural Tradeoffs

- **More layers vs lower ceremony:** layering helps as codebases grow, but tiny features can be over-abstracted.
- **Centralized selectors vs tailored queries:** reuse is good until selector methods become bloated.
- **Interface seams vs simplicity:** inject dependencies when they create genuine test or substitution value.

## Anti-Patterns

1. **God service class** — orchestration, queries, validations, and integrations in one place.
2. **Pattern-by-name only** — class names imply design without actually enforcing boundaries.
3. **Test-only branching instead of DI** — `Test.isRunningTest()` hiding a missing seam.
4. **One savepoint per DML** — savepoint bookkeeping consuming the DML statement budget and invalidating later savepoints.
5. **A dynamically-named class with no fallback** — a Custom Metadata row that outlives the Apex class it names.
6. **Undeclared sharing on inner classes** — the same source meaning different things at different API versions.

## Official Sources Used

- Apex Developer Guide, "Using the `with sharing`, `without sharing`, and `inherited sharing` Keywords" (L4803–4968) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf — supports the per-layer sharing choice in `SKILL.md` Core Concepts, the entry-point rule and async override in `references/gotchas.md` § "`inherited sharing` Behaves Differently...", the inner-class rule behind anti-pattern 9, and the API 67.0 default-sharing change (L4961–4968).
- Apex Developer Guide, "Static and Instance Methods, Variables, and Initialization Code" (L3730–3800, L3851–3862) — supports the "Singleton Means Static, For One Transaction" concept, the Bulk API chunking gotcha (L3789–3791), and the static-initialisation-order gotcha (L3733–3734, L3858–3860).
- Apex Developer Guide, "Generating Savepoints and Rolling Back Transactions" and its Versioned Behavior Changes (L8679–8700, L8773–8788) — supports the unit-of-work pattern in `references/code-examples.md` § 4, the DML-statement cost (L8691), "statics aren't reverted during a rollback" (L8692–8693), the cross-trigger savepoint error (L8689–8690), the rollback-deletes-your-log gotcha (L8682–8684), and the API 60.0 test-savepoint release (L8783–8784).
- Apex Developer Guide, "Access Modifiers" / "Extending a Class" Versioned Behavior Changes (L3359–3364, L4039–4060, L4568–4578) — supports the API 65.0 `abstract`/`override` access-modifier rule enforced by the checker and stated in the Questions table, plus "methods and classes are final by default".
- Apex Reference Guide, `Type` class — `forName(fullyQualifiedName)`, `forName(namespace, name)`, `newInstance()` (L241915–241990, L242049–242132, L242296–242327) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf — supports the strategy factory in `references/code-examples.md` § 6, the public/global-only restriction, the managed-package null return, and the no-argument-constructor constraint.
- Apex Reference Guide, Custom Metadata Type Methods — `getAll()` (L204532–204585) — supports the 255-character truncation gotcha and the decision to store only a class name in `Case_Escalation_Strategy__mdt`.
- Apex Developer Guide, "Execution Governors and Limits" (L19530–19620) — supports the 100 SOQL / 150 DML per-transaction figures used in the savepoint and bulk gotchas, the 16-deep recursive-trigger stack limit, and the "custom metadata records can have unlimited SOQL queries" note (L19614–19615).
- Metadata API Developer Guide, `ApexClass` (L22212–22285) and `CustomMetadata` (L41451–41560) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf — supports the `.cls-meta.xml` `apiVersion`/`status` fields, the `Inactive`-is-trigger-only note, and the `.md` record file shape and `xsi:type` values in `references/code-examples.md` § 7 and § 9.
- Object Reference for Salesforce, `Case.IsEscalated` and `Task.Subject` (L62470–62477, L278321–278326) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf — supports the escalation field being API-writable and the 255-character `Task.Subject` limit the rollback test deliberately exceeds.
- Salesforce Well-Architected Overview — scalability, reliability, and operational excellence framing for the pillar tags above.
