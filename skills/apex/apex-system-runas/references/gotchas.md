# Gotchas — Apex System Runas

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: What `runAs` enforces changed in API 67.0 — and it is gated on the class, not the org

**What happens:** The long-standing folklore "`System.runAs` enforces sharing but not FLS" is version-dependent, and the
Apex Developer Guide now states the opposite as the default. Version 67.0 of the guide opens *Using the runAs Method*
with: "Generally, all Apex code runs in user mode, where the object-level and field-level permissions of the current user
are enforced." It then adds the note: "The user's sharing rules and object-level and field-level permissions are enforced
within a runAs block, regardless of the sharing mode (`with sharing` or `without sharing`) of the test class."

The controlling switch is stated separately under *Versioned Behavior Changes*: "In API version 67.0 and later, Apex runs
in user context by default, meaning that the current user's permissions and field-level security (FLS) are enforced during
code execution. In API version 66.0 and earlier, system mode is the default."

**When it occurs:** The moment the `apiVersion` in a class's `.cls-meta.xml` crosses 66.0 → 67.0. A Summer '26 org runs
a class pinned to 58.0 with the old system-mode default quite happily, so "our org is on Summer '26" tells you nothing.
Two failure directions:

- **Raising the version breaks passing tests.** A test that read `Account.Hidden__c` inside `runAs(lowPrivUser)` and
  asserted a value silently succeeded at 66.0. At 67.0 the same query throws, and the test fails on a line nobody touched.
- **Staying on the old version keeps a false-negative test.** A pre-67.0 test wrapped in `runAs` that "proves" a restricted
  user cannot see a field proves nothing — the query never enforced FLS in the first place.

**How to avoid:** Read the `apiVersion` out of the `.cls-meta.xml` before you interpret any `runAs` assertion, and state
which row you are on in the test's header comment. On a 66.0-or-earlier class, back every FLS claim with an explicit
`WITH USER_MODE` query, an `AccessLevel.USER_MODE` `Database` call, or `Security.stripInaccessible(...).getRecords()` —
`runAs` alone is not evidence. See `agents/_shared/AGENT_CONTRACT.md` § "Apex security idiom by API version" for the
full version table.

---

## Gotcha 2: Inside `runAs`, the sharing mode comes from the callee, not the test class

**What happens:** Wrapping a call in `runAs` does not impose the test class's sharing declaration on the code being
tested. The guide is explicit: "If a user-defined method is called in the runAs block, the sharing mode enforced is that
of the class where the method is defined, not the test class."

**When it occurs:** Any test that calls into production code from inside `runAs` — which is every useful `runAs` test.
An `@IsTest private with sharing class` calling `AccountService` — declared `without sharing` — gets `without sharing`
behaviour for that call. The test then asserts that a restricted user "can see" records they could never see through the
UI, and the sharing bug ships.

**How to avoid:** Assert sharing behaviour against a bare SOQL query issued *in the test class itself* inside the `runAs`
block, not against the return value of a service method. If you must assert through the service, read the service class's
sharing keyword first and write the expectation against that, not against what the test class declares.

---

## Gotcha 3: The setup-object list is documented as incomplete

**What happens:** Mixing DML on a setup sObject with DML on a normal sObject in one transaction fails with the
`MIXED_DML_OPERATION` status code — documented in the SOAP API `StatusCode` enumeration as: "There are limits on what
kinds of DML operations can be performed in the same transaction." The Apex Developer Guide lists the offending objects
(`AuthSession`, `ContentWorkspace`, `FieldPermissions`, `ForecastingShare`, `Group`, `GroupMember`, `ObjectPermissions`,
`ObjectTerritory2AssignmentRule`, `ObjectTerritory2AssignmentRuleItem`, `PermissionSet`, `PermissionSetAssignment`,
`QueueSObject`, `RuleTerritory2Association`, `SetupEntityAccess`, `Territory`, `Territory2`, `Territory2Model`, `User`,
`UserPackageLicense`, `UserRole`, `UserTerritory`, `UserTerritory2Association`) and then undercuts the list with a note:
"This list includes sObjects that cannot be used together in the same DML transaction, but is not an exhaustive list."

