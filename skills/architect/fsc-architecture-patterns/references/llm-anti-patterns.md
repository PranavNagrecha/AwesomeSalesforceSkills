# LLM Anti-Patterns — FSC Architecture Patterns

Common mistakes AI coding assistants make when generating or advising on FSC architecture. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Conflating Compliant Data Sharing with Standard Sharing Rules

**What the LLM generates:** When asked how to control which FSC advisors can see which financial accounts, the LLM recommends designing criteria-based sharing rules (e.g., "create a sharing rule that shares FinancialAccount records owned by a user to all users in the same role"). It may acknowledge FSC exists but treat the sharing problem as a generic Salesforce sharing problem.

**Why it happens:** Standard Salesforce sharing rules are heavily represented in training data. CDS is an FSC-specific framework with a smaller documentation footprint. LLMs default to the more common pattern and miss the FSC-specific mechanism even when the context clearly involves FSC.

**Correct pattern:**

```
For FSC financial record access control:
1. Enable Compliant Data Sharing in FSC Settings
2. Set FinancialAccount OWD to Private
3. Use FinancialAccountRole records to track advisor-client relationships
4. Configure CDS share sets to grant access based on active FinancialAccountRole records
5. Do NOT use criteria-based sharing rules as the primary financial account access control
```

**Detection hint:** If the output contains "criteria-based sharing rule" or "sharing rule" as the primary recommendation for FSC financial account visibility without also mentioning "Compliant Data Sharing" or "FinancialAccountRole," flag it for review.

---

## Anti-Pattern 2: Ignoring the Managed-Package vs. Platform-Native Distinction

**What the LLM generates:** Code examples and SOQL queries that reference `FinServ__FinancialAccount__c`, `FinServ__FinancialHolding__c`, and other namespaced objects regardless of whether the target org uses platform-native FSC. The LLM applies the managed-package namespace universally because it is more prevalent in its training data.

**Why it happens:** The managed-package FSC model has years of documentation, community forum posts, and code samples that predate the platform-native model's Winter '23 introduction. LLMs trained on pre-2023 data or on a corpus weighted toward older FSC implementations will default to the `FinServ__` namespace.

**Correct pattern:**

```
// Managed-package FSC (FinServ__ namespace) — pre-Winter '23 or legacy orgs
List<FinServ__FinancialAccount__c> accounts = [
    SELECT Id, FinServ__FinancialAccountNumber__c, FinServ__Balance__c
    FROM FinServ__FinancialAccount__c
    WHERE FinServ__PrimaryOwner__c = :clientId
];

// Platform-native FSC (no namespace) — greenfield post-Winter '23
List<FinancialAccount> accounts = [
    SELECT Id, FinancialAccountNumber, Balance
    FROM FinancialAccount
    WHERE PrimaryOwner.Id = :clientId
];
```

**Detection hint:** If the generated SOQL or Apex contains `FinServ__` namespace prefixes and the context is a post-Winter '23 implementation or an org described as platform-native, the answer is wrong.

---

## Anti-Pattern 3: Recommending Synchronous Callouts to Core Banking from Record Save Events

**What the LLM generates:** Apex trigger code that performs a synchronous `HttpRequest` callout to a core banking API inside `after insert` or `after update` on `FinancialAccount`. The intent is to fetch the latest balance or validate an account number against the banking system in real time during the record save.

**Why it happens:** Synchronous Apex callouts are the most commonly documented integration pattern. LLMs default to them when asked for "real-time" integration without considering the Salesforce callout limits (100 per transaction, 120-second timeout) or the implications of coupling the record save transaction to an external system's availability.

**Correct pattern:**

```apex
// WRONG: synchronous callout from trigger
trigger FinancialAccountTrigger on FinancialAccount (after insert) {
    for (FinancialAccount fa : Trigger.new) {
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:CoreBanking/accounts/' + fa.FinancialAccountNumber);
        // ... this couples every save to core banking availability
    }
}

// CORRECT: publish Platform Event from trigger, subscriber handles callout async
trigger FinancialAccountTrigger on FinancialAccount (after insert) {
    List<BankingSync__e> events = new List<BankingSync__e>();
    for (FinancialAccount fa : Trigger.new) {
        events.add(new BankingSync__e(
            FinancialAccountId__c = fa.Id,
            Action__c = 'VALIDATE'
        ));
    }
    EventBus.publish(events);
}
```

