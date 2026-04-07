# Examples — CPQ Apex Plugins

## Example 1: JS QCP Hook to Apply a Volume-Based Surcharge After Calculation

**Context:** A manufacturing org sells configurable machines. For any quote line where the product family is "Heavy Equipment" and quantity exceeds 5, a 3% handling surcharge must be added to the `SBQQ__CustomerPrice__c` field. The pricing team has confirmed that CPQ price rules cannot express a percentage surcharge against a final customer price without a plugin.

**Problem:** Writing an `after update` trigger on `SBQQ__QuoteLine__c` to set `SBQQ__CustomerPrice__c` causes a race condition: CPQ recalculates after the trigger fires and overwrites the field with the engine's computed value. The surcharge silently disappears on every save.

**Solution:**

```javascript
// Stored in SBQQ__CustomScript__c.SBQQ__Code__c
// SBQQ__Active__c must be true on the record

export function onAfterCalculate(quoteModel, quoteLineModels, conn) {
    const SURCHARGE_RATE = 0.03;
    const SURCHARGE_FAMILY = 'Heavy Equipment';
    const SURCHARGE_QTY_THRESHOLD = 5;

    quoteLineModels.forEach(function(line) {
        var record = line.record;
        var family = record['SBQQ__ProductFamily__c'];
        var qty = record['SBQQ__Quantity__c'] || 0;

        if (family === SURCHARGE_FAMILY && qty > SURCHARGE_QTY_THRESHOLD) {
            var basePrice = record['SBQQ__CustomerPrice__c'] || 0;
            record['SBQQ__CustomerPrice__c'] = basePrice * (1 + SURCHARGE_RATE);
        }
    });

    // Every hook MUST return a resolved Promise — never return undefined
    return Promise.resolve();
}

// All unused hooks must still be exported and return Promise.resolve()
export function onInit(quoteModel, quoteLineModels, conn) {
    return Promise.resolve();
}
export function onBeforeCalculate(quoteModel, quoteLineModels, conn) {
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

**Why it works:** `onAfterCalculate` fires after CPQ has finished its full calculation pass. Mutations to `quoteLineModels[i].record` fields at this point are respected and written to the database when the quote is saved. Because the hook returns a `Promise`, CPQ's engine awaits it correctly and does not overwrite the surcharge in a subsequent pass.

---

## Example 2: Apex OrderPlugin to Create a Fulfillment Record on Order Creation

**Context:** A logistics org uses CPQ to generate orders. When CPQ creates an order from a quote, a custom `Fulfillment__c` record must be created and linked to each `OrderItem`. No JS equivalent exists for `OrderPlugin`.

**Problem:** An `after insert` trigger on `OrderItem` fires correctly but runs outside CPQ's Unit of Work, causing partial failures when CPQ's own transaction rolls back — the `Fulfillment__c` records are created even when the order commit fails, leaving orphaned records.

**Solution:**

```apex
// Apex class — must be global to implement the managed SBQQ interface
global class FulfillmentOrderPlugin implements SBQQ.OrderPlugin {

    global void onBeforeInsert(
        List<Order> orders,
        SBQQ.DefaultOrderProduct defaultOrderProduct,
        Database.UnitOfWork uow
    ) {
        // No action needed before insert for this requirement
    }

    global void onAfterInsert(
        List<Order> orders,
        SBQQ.DefaultOrderProduct defaultOrderProduct,
        Database.UnitOfWork uow
    ) {
        for (Order o : orders) {
            for (OrderItem item : o.OrderItems) {
                Fulfillment__c f = new Fulfillment__c(
                    Order__c       = o.Id,
                    OrderItem__c   = item.Id,
                    Status__c      = 'Pending',
                    Quantity__c    = item.Quantity
                );
                // Register with CPQ's UoW — do NOT call insert directly
                uow.registerNew(f);
            }
        }
    }
}
```

**Registration:** In CPQ Settings (Setup > Installed Packages > Salesforce CPQ > Configure > Order Management tab), enter `FulfillmentOrderPlugin` in the **Order Plugin** field.

**Why it works:** Registering new records through the `uow` (Unit of Work) provided by CPQ ensures that `Fulfillment__c` inserts participate in the same Salesforce transaction as the order. If the order commit fails, the UoW rolls back all registered records together, preventing orphans.

---

## Example 3: Apex ConfigurationInitializerPlugin to Pre-Select Options Based on Account Segment

**Context:** A SaaS org has a product with optional add-ons. When a rep configures the product for an "Enterprise" account, three specific options must be pre-selected and their quantities set to 1. Currently reps forget to select them, causing incorrect orders.

**Problem:** Product rules can highlight or validate options but cannot pre-select them during the initial load of the configuration screen before the user has interacted with the page.

**Solution:**

```apex
global class EnterpriseDefaultsInitializer implements SBQQ.ConfigurationInitializerPlugin {

    private static final Set<String> ENTERPRISE_OPTION_CODES = new Set<String>{
        'SUPPORT-PREMIUM', 'SSO-SAML', 'AUDIT-LOG'
    };

    global void initialize(SBQQ.ProductModel productModel, String configurationId) {
        // configurationId is the SBQQ__ProductOption__c record Id context
        // productModel.options contains the list of SBQQ.OptionModel entries

        // Retrieve the account segment from the quote via the configurationId
        // (configurationId maps to the SBQQ__QuoteLineGroup__c or the quote itself)
        String segment = getAccountSegment(configurationId);

        if (segment != 'Enterprise') {
            return; // No defaults for non-Enterprise
        }

        for (SBQQ.OptionModel opt : productModel.options) {
            String code = (String) opt.record.get('SBQQ__ProductCode__c');
            if (ENTERPRISE_OPTION_CODES.contains(code)) {
                opt.record.put('SBQQ__Quantity__c', 1);
                opt.record.put('SBQQ__Selected__c', true);
            }
        }
    }

    private String getAccountSegment(String configurationId) {
        // Query the related quote to find account segment
        List<SBQQ__QuoteLine__c> lines = [
            SELECT SBQQ__Quote__r.SBQQ__Account__r.Account_Segment__c
            FROM SBQQ__QuoteLine__c
            WHERE Id = :configurationId
            LIMIT 1
        ];
        if (!lines.isEmpty()) {
            return (String) lines[0].getSObject('SBQQ__Quote__r')
                                    .getSObject('SBQQ__Account__r')
                                    .get('Account_Segment__c');
        }
        return null;
    }
}
```

**Registration:** CPQ Settings > Products tab > **Initializer Plugin** field: enter `EnterpriseDefaultsInitializer`.

**Why it works:** `ConfigurationInitializerPlugin.initialize()` fires before the configuration screen renders. Mutations to `opt.record` fields are reflected in the initial UI state, so options appear pre-checked when the rep opens the configurator.

---

## Anti-Pattern: Using Apex Triggers Instead of Plugin Hooks for Calculated Fields

**What practitioners do:** Write an `after update` trigger on `SBQQ__QuoteLine__c` to override `SBQQ__CustomerPrice__c` based on custom business logic, because triggers are familiar and appear to work in developer testing.

**What goes wrong:** CPQ's calculation engine performs multiple passes on quote lines during a single save. After the trigger sets the field, CPQ's next internal recalculation reads the database-committed value and overwrites it with the engine's own computed result. In lightweight test scenarios the trigger appears to win because only one pass occurs, but in production with complex price rules and multi-line quotes the overwrite is consistent and silent. The field reverts to CPQ's value with no error message to the user.

**Correct approach:** Use the JS QCP `onAfterCalculate` hook (or the legacy Apex `QuoteCalculatorPlugin`) to mutate line fields after the engine has completed its pass. Plugin hooks run inside the CPQ calculation transaction and their mutations are written to the database after all calculation passes are complete.
