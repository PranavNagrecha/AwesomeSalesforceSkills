# LLM Anti-Patterns — Historical Order Migration

Common mistakes AI coding assistants make when generating or advising on CPQ historical order migration.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Standard Bulk API 2.0 at Default Batch Size for CPQ Objects

**What the LLM generates:** "Use Bulk API 2.0 to load your SBQQ__Subscription__c records efficiently. Set the batch size to 200 or higher for best throughput. This will load all 10,000 records in about 50 batches."

**Why it happens:** LLMs are trained on general Salesforce data migration guidance where Bulk API 2.0 at high batch sizes is the correct and recommended approach. CPQ Legacy Data Upload is a narrow exception documented in CPQ-specific help articles that are less prevalent in general Salesforce training data. The LLM applies the general rule without recognizing the CPQ exception.

**Correct pattern:**

```text
For CPQ Legacy Data Upload, batch size must be 1 for all CPQ objects:
- SBQQ__Quote__c
- SBQQ__QuoteLine__c
- SBQQ__Subscription__c
- SBQQ__Asset__c

Use Salesforce REST API single-record inserts or Data Loader with batch size = 1.
Do NOT use Bulk API 2.0 default batch sizes for these objects.
```

**Detection hint:** Any recommendation that includes "Bulk API", "batch size 200", or "throughput optimization" in the context of CPQ Subscription or Asset loads should be treated as suspect. Check for explicit mention of batch size 1.

---

## Anti-Pattern 2: Omitting the Quote and Quote Line Load Steps

**What the LLM generates:** "For historical CPQ migration, load your Contracts first, then load SBQQ__Subscription__c records referencing the Contract IDs. This will establish the subscription records that CPQ needs for renewals."

**Why it happens:** The LLM focuses on the Subscription record as the obvious renewal-driving object and skips the Quote and Quote Line steps because they seem like optional historical artifacts. The relationship between the approved primary Quote and the Contract's renewal engine is not prominent in general CPQ documentation.

**Correct pattern:**

```text
Full required load sequence for CPQ Legacy Data Upload:
1. SBQQ__Quote__c (Status=Approved, Primary=true)
2. SBQQ__QuoteLine__c (references parent Quote)
3. Contract (SBQQ__Quote__c field populated)
4. SBQQ__Subscription__c (references Contract and Product)
5. SBQQ__Asset__c (if amendments required)

Skipping steps 1-2 produces Contracts without a linked approved Quote,
which causes the renewal engine to generate blank or incorrect renewal lines.
```

**Detection hint:** Any migration plan that lists Contract or Subscription as the first load step without first loading SBQQ__Quote__c is missing the required Quote anchor. Look for `SBQQ__Quote__c` in the load sequence before Contract.

---

## Anti-Pattern 3: Populating Both SBQQ__RootId__c and SBQQ__RevisedAsset__c on Asset Records

**What the LLM generates:** "To preserve the full amendment chain, populate both `SBQQ__RootId__c` with the original asset's ID and `SBQQ__RevisedAsset__c` with the previous version's ID. This gives CPQ both the root reference and the chain reference."

**Why it happens:** The LLM infers that providing more relationship information (both root and revised pointers) would help CPQ traverse the chain better. The mutual exclusivity constraint between these two fields on revised assets is counter-intuitive and not derivable from the field names alone.

**Correct pattern:**

```text
SBQQ__Asset__c field rules for Legacy Data Upload:

Original (root) asset:
  SBQQ__RootId__c: null (CPQ sets this to its own ID post-insert via trigger)
  SBQQ__RevisedAsset__c: null

Revised (amended) asset:
  SBQQ__RootId__c: null  ← MUST be null when RevisedAsset is populated
  SBQQ__RevisedAsset__c: <Id of asset being replaced by this revision>
```

**Detection hint:** Any code or CSV mapping that sets both `SBQQ__RootId__c` and `SBQQ__RevisedAsset__c` to non-null values on the same SBQQ__Asset__c record is incorrect. Search CSV mapping definitions for rows where both fields are non-empty.

---

## Anti-Pattern 4: Loading CPQ Quotes with Status = Draft for Historical Records

**What the LLM generates:** "Insert the historical SBQQ__Quote__c records with their original status values from the source system. If they were in Draft when the order was placed, insert them as Draft. The important data is on the Subscription records anyway."

**Why it happens:** The LLM treats the Quote status as a data accuracy concern (preserving the source value) rather than understanding that `Status = Approved` and `Primary = true` are technical requirements for CPQ's renewal engine to recognize the Quote, not workflow states.

**Correct pattern:**

```text
All historical SBQQ__Quote__c records for Legacy Data Upload must be:
  SBQQ__Status__c = Approved
  SBQQ__Primary__c = true

These are not workflow indicators — they are technical flags that CPQ's
renewal engine uses to identify the authoritative quote for a contract.
A Draft or non-Primary quote is invisible to the renewal engine.
```

**Detection hint:** Any CSV mapping for SBQQ__Quote__c that does not explicitly set `SBQQ__Status__c = Approved` and `SBQQ__Primary__c = true` for all historical load records is incorrect. Grep the CSV mapping spec for these fields.

---

## Anti-Pattern 5: Advising Legacy Data Upload for Asset-Based Renewal Orgs

**What the LLM generates:** "Use CPQ Legacy Data Upload to load your historical subscriptions and assets. This is the supported approach for all CPQ renewal models."

**Why it happens:** The LLM generalizes the Legacy Data Upload guidance to all CPQ orgs without recognizing the contract-based vs. asset-based renewal model distinction. The distinction is documented in CPQ-specific help articles that may not be prominent in training data.

**Correct pattern:**

```text
CPQ Legacy Data Upload applies ONLY to contract-based renewal model orgs.

Before recommending Legacy Data Upload, confirm:
  SELECT SBQQ__RenewalModel__c FROM SBQQ__CustomAction__c
  (or check CPQ Package Settings in Setup)

If RenewalModel = 'Contract Based': use Legacy Data Upload procedures.
If RenewalModel = 'Asset Based': do NOT use Legacy Data Upload procedures.
  Consult CPQ Asset-Based Renewal documentation for the correct migration approach.
```

**Detection hint:** Any Legacy Data Upload recommendation that does not first confirm the org's renewal model setting is incomplete. The renewal model check must be the first step in any CPQ historical migration workflow.

---

## Anti-Pattern 6: Forgetting to Disable CPQ Price and Product Rules Before Load

**What the LLM generates:** "Insert your SBQQ__Quote__c and SBQQ__QuoteLine__c records with the correct field values from your source system. The pricing data will be preserved as-is."

**Why it happens:** The LLM models the insert as a straightforward data operation where fields written to the CSV are the fields stored in the database. It does not account for the CPQ package automation that fires on every Quote and Quote Line save, potentially overwriting the loaded pricing values.

**Correct pattern:**

```text
Pre-load configuration steps (mandatory before any Quote or Quote Line insert):
1. CPQ Package Settings > Pricing and Calculation > Disable Background Pricing = true
2. CPQ Package Settings > Quote Line Editor > Disable Price Rules = true
3. Optionally: disable any CPQ-triggered Flows on SBQQ__Quote__c and SBQQ__QuoteLine__c

These must be re-enabled after all records are loaded and validated.
```

**Detection hint:** Any CPQ Legacy Data Upload plan that does not include a "disable CPQ rules" step before Quote and Quote Line insertion is missing a required pre-load configuration step. Look for explicit mention of price rule and product rule disablement.
