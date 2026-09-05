# Well-Architected Notes — Apex Mocking And Stubs

## Relevant Pillars

### Reliability

Reliable Apex tests require realistic control over dependencies and failure paths. Good mocks and stubs improve behavioral confidence, not just deployment coverage.

Tag findings as Reliability when:
- failure scenarios are not mockable or untested
- production code hides missing seams with test-only branching
- tests depend on real external behavior accidentally

### Operational Excellence

Mocking infrastructure improves maintainability when it is focused and consistent across the team.

Tag findings as Operational Excellence when:
- mock classes are duplicated inconsistently
- fixture management is unclear
- there is no agreed pattern for collaborator seams

## Architectural Tradeoffs

- **Transport mock vs collaborator stub:** one validates HTTP behavior; the other validates orchestration around internal dependencies.
- **Inline mock classes vs reusable fixtures:** reuse helps until the mock framework becomes harder to understand than the tests.
- **Static resource fixtures vs inline JSON:** static resources keep tests cleaner for large payloads but require fixture maintenance discipline.

## Anti-Patterns

1. **`Test.isRunningTest()` as a seam substitute** — hides a structural problem.
2. **Only happy-path mocks** — undercuts confidence in failure handling.
3. **Mocking framework overbuild** — tests become harder to reason about than the production code.

## Official Sources Used

- Apex Developer Guide, "Build a Mocking Framework with the Stub API" (L42046–42097, L42099–42192) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf — supports the three-step stub workflow, the `MockProvider` shape reused in `references/code-examples.md` § 3, and the "non-virtual classes are stubbable" gotcha.
- Apex Developer Guide, "Apex Stub API Limitations" (L42199–42219) — supports the exact cannot-mock list (statics/`@future`, private methods, properties, triggers, inner classes, system types, `Batchable` implementors, private-constructor-only classes, iterators as parameter/return types) in `references/gotchas.md` and anti-pattern 3, plus the same-namespace rule for `Test.createStub()`.
- Apex Developer Guide, "Testing HTTP Callouts" and "Performing DML Operations and Mock Callouts" (L35384–35430, L35675–35681) — supports the "tests fail rather than skip a real callout" gotcha, the 6 MB code-size exclusion for `@IsTest` mock classes, the managed-package namespace rule for `Test.setMock`, and the `startTest` → `setMock` ordering in anti-pattern 7.
- Apex Reference Guide, `StubProvider` Interface and `handleMethodCall(...)` (L238439–238462, L238486–238509) — supports the fixed six-parameter signature and each parameter's type, which the checker's signature-drift rule enforces.
- Apex Reference Guide, `Test.createStub(parentType, stubProvider)` and `Test.setMock(interfaceType, instance)` (L240273–240300, L240947–240970) — supports the Decision Guidance table's split between transport mocks and seam stubs: `setMock` intercepts HTTP/WSDL transport only, `createStub` returns a stubbed object.
- Apex Developer Guide, "Using the runAs Method" and "Using Limits, startTest, and stopTest" (L41324–41333, L41428–41450) — supports the sharing-context gotcha (a method's sharing mode inside `runAs` is that of its defining class) and the "`startTest` adds a context, it does not refresh one" note behind the bulk test's limit assertions.
- Apex Developer Guide, "Versioned Behavior Changes" for sharing (L4960–4968) — supports the API 67.0 default-sharing reversal that changes how a stubbed selector behaves between class versions.
- Metadata API Developer Guide, `ApexClass` (L22212–22245) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf — supports the `apiVersion` / `status` fields in the `.cls-meta.xml` and `package.xml` blocks in `references/code-examples.md` § 6–7.
