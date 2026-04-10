# Examples — CPQ API and Automation

## Example 1: Programmatic Quote Creation with Products and Calculation

**Context:** An integration platform receives a signed order from an external system and needs to create a CPQ quote in Salesforce with the correct products and pricing — no user interaction.

**Problem:** The integration team inserts `SBQQ__QuoteLine__c` records directly via REST. Quote totals are null and the `SBQQ__NetPrice__c` fields on all lines are zero because no pricing engine ran.

**Solution:**

```apex
public class ProgrammaticQuoteBuilder {

    public static void buildQuote(Id opportunityId, List<Id> productIds) {
        // Step 1: Create the quote header (DML is fine for header fields only)
        SBQQ__Quote__c quote = new SBQQ__Quote__c(
            SBQQ__Opportunity2__c = opportunityId,
            SBQQ__Primary__c      = false
        );
        insert quote;

        // Step 2: Read the empty quote model
        String quoteModel = SBQQ.ServiceRouter.read('QuoteReader', quote.Id);

        // Step 3: For each product, load its model and add it to the quote
        for (Id productId : productIds) {
            String productModel = SBQQ.ServiceRouter.read('ProductLoader', productId);
            // QuoteProductAdder expects a JSON wrapper with quote and products keys
            String addPayload = buildAddPayload(quoteModel, productModel);
            quoteModel = SBQQ.ServiceRouter.save('QuoteProductAdder', addPayload);
        }

        // Step 4: Calculate pricing (sync — suitable for small line counts)
        String calculatedModel = SBQQ.ServiceRouter.save('QuoteCalculator', quoteModel);

        // Step 5: Persist the calculated model
        SBQQ.ServiceRouter.save('QuoteSaver', calculatedModel);
    }

    // Construct the combined payload required by QuoteProductAdder
    private static String buildAddPayload(String quoteModel, String productModel) {
        // The payload shape is: {"quote": <quoteModel>, "products": [<productModel>]}
        // In production, use a proper JSON builder or a wrapper Apex class
        return '{"quote":' + quoteModel + ',"products":[' + productModel + ']}';
    }
}
```

**Why it works:** Every step goes through `SBQQ.ServiceRouter` with the correct loader string sequence: `QuoteReader` → `QuoteProductAdder` → `QuoteCalculator` → `QuoteSaver`. The pricing engine runs during `QuoteCalculator` and all downstream price fields are populated correctly before `QuoteSaver` writes them to the database.

---

## Example 2: Async Calculation with CalculateCallback

**Context:** A nightly batch job needs to re-price all active quotes after a global price book update. Some quotes have 150–300 lines. The sync calculate path is hitting CPU governor limit exceptions.

**Problem:** `SBQQ.ServiceRouter.save('QuoteCalculator', model)` inside a batch execute method throws `System.LimitException: Apex CPU time limit exceeded` for large quotes.

**Solution:**

```apex
// Step 1: Implement the callback — must be global
global class QuoteRecalcCallback implements SBQQ.CalculateCallback {

    global void onCalculated(String quoteModel) {
        try {
            SBQQ.ServiceRouter.save('QuoteSaver', quoteModel);
        } catch (Exception e) {
            // onCalculated errors are silent — log explicitly
            insert new CPQ_Calculation_Error__c(
                Quote_Model_Snippet__c = quoteModel.left(1000),
                Error_Message__c       = e.getMessage(),
                Stack_Trace__c         = e.getStackTraceString()
            );
        }
    }
}

// Step 2: Trigger async calculation from batch or trigger context
public class RecalcBatch implements Database.Batchable<SObject>, Database.AllowsCallouts {

    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator(
            'SELECT Id FROM SBQQ__Quote__c WHERE SBQQ__Status__c = \'Draft\''
        );
    }

    public void execute(Database.BatchableContext bc, List<SBQQ__Quote__c> quotes) {
        for (SBQQ__Quote__c q : quotes) {
            SBQQ.ServiceRouter.calculateInBackground(q.Id, new QuoteRecalcCallback());
        }
    }

    public void finish(Database.BatchableContext bc) {}
}
```

