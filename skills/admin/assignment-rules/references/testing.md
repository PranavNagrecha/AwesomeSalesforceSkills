# Testing — Assignment Rules

Two layers: an Apex test that proves the rule routes a record when the header is set (and does nothing when it is not), and a manual channel matrix for everything Apex cannot reach.

## Apex test: owner after DML with the assignment header

Assignment rules are setup metadata, so a test sees the org's real active rule. That makes the test environment-dependent: it passes only in an org whose active rule contains the entry being asserted. Deploy the queue and the rule with the test (scratch org or sandbox), and assert the precondition so a wrong org fails loudly instead of confusingly.

```apex
@IsTest
private class LeadAssignmentRuleTest {

    // Precondition: the org's active Lead assignment rule has an entry
    //   Lead.State equals CA  ->  Queue West_Region_Queue
    // Deploy assignmentRules/Lead.assignmentRules-meta.xml and the queue
    // together with this class (see references/metadata-examples.md).

    @IsTest
    static void insertWithHeader_routesCaLeadToWestQueue() {
        System.assertEquals(1,
            [SELECT COUNT() FROM AssignmentRule WHERE SobjectType = 'Lead' AND Active = true],
            'Exactly one active Lead assignment rule is required for this test');

        Group westQueue = [
            SELECT Id FROM Group
            WHERE Type = 'Queue' AND DeveloperName = 'West_Region_Queue'
            LIMIT 1
        ];

        Database.DMLOptions dmo = new Database.DMLOptions();
        dmo.assignmentRuleHeader.useDefaultRule = true;

        Lead l = new Lead(LastName = 'Rule Test', Company = 'Acme', State = 'CA');

        Test.startTest();
        Database.SaveResult sr = Database.insert(l, dmo);
        Test.stopTest();

        System.assert(sr.isSuccess(), sr.getErrors());
        Lead saved = [SELECT OwnerId FROM Lead WHERE Id = :l.Id];
        System.assertEquals(westQueue.Id, saved.OwnerId,
            'Active assignment rule should route CA leads to the West queue');
    }

    @IsTest
    static void insertWithoutHeader_keepsRunningUserAsOwner() {
        Lead l = new Lead(LastName = 'No Header', Company = 'Acme', State = 'CA');

        insert l;   // plain DML: no assignment header, rule must not run

        Lead saved = [SELECT OwnerId FROM Lead WHERE Id = :l.Id];
        System.assertEquals(UserInfo.getUserId(), saved.OwnerId,
            'Plain DML must not invoke assignment rules');
    }
}
```

Notes:

- `Database.insert(records, dmo)` is the only Apex path that invokes the rule; a DML statement cannot carry the header (`apex/apex-dml-patterns`).
- Use a specific rule instead of the active one with `dmo.assignmentRuleHeader.assignmentRuleId = <Id>`; look the Id up by name with `SELECT Id FROM AssignmentRule WHERE Name = '...' AND SobjectType = 'Lead'` rather than hard-coding it, because Ids differ per org.
- For Case, the same code applies with a `Case` record; add `dmo.emailHeader.triggerAutoResponseEmail = true` if production code is expected to trigger the auto-response, and remember that test context never sends email.
- The second test is the one that catches regressions where a developer "simplifies" `Database.insert` back to `insert`.

## Manual channel matrix

Run once per channel that creates the object, in the org where the rule is active. Record the actual owner next to the expected owner.

| Channel | Set-up for the test | Expected owner | Verify |
|---|---|---|---|
| Web-to-Lead / Web-to-Case form | Submit one record per rule entry, plus one that matches no entry | Entry target; catch-all target for the last one | Record's Owner field; queue list view |
| Email-to-Case | Send one email per routing address you rely on | Entry target based on Origin / routing address | Owner plus the auto-response arriving from the expected sender |
| Lightning UI | Create with the assignment checkbox ticked, then again unticked | Entry target; creating user | Owner on both records |
| REST / SOAP integration | Fire the integration's real create call against a sandbox | Entry target | Owner is the queue, not the integration user |
| Data Loader / Bulk API | Load 3 rows with the assignment rule Id set | Entry targets per row | Owner per row in the success file |
| Apex | Run the test class above | As asserted | Test result |

Sandbox caveat: after a refresh, email deliverability is system-only and usernames carry the sandbox suffix, so user-targeted entries and auto-response emails behave differently from production (`references/migration-and-sandbox.md`).
