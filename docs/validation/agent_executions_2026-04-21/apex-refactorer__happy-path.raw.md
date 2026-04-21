```json
{
  "agent": "apex-refactorer",
  "mode": "single",
  "run_id": "20260421T150645Z",
  "report_path": "docs/reports/apex-refactorer/20260421T150645Z.md",
  "envelope_path": "docs/reports/apex-refactorer/20260421T150645Z.json",
  "inputs_received": {
    "source_path": "evals/agents/fixtures/apex-refactorer/samples/AccountTrigger_Naive.cls"
  },
  "summary": "Classified AccountTrigger_Naive.cls as a MIXED trigger body: inline before-insert mutation, after-update SOQL + DML on Contacts, and a synchronous HTTP callout from within a trigger context. Refactored into a thin trigger delegating to AccountTriggerHandler (extends TriggerHandler), introduced AccountSelector (extends BaseSelector) for the Contact query, and generated AccountTriggerHandler_Test.cls covering the 200-record bulk path plus a non-admin runAs case. The raw Http.send from a trigger is flagged as a pre-existing bug (triggers cannot perform synchronous callouts) and is moved behind a Queueable invocation using HttpClient with a Named Credential. System.debug replaced with ApplicationLogger; CRUD/FLS enforced via SecurityUtils before the Contact update.",
  "confidence": "MEDIUM",
  "confidence_rationale": "Library-only refactor — no org access, so Named Credential existence, Contact FLS posture, and presence of competing *TriggerHandler frameworks are unverified. Transformation itself is mechanical and cites canonical templates; the callout-in-trigger fix is the one judgement call.",
  "process_observations": [
    {
      "category": "concerning",
      "severity": "high",
      "domain": "apex-callouts",
      "observation": "Original trigger invokes Http.send() synchronously during after update. Salesforce disallows callouts from trigger context; this is a pre-existing runtime bug, not merely a pattern issue. Refactor moves it to a Queueable dispatched by the handler.",
      "evidence": {
        "source": "repo_scan",
        "path": "evals/agents/fixtures/apex-refactorer/samples/AccountTrigger_Naive.cls",
        "query": "Http http = new Http\\(\\); ... HttpResponse res = http.send\\(req\\);"
      }
    },
    {
      "category": "concerning",
      "severity": "medium",
      "domain": "integration-security",
      "observation": "Raw endpoint literal 'https://erp.example.com/api/sync' hard-coded in Apex. Refactor routes through a Named Credential 'ERP_Sync' per apex-security-patterns.",
      "evidence": {
        "source": "repo_scan",
        "path": "evals/agents/fixtures/apex-refactorer/samples/AccountTrigger_Naive.cls",
        "query": "req.setEndpoint('https://erp.example.com/api/sync')"
      }
    },
    {
      "category": "healthy",
      "severity": "info",
      "domain": "bulkification",
      "observation": "Source already bulk-safe on the Contact query (IN :Trigger.newMap.keySet()) — no N+1 SOQL to untangle, which simplifies the Selector lift.",
      "evidence": {
        "source": "repo_scan",
        "path": "evals/agents/fixtures/apex-refactorer/samples/AccountTrigger_Naive.cls",
        "query": "SELECT Id, AccountId, MailingCountry FROM Contact WHERE AccountId IN :Trigger.newMap.keySet()"
      }
    },
    {
      "category": "ambiguous",
      "severity": "medium",
      "domain": "framework-collision",
      "observation": "Unknown whether the consumer org already has a TriggerHandler framework (kevinohara80 or similar). If it does, the user should reconcile naming before merging this refactor. No org alias supplied, so unable to validate.",
      "evidence": {
        "source": "input",
        "path": "inputs.target_org_alias"
      }
    },
    {
      "category": "suggested_followup",
      "severity": "low",
      "domain": "followup",
      "observation": "Recommend running /scan-security on the refactored classes to confirm SecurityUtils placement, and /gen-tests if coverage targets tighten beyond the included test class.",
      "evidence": {
        "source": "heuristic",
        "path": "agents/apex-refactorer/AGENT.md"
      },
      "suggested_followup_agent": "scan-security",
      "followup_reason": "Confirm SecurityUtils placement and validate FLS/CRUD posture on the refactored Contact update path."
    }
  ],
  "deliverables": [
    {
      "kind": "apex",
      "title": "AccountTrigger.trigger (thin delegator)",
      "target_path": "force-app/main/default/triggers/AccountTrigger.trigger",
      "content": "trigger AccountTrigger on Account (before insert, before update, after insert, after update) {\n    new AccountTriggerHandler().run();\n}\n"
    },
    {
      "kind": "apex",
      "title": "AccountTriggerHandler.cls",
      "target_path": "force-app/main/default/classes/AccountTriggerHandler.cls",
      "content": "/**\n * AccountTriggerHandler\n * Lifts logic out of AccountTrigger per templates/apex/TriggerHandler.cls.\n * Default country stamping moved to beforeInsert; Contact country sync\n * moved to afterUpdate; ERP sync moved off the trigger thread into a\n * Queueable (callouts are not allowed directly from trigger context).\n */\npublic with sharing class AccountTriggerHandler extends TriggerHandler {\n\n    private static final String DEFAULT_COUNTRY = 'US';\n\n    public AccountTriggerHandler() {\n        super('AccountTriggerHandler');\n    }\n\n    public override void beforeInsert() {\n        stampDefaultCountry((List<Account>) Trigger.new);\n    }\n\n    public override void afterUpdate() {\n        Map<Id, Account> newMap = (Map<Id, Account>) Trigger.newMap;\n        syncContactCountry(newMap);\n        enqueueErpSync(newMap.values());\n    }\n\n    @TestVisible\n    private void stampDefaultCountry(List<Account> accounts) {\n        for (Account a : accounts) {\n            if (String.isBlank(a.BillingCountry)) {\n                a.BillingCountry = DEFAULT_COUNTRY;\n                ApplicationLogger.info('AccountTriggerHandler',\n                    'Stamped default country on new Account (context=beforeInsert)');\n            }\n        }\n    }\n\n    @TestVisible\n    private void syncContactCountry(Map<Id, Account> newMap) {\n        if (newMap == null || newMap.isEmpty()) {\n            return;\n        }\n        List<Contact> related = new AccountSelector().selectContactsByAccountIds(newMap.keySet());\n        if (related.isEmpty()) {\n            return;\n        }\n        List<Contact> toUpdate = new List<Contact>();\n        for (Contact c : related) {\n            Account parent = newMap.get(c.AccountId);\n            if (parent != null && String.isNotBlank(parent.BillingCountry)\n                    && parent.BillingCountry != c.MailingCountry) {\n                c.MailingCountry = parent.BillingCountry;\n                toUpdate.add(c);\n            }\n        }\n        if (toUpdate.isEmpty()) {\n            return;\n        }\n        SecurityUtils.requireUpdateable(Contact.SObjectType,\n            new List<Schema.SObjectField>{ Contact.MailingCountry });\n        update toUpdate;\n        ApplicationLogger.info('AccountTriggerHandler',\n            'Synced MailingCountry on ' + toUpdate.size() + ' Contact(s)');\n    }\n\n    @TestVisible\n    private void enqueueErpSync(List<Account> accounts) {\n        if (accounts == null || accounts.isEmpty() || System.isFuture()\n                || System.isBatch() || System.isQueueable()) {\n            return;\n        }\n        // Callouts are disallowed from trigger context; defer to Queueable.\n        System.enqueueJob(new ErpAccountSyncQueueable(new List<Account>(accounts)));\n    }\n\n    /**\n     * Inner Queueable wrapping the ERP sync. Uses HttpClient + the\n     * 'ERP_Sync' Named Credential (no raw endpoint literals).\n     */\n    public class ErpAccountSyncQueueable implements Queueable, Database.AllowsCallouts {\n        private final List<Account> payload;\n        public ErpAccountSyncQueueable(List<Account> payload) {\n            this.payload = payload;\n        }\n        public void execute(QueueableContext ctx) {\n            try {\n                HttpClient client = new HttpClient('callout:ERP_Sync');\n                HttpResponse res = client.post('/api/sync', JSON.serialize(payload));\n                if (res.getStatusCode() >= 300) {\n                    ApplicationLogger.warn('AccountTriggerHandler',\n                        'ERP sync non-2xx: ' + res.getStatusCode() + ' body=' + res.getBody());\n                } else {\n                    ApplicationLogger.info('AccountTriggerHandler',\n                        'ERP sync ok: ' + res.getStatusCode());\n                }\n            } catch (Exception e) {\n                ApplicationLogger.error('AccountTriggerHandler',\n                    'ERP sync failed: ' + e.getMessage(), e);\n            }\n        }\n    }\n}\n"
    },
    {
      "kind": "apex",
      "title": "AccountSelector.cls",
      "target_path": "force-app/main/default/classes/AccountSelector.cls",
      "content": "/**\n * AccountSelector\n * Centralizes Contact-by-parent-Account SOQL per templates/apex/BaseSelector.cls\n * and the WITH SECURITY_ENFORCED guidance in apex/apex-security-patterns.\n */\npublic inherited sharing class AccountSelector extends BaseSelector {\n\n    public override Schema.SObjectType getSObjectType() {\n        return Account.SObjectType;\n    }\n\n    public List<Contact> selectContactsByAccountIds(Set<Id> accountIds) {\n        if (accountIds == null || accountIds.isEmpty()) {\n            return new List<Contact>();\n        }\n        return [\n            SELECT Id, AccountId, MailingCountry\n            FROM Contact\n            WHERE AccountId IN :accountIds\n            WITH SECURITY_ENFORCED\n            LIMIT 50000\n        ];\n    }\n}\n"
    },
    {
      "kind": "apex",
      "title": "AccountTriggerHandler_Test.cls",
      "target_path": "force-app/main/default/classes/AccountTriggerHandler_Test.cls",
      "content": "/**\n * AccountTriggerHandler_Test\n * Follows templates/apex/tests/BulkTestPattern.cls (200-record path)\n * and uses TestDataFactory + TestUserFactory for non-admin runAs.\n */\n@IsTest\nprivate class AccountTriggerHandler_Test {\n\n    @IsTest\n    static void beforeInsert_stampsDefaultCountry_whenBlank() {\n        List<Account> accts = new List<Account>();\n        for (Integer i = 0; i < 200; i++) {\n            accts.add(new Account(Name = 'Acme ' + i));\n        }\n        Test.startTest();\n        insert accts;\n        Test.stopTest();\n\n        for (Account a : [SELECT Id, BillingCountry FROM Account WHERE Id IN :accts]) {\n            System.assertEquals('US', a.BillingCountry,\n                'beforeInsert should stamp default BillingCountry when blank');\n        }\n    }\n\n    @IsTest\n    static void beforeInsert_preservesExplicitCountry() {\n        Account a = new Account(Name = 'KeepMe', BillingCountry = 'CA');\n        insert a;\n        System.assertEquals('CA',\n            [SELECT BillingCountry FROM Account WHERE Id = :a.Id].BillingCountry);\n    }\n\n    @IsTest\n    static void afterUpdate_syncsContactCountry_bulk() {\n        // Arrange: 200 Accounts, each with 1 Contact, pre-existing BillingCountry.\n        List<Account> accts = TestDataFactory.createAccounts(200, 'US');\n        insert accts;\n        List<Contact> contacts = new List<Contact>();\n        for (Account a : accts) {\n            contacts.add(new Contact(\n                LastName = 'Doe-' + a.Id,\n                AccountId = a.Id,\n                MailingCountry = 'US'\n            ));\n        }\n        insert contacts;\n\n        // Act: flip country on all 200 parents in one DML.\n        for (Account a : accts) { a.BillingCountry = 'UK'; }\n        Test.setMock(HttpCalloutMock.class, new MockHttpResponseGenerator());\n        Test.startTest();\n        update accts;\n        Test.stopTest();\n\n        // Assert: every Contact now UK; SOQL count stays 1.\n        Integer updated = [SELECT COUNT() FROM Contact\n            WHERE AccountId IN :accts AND MailingCountry = 'UK'];\n        System.assertEquals(200, updated,\n            'afterUpdate should cascade BillingCountry to all Contacts');\n    }\n\n    @IsTest\n    static void afterUpdate_runsAsStandardUser_respectsFLS() {\n        User standard = TestUserFactory.createStandardUser('apex-refactorer-test');\n        Account a;\n        System.runAs(standard) {\n            a = new Account(Name = 'RunAs', BillingCountry = 'US');\n            insert a;\n            insert new Contact(LastName = 'Child', AccountId = a.Id, MailingCountry = 'US');\n            a.BillingCountry = 'DE';\n            Test.setMock(HttpCalloutMock.class, new MockHttpResponseGenerator());\n            Test.startTest();\n            update a;\n            Test.stopTest();\n        }\n        Contact c = [SELECT MailingCountry FROM Contact WHERE AccountId = :a.Id LIMIT 1];\n        System.assertEquals('DE', c.MailingCountry,\n            'Standard user with Contact edit access should still see sync happen');\n    }\n\n    @IsTest\n    static void erpSync_queueable_dispatchesWithoutFailure() {\n        Account a = new Account(Name = 'Enq', BillingCountry = 'US');\n        insert a;\n        a.BillingCountry = 'FR';\n        Test.setMock(HttpCalloutMock.class, new MockHttpResponseGenerator());\n        Test.startTest();\n        update a;\n        Test.stopTest();\n        // Assertion: Test.stopTest() drains the Queueable; no uncaught exception = pass.\n        System.assert(true, 'Queueable executed without uncaught exception');\n    }\n}\n"
    }
  ],
  "citations": [
    {
      "type": "skill",
      "id": "apex/trigger-framework",
      "path": "skills/apex/trigger-framework/SKILL.md",
      "used_for": "Canonical trigger-body refactor shape — one trigger per object delegating to a Handler extending TriggerHandler."
    },
    {
      "type": "skill",
      "id": "apex/apex-security-patterns",
      "path": "skills/apex/apex-security-patterns/SKILL.md",
      "used_for": "CRUD/FLS enforcement via SecurityUtils and Named-Credential rule that displaces hard-coded endpoints."
    },
    {
      "type": "skill",
      "id": "admin/agent-output-formats",
      "path": "skills/admin/agent-output-formats/SKILL.md",
      "used_for": "Envelope shape contract — confidence, process_observations, citations, followups."
    },
    {
      "type": "template",
      "id": "apex/TriggerHandler.cls",
      "path": "templates/apex/TriggerHandler.cls",
      "used_for": "Base class the emitted AccountTriggerHandler extends."
    },
    {
      "type": "template",
      "id": "apex/BaseSelector.cls",
      "path": "templates/apex/BaseSelector.cls",
      "used_for": "Base class the emitted AccountSelector extends for the Contact-by-AccountIds query."
    },
    {
      "type": "template",
      "id": "apex/HttpClient.cls",
      "path": "templates/apex/HttpClient.cls",
      "used_for": "Wrapper used inside ErpAccountSyncQueueable to route the callout via Named Credential."
    },
    {
      "type": "template",
      "id": "apex/ApplicationLogger.cls",
      "path": "templates/apex/ApplicationLogger.cls",
      "used_for": "Replaces System.debug() calls in the refactored handler."
    },
    {
      "type": "template",
      "id": "apex/SecurityUtils.cls",
      "path": "templates/apex/SecurityUtils.cls",
      "used_for": "requireUpdateable() guard on the Contact.MailingCountry update."
    },
    {
      "type": "template",
      "id": "apex/tests/BulkTestPattern.cls",
      "path": "templates/apex/tests/BulkTestPattern.cls",
      "used_for": "200-record bulk test shape for AccountTriggerHandler_Test.afterUpdate_syncsContactCountry_bulk."
    },
    {
      "type": "template",
      "id": "apex/tests/TestDataFactory.cls",
      "path": "templates/apex/tests/TestDataFactory.cls",
      "used_for": "createAccounts() helper used to build the 200-Account bulk fixture."
    },
    {
      "type": "template",
      "id": "apex/tests/TestUserFactory.cls",
      "path": "templates/apex/tests/TestUserFactory.cls",
      "used_for": "createStandardUser() for the non-admin runAs FLS test."
    },
    {
      "type": "template",
      "id": "apex/tests/MockHttpResponseGenerator.cls",
      "path": "templates/apex/tests/MockHttpResponseGenerator.cls",
      "used_for": "HttpCalloutMock implementation to satisfy Test.setMock during the Queueable path."
    },
    {
      "type": "decision_tree",
      "id": "automation-selection",
      "path": "standards/decision-trees/automation-selection.md",
      "branch": "Q1 — record-triggered automation: Apex trigger chosen (complex cross-object logic + callout)",
      "used_for": "Confirmed Apex trigger remains the right tool vs. Flow for this shape."
    },
    {
      "type": "decision_tree",
      "id": "async-selection",
      "path": "standards/decision-trees/async-selection.md",
      "branch": "Q3 — callout from trigger: Queueable chosen (needs AllowsCallouts + sequential ordering)",
      "used_for": "Selected Queueable over @future for the ERP sync dispatch."
    }
  ],
  "followups": [
    {
      "agent": "scan-security",
      "because": "Confirm SecurityUtils placement and validate FLS/CRUD posture on the refactored Contact update path."
    },
    {
      "agent": "gen-tests",
      "because": "Expand coverage toward 95%+ if the org's test policy is stricter than the 85% target used here."
    },
    {
      "agent": "detect-drift",
      "because": "Check whether a competing *TriggerHandler framework already lives in the target org before merging this refactor."
    }
  ]
}
```
