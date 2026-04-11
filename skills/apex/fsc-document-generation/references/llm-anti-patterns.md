# LLM Anti-Patterns — FSC Document Generation

Common mistakes AI coding assistants make when generating or advising on FSC document generation workflows. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Claiming DocGen Is Fully Included with FSC Licensing and Needs No Additional Setup

**What the LLM generates:** "OmniStudio DocGen is included with your FSC Industries license — just enable it in Setup and start creating templates. No additional licenses are required."

**Why it happens:** LLMs correctly know that DocGen is bundled with the Industries license at the org level and incorrectly generalizes this to mean individual users need no further access grants. Training data on DocGen frequently describes the bundling without distinguishing the per-user permission set license requirement.

**Correct pattern:**

```
OmniStudio DocGen is provisioned at the org level with FSC Industries licensing, but
individual users require one of three separate permission set licenses:
- DocGen Designer: for users who author and edit templates
- DocGen User: for users who trigger document generation from the UI
- DocGen Runtime: for integration users running automated API/batch generation

Assign these via Setup → Permission Set Licenses → Assign Users. The Runtime license
is the most frequently missed, causing silent failures in automated batch jobs.
```

**Detection hint:** Any advice that says "no additional licenses" or "just enable DocGen" without mentioning permission set license assignment for DocGen Designer/User/Runtime is incorrect.

---

## Anti-Pattern 2: Recommending Document Builder for Financial Account Statements

**What the LLM generates:** Code or configuration using Salesforce Document Builder (the newer, simpler tool) to generate account statements, arguing it is the "modern replacement" for OmniStudio DocGen in FSC.

**Why it happens:** Document Builder GA'd in Winter '25 and LLMs trained on recent Salesforce releases treat it as the preferred document generation tool. The critical PCI DSS compliance exclusion for Document Builder is absent or underweighted in most training data.

**Correct pattern:**

```
Use OmniStudio DocGen for all FSC compliance documents (account statements, disclosures,
contracts). Document Builder is explicitly excluded from Salesforce's PCI DSS compliance
attestation (as of Winter '25). This makes it unsuitable for financial documents containing
regulated data.

Reserve Document Builder for non-compliance use cases: marketing letters, meeting agendas,
internal reports.
```

**Detection hint:** Any recommendation to use Document Builder (Setup → Document Builder, or the `ConnectApi.DocumentBuilder` namespace) for FSC account statements, client disclosures, or regulatory documents is an error.

---

## Anti-Pattern 3: Omitting AuthorizationFormConsent After DocGen Document Delivery

**What the LLM generates:** An OmniScript flow or Apex service that calls DocGen, stores the PDF as a ContentDocument, and sends an email — but contains no AuthorizationFormConsent write. The LLM considers the workflow complete.

**Why it happens:** LLMs understand DocGen as a document generation tool and understand ContentDocument storage as proof of existence. The FSC-specific compliance requirement to write an AuthorizationFormConsent record as the machine-readable delivery proof is not widely documented and is easily missed in training data.

**Correct pattern:**

```apex
// After DocGen generates and stores the PDF, always write the consent record:
AuthorizationFormConsent consent = new AuthorizationFormConsent(
    AuthorizationFormId = authorizationFormId,   // the versioned legal document form
    ConsentGiverId = contactId,
    Status = 'Agreed',
    ConsentGivenAt = Datetime.now()
);
insert consent;

// Link the PDF to the consent record for auditability
insert new ContentDocumentLink(
    ContentDocumentId = generatedPdfId,
    LinkedEntityId = consent.Id,
    ShareType = 'V',
    Visibility = 'AllUsers'
);
```

**Detection hint:** Any FSC disclosure or compliance document workflow that ends with `insert contentDocumentLink` (linking to the parent account or contact) without also inserting an `AuthorizationFormConsent` is incomplete from a FINRA/GDPR standpoint.

---

## Anti-Pattern 4: Running DocGen Batch Jobs Without Rate-Limit Handling

**What the LLM generates:** A `Database.Batchable` class that calls the DocGen API in the `execute()` method, parses the response as a success on any non-exception path, and has no handling for HTTP 429 (Too Many Requests) or 503 responses.

**Why it happens:** LLMs generate standard Apex callout patterns where a non-exception HTTP response is treated as success. The DocGen API's 1000 documents/hour hard cap and its silent failure mode (returning a 429/503 that Apex callout code often ignores) are not standard Apex platform behavior and are therefore missing from most LLM-generated batch job code.

**Correct pattern:**

```apex
HttpResponse res = http.send(req);
if (res.getStatusCode() == 429 || res.getStatusCode() == 503) {
    // Rate limited — log and schedule retry, do not treat as success
    DocGenRetryQueue__c retry = new DocGenRetryQueue__c(
        BatchId__c = batchId,
        AccountIds__c = JSON.serialize(chunkedIds),
        RetryAfter__c = Datetime.now().addHours(1)
    );
    insert retry;
    return;
}
if (res.getStatusCode() != 200 && res.getStatusCode() != 202) {
    throw new DocGenException('Unexpected DocGen API response: ' + res.getStatusCode());
}
```

**Detection hint:** Any DocGen callout that only checks `res.getStatusCode() == 200` or catches exceptions but ignores HTTP 429/503 is missing rate-limit handling. Look for absent retry queue logic in batch DocGen jobs processing more than 200 records.

---

## Anti-Pattern 5: Using OmniScript for Headless Batch Document Generation

**What the LLM generates:** An OmniScript configured as a "batch" document generation mechanism — suggesting it be invoked by a scheduled job or Apex trigger to generate documents for thousands of accounts without a user session.

**Why it happens:** LLMs correctly know OmniScripts can call DocGen and associate OmniScripts with "OmniStudio automation." They do not reliably distinguish between the interactive OmniScript engine (which requires a live user session) and the DocGen API (which supports headless server-side processing).

**Correct pattern:**

```
OmniScript requires a user session and renders in a browser UI context. It is not
designed for headless or batch invocation. For automated document generation:

- Use the DocGen REST API directly from Apex (Database.Batchable + Database.AllowsCallouts)
- Use the DocGen API via Integration Procedures (OmniStudio server-side automation)
- Do NOT attempt to invoke OmniScripts via Apex or scheduled jobs for batch document production

The Apex Batchable pattern with Database.AllowsCallouts is the correct architecture
for large-volume FSC statement runs.
```

**Detection hint:** Any batch architecture that references `OmniScriptController`, `OmniScriptSaveAction`, or attempts to instantiate an OmniScript programmatically from a scheduled Apex context for bulk document generation is using the wrong execution model.
