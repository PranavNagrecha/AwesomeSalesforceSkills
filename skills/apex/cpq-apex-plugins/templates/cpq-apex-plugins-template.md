# CPQ Apex Plugins — Work Template

Use this template when implementing or reviewing a CPQ plugin in Apex or JavaScript (JS QCP).

## Scope

**Skill:** `apex/cpq-apex-plugins`

**Request summary:** (fill in what the user asked for — e.g., "add volume surcharge logic to the CPQ calculator")

## Context Gathered

Record answers to the Before Starting questions from SKILL.md:

- **CPQ package version:** (e.g., Spring '26 v66.0)
- **Plugin type needed:** (QuoteCalculatorPlugin / JS QCP / OrderPlugin / ContractingPlugin / ProductSearchPlugin / ConfigurationInitializerPlugin / QuoteTermPlugin / ProductRulePlugin / ConfigurationAttributePlugin)
- **Active JS QCP present?** (query: `SELECT Id, Name, SBQQ__Active__c FROM SBQQ__CustomScript__c WHERE SBQQ__Active__c = true`)
- **Currently registered Apex plugins:** (query CPQ Settings for each plugin field)
- **Affected quote line fields:** (list field API names the plugin will read or write)
- **Governor limit context:** (CPU and SOQL headroom available — check existing debug logs)

## Approach

Which pattern from SKILL.md applies? (choose one and justify)

- [ ] **JS QCP** — modern calculator customization; JS code stored in SBQQ__CustomScript__c
- [ ] **Apex QuoteCalculatorPlugin + CalculateCallback** — calculator customization requiring async Apex
- [ ] **Apex OrderPlugin** — logic at order creation; no JS equivalent
- [ ] **Apex ContractingPlugin** — logic at contract creation; no JS equivalent
- [ ] **Apex ProductSearchPlugin** — filter or reorder catalog search results
- [ ] **Apex ConfigurationInitializerPlugin** — pre-populate configurator options on screen load

**Why this approach over alternatives:** (fill in)

## Implementation Checklist

- [ ] Confirmed no conflicting active plugin of the same type is already registered
- [ ] For JS QCP: every exported hook function returns a `Promise` in every code branch
- [ ] For Apex: class declared `global`; all overridden methods declared `global`
- [ ] No SOQL inside loop iterations — IDs collected before loop, Map used for lookups
- [ ] No Apex triggers on `SBQQ__Quote__c` or `SBQQ__QuoteLine__c` modifying price fields
- [ ] Plugin registered in CPQ Settings in the correct field (not just deployed as Apex)
- [ ] Debug logs reviewed with SBQQ category at FINEST level — plugin fires at expected lifecycle point
- [ ] CPU time and SOQL count reviewed in debug logs under realistic line counts (20+ lines)

## Plugin Registration Reference

| Plugin Type | CPQ Settings Field API Name |
|---|---|
| JS QCP | `SBQQ__CustomScript__c.SBQQ__Active__c = true` (no Settings field) |
| Apex Quote Calculator Plugin | `SBQQ__CustomActionSettings__c.SBQQ__QuoteCalculatorPlugin__c` |
| Apex Order Plugin | `SBQQ__CustomActionSettings__c.SBQQ__OrderPlugin__c` |
| Apex Contracting Plugin | `SBQQ__CustomActionSettings__c.SBQQ__ContractingPlugin__c` |
| Apex Product Search Plugin | `SBQQ__CustomActionSettings__c.SBQQ__ProductSearchPlugin__c` |
| Apex Initializer Plugin | `SBQQ__CustomActionSettings__c.SBQQ__InitializerPlugin__c` |

## JS QCP Hook Skeleton

```javascript
// Store this in SBQQ__CustomScript__c.SBQQ__Code__c
// Set SBQQ__Active__c = true on the record

export function onInit(quoteModel, quoteLineModels, conn) {
    // Fires when the calculator initializes
    return Promise.resolve();
}

export function onBeforeCalculate(quoteModel, quoteLineModels, conn) {
    // Fires before the CPQ calculation engine runs
    return Promise.resolve();
}

export function onAfterCalculate(quoteModel, quoteLineModels, conn) {
    // Fires after the calculation engine completes — safest place to set final prices
    return Promise.resolve();
}

export function onBeforePriceRules(quoteModel, quoteLineModels, conn) {
    return Promise.resolve();
}

export function onAfterPriceRules(quoteModel, quoteLineModels, conn) {
    return Promise.resolve();
}

export function onBeforeCalculatePrices(quoteModel, quoteLineModels, conn) {
    return Promise.resolve();
}

export function onAfterCalculatePrices(quoteModel, quoteLineModels, conn) {
    return Promise.resolve();
}
```

## Apex Plugin Skeleton (OrderPlugin example — adapt for other types)

```apex
global class MyOrderPlugin implements SBQQ.OrderPlugin {

    global void onBeforeInsert(
        List<Order> orders,
        SBQQ.DefaultOrderProduct defaultOrderProduct,
        Database.UnitOfWork uow
    ) {
        // Logic before order records are inserted
        // Use uow.registerNew() / uow.registerDirty() — do NOT call DML directly
    }

    global void onAfterInsert(
        List<Order> orders,
        SBQQ.DefaultOrderProduct defaultOrderProduct,
        Database.UnitOfWork uow
    ) {
        // Logic after order records are inserted
    }
}
```

## Validation Queries

```sql
-- Check for active JS QCP
SELECT Id, Name, SBQQ__Active__c, SBQQ__Code__c
FROM SBQQ__CustomScript__c
WHERE SBQQ__Active__c = true

-- Check CPQ Settings plugin registrations
SELECT SBQQ__QuoteCalculatorPlugin__c,
       SBQQ__OrderPlugin__c,
       SBQQ__ContractingPlugin__c,
       SBQQ__ProductSearchPlugin__c,
       SBQQ__InitializerPlugin__c
FROM SBQQ__CustomActionSettings__c
LIMIT 1
```

## Notes

(Record any deviations from the standard pattern and why — e.g., "used `without sharing` on OrderPlugin because price book entries are not visible to the rep's profile")
