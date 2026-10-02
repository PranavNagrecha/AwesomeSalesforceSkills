# Gotchas — Test Class Standards

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Async Work Finishes At `Test.stopTest()`, Not Before

**What happens:** A test enqueues a Queueable, immediately queries the database, and finds no updates.

**When it occurs:** Async code is exercised without a proper `Test.startTest()` / `Test.stopTest()` boundary.

**How to avoid:** Place the action under test between `startTest()` and `stopTest()`, and assert after `stopTest()`.

---

## Gotcha 2: `SeeAllData=true` Masks Missing Setup

**What happens:** The test passes in one sandbox because existing Accounts, Record Types, or custom settings happen to exist. The deployment then fails in another org.

**When it occurs:** Teams use live org data as a shortcut instead of building factories or isolated setup.

**How to avoid:** Default to isolated test data. If `SeeAllData=true` is truly required, document the reason and keep the test as narrow as possible.

---

## Gotcha 3: Mixed DML Can Break Perfectly Good Tests

**What happens:** A test creates a `User` and setup-related records alongside normal business records and gets a Mixed DML exception.

**When it occurs:** Permission, role, queue, or user setup is created in the same transaction as non-setup object DML.

**How to avoid:** Separate setup-object creation patterns appropriately, and design factories with user setup in mind when security context matters.

---

## Gotcha 4: Assertion-Light Tests Create False Confidence

**What happens:** Coverage looks healthy, but a production regression slips through because the tests only assert on counts or `System.assert(true)`.

**When it occurs:** Teams optimize for deployment thresholds instead of behavior contracts.

**How to avoid:** Assert on specific field values, thrown exceptions, related records, and failure-path outcomes.

---

## Gotcha 5: The Stub API Cannot Mock Every Apex Member

**What happens:** A developer reaches for `Test.createStub()` to fake a static utility method, a private helper, or a trigger, and the stub silently fails to intercept the call or throws at stub-creation time.

**When it occurs:** The mocked type exposes the collaboration point as a static or `@future` method, a private method, a property getter/setter, a trigger, an inner class, a system type, a class that implements the `Batchable` interface, or a class that has only private constructors — none of which the Stub API supports. The mocked type must also be in the same namespace as the `Test.createStub()` call.

**How to avoid:** Design the seam you want to mock as a non-static, non-private instance method on a top-level class. If a static utility must be substituted, wrap it behind an injectable instance method, or fall back to a hand-written test double for that specific case.

---

## Gotcha 6: `Assert` Messages Must Be Strings

**What happens:** Code that passed an sObject or other object as the message argument to `System.assertEquals` fails to compile when mechanically converted to the `Assert` class.

**When it occurs:** Migrating legacy assertions where the third argument was a non-`String` object; the legacy `System.assert*` methods tolerated arbitrary objects, but the `Assert` methods require a `String` message.

