# Examples — Sales Cloud Integration Patterns

## Example 1: Bidirectional Account Sync with ERP Using External ID Upsert

**Context:** A manufacturing company uses SAP as the ERP system of record for billing addresses and payment terms. Salesforce owns account ownership, territory, and engagement data. Both systems need a complete Account view.

**Problem:** Without field-level mastery, each sync overwrites the other system's changes. A nightly ERP sync replaces the account owner that a sales rep just updated. Sales data disappears.

**Solution:**

```apex
// Inbound sync from ERP — only updates ERP-mastered fields
public class ERPAccountInboundSync {

    public static void syncAccounts(List<ERP_Account_Payload> payloads) {
        List<Account> toUpsert = new List<Account>();

        for (ERP_Account_Payload p : payloads) {
            Account a = new Account();
            a.ERP_Account_ID__c = p.erpAccountId;  // External ID for upsert
            // Only ERP-mastered fields
            a.BillingStreet = p.billingStreet;
            a.BillingCity = p.billingCity;
            a.BillingState = p.billingState;
            a.BillingPostalCode = p.billingPostalCode;
            a.BillingCountry = p.billingCountry;
            a.Payment_Terms__c = p.paymentTerms;
            a.Tax_ID__c = p.taxId;
            // DO NOT set OwnerId, Territory__c, or any SF-mastered field
            toUpsert.add(a);
        }

        IntegrationContext.isInbound = true; // Prevent outbound re-trigger
        Database.UpsertResult[] results = Database.upsert(toUpsert, Account.ERP_Account_ID__c, false);
        IntegrationContext.isInbound = false;

        for (Database.UpsertResult r : results) {
            if (!r.isSuccess()) {
                IntegrationLogger.logFailure('ERP_Account_Inbound', r);
            }
        }
    }
}
```

**Why it works:** The External ID upsert eliminates a separate SOQL lookup. Setting `IntegrationContext.isInbound = true` before DML prevents the outbound trigger from firing, stopping the ping-pong loop. Only ERP-mastered fields are populated on the Account SObject, so Salesforce-owned data is never touched.

---

## Example 2: Marketing Lead Sync with Conversion Event Handling

**Context:** A B2B SaaS company uses HubSpot for marketing. Leads created by HubSpot are synced to Salesforce. When sales converts a Lead, HubSpot must switch its reference to the new Contact ID.

**Problem:** After conversion, HubSpot continues pushing updates to the Lead ID. Salesforce rejects these updates because converted Leads are read-only. HubSpot's sync queue fills with failures.

**Solution:**

```apex
// Trigger on Lead to detect conversion and notify marketing platform
trigger LeadConversionNotifier on Lead (after update) {
    List<Lead_Conversion_Event__e> events = new List<Lead_Conversion_Event__e>();

    for (Lead l : Trigger.new) {
        Lead oldLead = Trigger.oldMap.get(l.Id);
        if (l.IsConverted && !oldLead.IsConverted) {
            events.add(new Lead_Conversion_Event__e(
                Marketing_Lead_ID__c = l.Marketing_Lead_ID__c,
                Converted_Contact_ID__c = l.ConvertedContactId,
                Converted_Account_ID__c = l.ConvertedAccountId,
                Converted_Opportunity_ID__c = l.ConvertedOpportunityId
            ));
        }
    }

    if (!events.isEmpty()) {
        EventBus.publish(events);
    }
}
```

**Why it works:** A platform event fires the moment conversion happens, giving the marketing platform immediate notice of the new Contact ID. The event payload includes all three converted IDs so the external system can update all its references in one pass.

---

## Example 3: Quote-to-Order Outbound to ERP

**Context:** A distribution company uses standard Salesforce Quotes. When a quote is approved and an Order is created, the order must be transmitted to the ERP system for fulfillment.

**Problem:** Without a clear lifecycle gate, orders are sent to ERP before approval, or the integration sends the quote instead of the order, causing SKU and quantity mismatches.

**Solution:**

```apex
// Flow-invocable action to send activated Order to ERP
public class OrderToERPSender {

    @InvocableMethod(label='Send Order to ERP' description='Transmits activated Order to ERP')
    public static void sendOrders(List<Id> orderIds) {
        List<Order> orders = [
            SELECT Id, OrderNumber, AccountId, Account.ERP_Account_ID__c,
                   EffectiveDate, Status,
                   (SELECT Id, Product2.ProductCode, Quantity, UnitPrice,
                    Product2.ERP_Product_ID__c
                    FROM OrderItems)
            FROM Order
            WHERE Id IN :orderIds AND Status = 'Activated'
        ];

        for (Order o : orders) {
            ERPOrderPayload payload = new ERPOrderPayload();
            payload.sfOrderId = o.OrderNumber;
            payload.erpAccountId = o.Account.ERP_Account_ID__c;
            payload.effectiveDate = o.EffectiveDate;

            for (OrderItem oi : o.OrderItems) {
                ERPOrderLinePayload line = new ERPOrderLinePayload();
                line.erpSku = oi.Product2.ERP_Product_ID__c;
                line.quantity = oi.Quantity;
                line.unitPrice = oi.UnitPrice;
                payload.lines.add(line);
            }

            // Enqueue async callout to avoid mixed-DML in trigger context
            System.enqueueJob(new ERPCalloutQueueable(payload));
        }
    }
}
```

**Why it works:** The `WHERE Status = 'Activated'` filter ensures only finalized orders reach ERP. Using `Product2.ERP_Product_ID__c` maps Salesforce products to ERP SKUs via the External ID, eliminating ambiguity. The async Queueable pattern avoids callout-in-trigger limits.

---

## Anti-Pattern: Full-Record Overwrite on Bidirectional Sync

**What practitioners do:** Send the entire Account record from ERP to Salesforce, overwriting all fields including OwnerId, Territory, and custom sales engagement fields.

**What goes wrong:** Sales reps lose their account assignments. Territory rules break. Activity history appears to belong to the integration user. Pipeline reports become unreliable.

**Correct approach:** Define a field-mastery matrix before building the integration. Each inbound sync should populate only the fields owned by the source system. Use a dedicated field set or explicit field list in the upsert to enforce this boundary.
