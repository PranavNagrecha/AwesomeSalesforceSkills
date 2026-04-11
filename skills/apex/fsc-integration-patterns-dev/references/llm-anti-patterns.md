# LLM Anti-Patterns — FSC Integration Patterns Dev

Common mistakes AI coding assistants make when generating or advising on FSC integration patterns.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Placing Callouts Inside FinancialHolding Triggers

**What the LLM generates:** An `after update` trigger on `FinancialHolding` that calls `new Http().send(req)` to fetch updated market prices from an external vendor API immediately after the record is written.

**Why it happens:** The prompt asks for "real-time price updates" and the LLM defaults to the trigger pattern, which is the most common Salesforce event hook. The Apex callout-after-DML restriction is a runtime constraint, not a compile-time constraint, so the generated code looks syntactically correct and passes static analysis.

**Correct pattern:**

```apex
// WRONG — callout after DML in trigger
trigger FinancialHoldingTrigger on FinancialHolding (after update) {
    Http http = new Http();
    HttpRequest req = new HttpRequest();
    req.setEndpoint('callout:MarketData/prices');
    // This will throw CalloutException at runtime
    HttpResponse res = http.send(req);
}

// CORRECT — defer to Batchable with Database.AllowsCallouts
public class MarketDataPriceBatch implements Database.Batchable<SObject>, Database.AllowsCallouts {
    public void execute(Database.BatchableContext bc, List<FinancialHolding> scope) {
        // Callout is legal here — fresh transaction, no prior DML
        Map<String,Decimal> prices = MarketDataService.getPrices(scope);
        update scope;
    }
}
```

**Detection hint:** Search generated code for `Http` or `HttpRequest` inside a class that also has `trigger` in its file name, or inside any method that could be invoked synchronously from a DML context.

---

## Anti-Pattern 2: Not Disabling Rollup-by-Lookup Before Bulk FinancialHolding Loads

**What the LLM generates:** A Bulk API or Apex batch upsert of FinancialHolding records with no mention of Rollup-by-Lookup or Wealth Management Custom Settings. The generated code runs the load and immediately validates rollup totals.

**Why it happens:** RBL is an FSC-specific configuration concern that is absent from general Salesforce integration training data. LLMs are not aware of the FSC Wealth Management Custom Setting that controls it, so they generate generic bulk upsert patterns without this prerequisite.

**Correct pattern:**

```
Before any bulk FinancialHolding or FinancialAccount load:
1. Confirm FinServ__WealthAppConfig__c.FinServ__EnableRollups__c = false for the integration user
2. Run the Bulk API job to completion
3. Execute DPE recalculation after job reaches JobComplete state
4. Validate rollup totals against custodian snapshot
```

**Detection hint:** Any generated integration plan for FinancialHolding bulk loads that does not mention "Rollup-by-Lookup", "RBL", "WealthAppConfig", or "DPE" is missing this critical prerequisite.

---

## Anti-Pattern 3: Using the Wrong FSC Namespace in SOQL and DML

**What the LLM generates:** Apex code that hardcodes `FinServ__FinancialAccount__c` and `FinServ__FinancialHolding__c` everywhere, without acknowledging that Core FSC orgs use `FinancialAccount` and `FinancialHolding` (no namespace).

**Why it happens:** The managed-package FSC deployment was the dominant pattern for years and is heavily represented in training data. Core FSC (standard object deployment) is relatively new and less documented in public repositories. LLMs default to the managed-package namespace.

**Correct pattern:**

```apex
// At configuration time, detect the FSC deployment type:
Boolean isManagedPackage = Schema.getGlobalDescribe().containsKey('FinServ__FinancialAccount__c');
String faObjectName = isManagedPackage ? 'FinServ__FinancialAccount__c' : 'FinancialAccount';

// Use dynamic SOQL or a configuration constant, never hardcode a single namespace
String query = 'SELECT Id, Name FROM ' + faObjectName + ' LIMIT 10';
List<SObject> results = Database.query(query);
```

