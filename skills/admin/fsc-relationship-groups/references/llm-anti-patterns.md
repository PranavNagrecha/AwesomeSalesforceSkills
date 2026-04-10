# LLM Anti-Patterns — FSC Relationship Groups

Common mistakes AI coding assistants make when generating or advising on FSC Relationship Groups.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Conflating Adding a Member to a Group with Setting That Group as Primary

**What the LLM generates:** Instructions or Apex code that create an ACR record to add a Person Account to a Household or Trust group, but omit setting `FinServ__PrimaryGroup__c = true`. The generated code treats ACR creation as the complete membership step without acknowledging that rollup aggregation requires the primary group designation.

**Why it happens:** LLMs trained on general Salesforce documentation understand ACR as a membership junction but may not have sufficient weight on the FSC-specific semantic that "member of a group" and "primary group member eligible for rollups" are separate concepts. Generic CRM training data does not include this FSC-specific distinction.

**Correct pattern:**

```apex
// WRONG — member is added but assets will NOT roll up to the group
AccountContactRelation acr = new AccountContactRelation(
    AccountId = householdId,
    ContactId = personAccount.PersonContactId
    // FinServ__PrimaryGroup__c omitted — defaults to false
    // FinServ__IncludeInGroup__c omitted — defaults to false
);

// CORRECT — all three FSC fields set explicitly
AccountContactRelation acr = new AccountContactRelation(
    AccountId = householdId,
    ContactId = personAccount.PersonContactId,
    FinServ__PrimaryGroup__c = true,
    FinServ__Primary__c = false,
    FinServ__IncludeInGroup__c = true
);
```

**Detection hint:** Search generated Apex for `AccountContactRelation` inserts that do not include both `FinServ__PrimaryGroup__c` and `FinServ__IncludeInGroup__c` in the field assignment list.

---

## Anti-Pattern 2: Using Account.Id Instead of Account.PersonContactId in ACR ContactId

**What the LLM generates:** Apex or SOQL that queries Person Accounts and uses `Account.Id` directly as the `ContactId` field in an ACR record insert. The generated code treats the Person Account's Account Id as a valid Contact Id.

**Why it happens:** LLMs understand that ACR has a `ContactId` field and that Person Accounts are Account records, but frequently conflate the Account Id and the underlying auto-created Contact Id. Training data on standard Account-Contact relationships reinforces the incorrect pattern because in non-Person Account orgs, `Account.Id` is always distinct from `Contact.AccountId`, but the Person Account `PersonContactId` field is a less-common concept.

**Correct pattern:**

```apex
// WRONG — uses Account.Id for ContactId; will fail or create a malformed ACR
Account pa = [SELECT Id FROM Account WHERE IsPersonAccount = true AND Name = 'Alice Chen' LIMIT 1];
AccountContactRelation acr = new AccountContactRelation(
    AccountId = householdId,
    ContactId = pa.Id  // WRONG — this is the Account Id, not the Contact Id
);

// CORRECT — queries PersonContactId explicitly
Account pa = [SELECT Id, PersonContactId FROM Account WHERE IsPersonAccount = true AND Name = 'Alice Chen' LIMIT 1];
AccountContactRelation acr = new AccountContactRelation(
    AccountId = householdId,
    ContactId = pa.PersonContactId  // CORRECT — underlying Contact Id for the Person Account
);
```

**Detection hint:** Flag any ACR insert where `ContactId` is set from an Account SOQL query that does not include `PersonContactId` in the SELECT clause.

---

## Anti-Pattern 3: Assuming FSC Enforces One-Primary-Group-Per-Member Without a Validation Rule

**What the LLM generates:** Code or instructions that set `FinServ__PrimaryGroup__c = true` on a new group ACR for a client who already belongs to another group, without first clearing the existing primary group designation. The LLM may state "Salesforce will prevent you from having two primary groups" or generate code that does not include a check for existing primary group ACRs.

**Why it happens:** LLMs generalize from Salesforce patterns where uniqueness constraints are platform-enforced (e.g., duplicate rules, unique field settings). The FSC primary group constraint is a data integrity expectation, not a platform validation. There is no out-of-box duplicate rule or unique field that enforces it, so LLMs that have not been fine-tuned on FSC-specific behavior will assume the platform handles it.

**Correct pattern:**

```apex
// WRONG — sets PrimaryGroup = true on new ACR without checking existing primary
AccountContactRelation newGroupAcr = new AccountContactRelation(
    AccountId = newGroupId,
    ContactId = personContactId,
    FinServ__PrimaryGroup__c = true  // Dangerous if existing primary group ACR exists
);
insert newGroupAcr;

// CORRECT — clear existing primary group designation first
List<AccountContactRelation> existingPrimary = [
    SELECT Id FROM AccountContactRelation
    WHERE ContactId = :personContactId
    AND FinServ__PrimaryGroup__c = true
    AND AccountId != :newGroupId
];
for (AccountContactRelation existing : existingPrimary) {
    existing.FinServ__PrimaryGroup__c = false;
}
update existingPrimary;

AccountContactRelation newGroupAcr = new AccountContactRelation(
    AccountId = newGroupId,
    ContactId = personContactId,
    FinServ__PrimaryGroup__c = true,
    FinServ__Primary__c = false,
    FinServ__IncludeInGroup__c = true
);
insert newGroupAcr;
```

