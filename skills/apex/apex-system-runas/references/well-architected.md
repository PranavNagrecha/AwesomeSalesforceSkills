# Well-Architected Notes — Apex System Runas

## Relevant Pillars

- **Secure (primary)** — `runAs` is the only mechanism Apex has for asserting that the access model behaves as designed.
  Salesforce Well-Architected treats access control as something you prove, not something you configure and hope for;
  a `runAs` test is that proof, and a `runAs` test that asserts nothing about permissions is a false attestation sitting
  in the suite where a reviewer will count it as coverage.
- **Reliable** — mixed-DML boundaries are a reliability concern more than a security one. Setup-object DML that is not
  partitioned fails at the transaction level, and the Apex Developer Guide notes mixed-DML validation is skipped during
  deployment — so the failure surfaces on the day someone runs the suite interactively, not on the day it was introduced.
- **Adaptable** — the enforcement semantics of `runAs` are pinned to each class's `apiVersion`. A suite whose assertions
  only hold at one version is a version upgrade blocked by its own tests.

Performance and Scalability are not load-bearing here beyond one budget item: each `runAs` call consumes a DML statement
from the transaction's allowance.

## Architectural Tradeoffs

**Impersonation fidelity vs test speed.** A faithful `runAs` test builds a real `User` with a real Profile and real
Permission Sets, which costs setup-object DML and forbids `@IsTest(IsParallel=true)` for that class — the setup objects
are documented as incompatible with it. The cheap alternative (assert against the admin context and reason about
permissions on paper) runs faster and proves nothing. Pay the setup cost on the classes where access control is the
requirement; do not pay it on classes where it is not.

**Fail-closed vs strip-and-continue.** Inside `runAs`, `WITH USER_MODE` / `AccessLevel.USER_MODE` fails the whole
operation on the first violation, while `Security.stripInaccessible(...).getRecords()` removes the inaccessible fields and
proceeds. That is a product decision wearing a technical costume: a bulk intake that discards one field is a better
outcome than a 10,000-record load that aborts; a financial adjustment that silently drops a field is worse than a failure.
Decide it per write path — the API 67.0 user-mode default does not decide it for you.

**Version pinning vs assertion stability.** Leaving a class at an old `apiVersion` keeps behaviour frozen and keeps a
green suite, at the cost of assertions that no longer mean what they say. Raising it makes `runAs` assertions honest and
converts the accumulated ambiguity into a batch of real test failures. The second is the cheaper debt to pay, but it
must be scheduled, not stumbled into.

## Anti-Patterns

1. **The FLS test that isn't.** A `runAs` block wrapping a bare SOQL query, asserting a restricted field is or isn't
   readable, with no `WITH USER_MODE` and no check of the class's `apiVersion`. It passes at one version and fails at
   another without a source change. Name the access mode in the query.
2. **Impersonation as a mixed-DML sticking plaster.** Scattering `runAs(new User(Id = UserInfo.getUserId()))` around
   whichever line threw, instead of giving all setup-object DML one structural boundary. The documented object list is
   explicitly "not an exhaustive list", so line-by-line patching is guaranteed to need patching again.
3. **Asserting sharing through a service call.** Calling production code from inside `runAs` and reading the result as
   evidence about sharing. The sharing mode applied is the callee class's, not the test class's — so a `without sharing`
   service returns records the impersonated user could never see, and the test certifies the bug.

## Official Sources Used

- Apex Developer Guide, Version 67.0 (Summer '26) — *Using the runAs Method*: confirms the user-mode default, that
  sharing plus object- and field-level permissions are enforced within the block regardless of the test class's sharing
  mode, that the callee's sharing mode wins for user-defined methods, that `runAs` is test-only, that each call costs a
  DML statement, and that user licence limits are ignored.
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_testing_tools_runas.htm (verified 2026-08-14)
- Apex Developer Guide, Version 67.0 — *sObjects That Can't Be Used Together in DML Operations*: the setup-object list,
  the "not an exhaustive list" caveat, and the `@IsTest (IsParallel=true)` incompatibility.
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dml_non_mix_sobjects.htm (verified 2026-08-14)
- Apex Developer Guide, Version 67.0 — *Apex Security and Sharing Model*: confirms user mode is the default in API 67.0+
  and system mode at 66.0 and earlier.
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_security_sharing_chapter.htm (verified 2026-08-14)
- Apex Developer Guide, Version 67.0 — *Set an Access Mode for Database Operations*: documents `WITH USER_MODE`,
  `WITH SYSTEM_MODE`, the `insert as user` DML form, `AccessLevel.USER_MODE`, and that a user-mode violation raises a
  `SecurityException`.
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_enforce_usermode.htm (verified 2026-08-14)
- Apex Developer Guide, Version 67.0 — *Enforce Security with the stripInaccessible Method*: confirms the strip-and-continue
  semantics contrasted above.
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_with_security_stripInaccessible.htm (verified 2026-08-14)
- SOAP API Developer Guide — *StatusCode* enumeration: the `MIXED_DML_OPERATION` entry referenced in `gotchas.md`.
  https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_calls_concepts_core_data_objects.htm (verified 2026-08-14)