**Detection hint:** Look for `HttpRequest`, `Http.send()`, or named credential callout patterns inside trigger or Flow contexts on FSC objects. Any synchronous callout on a record save event for a financial account should be flagged.

---

## Anti-Pattern 4: Treating FSC CDS Activation as Sufficient Without OWD Verification

**What the LLM generates:** Instructions that tell the user to enable Compliant Data Sharing in FSC Settings, configure share sets, and assign `FinancialAccountRole` records — and declare the sharing model complete. The LLM omits the critical step of setting the OWD for `FinancialAccount` to Private.

**Why it happens:** CDS activation and share-set configuration are the visible FSC-specific steps. OWD is a separate, platform-level setting that applies across all objects. LLMs that describe CDS as a self-contained feature omit the prerequisite OWD configuration because it lives outside the FSC Settings context.

**Correct pattern:**

```
CDS activation checklist (in order):
1. Navigate to Setup > Sharing Settings
2. Set FinancialAccount OWD to Private (required before CDS is meaningful)
3. Navigate to Setup > Financial Services > FSC Settings > Sharing
4. Enable Compliant Data Sharing
5. Configure share sets targeting FinancialAccountRole-based access
6. Validate: create a test user with no FinancialAccountRole records
             confirm they see zero FinancialAccount records
```

**Detection hint:** If CDS configuration instructions do not mention OWD or do not include a validation step confirming that a user with no `FinancialAccountRole` records cannot see any financial accounts, the guidance is incomplete.

---

## Anti-Pattern 5: Recommending Person Account Disablement as a Remediation Step

**What the LLM generates:** When an FSC org has data quality issues or structural problems with client records, the LLM suggests "disabling Person Accounts and restructuring the data model to use standard Contacts." It presents this as a clean-up option without flagging that this is impossible once Person Account records exist and that the attempt will be blocked by the platform.

**Why it happens:** Person Account disablement is a valid platform operation when no Person Account records exist. LLMs that have seen documentation for the disablement process may apply it generically without checking the precondition.

**Correct pattern:**

```
Person Account disablement is blocked by Salesforce when Person Account records exist.
There is no supported in-place migration from Person Account to standard Contact + Account.

If the data model must change:
- Export all Person Account records
- Create a new org configured with standard Contacts (no Person Accounts)
- Transform and re-import all client data
- Re-configure all FSC features, integrations, and automations

This is a full re-implementation project, not a configuration change.
Do not suggest Person Account disablement to a live FSC org with existing client records.
```

**Detection hint:** If the output contains "disable Person Accounts" or "switch to standard Contacts" as a remediation step for an FSC org that already has client records, it is incorrect.

---

## Anti-Pattern 6: Omitting the Rollup Batch from FSC Household Architecture Designs

**What the LLM generates:** An FSC household architecture design that describes household-level KPIs (Total AUM, total financial goals) as real-time computed values — either via roll-up summary fields or formula fields — without mentioning the FSC rollup batch engine or its asynchronous characteristics.

**Why it happens:** Standard Salesforce roll-up summary fields update synchronously on parent records. LLMs apply this mental model to FSC household aggregates, not recognizing that FSC household rollups use a separate asynchronous batch mechanism with configurable schedules.

**Correct pattern:**

```
FSC Household Rollups are NOT synchronous roll-up summary fields.

They are populated by the FSC Rollup Batch Engine:
- Must be scheduled explicitly in FSC Settings > Rollup Settings
- Updates run asynchronously on the configured schedule (e.g., nightly)
- Rollup fields show the value from the last successful batch run
- If the batch fails, fields show stale data with no platform alert

Architecture implications:
- Do not commit to real-time household KPI SLAs (e.g., "dashboard refreshes instantly on trade")
- Include rollup batch schedule and monitoring in the operational runbook
- Supplement with reporting snapshots for historical household performance analysis
```

**Detection hint:** If an FSC architecture design describes household aggregates (Total AUM, Net Worth) as "real-time" or computes them via formula fields or standard roll-up summaries without mentioning the FSC rollup batch, the design is technically incorrect.
