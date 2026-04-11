# LLM Anti-Patterns — NPSP Data Model

Common mistakes AI coding assistants make when generating or advising on NPSP Data Model.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Collapsing All NPSP Namespaces to npsp__

**What the LLM generates:**

```soql
SELECT Id, npsp__Amount__c FROM npsp__OppPayment__c WHERE npsp__Opportunity__c = :oppId
```

Or in Apex:

```apex
List<npsp__OppPayment__c> payments = [SELECT Id FROM npsp__OppPayment__c];
```

**Why it happens:** NPSP is marketed under the "npsp" brand name and the LLM's training data contains many references to "npsp objects" without distinguishing which sub-package owns each object. The model generalizes the brand name to a namespace prefix, which is only correct for GAU/Allocation objects.

**Correct pattern:**

```soql
-- Payments use npe01__ namespace, not npsp__
SELECT Id, npe01__Payment_Amount__c, npe01__Payment_Date__c
FROM npe01__OppPayment__c
WHERE npe01__Opportunity__c = :oppId
```

**Detection hint:** Any NPSP query or Apex class that uses `npsp__OppPayment__c`, `npsp__Recurring_Donation__c`, `npsp__Relationship__c`, or `npsp__Affiliation__c` contains a namespace error. Only `npsp__Allocation__c` and `npsp__General_Accounting_Unit__c` correctly use the `npsp__` prefix.

---

## Anti-Pattern 2: Creating Installment Opportunities Without a Parent Recurring Donation

**What the LLM generates:**

```apex
// Creating a monthly donation installment
Opportunity inst = new Opportunity(
    Name = 'Monthly Gift - March 2025',
    AccountId = contactAcctId,
    Amount = 100,
    StageName = 'Pledged',
    CloseDate = Date.newInstance(2025, 3, 31),
    RecordTypeId = donationRtId
);
insert inst;
```

**Why it happens:** The LLM treats NPSP installment Opportunities as standard Opportunities and generates a clean insert without referencing the recurring donation parent. This appears valid because the Opportunity object itself does not require the NPSP lookup field.

**Correct pattern:**

```apex
// Always create the parent recurring donation first
npe03__Recurring_Donation__c rd = new npe03__Recurring_Donation__c(
    Name = 'Monthly Gift - Jane Doe',
    npe03__Contact__c = contactId,
    npe03__Amount__c = 100,
    npe03__Installment_Period__c = 'Monthly',
    npe03__Date_Established__c = Date.today(),
    npe03__Open_Ended_Status__c = 'Open'
);
insert rd;
// NPSP will auto-generate the installment Opportunities
// OR set the lookup explicitly if creating installments programmatically:
Opportunity inst = new Opportunity(
    Name = 'Monthly Gift - March 2025',
    AccountId = contactAcctId,
    Amount = 100,
    StageName = 'Pledged',
    CloseDate = Date.newInstance(2025, 3, 31),
    RecordTypeId = donationRtId,
    npe03__Recurring_Donation__c = rd.Id  // required for rollup integrity
);
insert inst;
```

**Detection hint:** Any Opportunity insert or Data Loader import for installment Opportunities that does not include a `npe03__Recurring_Donation__c` field mapping should be flagged for review.

---

## Anti-Pattern 3: Assuming GAU Allocations Are a Child Relationship of Opportunity (Master-Detail)

**What the LLM generates:**

```soql
-- Incorrect: tries to traverse from Opportunity as if allocation is a master-detail child
SELECT Id, (SELECT npsp__Amount__c FROM npsp__Allocations__r)
FROM Opportunity
WHERE Id = :oppId
```

**Why it happens:** The LLM knows that NPSP allocations relate to Opportunities and assumes the relationship is a standard master-detail (which supports subquery traversal from the parent). Training data on Salesforce relationship queries reinforces this pattern for master-detail objects.

**Correct pattern:**

```soql
-- Correct: query allocation directly, filter by Opportunity ID
SELECT Id, npsp__Amount__c, npsp__Percent__c,
       npsp__General_Accounting_Unit__r.Name,
       npsp__Opportunity__c
FROM npsp__Allocation__c
WHERE npsp__Opportunity__c = :oppId
```