**How to avoid:** Pass an explicit `String` message (call `String.valueOf(...)` if you were relying on an object's debug form). The legacy methods remain supported, so there is no need to migrate working tests purely for style.

---

## Gotcha 7: `@TestSetup` Is Not Allowed In A `SeeAllData=true` Class

**What happens:** A class is annotated `@IsTest(SeeAllData=true)` and its `@TestSetup` method silently stops being the shared fixture — the compiler rejects it, or the team deletes it and duplicates the setup into every method.

**When it occurs:** Someone adds `SeeAllData=true` to an existing class that already had a working `@TestSetup` method. "Test setup methods are supported only with the default data isolation mode for a test class. If the test class or a test method has access to organization data by using the `@IsTest(SeeAllData=true)` annotation, test setup methods aren't supported in this class" (apexdev L6272-L6273).

**How to avoid:** Treat `SeeAllData=true` as a whole-class decision that costs you the shared fixture, and split the one method that genuinely needs org data into its own class. Note also that `@IsTest(SeeAllData=false)` on a method inside a `SeeAllData=true` class is ignored (apexdev L5812-L5813), and that `SeeAllData=true` cannot be combined with `@IsTest(IsParallel=true)` (apexdev L5824), so one careless annotation drops the class out of the parallel pool.

---

## Gotcha 8: Static State Does Not Carry From `@TestSetup` Into A Test Method

**What happens:** A test seeds a static cache, a `Map` of record Ids, or a feature-flag singleton in `@TestSetup`, then reads it in a test method and finds it empty or back at its initializer value.

**When it occurs:** Any time state is passed between methods through a static rather than through the database. "Every test method, including the test setup method, runs as a separate transaction. The static context of the test class is reinitialized before each transaction begins" (apexdev L41032-L41034), and a static changed in one test method is not visible to the next (apexdev L40551-L40553).

**How to avoid:** Pass state through queried records, not statics. If the code under test caches in a static, assert that the cache repopulates from scratch rather than assuming a warm cache — and use `@TestVisible` to reset it explicitly at the top of the method that depends on it.

---

## Gotcha 9: `Test.setMock` Must Come After `Test.startTest()` When DML Ran First

**What happens:** A test inserts records, registers a callout mock, runs the method, and fails with an uncommitted-work error instead of receiving the mock response.

**When it occurs:** "By default, callouts aren't allowed after DML operations in the same transaction because DML operations result in pending uncommitted work that prevents callouts from executing" — the fix is that "the `Test.startTest` statement must appear before the `Test.setMock` statement", and the DML must sit outside the `startTest`/`stopTest` block (apexdev L35135-L35141).

**How to avoid:** Fix the order: DML, then `Test.startTest()`, then `Test.setMock(...)`, then the action, then `Test.stopTest()`. DML that happens *after* the mock callout needs no special handling.

---

## Gotcha 10: A Published Platform Event Is Not Delivered Until `Test.getEventBus().deliver()`

**What happens:** A test publishes a platform event and asserts on what the event trigger should have written. Nothing was written, because the subscriber never ran.

**When it occurs:** `EventBus.publish(...)` inside a test queues the message; the platform-event trigger fires only when the test explicitly delivers it (apexdev L29673-L29674). For a `BatchApexErrorEvent` raised by a failed batch job, the `deliver()` call belongs after `Test.stopTest()` (apexdev L17912-L17916).

**How to avoid:** Publish, call `Test.getEventBus().deliver()`, then assert. If the subscriber itself publishes a downstream event, add another `deliver()` for each hop (apexdev L17938-L17940). Capture the `EventBus.publish` result rather than discarding it, so a failed publish is visible in the test rather than showing up as a missing side effect.

---

## Gotcha 11: Every `System.runAs` Call Spends A DML Statement

**What happens:** A test that loops `System.runAs` over a set of users to prove per-profile visibility hits the 150-DML-statement limit before it finishes, and the failure looks unrelated to sharing.

**When it occurs:** "Every call to `runAs` counts against the total number of DML statements issued in the process" (apexdev L41339). A per-user loop therefore burns one statement per iteration on top of the DML the test itself performs.

**How to avoid:** Mint the users in bulk once (`TestUserFactory.createUsers`), then use a small fixed number of `runAs` blocks — one per access profile you actually need to distinguish — rather than one per record. Remember that inside a `runAs` block the user's sharing and object/field permissions are enforced regardless of the test class's `with sharing` mode (apexdev L41331-L41333).

---

## Gotcha 12: Some Records Cannot Be Created In A Test At All

**What happens:** A factory method for history, feed, or a non-createable standard object compiles, then fails at run time or silently inserts nothing, and the test that depends on it is quietly disabled.

**When it occurs:** "Some standard objects aren't creatable" (apexdev L40772); field history and `FeedTrackedChange` records "can't be created in test methods because they require other sObject records to be committed first" (apexdev L40776-L40782); and sObjects with unique constraints (`CollaborationGroup`, for example) reject duplicate inserts whether or not `SeeAllData=true` is set (apexdev L40773-L40775).

**How to avoid:** Check creatability before designing the fixture. Where the record genuinely cannot be made, test the layer above it against a stub or a mock instead of the record, and say so in a comment. `Test.loadData(Account.sObjectType, 'myResource')` (apexdev L40896-L40904) covers the separate case of bulk fixture data that is tedious to build in code but perfectly creatable.

---

## Gotcha 13: A Test For User-Mode Code Fails At Validation Unless It Runs As A Permissioned User

**What happens:** A package compiles clean — every component reports `ok` — and then every single test method fails, at validation, before any assertion runs. The two error strings, verbatim, so you can grep a deploy log for them:

```
System.QueryException: No such column 'Tier2_Notified_At__c' on entity 'Case'. If you are
attempting to use a custom field, be sure to append the '__c' after the custom field name.

System.DmlException: Operation failed due to fields being inaccessible on Sobject
Integration_Failure__c, check errors on Exception or Result!
```

The first is what `WITH USER_MODE` SOQL does when the running user has no read FLS on a field; the second is what `Database.insert(records, AccessLevel.USER_MODE)` (or `insert as user`) does when the running user has no create FLS. Neither says "permissions" in the headline, which is why the usual first reaction is to go looking for a missing field in `package.xml` that is in fact present and deployed.

**When it occurs:** Four conditions have to line up, and in a greenfield build they always do.

1. The code under test enforces user mode. "In user mode, the object permissions, field-level security, and sharing rules of the current user are enforced" (apexdev L11437-L11439; see also L11955-L11987 for the `WITH USER_MODE`, `as user` and `AccessLevel.USER_MODE` spellings). From API 67.0 onward this is not a choice — "In API version 67.0 and later, Apex runs in user context by default, meaning that the current user's permissions and field-level security (FLS) are enforced during code execution" (apexdev L11744-L11745), and `WITH SECURITY_ENFORCED` no longer compiles — "In API version 67.0 and later, you can't use the WITH SECURITY_ENFORCED clause in SOQL SELECT queries in Apex code. Instead, use the WITH USER_MODE clause" (apexdev L11741-L11743). A build created today is therefore in this trap by default, not by choosing to be.
2. The custom fields ship **in the same deployment** as the code.
3. The test methods run as the deploying user, because the class has no `System.runAs` block for anybody else.
4. That deploying user's FLS comes from a profile, and the profile is not in the request. Profile deployment is an overlay — "We designed Profile metadata deployment to overlay the existing Profile settings in a target org" (api_meta L97626-L97631) — so a profile absent from the request is not touched, and keeps exactly the FLS it already had. For a field created by this very deployment, that is none. Including the profile is not a fix on its own either, because profile metadata is scoped to what travelled with it: "profiles only include field-level security for fields included in custom objects returned in the same RetrieveRequest as the profiles" (api_meta L97622-L97625), and a wildcard retrieve of profiles carries permissions "for all custom objects in your organization but don't include permissions for standard objects, such as Account, and standard fields" (api_meta L98487-L98492) — which is precisely the shape of `Case.Tier2_Notified_At__c`, a custom field on a standard object. UNVERIFIED (2026-09-12): the corpus states this scoping for `RetrieveRequest`; that deployment applies the identical scoping is an inference from the overlay semantics above, not a quoted deploy-side sentence.

So the permission set in the deployment does carry the field permissions — and nothing assigns it to the user the tests actually run as. A System Administrator profile does not save you: on a field created by this very deployment, that profile has whatever FLS the deployment gave it, which is nothing.

`RunSpecifiedTests` and `RunLocalTests` both hit this, and `--dry-run` hits it exactly as a production deploy would. That is the useful part: the validation run is not being pedantic, it is showing you the outage.

**How to avoid:** Make the permissioned user part of the fixture, not part of one method.

- Build the user with `templates/apex/tests/TestUserFactory.cls` — `createUser(profileName, permissionSetNames)` already inserts the `User` and the `PermissionSetAssignment` rows for the named sets.
- Name the permission set(s) the deployment ships. If the answer is "none", the build has an access gap that no test can paper over, and that is the finding.
- Put the assertions inside `System.runAs(testUser)`. Salesforce's own integration-test example does exactly this — "use `System.runAs()` to run integration test logic as a specific user, including setting up the necessary permission set assignments" (apexdev L42448-L42462).
- Do not mistake `System.runAs(new User(Id = UserInfo.getUserId()))` for this. That idiom exists to separate setup-object DML from ordinary DML in one transaction (apexdev L8931-L8942); it re-enters the *same* user's context and grants no permission. A class can be full of it and still be running as the admin who has no FLS.
- `System.runAs` is the right tool rather than a wish: "the user's sharing rules and object-level and field-level permissions are enforced within a `runAs` block, regardless of the sharing mode (`with sharing` or `without sharing`) of the test class" (apexdev L41331-L41333). Budget for Gotcha 11 — each call spends a DML statement.
- Catch it before the org does: `python3 skills/apex/test-class-standards/scripts/check_test_class_standards.py --manifest-dir <classes dir>` raises `user-mode-test-without-runas` (ERROR) when a non-test class in the tree carries `WITH USER_MODE`, `AccessLevel.USER_MODE`, `WITH SECURITY_ENFORCED` or `stripInaccessible` and the test class alongside it has no permissioned `runAs` block.

**Where this came from:** a validate-only deploy (`sf project deploy start --dry-run --test-level RunSpecifiedTests`) of the `tier2-webhook` build: 38 components `ok`, 28 of 28 test methods failed, coverage 34.9%. Evidence in `.sfskills/builds/tier2-webhook/reports/mock-deploy/2026-09-12T13-08-43Z/summary.md`.

**See also:** fixing this gotcha does not finish the job — Gotcha 14 is the failure that surfaces next, once the tests actually run as a permissioned user.

---

## Gotcha 14: User-Mode DML Counts A Null-Assigned Field As Populated

**What happens:** Gotcha 13's fix lands — every test method now runs inside `System.runAs(agent)` — and the `@TestSetup` seed insert still fails, for every test class in the deployment, at the same line:

```
System.DmlException: Operation failed due to fields being inaccessible on Sobject
Case, check errors on Exception or Result! ... fieldNames: AccountId
```

The running user holds the permission set the deployment ships, and grants create access on the fields the test actually cares about. The field the org names is not one any test method populates on purpose.

**When it occurs:** The seed calls a shared factory — `TestDataFactory.createCases(count, accountId, overrides)`, or the `Contact` / `Opportunity` builders, same shape — and passes `null` for `accountId` because the test has no Account to link. The factory's constructor assigns the lookup unconditionally: `Case c = new Case(..., AccountId = accountId);`. Assigning a variable into a field in the constructor marks that field populated on the sObject regardless of the value — the platform cannot distinguish "explicitly set to null" from "never touched" once the constructor runs, so the field rides along on the DML request. At API 67.0+, Apex runs in user context by default (apexdev L11744-L11745), so that DML — a plain `insert` inside `System.runAs`, no `AccessLevel` keyword needed — checks FLS on every field the request carries, including the null one. If the running user has no create access on that field (a Standard User rarely has create on `Case.AccountId`, `Contact.AccountId`, or `Opportunity.AccountId` by default, even holding a permission set scoped to the build's own custom fields), the insert fails on a field the test never meant to set.