**Detection hint:** Look for ACR inserts with `FinServ__PrimaryGroup__c = true` that are not preceded by a SOQL query checking for existing primary group ACRs for the same `ContactId`.

---

## Anti-Pattern 4: Treating All Three FSC Record Types as Equivalent Containers

**What the LLM generates:** Instructions to use a Household record type for a Trust or Professional Group scenario, or to freely swap record types based on availability rather than use case. The LLM may say "just use the Household type — it's the same structure" or generate code that creates a Trust group using the Household record type because it is known to be active in the org.

**Why it happens:** LLMs see that all three group types are Account records and infer that the record type is purely cosmetic. Training data on Account record types in other clouds reinforces this — in Sales Cloud, record types on Account are often used for simple categorization without functional consequences. In FSC, the record type determines which Lightning components, page layouts, and financial planning features are available on the group record.

**Correct pattern:**

```
// WRONG — using Household record type for a trust
Account trust = new Account(
    Name = 'Smith Family Trust',
    RecordTypeId = [SELECT Id FROM RecordType WHERE SobjectType = 'Account' AND Name = 'Household' LIMIT 1].Id
);

// CORRECT — use the Trust record type for a trust entity
Account trust = new Account(
    Name = 'Smith Family Trust',
    RecordTypeId = [SELECT Id FROM RecordType WHERE SobjectType = 'Account' AND Name = 'Trust' LIMIT 1].Id
);
```

**Detection hint:** Flag any generated Account insert intended for a trust or business entity that uses the `Household` record type. Check whether the record type name matches the intended group type.

---

## Anti-Pattern 5: Omitting FinServ__IncludeInGroup__c from Programmatic ACR Creation

**What the LLM generates:** Apex, Flow configuration, or Data Loader instructions that create ACR records with `FinServ__PrimaryGroup__c = true` but omit `FinServ__IncludeInGroup__c`. The LLM treats `FinServ__PrimaryGroup__c` as sufficient for rollup inclusion and does not mention `FinServ__IncludeInGroup__c`.

**Why it happens:** The name `FinServ__PrimaryGroup__c` suggests it is the main switch for group behavior, and LLMs tend to focus on the most prominent or descriptive field name. `FinServ__IncludeInGroup__c` has a less obvious name and its role as a separate rollup gate is an FSC-specific nuance not obvious from field naming alone.

**Correct pattern:**

```apex
// WRONG — PrimaryGroup is set but IncludeInGroup is omitted; assets excluded from rollups
AccountContactRelation acr = new AccountContactRelation(
    AccountId = householdId,
    ContactId = personContactId,
    FinServ__PrimaryGroup__c = true,
    FinServ__Primary__c = true
    // FinServ__IncludeInGroup__c not set — defaults to false
    // Member appears in household but zero financial data rolls up
);

// CORRECT — all three fields explicitly set
AccountContactRelation acr = new AccountContactRelation(
    AccountId = householdId,
    ContactId = personContactId,
    FinServ__PrimaryGroup__c = true,
    FinServ__Primary__c = true,
    FinServ__IncludeInGroup__c = true  // Required for rollup inclusion
);
```

**Detection hint:** Any ACR insert that sets `FinServ__PrimaryGroup__c = true` without also setting `FinServ__IncludeInGroup__c = true` should be flagged as potentially missing rollup inclusion.

---

## Anti-Pattern 6: Advising a Custom Object Instead of an FSC Relationship Group Record Type

**What the LLM generates:** Recommendations to create a custom object (e.g., `RelationshipGroup__c` or `ClientGroup__c`) to model group relationships, with custom lookup fields back to Account. The LLM may suggest this as a more flexible or "cleaner" approach than using Account record types.

**Why it happens:** LLMs trained on general Salesforce architecture patterns learn that custom objects are often used for many-to-many relationships. In non-FSC orgs, this would be the correct pattern. The LLM does not weight the FSC-specific consequence that custom group objects are invisible to the FSC rollup engine, FSC Lightning components, FSC dashboards, and financial planning features.

**Correct pattern:**

```
// WRONG — custom object bypasses FSC rollup engine and Lightning components
RelationshipGroup__c customGroup = new RelationshipGroup__c(Name = 'Smith Household');
insert customGroup;
// No FSC rollup, no FSC Group Members panel, no FSC Financial Summary component

// CORRECT — Account with FSC record type
Account household = new Account(
    Name = 'Smith Household',
    RecordTypeId = [SELECT Id FROM RecordType WHERE SobjectType = 'Account' AND Name = 'Household' LIMIT 1].Id
);
insert household;
// All FSC components, rollups, and relationship panels work correctly
```

**Detection hint:** Any generated solution that introduces a new custom object for grouping FSC clients should be flagged. Check whether the proposed design uses Account with an FSC record type or a custom object.
