# LLM Anti-Patterns — Banking and Lending Architecture

Common mistakes AI coding assistants make when generating or advising on Banking and Lending Architecture.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Digital Lending Without Confirming OmniStudio

**What the LLM generates:** Architecture recommendations that include FSC Digital Lending OmniScripts, FlexCards, and Integration Procedures without noting the OmniStudio licensing dependency.

**Why it happens:** LLMs present Digital Lending as a feature of FSC because documentation often discusses them together. The separate OmniStudio licensing requirement is not always prominent in overview documentation.

**Correct pattern:**

```text
Before recommending Digital Lending:
1. Confirm OmniStudio is licensed in the target org
2. Confirm industriesdigitallending namespace is accessible
3. If OmniStudio is NOT available, recommend custom Screen Flow + ResidentialLoanApplication
   without the Digital Lending platform layer
```

**Detection hint:** Any Digital Lending recommendation that does not include an OmniStudio prerequisite confirmation step should be flagged.

---

## Anti-Pattern 2: Synchronous Apex Payment Processing

**What the LLM generates:** Apex trigger code that initiates a payment callout to an external payment processor API synchronously when a Payment or Transaction record is inserted or updated.

**Why it happens:** Synchronous Apex HTTP callouts are the most common Salesforce external integration pattern in training data. LLMs apply this pattern by default without understanding payment processing governor limits and latency requirements.

**Correct pattern:**

```apex
// WRONG: synchronous callout in trigger
trigger PaymentTrigger on Payment__c (after insert) {
    Http h = new Http();
    HttpRequest req = new HttpRequest();
    req.setEndpoint('callout:PaymentProcessor/initiate');
    // This hits the 100-callout limit in bulk and fails on processor latency
    HttpResponse resp = h.send(req);
}

// CORRECT: enqueue async job or use Integration Procedure
// Integration Procedure via OmniStudio (recommended for Digital Lending orgs)
// OR Queueable Apex for non-OmniStudio orgs:
public class PaymentCalloutQueueable implements Queueable, Database.AllowsCallouts {
    public void execute(QueueableContext ctx) {
        // Make callout here — outside transaction context, safe from 100-callout limit
    }
}
```

**Detection hint:** Any `HttpRequest` or `Http.send()` call inside a trigger class is a payment architecture anti-pattern flag.

---

## Anti-Pattern 3: Using ResidentialLoanApplication for Post-Close Loan Servicing

**What the LLM generates:** Data model designs that extend ResidentialLoanApplication with custom fields for balance tracking, payment history, statement dates, and interest accrual to manage serviced loans.

**Why it happens:** ResidentialLoanApplication is the most prominent FSC lending object in documentation. LLMs extend it for the full loan lifecycle without knowing that FinancialAccount (Liability type) is the correct post-close representation in FSC.

**Correct pattern:**

```text
Loan Lifecycle Object Mapping:
Application → funding:  ResidentialLoanApplication (and child objects)
Post-close servicing:   FinancialAccount (subtype: Mortgage, Personal Loan, etc.)

On loan close/funding:
- Create FinancialAccount (Liability type) record
- Link to borrower Account and household
- This enables FSC Banker summary views and household net worth calculations
- ResidentialLoanApplication status transitions to Closed/Funded
```

**Detection hint:** Any architecture that stores loan balance, payment history, or interest information on ResidentialLoanApplication custom fields should be flagged for FinancialAccount review.

---

## Anti-Pattern 4: Omitting loanApplicantAutoCreation Flag in Integration Design

**What the LLM generates:** Integration designs or data migration scripts that insert LoanApplicant records without mentioning the `loanApplicantAutoCreation` IndustriesSettings flag or explicitly creating the linked Person Account.

**Why it happens:** The `loanApplicantAutoCreation` flag is an IndustriesSettings configuration item that does not appear in standard object documentation. LLMs are unaware of it and generate LoanApplicant insert patterns that assume automatic Account creation.

**Correct pattern:**

```text
Before inserting LoanApplicant records:
1. Confirm IndustriesSettings.loanApplicantAutoCreation = true
   OR
2. Explicitly create Person Account records first and link via ApplicantId

SOQL to verify after load:
SELECT COUNT() FROM LoanApplicant WHERE ApplicantId = null
-- Result should be 0 if auto-creation is working or manual linking is complete
```

**Detection hint:** Any LoanApplicant insertion pattern that does not reference `loanApplicantAutoCreation` or explicit Person Account creation is a flag.

---

## Anti-Pattern 5: Designing Core Banking as Real-Time Bidirectional Sync

**What the LLM generates:** Integration architecture that specifies real-time bidirectional synchronization between Salesforce and the core banking system for all loan and account data, using REST API calls triggered by record changes on both sides.

**Why it happens:** Real-time bidirectional sync is a common integration goal stated in requirements. LLMs propose this without understanding the data volume, conflict resolution complexity, and governor limit implications for banking-scale data.

**Correct pattern:**

```text
Recommended banking integration patterns (from Salesforce Integration Architecture guide):

High-volume account data: Batch Data Synchronization (Bulk API 2.0, scheduled nightly)
Real-time payment status: Remote Call-In (core banking calls SF REST API for status updates)
Loan origination submission: Remote Process Invocation - Request and Reply (synchronous)
Balance/transaction history: Batch Data Synchronization (not real-time; daily/hourly refresh)

Avoid true bidirectional real-time sync — it creates conflict resolution requirements
that neither Salesforce nor the core banking system is designed to handle at scale.
```

**Detection hint:** Any architecture diagram showing two-way real-time arrows between Salesforce and a core banking system should be reviewed for pattern appropriateness and conflict resolution design.