**How to probe it:** the org's message names no field until you make it. Wrap the seed in try/catch and rethrow with the diagnostic attached:

```apex
try {
    insert TestDataFactory.createCases(1, null, null);
} catch (DmlException e) {
    List<String> failedFields = e.getDmlFieldNames(0);
    Map<String, Schema.SObjectField> fieldMap = Case.SObjectType.getDescribe().fields.getMap();
    for (String f : failedFields) {
        System.debug(f + ' createable=' + fieldMap.get(f).getDescribe().isCreateable());
    }
    System.debug('profile=' + [SELECT Profile.Name FROM User WHERE Id = :UserInfo.getUserId()].Profile.Name);
    System.debug('psa=' + [SELECT COUNT() FROM PermissionSetAssignment WHERE AssigneeId = :UserInfo.getUserId()]);
    throw e;
}
```

`e.getDmlFieldNames(0)` turns the generic message into `fieldNames: AccountId`; the describe loop turns that into `AccountId createable=false`; the last two lines rule out "wrong user" or "permission set never assigned" as the cause. This is the exact probe that closed S2-F-12 in the `tier2-webhook` build: `createable=true Subject=true Status=true Origin=true AccountId=false Tier2_Notified_At__c=true profile=Standard User psa=1 | fields=AccountId | code=CANNOT_INSERT_UPDATE_ACTIVATE_ENTITY`.

