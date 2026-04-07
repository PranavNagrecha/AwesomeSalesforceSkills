# LLM Anti-Patterns — Financial Account Setup

Common mistakes AI coding assistants make when generating or advising on FSC Financial Account configuration.
These patterns help the consuming agent self-check its own output.

---

## Anti-Pattern 1: Confusing FSC FinancialAccount with the Standard Account Object

**What the LLM generates:** Advice or SOQL that queries `Account` when the question is about financial account balances, account types, or holdings. For example:

```soql
-- Wrong: treating Account as the financial account record
SELECT Id, Name, AnnualRevenue FROM Account WHERE AccountType__c = 'Brokerage'
```

**Why it happens:** LLMs are trained on vastly more standard Salesforce content (Account, Contact, Opportunity) than FSC-specific content. When a user asks about "financial accounts," the LLM associates the word "account" with the standard Account object. The `AnnualRevenue` field is further evidence of conflation — that field has nothing to do with FSC financial account balances.

**Correct pattern:**

```soql
-- Correct: managed-package FSC org
SELECT Id, Name, FinServ__Balance__c, FinServ__FinancialAccountType__c
FROM FinServ__FinancialAccount__c
WHERE FinServ__PrimaryOwner__c = :accountId

-- Correct: Core FSC org (Winter '23+)
SELECT Id, Name, Balance, FinancialAccountType
FROM FinancialAccount
WHERE PrimaryOwner.Id = :accountId
```

**Detection hint:** Flag any answer to an FSC financial account question that references the standard `Account` object, `AnnualRevenue`, or `AccountType` (standard field). These are hallmarks of standard Account conflation.

---

## Anti-Pattern 2: Using Wrong API Names for Managed-Package vs Core FSC

**What the LLM generates:** SOQL, Apex, or Flow field references that mix namespaced and non-namespaced API names:

```apex
// Wrong: mixing namespace and no-namespace in managed-package context
FinServ__FinancialAccount__c fa = new FinServ__FinancialAccount__c();
fa.Balance__c = 10000; // WRONG — should be FinServ__Balance__c in managed-package
fa.PrimaryOwner__c = contactId; // WRONG — should be FinServ__PrimaryOwner__c
```

**Why it happens:** LLMs inconsistently apply or omit the `FinServ__` namespace prefix because training data includes both managed-package and Core FSC examples interleaved without clear labeling of which model applies.

**Correct pattern:**

```apex
// Managed-package org — ALL fields use FinServ__ prefix
FinServ__FinancialAccount__c fa = new FinServ__FinancialAccount__c();
fa.FinServ__Balance__c = 10000;
fa.FinServ__PrimaryOwner__c = contactId;
fa.FinServ__FinancialAccountType__c = 'Individual Brokerage';

// Core FSC org (Winter '23+) — NO namespace prefix
FinancialAccount fa = new FinancialAccount();
fa.Balance = 10000;
fa.PrimaryOwnerId = contactId;
fa.FinancialAccountType = 'Individual Brokerage';
```

**Detection hint:** Any code that uses `FinServ__FinancialAccount__c` (managed-package object name) but then references fields without the `FinServ__` prefix is broken. Flag mismatches between the object name namespace and the field name namespace.

---

## Anti-Pattern 3: Skipping FinancialAccountRole Records and Relying Only on PrimaryOwner Lookup

**What the LLM generates:** Code or setup instructions that create `FinancialAccount` records and populate only the `FinServ__PrimaryOwner__c` lookup field, without creating any `FinancialAccountRole` child records:

```apex
// Wrong: only setting PrimaryOwner lookup — rollup will NOT work
FinServ__FinancialAccount__c fa = new FinServ__FinancialAccount__c(
    Name = 'Chen Brokerage',
    FinServ__PrimaryOwner__c = contactId,
    FinServ__Balance__c = 50000
);
insert fa;
// Missing: FinancialAccountRole creation
```

**Why it happens:** The `FinServ__PrimaryOwner__c` field name sounds like it should be sufficient to designate ownership. LLMs do not know that the FSC rollup engine reads from the separate `FinancialAccountRole` junction object, not from this lookup field.

**Correct pattern:**