**Why it works:** `calculateInBackground` enqueues a CPQ-managed queueable job that runs the pricing engine outside the calling transaction. This sidesteps the CPU limit in the batch execute method. The `CalculateCallback.onCalculated` receives the fully calculated model and saves it. The explicit try/catch in `onCalculated` captures failures that would otherwise disappear silently.

---

## Example 3: Contract Amendment via API

**Context:** A customer service process needs to add a product to an existing active contract without opening the CPQ UI. The contract is already activated and has existing subscriptions.

**Problem:** The team inserts a new `SBQQ__Subscription__c` record directly on the contract. The amendment quote is never created, the change is not versioned, and the renewal process later fails because the subscription model is inconsistent.

**Solution:**

```apex
public class ContractAmendmentService {

    public static Id amendContract(Id contractId, Id newProductId) {
        // Step 1: Validate contract is activated
        Contract c = [SELECT SBQQ__Status__c FROM Contract WHERE Id = :contractId];
        if (c.SBQQ__Status__c != 'Activated') {
            throw new IllegalStateException(
                'Contract must be Activated before amendment. Current status: ' + c.SBQQ__Status__c
            );
        }

        // Step 2: Load the amendment model (creates an amendment quote model)
        String amendModel = SBQQ.ServiceRouter.read('ContractAmender', contractId);

        // Step 3: Load the new product and add it to the amendment quote model
        String productModel = SBQQ.ServiceRouter.read('ProductLoader', newProductId);
        String addPayload = '{"quote":' + amendModel + ',"products":[' + productModel + ']}';
        String updatedModel = SBQQ.ServiceRouter.save('QuoteProductAdder', addPayload);

        // Step 4: Calculate and save
        String calculatedModel = SBQQ.ServiceRouter.save('QuoteCalculator', updatedModel);
        SBQQ.ServiceRouter.save('QuoteSaver', calculatedModel);

        // Step 5: Extract the new quote Id from the saved model for downstream use
        Map<String, Object> modelMap =
            (Map<String, Object>) JSON.deserializeUntyped(calculatedModel);
        Map<String, Object> record = (Map<String, Object>) modelMap.get('record');
        return (Id) record.get('Id');
    }
}
```

**Why it works:** `ContractAmender` produces a properly structured amendment quote that is delta-aware — it knows which subscriptions already exist on the contract and only adds the new product as a new line. The resulting amendment quote is version-controlled by CPQ and feeds correctly into future renewal and contracting flows.

---

## Anti-Pattern: Direct DML on SBQQ__QuoteLine__c for Pricing Fields

**What practitioners do:** To update a discount on a quote line from Apex, they run:

```apex
SBQQ__QuoteLine__c line = [SELECT Id FROM SBQQ__QuoteLine__c WHERE Id = :lineId];
line.SBQQ__Discount__c = 15;
update line;
```

**What goes wrong:** The `update` DML writes the discount to the database but does not trigger the CPQ pricing engine. `SBQQ__NetPrice__c`, `SBQQ__CustomerPrice__c`, `SBQQ__PartnerPrice__c`, `SBQQ__RegularTotal__c`, and the quote header total fields (`SBQQ__NetTotal__c`, `SBQQ__GrossTotal__c`) all remain at their previous values. The quote is now financially inconsistent. When the user next opens the quote in the CPQ UI and saves, CPQ recalculates and may overwrite the 15% discount with the engine's own result — or apply it and produce totals that differ from what the integration intended.

**Correct approach:** Read the quote model via `QuoteReader`, parse the JSON to find the target line, set the discount field in the model, pass the modified model to `QuoteCalculator`, then save via `QuoteSaver`. All fields are then calculated consistently by the pricing engine.