**Detection hint:** Any SOQL query from Opportunity that includes a subquery referencing allocations, or that references a relationship name like `Allocations__r` or `npsp__Allocations__r`, is using the wrong pattern.

---

## Anti-Pattern 4: Deleting Opportunities Without Handling GAU Allocations

**What the LLM generates:**

```apex
// Bulk delete opportunities
delete [SELECT Id FROM Opportunity WHERE StageName = 'Cancelled'];
```

**Why it happens:** Standard Salesforce delete patterns do not require pre-deletion of child records when those records are in a lookup relationship. The LLM applies the general pattern without knowing that NPSP allocations are lookup-related (not cascade-deleted) and that orphaned allocations corrupt GAU reporting.

**Correct pattern:**

```apex
List<Opportunity> oppsToDelete = [
    SELECT Id FROM Opportunity WHERE StageName = 'Cancelled'
];
Set<Id> oppIds = new Map<Id, Opportunity>(oppsToDelete).keySet();

// Delete allocations first to prevent orphans
List<npsp__Allocation__c> allocs = [
    SELECT Id FROM npsp__Allocation__c
    WHERE npsp__Opportunity__c IN :oppIds
];
if (!allocs.isEmpty()) {
    delete allocs;
}
delete oppsToDelete;
```

**Detection hint:** Any Apex or script that deletes Opportunity records in an NPSP org without a preceding query and delete (or explicit null-out) of `npsp__Allocation__c` records should be flagged.

---

## Anti-Pattern 5: Using npe4__ and npe5__ Interchangeably for Relationships and Affiliations

**What the LLM generates:**

```apex
// Trying to find a Contact's organizational affiliations
List<npe4__Relationship__c> affiliations = [
    SELECT Id, npe4__Contact__c, npe4__RelatedContact__c
    FROM npe4__Relationship__c
    WHERE npe4__Contact__c = :contactId
];
```

**Why it happens:** The LLM conflates "relationship" (contact-to-contact) with "affiliation" (contact-to-account). Both are NPSP junction-like objects and the LLM guesses at the namespace without distinguishing the two concepts.

**Correct pattern:**

```apex
// npe4__Relationship__c = Contact-to-Contact relationship (e.g., Spouse, Colleague)
List<npe4__Relationship__c> relationships = [
    SELECT Id, npe4__Contact__c, npe4__RelatedContact__c, npe4__Type__c
    FROM npe4__Relationship__c
    WHERE npe4__Contact__c = :contactId
];

// npe5__Affiliation__c = Contact-to-Account affiliation (e.g., employer, board member)
List<npe5__Affiliation__c> affiliations = [
    SELECT Id, npe5__Contact__c, npe5__Account__c, npe5__Role__c, npe5__Primary__c
    FROM npe5__Affiliation__c
    WHERE npe5__Contact__c = :contactId
];
```

**Detection hint:** Any code that uses `npe4__Relationship__c` to find a Contact's organizational affiliations (Account linkages) or uses `npe5__Affiliation__c` to find Contact-to-Contact relationships has the objects swapped. The namespace suffix is a reliable indicator: `npe4__` = person-to-person, `npe5__` = person-to-organization.

---

## Anti-Pattern 6: Using npo02__ for Household Rollup Fields When the Skill Scope Is Payments or Recurring Donations

**What the LLM generates:**

```apex
// Checking total donations on a contact — mixing up namespace contexts
Contact c = [SELECT Id, npsp__TotalOppAmount__c FROM Contact WHERE Id = :contactId];
```

**Why it happens:** NPSP rollup fields on Contact are actually in the `npo02__` namespace (the Households package), not `npsp__`. The LLM defaults to `npsp__` because that is the brand prefix, missing that household summary fields belong to a sixth related namespace.

**Correct pattern:**

```apex
// Household rollup fields on Contact use the npo02__ namespace
Contact c = [
    SELECT Id,
           npo02__TotalOppAmount__c,
           npo02__TotalMembershipOppAmount__c,
           npo02__LastOppAmount__c
    FROM Contact
    WHERE Id = :contactId
];
```

**Detection hint:** Any reference to `npsp__TotalOppAmount__c`, `npsp__LastOppAmount__c`, or similar giving-summary fields on Contact should be checked against the actual namespace — household summary fields use `npo02__`, not `npsp__`.