**How to avoid:** two fixes, and both are required — one without the other reproduces the failure in a different shape.

- The factory must populate a lookup only when it is given one: construct the record without the field, then `if (accountId != null) { record.AccountId = accountId; }` — never assign a possibly-null parameter directly inside a constructor's field list. `templates/apex/tests/TestDataFactory.cls` follows this for every lookup argument (`Contact`, `Opportunity`, `Case`).
- Independently, the permissioned user built for Gotcha 13 must be able to create every field the seed actually does populate. The factory fix removes a field the test never needed; it does not grant FLS for the fields the test does need.

**Where this came from:** run 7 of the `tier2-webhook` M1 mock deploy, immediately after the Gotcha 13 fix landed — 30 of 30 test methods failed on the same `@TestSetup` seed insert, inside `System.runAs`, on a factory-populated `AccountId` no test method referenced. See `.sfskills/builds/tier2-webhook/reports/MOCK-DEPLOY-M1.md` run 7.

**See also:** Gotcha 13 gets a test into `System.runAs` with a permissioned user; this gotcha is the layer underneath — the shared factory itself has to stop volunteering fields nobody asked for.

---

## Gotcha 15: Seed In System Mode, Act As The Persona

**What happens:** Gotchas 13 and 14 are both fixed — every test runs inside `System.runAs(agent)`, the factory no longer volunteers a null lookup — and the `@TestSetup` seed insert *still* fails, on a field neither of those gotchas mentions:

