# Apex Trigger Bypass And Kill-Switch — Implementation Template

Use this template when shipping bypass / kill-switch capability for an Apex
trigger handler. The repo's canonical building blocks are
`templates/apex/TriggerControl.cls` and
`templates/apex/cmdt/Trigger_Setting__mdt.object-meta.xml` — reference them
directly; do not re-implement.

## Scope

**Skill:** `apex-trigger-bypass-and-killswitch-patterns`

**Request summary:** (fill in)

**Bypass scope chosen** (pick one or more):
- [ ] Org-wide kill switch (CMDT `Trigger_Setting__mdt.Is_Active__c = false`)
- [ ] Per-user / integration-user (Custom Permission `Bypass_Triggers`)
- [ ] Per-profile or short-lived (Hierarchy Custom Setting)
- [ ] In-transaction cascade (programmatic `TriggerControl.bypass/restore`)

---

## Step 1 — Custom Metadata schema (canonical)

Reuse the canonical CMDT type at
`templates/apex/cmdt/Trigger_Setting__mdt.object-meta.xml`. Required fields:

| Field | Type | Purpose |
|---|---|---|
| `Object_API_Name__c` | Text(80) | The SObject API name (e.g. `Account`) |
| `Handler_Class__c` | Text(80) | The handler class name (e.g. `AccountTriggerHandler`) |
| `Is_Active__c` | Checkbox | When false, the handler is bypassed |

One CMDT record per (object, handler) pair. Default `Is_Active__c = true`.

---

## Step 2 — Custom Permission

```xml
<!-- force-app/main/default/customPermissions/Bypass_Triggers.customPermission-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<CustomPermission xmlns="http://soap.sforce.com/2006/04/metadata">
    <isLicensed>false</isLicensed>
    <label>Bypass Triggers</label>
</CustomPermission>
```

Assign via Permission Set `Integration_User_Bypass`. Never grant directly
to a profile or via a User-object checkbox.

---

## Step 3 — Handler `run()` override with kill-switch check

```apex
public with sharing class AccountTriggerHandler extends TriggerHandler {
    private static final String SOBJ = 'Account';
    private static final String HANDLER = 'AccountTriggerHandler';

    public override void run() {
        if (!TriggerControl.isActive(SOBJ, HANDLER)) {
            ApplicationLogger.info(
                HANDLER,
                'Bypass active for user ' + UserInfo.getUserId()
                    + ' — skipping handler'
            );
            return;
        }
        super.run();
    }
}
```

`TriggerControl.isActive` (see `templates/apex/TriggerControl.cls`) already:
- checks `FeatureManagement.checkPermission('TriggerControl_BypassAll')`
- queries `Trigger_Setting__mdt` once per transaction (cached)
- defaults to `true` if no record exists (fail-open by design)

---

## Step 4 — Programmatic bypass for cascade DML

```apex
public with sharing class OpportunityWonService {
    public static void onWon(Set<Id> oppIds) {
        List<Account> updates = buildAccountUpdates(oppIds);

        try {
            TriggerControl.bypass('Account', 'AccountTriggerHandler');
            ApplicationLogger.info(
                'OpportunityWonService',
                'Programmatic bypass: AccountTriggerHandler for ' + updates.size() + ' rows'
            );
            update updates;
        } finally {
            TriggerControl.restore('Account', 'AccountTriggerHandler');
        }
    }
}
```

Rules:
- Always `try/finally`. Restore must run even if `update` throws.
- Log the bypass invocation. Forensics depends on it.
- Do NOT enqueue Queueable / `@future` work expecting the bypass to carry
  over. Re-apply at the top of the asynchronous entry point if needed.

---

## Step 5 — Test pattern

```apex
@IsTest
private class AccountTriggerHandlerTest {

    @IsTest
    static void handlerRunsByDefault() {
        // No bypass overrides — handler MUST run.
        Test.startTest();
        insert new Account(Name='Acme');
        Test.stopTest();
        Account a = [SELECT Id, Territory__c FROM Account WHERE Name='Acme'];
        System.assertNotEquals(null, a.Territory__c,
            'Handler should have set Territory__c on insert');
    }

    @IsTest
    static void killSwitchBypassesHandler() {
        TriggerControl.overrideForTest('Account', 'AccountTriggerHandler', false);
        Test.startTest();
        insert new Account(Name='Acme');
        Test.stopTest();
        Account a = [SELECT Id, Territory__c FROM Account WHERE Name='Acme'];
        System.assertEquals(null, a.Territory__c,
            'Handler must NOT have run when kill switch is off');
    }
}
```

---

## Verification

After deploying:

- [ ] `Trigger_Setting__mdt` record for the (object, handler) exists with
      `Is_Active__c = true`
- [ ] `Bypass_Triggers` Custom Permission deployed
- [ ] `Integration_User_Bypass` Permission Set grants the Custom Permission
- [ ] Integration user is assigned the Permission Set
- [ ] Handler `run()` calls `TriggerControl.isActive(...)` first and exits
      cleanly if false
- [ ] All programmatic bypass blocks use `try/finally`
- [ ] Every bypass invocation writes one `Application_Log__c` row
- [ ] Tests prove (a) default-run path and (b) kill-switch-off path
- [ ] Runbook entry documents how to flip `Is_Active__c` and how to verify
      in production

## Notes

Record any deviations and why:

-
