# Examples — File And Document Integration

## Example 1: REST Multipart File Upload with Record Linking

**Context:** An external case management system needs to attach PDF documents to Salesforce Case records via the REST API. Files range from 1 MB to 500 MB.

**Problem:** Without multipart upload, developers attempt base64 encoding which fails for files over 28 MB and wastes bandwidth for all file sizes. Without explicit record linking, uploaded files land in the user's personal file library with no connection to the Case.

**Solution:**

```bash
# Multipart REST upload with FirstPublishLocationId to auto-link to Case
curl -X POST "https://myinstance.salesforce.com/services/data/v63.0/sobjects/ContentVersion/" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: multipart/form-data; boundary=boundary_string" \
  --form 'entity_content={
    "Title": "Case_Resolution_Report",
    "PathOnClient": "Case_Resolution_Report.pdf",
    "FirstPublishLocationId": "500xx000000abcDEF"
  };type=application/json' \
  --form "VersionData=@/path/to/report.pdf;type=application/pdf"
```

```apex
// Apex equivalent for programmatic upload within Salesforce
ContentVersion cv = new ContentVersion();
cv.Title = 'Case_Resolution_Report';
cv.PathOnClient = 'Case_Resolution_Report.pdf';
cv.VersionData = fileBlob; // Blob from file source
cv.FirstPublishLocationId = caseId; // Links file to Case automatically
insert cv;

// If linking to additional records after insert:
ContentVersion inserted = [SELECT ContentDocumentId FROM ContentVersion WHERE Id = :cv.Id];
ContentDocumentLink cdl = new ContentDocumentLink();
cdl.ContentDocumentId = inserted.ContentDocumentId;
cdl.LinkedEntityId = additionalRecordId;
cdl.ShareType = 'V'; // Viewer access
insert cdl;
```

**Why it works:** Setting `FirstPublishLocationId` during insert eliminates the need for a separate ContentDocumentLink creation step. The multipart upload avoids the 33% base64 inflation, supporting files up to 2 GB. The ContentDocumentLink with explicit `ShareType` ensures correct access control when linking to additional records.

---

## Example 2: Asynchronous Virus Scanning on File Upload

**Context:** A financial services org requires all uploaded documents to be scanned for malware before they become accessible to users. The org uses ClamAV exposed via a REST endpoint behind a Named Credential.

**Problem:** Salesforce has no built-in virus scanning for CRM file uploads. Files uploaded by users or integrations are immediately accessible, creating a compliance gap. Attempting to scan synchronously in a trigger fails because callouts are prohibited in trigger execution context.

**Solution:**

```apex
// Trigger: fires after ContentVersion insert
trigger ContentVersionVirusScan on ContentVersion (after insert) {
    List<Id> newVersionIds = new List<Id>();
    for (ContentVersion cv : Trigger.new) {
        // Only scan new uploads, not version updates from scanning process
        if (cv.Scan_Status__c == null) {
            newVersionIds.add(cv.Id);
        }
    }
    if (!newVersionIds.isEmpty()) {
        System.enqueueJob(new VirusScanQueueable(newVersionIds));
    }
}

// Queueable: performs the actual scan callout
public class VirusScanQueueable implements Queueable, Database.AllowsCallouts {
    private List<Id> contentVersionIds;

    public VirusScanQueueable(List<Id> cvIds) {
        this.contentVersionIds = cvIds;
    }

    public void execute(QueueableContext ctx) {
        List<ContentVersion> versions = [
            SELECT Id, VersionData, Title, ContentDocumentId
            FROM ContentVersion
            WHERE Id IN :contentVersionIds
        ];

        for (ContentVersion cv : versions) {
            HttpRequest req = new HttpRequest();
            req.setEndpoint('callout:Virus_Scanner/scan');
            req.setMethod('POST');
            req.setBodyAsBlob(cv.VersionData);
            req.setTimeout(120000); // 2 minute timeout for large files

            HttpResponse res = new Http().send(req);

            if (res.getStatusCode() == 200) {
                Map<String, Object> result = (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
                Boolean isMalicious = (Boolean) result.get('malicious');

                if (isMalicious) {
                    // Quarantine: delete the file and notify security
                    ContentDocument doc = [SELECT Id FROM ContentDocument WHERE Id = :cv.ContentDocumentId];
                    delete doc; // Deletes all versions
                    // Send alert to security team via custom notification or email
                } else {
                    cv.Scan_Status__c = 'Clean';
                }
            } else {
                cv.Scan_Status__c = 'Scan_Failed';
            }
        }
        update versions;
    }
}
```

**Why it works:** The Queueable pattern allows HTTP callouts that are impossible in trigger context. The Named Credential (`Virus_Scanner`) handles authentication to the external scanning service without hardcoded credentials. The `Scan_Status__c` field provides visibility into scan state, and the null check in the trigger prevents recursive scanning when the status field is updated.

---

## Anti-Pattern: Using Attachment Object Instead of ContentVersion

**What practitioners do:** Developers familiar with older Salesforce APIs create `Attachment` records to store files on parent records, using `ParentId` and `Body` fields. Some integrations still target the Attachment object because legacy documentation or training materials reference it.

**What goes wrong:** The Attachment object is a legacy storage mechanism. It lacks versioning, sharing controls beyond the parent record, and modern file features like previews and file-level collaboration. Attachments do not appear in the Files tab or Lightning file components. Salesforce has progressively restricted Attachment functionality — new orgs default to ContentVersion, and migrating from Attachments to ContentVersion later requires data migration tooling. The Attachment object also has a lower per-record size limit (25 MB) compared to ContentVersion via REST multipart (2 GB).

**Correct approach:** Always use ContentVersion for new file storage. Create ContentDocumentLink records to associate files with parent records. If migrating from Attachments, use the Salesforce Content Migration tool or a custom batch Apex job to convert Attachment records to ContentVersion records with proper ContentDocumentLink wiring.
