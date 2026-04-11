# FSC Apex Extensions — Work Template

Use this template when working on tasks that extend Financial Services Cloud behavior through Apex.

## Scope

**Skill:** `fsc-apex-extensions`

**Request summary:** (fill in what the user asked for — e.g., "add custom trigger logic on FinancialAccount without breaking rollups")

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here before writing any code.

- **FSC namespace in use:** [ ] `FinServ__` (managed package) [ ] Platform-native FSC (post-Winter '23)
- **FSC package version installed:** ___ (check Setup > Installed Packages > Financial Services Cloud)
- **Org API version:** ___ (confirm it matches or is compatible with the FSC package version)
- **Active TriggerSettings__c flags for the target object:** (list the flags relevant to this work)
- **Compliant Data Sharing enabled on affected objects:** [ ] Yes [ ] No
- **Bulk DML involved:** [ ] Yes — requires post-load rollup recalculation [ ] No

## Approach

Which pattern from SKILL.md applies?

- [ ] **Safe Trigger Co-Existence** — Custom trigger on same object/event as FSC built-in
  - FSC trigger flag to disable: `FinServ__[Object]Trigger__c`
  - try/finally guard confirmed: [ ]
- [ ] **Post-Bulk-Load Rollup Reset** — Bulk DML on FSC financial objects
  - Recalculation invocation location: ___
  - Batch size set to 200: [ ]
- [ ] **CDS Participant Registration** — Sharing access on CDS-governed object
  - Share role name: ___
  - Using `FinServ__ShareParticipant__c` insert (not direct share DML): [ ]

## Implementation Checklist

- [ ] `FinServ__TriggerSettings__c` disable/re-enable wrapped in `try/finally` block
- [ ] No permanent FSC trigger disablement — flags restored to original value in `finally`
- [ ] `FinServ.RollupRecalculationBatchable` invoked with explicit batch size of 200 (if bulk DML)
- [ ] Sharing implemented via `FinServ__ShareParticipant__c` — no direct `AccountShare`/`FinancialAccountShare` DML
- [ ] Test class inserts `FinServ__TriggerSettings__c` record in `@TestSetup`
- [ ] Tested in a full-copy sandbox with the same FSC package version as production
- [ ] Household totals spot-checked after rollup recalculation confirmed complete

## Notes

Record any deviations from the standard pattern and why.

---

## Code Stubs

### Trigger Handler with TriggerSettings Guard

```apex
public class [ObjectName]TriggerHandler {
    public static void handle[Event](
        List<FinServ__[Object]__c> newList,
        Map<Id, FinServ__[Object]__c> oldMap
    ) {
        FinServ__TriggerSettings__c ts = FinServ__TriggerSettings__c.getInstance();
        Boolean wasEnabled = ts.FinServ__[Object]Trigger__c;
        try {
            if (wasEnabled) {
                ts.FinServ__[Object]Trigger__c = false;
                upsert ts;
            }
            // --- your custom logic here ---

        } finally {
            if (wasEnabled) {
                ts.FinServ__[Object]Trigger__c = true;
                upsert ts;
            }
        }
    }
}
```

### Post-Bulk-Load Rollup Recalculation

```apex
// In finish() of migration/integration batch, or as a standalone Queueable:
Database.executeBatch(new FinServ.RollupRecalculationBatchable(), 200);
```

### CDS Participant Registration

```apex
FinServ__ShareRole__c role = [SELECT Id FROM FinServ__ShareRole__c WHERE Name = '[RoleName]' LIMIT 1];
insert new FinServ__ShareParticipant__c(
    FinServ__FinancialAccount__c = financialAccountId,
    FinServ__User__c             = userId,
    FinServ__ShareRole__c        = role.Id
);
```

### Test Class TriggerSettings Setup

```apex
@TestSetup
static void setup() {
    insert new FinServ__TriggerSettings__c(
        SetupOwnerId = UserInfo.getOrganizationId(),
        FinServ__AccountTrigger__c = true,
        FinServ__FinancialAccountTrigger__c = true
        // add other flags as needed for the objects under test
    );
}
```
