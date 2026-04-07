# LLM Anti-Patterns — Household Model Configuration

Common mistakes AI coding assistants make when generating or advising on FSC household model configuration. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Conflating FSC and NPSP Household Models

**What the LLM generates:** Instructions that mix FSC and NPSP household concepts — for example, advising the user to run NPSP's household naming batch in an FSC org, or suggesting that `Contact.AccountId` is the correct way to link members to an FSC household. Sometimes the LLM generates code that uses `npe01__One2OneContact__c` or other NPSP fields in an FSC context.

**Why it happens:** Both FSC and NPSP use the Account object for households, and both are high-traffic topics in training data. LLMs trained on Salesforce content frequently blend the two models because the surface vocabulary is similar ("household account," "primary contact," "member rollup"). NPSP appears more frequently in community content because it predates FSC, so NPSP patterns can dominate completions even when the prompt specifies FSC.

**Correct pattern:**

```
FSC household membership:
  - Junction object: AccountContactRelation (ACR)
  - Membership fields: FinServ__PrimaryGroup__c, FinServ__Primary__c, FinServ__IncludeInGroup__c
  - Rollup engine: FSC triggers + FinServ.RollupBatchJob
  - Member type: Person Accounts

NPSP household membership:
  - Direct lookup: Contact.AccountId (Contact belongs to Household Account)
  - Rollup engine: NPSP Rollup Summaries
  - Member type: standard Contacts

These models are INCOMPATIBLE. Never mix them in the same org.
```

**Detection hint:** Look for any reference to NPSP fields (`npe01__`, `npsp__`, `npo02__`) in an FSC context, or references to modifying `Contact.AccountId` directly to manage FSC household membership. Both are incorrect.

---

## Anti-Pattern 2: Using `Account.Id` Instead of `Account.PersonContactId` in ACR Creation

**What the LLM generates:** Apex that creates an `AccountContactRelation` and sets `ContactId = personAccount.Id`. This looks plausible because `Id` is the standard record identifier, but Person Accounts expose a Contact `Id` through a separate field.

**Why it happens:** The standard pattern for ACR creation uses `ContactId`, and `Id` is the most natural Apex field for record identification. LLMs do not reliably model the internal dual-object structure of Person Accounts, where a single record is simultaneously an Account and a Contact with distinct IDs for each.

**Correct pattern:**

```apex
// WRONG — uses Account.Id, which is the Account record Id, not the Contact Id
AccountContactRelation acr = new AccountContactRelation(
    AccountId = householdId,
    ContactId = personAccount.Id // INCORRECT
);

// CORRECT — uses Account.PersonContactId, the underlying Contact Id
Account pa = [SELECT Id, PersonContactId FROM Account WHERE Id = :personAccountId LIMIT 1];
AccountContactRelation acr = new AccountContactRelation(
    AccountId = householdId,
    ContactId = pa.PersonContactId // CORRECT
);
```

**Detection hint:** Look for ACR insert statements where `ContactId` is set directly from a Person Account query result using `.Id`. The correct field is always `.PersonContactId`.

---

## Anti-Pattern 3: Omitting `FinServ__IncludeInGroup__c = true` in Programmatic ACR Creation

**What the LLM generates:** Apex or Flow that creates ACR records with only `AccountId`, `ContactId`, `FinServ__PrimaryGroup__c`, and `FinServ__Primary__c` set — without including `FinServ__IncludeInGroup__c`. This creates syntactically valid ACR records that appear to represent household membership but exclude the member from all rollup calculations.

**Why it happens:** LLMs focus on the "relationship" fields (`PrimaryGroup`, `Primary`) as the semantically meaningful membership designators. `IncludeInGroup__c` reads like an optional flag, and its name does not convey that it gates the entire rollup system. Training data may show examples where it is omitted because the example was created via the FSC UI (which sets it automatically) and the generated code was written from schema inspection alone.

**Correct pattern:**

```apex
AccountContactRelation acr = new AccountContactRelation(
    AccountId = householdId,
    ContactId = pa.PersonContactId,
    FinServ__PrimaryGroup__c = true,
    FinServ__Primary__c = false,
    FinServ__IncludeInGroup__c = true  // REQUIRED — omitting this excludes member from all rollups
);
```