Three sub-rules are easy to miss:

- `Group`: "You can only insert and update a group in a transaction with other sObjects. Other DML operations aren't allowed."
- `GroupMember`: "With legacy Apex code saved using Salesforce API version 14.0 and earlier, you can insert and update a
  group member with other sObjects in the same transaction."
- "These sObjects also can't be used with the `@IsTest (IsParallel=true)` annotation." Adding `IsParallel=true` to speed
  up a suite that creates users is not a free win.

**When it occurs:** Most often when a helper you did not write inserts a `PermissionSetAssignment` or a `QueueSObject`
several frames down from your `insert account`.

**How to avoid:** Treat the list as a floor, not a ceiling. Put *all* setup-object DML inside
`System.runAs(new User(Id = UserInfo.getUserId())) { ... }` in `@TestSetup` and keep record data outside it, so a newly
classified setup object cannot break the suite later.

---

## Gotcha 4: Mixed-DML validation is skipped during deployment

**What happens:** The Apex Developer Guide notes: "Because validation for mixed DML operations is skipped during
deployment, there can be a difference in the number of test failures when tests are deployed versus when run in the
user interface."

**When it occurs:** A test with a genuine mixed-DML defect passes in the deployment's test run and then fails the first
time somebody runs it from Developer Console or Test Setup — or vice versa, which is the version that generates the
"but it passed in CI" ticket.

**How to avoid:** Never treat a green deployment as proof that the setup-object DML in a test is well-formed. Run the
suite interactively (or via `sf apex run test`) in the source sandbox before promoting, and fix the mixed-DML boundary
rather than relying on the deploy-time gap.

---

## Gotcha 5: `runAs` spends DML statements and ignores licence limits

**What happens:** Two documented behaviours with opposite signs. "Every call to `runAs` counts against the total number
of DML statements issued in the process" — a loop that impersonates 60 users has spent 60 of the 150 synchronous DML
statements before doing any work. And: "The runAs method ignores user license limits. You can create users with runAs
even if your organization has no additional user licenses."

**When it occurs:** The licence half bites in production, not in the test. A green test proves a Profile/Permission Set
combination *behaves* correctly; it proves nothing about whether the org can actually provision a user on that licence.

**How to avoid:** Impersonate once per scenario and assert several things inside one block rather than re-entering
`runAs` per assertion. Separately, confirm licence availability for the target Profile — and the User Licence its
Permission Sets require — in Setup before promising the feature, because no Apex test can fail for a licence you do not own.

## Official Sources Used

- Apex Developer Guide, Version 67.0 (Summer '26) — *Using the runAs Method*: confirms user-mode default, the FLS/sharing
  note, the callee-sharing-mode rule, "only in test methods", the DML-statement cost, and the licence-limit exemption.
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_testing_tools_runas.htm (verified 2026-08-14)
- Apex Developer Guide, Version 67.0 — *sObjects That Can't Be Used Together in DML Operations*: the setup-object list,
  the "not an exhaustive list" note, the `Group` / `GroupMember` sub-rules, and the `IsParallel=true` restriction.
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dml_non_mix_sobjects.htm (verified 2026-08-14)
- Apex Developer Guide, Version 67.0 — *Mixed DML Operations in Test Methods*: the deployment-vs-UI validation note.
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dml_non_mix_sobjects_test_methods.htm (verified 2026-08-14)
- Apex Developer Guide, Version 67.0 — *Apex Security and Sharing Model*:
  API 67.0 user-context default vs system mode at 66.0 and earlier.
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_security_sharing_chapter.htm (verified 2026-08-14)
- SOAP API Developer Guide — *StatusCode* enumeration: the `MIXED_DML_OPERATION` entry.
  https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_calls_concepts_core_data_objects.htm (verified 2026-08-14)
