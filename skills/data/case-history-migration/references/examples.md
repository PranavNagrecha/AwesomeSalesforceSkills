# Examples — Case History Migration

## Example 1: Migrating Case Emails from Zendesk with Attachments

**Context:** A company is cutting over from Zendesk to Salesforce Service Cloud. They have 120,000 tickets (Cases), each with an average of 6 email messages and 1.2 file attachments. The business requires the full email timeline and attached files to be visible on each Case record in Salesforce.

**Problem:** Without this skill's guidance, a practitioner might:
- Set `EmailMessage.Status = '3'` (Sent) on all outbound emails, permanently locking 400,000 records
- Attempt to insert ContentDocumentLink via Bulk API 2.0, causing silent failures where no files appear on Cases
- Miss the EmailMessageRelation step, resulting in emails that display in the timeline but have no linked Contacts

**Solution:**

```python
# Step 1: Load Cases via Bulk API 2.0
# CSV columns: Legacy_Case_Id__c, Subject, Description, Status, Priority,
#              AccountId, ContactId, OwnerId, CreatedDate

# Step 2: Load CaseComments
# CSV columns: ParentId (= Case.Legacy_Case_Id__c cross-ref), CommentBody,
#              IsPublished, CreatedDate, CreatedById

# Step 3: Load EmailMessages — NOTE: Status must NOT be '3'
# CSV columns: ParentId, Subject, TextBody, HtmlBody, FromAddress, ToAddress,
#              MessageDate, Status, Incoming
# Status mapping:
#   inbound emails  → Status = '1' (Read)
#   outbound emails → Status = '2' (Replied)

# Step 4: Load EmailMessageRelation
# CSV columns: EmailMessageId, RelationId (ContactId or UserId), RelationAddress,
#              RelationObjectType ('Contact', 'User', 'Lead'), Type ('toAddress', 'ccAddress')

# Step 5: Load ContentVersion via Bulk API 2.0
# CSV columns: Title, PathOnClient, VersionData (base64), FirstPublishLocationId (CaseId)

# Step 6: Query ContentDocumentId for each inserted ContentVersion
import csv, json

def query_content_document_ids(sf_session, version_ids: list[str]) -> dict[str, str]:
    """Return {ContentVersionId: ContentDocumentId} for inserted versions."""
    id_list = "', '".join(version_ids)
    soql = f"SELECT Id, ContentDocumentId FROM ContentVersion WHERE Id IN ('{id_list}')"
    result = sf_session.query(soql)
    return {row['Id']: row['ContentDocumentId'] for row in result['records']}

# Step 7: Insert ContentDocumentLink via REST API (NOT Bulk API)
import urllib.request

def insert_content_document_link(instance_url: str, access_token: str,
                                  content_document_id: str, linked_entity_id: str,
                                  share_type: str = 'V') -> dict:
    """Insert a single ContentDocumentLink via REST API."""
    url = f"{instance_url}/services/data/v62.0/sobjects/ContentDocumentLink"
    payload = json.dumps({
        "ContentDocumentId": content_document_id,
        "LinkedEntityId": linked_entity_id,
        "ShareType": share_type
    }).encode()
    req = urllib.request.Request(url, data=payload, method='POST')
    req.add_header('Authorization', f'Bearer {access_token}')
    req.add_header('Content-Type', 'application/json')
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())
```

**Why it works:** Each object is inserted in strict dependency order. EmailMessage Status values are set to '1' and '2' to avoid the permanent locking behavior of Status='3'. ContentDocumentLink uses the REST API because Bulk API 2.0 does not support it. EmailMessageRelation is explicitly loaded to create Contact linkage from the raw address strings on EmailMessage.

---

## Example 2: Preserving CaseHistory Audit Trail via Task Records

**Context:** A company migrating from ServiceNow has a full audit log of case status changes, owner reassignments, and priority escalations. The business wants to see this history in Salesforce. A junior developer assumes CaseHistory is insertable like OpportunityHistory workarounds.

**Problem:** Attempting to insert CaseHistory directly:

```
POST /services/data/v62.0/sobjects/CaseHistory
→ 400 Bad Request
{
  "errorCode": "INVALID_TYPE_FOR_OPERATION",
  "message": "entity type Case History does not support create"
}
```

This error is permanent — there is no permission, setting, or API flag that enables direct CaseHistory inserts.

**Solution:**

```python
# For each historical field-change event in the source audit log,
# create a Task record on the Case.

# CSV columns for Task load:
# WhatId (= Case.Legacy_Case_Id__c cross-ref), Subject, ActivityDate, Status,
# Description, OwnerId

# Example row:
# WhatId: Case.Legacy_Case_Id__c = "ZD-10045"
# Subject: "Historical Change: Status New → In Progress"
# ActivityDate: 2024-03-15
# Status: Completed
# Description: "Changed by john.smith@example.com on 2024-03-15. Previous: New. New: In Progress."
# OwnerId: <Salesforce UserId of john.smith>

# For high-volume audit logs (500,000+ rows), load via Bulk API 2.0:
# Tasks support Bulk API 2.0 and can be loaded at full throughput.
# WhatId cross-reference: Case.Legacy_Case_Id__c resolves without pre-querying Case Ids.

def build_task_rows_from_audit_log(audit_rows: list[dict]) -> list[dict]:
    """Convert source audit log rows to Salesforce Task CSV rows."""
    task_rows = []
    for row in audit_rows:
        task_rows.append({
            "WhatId": f"Case.Legacy_Case_Id__c={row['legacy_case_id']}",
            "Subject": f"Historical Change: {row['field']} {row['old_value']} → {row['new_value']}",
            "ActivityDate": row['changed_at'][:10],  # YYYY-MM-DD
            "Status": "Completed",
            "Description": (
                f"Field: {row['field']} | "
                f"Old: {row['old_value']} | "
                f"New: {row['new_value']} | "
                f"Changed by: {row['changed_by']} | "
                f"Source system: {row['source']}"
            ),
            "OwnerId": row['salesforce_user_id'],
        })
    return task_rows
```

**Why it works:** Tasks are insertable via Bulk API 2.0, support WhatId cross-references for parent resolution, appear in the Case activity timeline in the Salesforce UI, and are reportable via SOQL. The audit information is preserved in queryable form even though CaseHistory itself is not insertable.

---

## Anti-Pattern: Setting EmailMessage Status='3' (Sent) on Historical Emails

**What practitioners do:** Export outbound emails from the legacy system and map the status directly. The legacy system's "Sent" status maps to Salesforce's `Status='3'` (Sent). The practitioner loads 200,000 EmailMessage records with `Status='3'`.

**What goes wrong:** Every one of those 200,000 EmailMessage records is now permanently locked. They cannot be updated (to fix incorrect FromAddress values), cannot be deleted (to remove test data), and cannot be re-linked. The Salesforce UI shows them as read-only. There is no API call, no permission set, and no Salesforce Support escalation path that unlocks a Status='3' EmailMessage — the records must be re-migrated from scratch using a data recovery process.

**Correct approach:** Use `Status='1'` (Read) for inbound emails and `Status='2'` (Replied) for outbound emails during migration. Status='3' should only be used when Salesforce itself sends an email via the `sendEmail` API or the Case email UI — it marks delivery confirmation. It has no safe use case in a data migration context.