**Detection hint:** Any ACR creation code or Flow Create Record element that does not explicitly set `FinServ__IncludeInGroup__c`. Treat an absence of this field as a likely bug.

---

## Anti-Pattern 4: Assuming `Rollups__c` Picklist Is Complete Without Verification

**What the LLM generates:** Configuration instructions or troubleshooting guidance that assume the `Rollups__c` picklist is pre-populated with all needed values and jumps straight to checking ACR fields or triggers when rollups are missing. The LLM does not prompt the user to verify the picklist.

**Why it happens:** The `Rollups__c` picklist is an unusual pattern — it is a metadata configuration that controls trigger behavior without any visible error when values are absent. LLMs rarely encounter documentation about this picklist in isolation; they see it mentioned only in FSC-specific release notes or deep admin guides. The more common rollup troubleshooting path (check ACR fields, check triggers, check FLS) does not include picklist auditing.

**Correct pattern:**

```
Rollup troubleshooting checklist — check IN THIS ORDER:
1. Verify Rollups__c picklist has a value for the relevant object type
   (Setup > Object Manager > Account > Fields > Rollups__c > Values)
2. Verify ACR FinServ__IncludeInGroup__c = true for the affected member
3. Verify ACR FinServ__PrimaryGroup__c is set correctly
4. Check FLS — rollup fields visible to the user's profile
5. Run batch rollup job and recheck
```

**Detection hint:** Any FSC rollup troubleshooting response that does not mention the `Rollups__c` picklist as the first or second check is likely incomplete.

---

## Anti-Pattern 5: Recommending the Batch Rollup Job as Optional Infrastructure

**What the LLM generates:** Setup instructions that configure ACR membership and FSC household records correctly but describe the batch rollup job (`FinServ.RollupBatchJob`) as "optional" or "only needed for large data volumes." The LLM may not mention the batch job at all, implying that trigger-based rollups are sufficient for all scenarios.

**Why it happens:** Trigger-based rollups work correctly for most interactive UI use cases, and LLMs optimize for the common case. The importance of the batch job for recovery scenarios (bulk data loads, failed trigger transactions, retroactive ACR flag changes) is a nuanced operational concern that does not appear prominently in introductory FSC content.

**Correct pattern:**

```
The FSC batch rollup job is REQUIRED infrastructure for any production FSC deployment:
- Needed after any bulk data load (triggers do not fire reliably at bulk scale)
- Needed when FinServ__IncludeInGroup__c is toggled retroactively on existing ACR records
- Needed when Rollups__c picklist values are added to an existing org
- Should be scheduled to run nightly (minimum) in all production orgs

// Schedule the batch job (managed-package FSC)
System.schedule(
    'FSC Nightly Rollup',
    '0 0 2 * * ?',  // 2 AM nightly
    new FinServ.RollupBatchJobScheduler()
);
```

**Detection hint:** Any FSC household configuration guidance that does not include batch rollup job scheduling, or that describes it as optional, is incomplete for production use.

---

## Anti-Pattern 6: Generating `FinServ__Primary__c = true` for All Members Without Uniqueness Enforcement

**What the LLM generates:** Data migration scripts or bulk ACR creation code that sets `FinServ__Primary__c = true` for every ACR record, reasoning that "every member should be a primary member of their household."

**Why it happens:** The field name "Primary" suggests importance and the LLM may default to `true` as the "safer" or "more complete" value. The business rule that only one member per household can be primary is not enforced by platform validation, so the LLM does not see a constraint to respect.

**Correct pattern:**

```apex
// WRONG — sets Primary = true for every member
for (AccountContactRelation acr : acrList) {
    acr.FinServ__Primary__c = true; // Creates multiple "primary" members per household
}

// CORRECT — exactly one member per household has Primary = true
// Designate the primary member explicitly; default others to false
AccountContactRelation primaryMemberAcr = acrList[0]; // Business-determined primary
primaryMemberAcr.FinServ__Primary__c = true;

for (Integer i = 1; i < acrList.size(); i++) {
    acrList[i].FinServ__Primary__c = false;
}
```

**Detection hint:** Any bulk ACR creation or update that sets `FinServ__Primary__c = true` without conditional logic to identify and limit which member receives the `true` value.