**Detection hint:** Any generated code that references `FinServ__` without a conditional namespace check or a comment acknowledging the Core FSC alternative is a potential namespace-mismatch bug.

---

## Anti-Pattern 4: Treating CDC as the Sole Inbound Custodian Data Mechanism

**What the LLM generates:** An architecture diagram or description where CDC on `FinancialAccountChangeEvent` is used to receive custodian position updates in real time, with no mention of a batch reconciliation backstop.

**Why it happens:** LLMs learn that CDC is Salesforce's event-driven change propagation mechanism and conflate outbound (Salesforce-to-external) and inbound (external-to-Salesforce) patterns. CDC is an outbound mechanism — it emits events when Salesforce records change. It does not receive events from external custodian systems.

**Correct pattern:**

```
Inbound custodian data: Bulk API 2.0 batch job (nightly) + FSC Integrations API Remote Call-In (real-time events)
Outbound Salesforce changes to downstream systems: CDC (FinancialAccountChangeEvent)

CDC does NOT ingest data from custodians. It emits Salesforce-side changes to external subscribers.
The 72-hour CDC event retention window makes it unsuitable as a sole reconciliation mechanism even for outbound replication.
```

**Detection hint:** Any architecture that uses CDC as an inbound data source from an external system (custodian, core banking) has the direction reversed.

---

## Anti-Pattern 5: Synchronous DML Upsert for Large FinancialHolding Loads Without Governor Limit Analysis

**What the LLM generates:** An Apex class that queries all FinancialHolding records to reconcile, then runs `upsert holdings;` in a loop or in a single DML statement, without considering the 10,000-row DML limit per transaction or the heap size limit.

**Why it happens:** LLMs generate the simplest working code first. For small test datasets (50–100 records) synchronous DML appears correct. The Bulk API is presented as an "optional optimization" rather than a hard requirement at scale.

**Correct pattern:**

```apex
// WRONG for large volumes
List<FinancialHolding> allHoldings = [SELECT Id, CurrentValue FROM FinancialHolding];
// upsert allHoldings; // Will hit 10,000 DML rows limit and heap limits at scale

// CORRECT: use Database.Batchable with appropriate scope
public class HoldingReconcileBatch implements Database.Batchable<SObject> {
    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator('SELECT Id, ExternalId__c, CurrentValue FROM FinancialHolding');
    }
    public void execute(Database.BatchableContext bc, List<FinancialHolding> scope) {
        // Scope of 200 keeps DML rows well within per-transaction limits
        upsert scope ExternalId__c;
    }
    public void finish(Database.BatchableContext bc) {}
}
```

**Detection hint:** Generated code that runs `upsert` or `Database.upsert` on a full query result without a `LIMIT` clause, or without being inside a `Batchable.execute()` method, is likely to hit governor limits at production scale.

---

## Anti-Pattern 6: Using Username/Password OAuth Flow for Integration Connected App

**What the LLM generates:** Integration code that authenticates to Salesforce using `grant_type=password` with a hardcoded integration username, password, and security token in the ETL or MuleSoft connector configuration.

**Why it happens:** Username/password OAuth flow is the simplest to demonstrate in documentation examples and tutorials. LLMs reproduce this pattern from those examples without flagging the security implications.

**Correct pattern:**

```
Use OAuth 2.0 JWT Bearer flow with a Connected App:
1. Generate an RSA key pair
2. Upload the public key to the Connected App certificate
3. The integration service signs a JWT assertion with the private key
4. Salesforce validates the assertion and issues an access token
5. No password or security token ever leaves the integration service

Store the private key in a secure secret manager (AWS Secrets Manager, Azure Key Vault, etc.)
Never store credentials in ETL configuration files, Apex code, or version control
```

**Detection hint:** Any integration configuration that contains `grant_type=password` or references `security_token` in connection settings is using the deprecated flow. Flag for replacement with JWT Bearer.
