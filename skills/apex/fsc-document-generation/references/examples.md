# Examples — FSC Document Generation

## Example 1: Batch Account Statement Generation with DocGen API

**Context:** A wealth management firm runs monthly account statements for 15,000 Financial Accounts. Statements must be rendered as PDFs, linked to the FinancialAccount record, and distributed via Experience Cloud portal or mailed via a print vendor. The firm has FSC with Industries licensing and OmniStudio DocGen enabled.

**Problem:** Without a controlled batch architecture, a naive implementation would attempt to call the DocGen API for all 15,000 accounts in a single Apex job or OmniScript loop, immediately hitting the server-side 1000 documents/hour cap. Most documents would fail silently, the batch would complete with a misleading "success" status, and thousands of clients would not receive statements.

**Solution:**

```apex
// Schedulable entry point — runs nightly at 11 PM
public class StatementGenerationScheduler implements Schedulable {
    public void execute(SchedulableContext sc) {
        // Batch size of 200 respects DocGen API throughput and governor limits
        Database.executeBatch(new StatementGenerationBatch(), 200);
    }
}

// Batchable class — queries active financial accounts needing statements
public class StatementGenerationBatch implements Database.Batchable<SObject>, Database.AllowsCallouts {

    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator([
            SELECT Id, Name, OwnerId, PersonContactId__c, StatementPreference__c
            FROM FinancialAccount
            WHERE StatementPreference__c IN ('Portal', 'Mail')
            AND Status = 'Active'
        ]);
    }

    public void execute(Database.BatchableContext bc, List<FinancialAccount> accounts) {
        List<String> accountIds = new List<String>();
        for (FinancialAccount fa : accounts) {
            accountIds.add(fa.Id);
        }

        // Call DocGen API with chunked record IDs
        // Named credential 'OmniStudioDocGen' holds auth details
        String docGenTemplateId = Label.StatementDocGenTemplateId;
        DocGenApiService.submitBatch(docGenTemplateId, accountIds);
    }

    public void finish(Database.BatchableContext bc) {
        // Insert a StatementRun__c audit record for operations review
        insert new StatementRun__c(
            RunDate__c = Date.today(),
            Status__c = 'Completed',
            BatchJobId__c = bc.getJobId()
        );
    }
}
```

**Why it works:** Chunking at 200 accounts per batch execution means a 15,000-account run takes approximately 75 batch executions. With the 1000 docs/hour server cap, spreading across a nightly window (11 PM to 7 AM) comfortably accommodates the full volume. The `Database.AllowsCallouts` interface is required because the DocGen API call is an HTTP callout from Apex.

---

## Example 2: FINRA Disclosure Delivery with AuthorizationFormConsent Audit Trail

**Context:** A registered investment adviser must deliver Form ADV Part 2 to all clients annually and record proof of delivery to satisfy FINRA Rule 4511 record-keeping requirements. The workflow must store the delivered PDF, timestamp the delivery, and be queryable by compliance officers.

**Problem:** A DocGen-only implementation generates the PDF and stores it as a ContentDocument, but leaves no structured compliance record. If a FINRA auditor asks for proof that a specific client received the disclosure on a specific date, the ContentDocument alone (especially if it has been modified or versioned) is insufficient — there is no machine-readable `ConsentGivenAt` timestamp tied to a versioned AuthorizationForm record.

**Solution:**

```apex
// Called from OmniScript action after DocGen renders the PDF
public class DisclosureConsentService {

    public static void recordDisclosureDelivery(
        Id contactId,
        Id authorizationFormId,
        Id contentDocumentId,
        String deliveryMethod  // 'Email', 'Portal', 'InPerson'
    ) {
        // Look up the DataUseLegalBasis representing FINRA Rule 4511
        DataUseLegalBasis legalBasis = [
            SELECT Id FROM DataUseLegalBasis
            WHERE Name = 'FINRA Rule 4511 Annual Disclosure'
            LIMIT 1
        ];

        // Create AuthorizationFormConsent — the regulatory proof record
        AuthorizationFormConsent consent = new AuthorizationFormConsent(
            AuthorizationFormId = authorizationFormId,
            ConsentGiverId = contactId,
            Status = 'Agreed',
            ConsentGivenAt = Datetime.now(),
            AuthorizationFormDataUseId = null  // set if using data-use-specific form
        );
        insert consent;

        // Link the rendered PDF to the consent record via ContentDocumentLink
        insert new ContentDocumentLink(
            ContentDocumentId = contentDocumentId,
            LinkedEntityId = consent.Id,
            ShareType = 'V',
            Visibility = 'AllUsers'
        );

        // Log delivery method as a custom field for compliance reporting
        consent.DeliveryMethod__c = deliveryMethod;
        update consent;
    }
}
```

**Why it works:** The `AuthorizationFormConsent` record with `Status = 'Agreed'` and a `ConsentGivenAt` timestamp is the FSC data model's native representation of a completed regulatory disclosure. Linking the `ContentDocument` (the PDF) to the consent record via `ContentDocumentLink` means a compliance query can retrieve both the proof of delivery and the actual document in a single SOQL join, satisfying FINRA record-keeping requirements for the 6-year retention period.

---

## Anti-Pattern: Using Document Builder for Client Account Statements

**What practitioners do:** Choose Document Builder (available from Setup → Document Builder, GA Winter '25) because its drag-and-drop interface is faster to configure than OmniStudio DocGen. They build account statement templates, merge account data, and deliver PDFs to clients.

**What goes wrong:** Document Builder is explicitly excluded from Salesforce's PCI DSS compliance attestation. Account statements frequently contain information that is PCI-in-scope (partial card numbers, account routing details) or that regulatory bodies require be generated in a PCI-controlled environment. Using Document Builder for these documents creates a compliance gap that is difficult to remediate without rebuilding the entire template and delivery workflow in OmniStudio DocGen. The feature gap is not visible at template-build time — it only surfaces during a compliance audit or PCI QSA assessment.

**Correct approach:** Use OmniStudio DocGen for all compliance-sensitive FSC documents. Reserve Document Builder for non-compliance use cases such as branded marketing letters, meeting agendas, or internal reports where PCI/FINRA scope is not a concern.