```
System.DmlException: Operation failed due to fields being inaccessible on Sobject Case,
check errors on Exception or Result! fieldNames: EntitlementId
```

The permissioned user holds every permission set the persona is meant to hold. The field failing is real, deliberately populated, and correct for the fixture. The persona genuinely does not have Create access to it — and should not, because an entitlement assignment is an admin-configured value, not something the agent sets by hand.

**When it occurs:** at API 67.0+, Apex runs in user context by default (apexdev L11744-L11745), so a plain `insert` inside `System.runAs(persona)` checks the persona's FLS on every populated field — including fixture-only fields the test needs to exist but that the persona's job never requires them to write: an `EntitlementId` set by an entitlement process, a lookup an integration user populates, a field an admin sets once at record creation. Gotcha 13 established that the test must run as a permissioned user, not the deploying admin; Gotcha 14 established that the factory must not volunteer fields nobody asked for. Neither gotcha distinguishes "fields the persona's code path writes" from "fields the fixture needs populated for the test to be meaningful" — and conflating the two produces a false choice: either grant the persona Create access to fields it does not use (widening the persona past what its layouts and processes justify, and reintroducing Gotcha 15's mirror image, F-60 in `admin/permission-sets-vs-profiles` — a persona with field access nobody asked it to have), or leave the fixture unable to seed at all.

**How to avoid:** Do not choose. Seed the fixture in system mode; run only the action under test as the persona.

- Build the fixture with `Database.insert(records, AccessLevel.SYSTEM_MODE)` — "In system mode, the object and field-level permissions of the current user are ignored, and the record sharing rules are controlled by the class sharing keywords" (apexdev L11436-L11439; `AccessLevel.SYSTEM_MODE` documented for `Database` DML methods including `insert` at apexdev L11995-L12003). Equivalently, insert inside `System.runAs` of an admin-set user (a `TestUserFactory` user on a profile that genuinely has the field, or the mixed-DML-fence idiom `System.runAs(new User(Id = UserInfo.getUserId()))` for setup-object DML) when the fixture also needs setup objects created in the same transaction.
- Keep `System.runAs(persona)` scoped to the action under test — the trigger, service call, or DML the requirement is actually about — not the fixture setup around it. `templates/apex/tests/TestDataFactory.insertAsSystem(List<SObject>)` wraps the system-mode insert so call sites read as intent, not as an incantation.
- Do not read a system-mode fixture insert failing as a permission gap to fix by widening the persona's permission set. Ask instead whether the field belongs on the persona's own permission set at all — `EntitlementId`, most admin-set lookups, and fields no layout or process for that persona ever writes usually do not, and granting them anyway is the exact anti-pattern `admin/permission-sets-vs-profiles` Gotcha "An Object Grant Without Field Grants Is A Persona That Cannot Fill In A Form" warns against in the other direction.
- Keep the two seams separate in the class: `@TestSetup` (or a helper called from it) does the system-mode seed; the `@IsTest` method's body — the part that calls the code under test — is what sits inside `System.runAs(persona)`.
- Catch it before the org does: `python3 skills/apex/test-class-standards/scripts/check_test_class_standards.py --manifest-dir <classes dir>` raises `fixture-seeded-as-persona` (WARN) when a permissioned `System.runAs` body seeds records with plain DML (a factory call or `new <SObject>(`) outside `Test.startTest()` / `Test.stopTest()`. The org remains the judge; `--strict` promotes the WARN.

**Where this came from:** `case-onboarding` build F-60 follow-on (M5 run 5/6): once the Tier 1 persona's permission sets were reviewed against F-60, the fixture still needed `EntitlementId` populated to exercise milestone logic, and the honest fix was a system-mode seed, not a wider grant. `.sfskills/builds/case-onboarding/reports/MOCK-DEPLOY-M5.md` run 5.

**See also:** Gotcha 13 gets the *action* under test into `System.runAs` with a permissioned user; Gotcha 14 stops the factory from volunteering fields nobody asked for; this gotcha draws the line between what the fixture needs to exist and what the persona is allowed to write, and puts each on the correct side of `System.runAs`.

---

## Gotcha 16: The runAs Scan Reads Code, Not Comments — In Both Directions

**What happens:** until 2026-09-19 the checker's `System.runAs` detection (`has_permissioned_runas`, `runas_blocks`, `find_fixture_seeded_as_persona`) blanked string literals on the raw file without blanking comments first. Two failures followed, found by the northwind-sales M3-S03 builder: a `System.runAs(rep)` spelled out in a class header comment satisfied the `user-mode-test-without-runas` ERROR on its own (a false pass), and an odd number of possessive apostrophes in ordinary comments — "the rep's manager's approval" — opened a phantom literal that blanked every real `System.runAs` below it (a false fail: seven real calls measured as zero).

**How to avoid:** comments are now stripped before literals at all four sites, with offsets preserved. Fixtures `runas-in-comment-only/` (1 ERROR expected) and `apostrophes-before-runas/` (0 expected) pin both directions. One honest consequence: a runAs block that apostrophes used to hide is now scanned, so a class may gain a `fixture-seeded-as-persona` WARN it never showed before (tier2-webhook M1-S03 gained one). Do not remove apostrophes from comments to satisfy a checker; if a result surprises you, read the rule.

---

## Gotcha 17: Seed The Object Grant Too — The Org's Own Permission Set Is Not In Your Package

**What happens:** Gotcha 15 moves fixture DML out of the persona's `runAs` block. The object-level twin bit northwind-sales M3-S03 on 2026-09-19: the service ran `SELECT … FROM Opportunity WITH USER_MODE` as a persona who held the build's own permission set (record types and two field grants) and nothing else, and every test method threw `System.QueryException: sObject type 'Opportunity' is not supported. If you are attempting to use a custom object, be sure to append the '__c' after the entity name` — user mode's way of saying the running user has no object permission. The design assumed the org's existing Sales Cloud permission set would supply Opportunity CRUD; that set was neither in the package nor in the validating org, and no static checker can see an assumption about org-held metadata. All three declared checkers were green before and after.

**How to avoid:** a persona test seeds every grant the code under test needs, object permissions included, when the grant is not in the package: inside the mixed-DML fence, insert a test-scoped `PermissionSet`, an `ObjectPermissions` row for the object (`PermissionsRead`/`PermissionsCreate`/`PermissionsEdit` as the code requires, `PermissionsViewAllRecords` false), and the `PermissionSetAssignment` for each persona user — alongside the build's own set, not instead of it. Do not pre-empt `FieldPermissions` on standard fields: the profile usually carries them, and the org will say so if not (it did not, on run 5). Keep the build's metadata as the requirement designed it; the test is where the org's assumed grants are made explicit.