```apex
// Correct: create FinancialAccount AND FinancialAccountRole
FinServ__FinancialAccount__c fa = new FinServ__FinancialAccount__c(
    Name = 'Chen Brokerage',
    FinServ__PrimaryOwner__c = contactId,
    FinServ__Balance__c = 50000,
    FinServ__FinancialAccountType__c = 'Individual Brokerage'
);
insert fa;

FinServ__FinancialAccountRole__c role = new FinServ__FinancialAccountRole__c(
    FinServ__FinancialAccount__c = fa.Id,
    FinServ__RelatedAccount__c = contactId,
    FinServ__Role__c = 'Primary Owner',
    FinServ__Active__c = true
);
insert role;
```

**Detection hint:** Any FSC financial account setup code that does not include creation of at least one `FinancialAccountRole` record with `Role = Primary Owner` is incomplete. Flag answers that show only `FinancialAccount` DML without the corresponding role record.

---

## Anti-Pattern 4: Assuming Cross-Household Joint Owner Rollup Works Out of the Box

**What the LLM generates:** Configuration advice stating that creating a `FinancialAccountRole` record with `Role = Joint Owner` for a person in a different household will automatically roll the balance up to that person's household.

**Why it happens:** The concept of "joint account ownership" implies both owners should see the account. LLMs generalize from this expectation and do not know the FSC rollup engine's technical boundary at the Primary Owner's household.

**Correct pattern:**

```
FSC managed-package rollup behavior:
- Balance rolls up ONLY to the Primary Owner's household (PrimaryGroup__c)
- Joint Owners in the SAME household also see the balance (shared household record)
- Joint Owners in a DIFFERENT household do NOT receive a rollup — their household balance is understated

For cross-household joint owner visibility, a custom solution is required:
- Add a custom currency field to the Household object (e.g., Custom_JointAccountBalance__c)
- Implement a Record-Triggered Flow or scheduled Apex that writes the balance
  to the Joint Owner's household after each update to FinancialAccount
- Do NOT write to the managed package's native rollup fields (FinServ__TotalBalance__c)
```

**Detection hint:** Any answer claiming "FSC will automatically include joint owner balances in both households" is incorrect for managed-package FSC. Flag this claim as a hallucinated capability.

---

## Anti-Pattern 5: Recommending Deletion of Picklist Values That Are in Use on Existing Records

**What the LLM generates:** Instructions to clean up the `FinancialAccountType` picklist by deleting old or duplicate values:

```
Steps:
1. Go to Setup > Object Manager > FinancialAccount > Fields > FinancialAccountType
2. Find the old value "Individual IRA"
3. Click Delete to remove it
```

**Why it happens:** LLMs give generic picklist cleanup instructions without accounting for the Salesforce behavior of deleting in-use picklist values. The standard pattern for picklist cleanup in other contexts (unused values) is to delete them, but FSC financial account types are almost always in active use on existing records.

**Correct pattern:**

```
Never delete a FinancialAccountType picklist value that may be in use on existing records.
Use the Replace workflow instead:

1. Go to Setup > Object Manager > FinancialAccount > Fields > FinancialAccountType
2. Click Edit next to the value you want to remove
3. Use "Replace" to migrate all existing records to the new value
4. Run a report to confirm 0 records still hold the old value
5. Only then remove the now-unused old value

This prevents records from being left in an indeterminate state where the
stored value no longer exists in the picklist definition.
```

**Detection hint:** Any answer that says "click Delete" on a picklist value without first checking record usage or recommending the Replace workflow is potentially destructive. Flag picklist deletion instructions that do not include record-usage verification.

---

## Anti-Pattern 6: Ignoring the FSC Rollup Batch Requirement After Bulk Data Loads

**What the LLM generates:** Bulk data load instructions (Data Loader, API) for `FinancialAccount` records followed by instructions to immediately verify household balance rollup totals in the UI — without mentioning the need to run the FSC rollup batch first.

**Why it happens:** In standard Salesforce, some calculations update in real time via triggers or formula fields. LLMs do not know that FSC household rollup is batch-driven and does not fire automatically on record insert via the API.

**Correct pattern:**

```
After any bulk insert or update of FinancialAccount records via Data Loader or API:

1. Complete the data load
2. Navigate to Setup > Financial Services > Run Account Rollup (or equivalent in FSC Admin app)
   — OR — schedule the rollup batch to run immediately after the load window
3. Wait for the batch to complete (Apex Jobs page)
4. Only then verify household rollup fields in the UI

Do not validate household balance totals immediately after a bulk API load —
the rollup batch has not run yet and figures will be stale or zero.
```

**Detection hint:** Any bulk FSC data load procedure that moves directly from "load records" to "verify household totals" without a step to trigger the rollup batch is missing a critical step.
