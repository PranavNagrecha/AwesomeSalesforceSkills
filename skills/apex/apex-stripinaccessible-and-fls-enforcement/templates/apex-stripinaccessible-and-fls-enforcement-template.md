# Apex stripInaccessible and FLS Enforcement — Pattern Template

Canonical method-level wrapper for enforcing CRUD/FLS on user-supplied records before DML.
Copy into your service / controller layer and adapt the `SObject` type and `AccessType`.

## Scope

**Skill:** `apex-stripinaccessible-and-fls-enforcement`

**Use when:** A method receives a `List<SObject>` from a less-privileged caller (LWC, Aura, REST, Visualforce, Flow invocable) and writes it to the database.

---

## Canonical Method-Level Wrapper

```apex
/**
 * Enforces field-level security on a user-supplied collection before DML.
 * - AccessType MUST match the DML below: CREATABLE / UPDATABLE / UPSERTABLE.
 * - DML is on `decision.getRecords()`, NEVER the original argument.
 * - Removed-field map is logged so silent stripping is observable.
 */
public with sharing class CaseIntakeService {

    public class IntakeException extends Exception {}

    public List<Case> ingest(List<Case> userSupplied) {
        if (userSupplied == null || userSupplied.isEmpty()) {
            return userSupplied;
        }

        // 1. Strip inaccessible CREATE fields (matches the insert below).
        SObjectAccessDecision decision =
            Security.stripInaccessible(AccessType.CREATABLE, userSupplied);

        // 2. Audit any privilege-escalation attempts.
        Map<String, Set<String>> removed = decision.getRemovedFields();
        if (!removed.isEmpty()) {
            ApplicationLogger.warn(
                'CaseIntakeService.ingest',
                'Stripped fields: ' + JSON.serialize(removed)
            );
        }

        // 3. Strip child relationships separately — strip is NOT recursive.
        List<CaseComment> nestedComments = new List<CaseComment>();
        for (Case c : (List<Case>) decision.getRecords()) {
            if (c.CaseComments != null) nestedComments.addAll(c.CaseComments);
        }

        // 4. DML on the SANITIZED list (never on `userSupplied`).
        List<Case> safe = (List<Case>) decision.getRecords();
        insert safe;

        // 5. If child collections existed, strip + DML them now that parent IDs exist.
        if (!nestedComments.isEmpty()) {
            for (Integer i = 0; i < safe.size(); i++) {
                if (safe[i].CaseComments == null) continue;
                for (CaseComment cc : safe[i].CaseComments) cc.ParentId = safe[i].Id;
            }
            SObjectAccessDecision childDecision =
                Security.stripInaccessible(AccessType.CREATABLE, nestedComments);
            insert childDecision.getRecords();
        }

        return safe;
    }
}
```

---

## Verification — System.runAs Test

The strip is a no-op under default test context. Wrap the assertion in `System.runAs` to prove enforcement.

```apex
@IsTest
private class CaseIntakeServiceTest {

    @TestSetup
    static void setupRestrictedUser() {
        // Build a user whose profile lacks Edit on Case.Internal_Notes__c.
        // Use templates/apex/tests/TestUserFactory if available.
    }

    @IsTest
    static void stripsNonCreatableFields() {
        User restricted = [
            SELECT Id FROM User WHERE Username = 'restricted@example.com.test' LIMIT 1
        ];
        Case c = new Case(
            Subject = 'Hello',
            Internal_Notes__c = 'PRIVILEGE ESCALATION ATTEMPT'
        );

        Test.startTest();
        System.runAs(restricted) {
            List<Case> result = new CaseIntakeService().ingest(new List<Case>{ c });
            Case persisted =
                [SELECT Id, Internal_Notes__c FROM Case WHERE Id = :result[0].Id];
            System.assertEquals(
                null,
                persisted.Internal_Notes__c,
                'stripInaccessible must scrub Internal_Notes__c for restricted user'
            );
        }
        Test.stopTest();
    }

    @IsTest
    static void doesNotStripForAdmin() {
        Case c = new Case(
            Subject = 'Hello',
            Internal_Notes__c = 'admin notes'
        );
        Test.startTest();
        // No runAs — runs as system test user with full FLS.
        List<Case> result = new CaseIntakeService().ingest(new List<Case>{ c });
        Test.stopTest();

        Case persisted =
            [SELECT Id, Internal_Notes__c FROM Case WHERE Id = :result[0].Id];
        System.assertEquals('admin notes', persisted.Internal_Notes__c);
    }
}
```

---

## Verification Checklist

- [ ] `Security.stripInaccessible` call is present
- [ ] `AccessType` matches the DML operation (CREATABLE/UPDATABLE/UPSERTABLE)
- [ ] DML targets `decision.getRecords()`, NOT the original argument
- [ ] `getRemovedFields()` is logged or surfaced
- [ ] Child relationships are stripped in a separate call
- [ ] One test under `System.runAs(restrictedUser)` asserts a field WAS stripped
- [ ] One test under default context confirms no-op for privileged user
- [ ] No `WITH USER_MODE` query feeding directly into a `READABLE` strip on the same path
- [ ] Method is on a `with sharing` (or `inherited sharing`) class for record-level visibility

---

## Cross-Reference

- `templates/apex/SecurityUtils.cls` — shared helper that wraps `stripInaccessible` with logging
- `standards/decision-trees/sharing-selection.md` — class-level sharing keyword choice (separate concern)
- `skills/apex/apex-with-user-mode-soql` — the read-side companion primitive
