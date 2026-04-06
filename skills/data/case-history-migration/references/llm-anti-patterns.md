# LLM Anti-Patterns — Case History Migration

Common mistakes AI coding assistants make when generating or advising on Case History Migration.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Setting EmailMessage Status='3' for All Outbound Historical Emails

**What the LLM generates:**
```python
# LLM incorrectly maps source "Sent" status to Salesforce Status='3'
email_row = {
    "ParentId": case_id,
    "Subject": row['subject'],
    "TextBody": row['body'],
    "Status": "3",  # WRONG — permanently locks the record
    "Incoming": "false",
}
```

**Why it happens:** LLMs trained on Salesforce documentation learn that Status='3' means "Sent" and apply this directly as a status mapping, without recognizing that the Sent status has a destructive side effect (permanent read-only lock) that is only documented in caveats of the EmailMessage object reference.

**Correct pattern:**
```python
# Map source status to safe migration equivalents
STATUS_MAP = {
    "sent":     "2",  # Replied — safe for outbound historical emails
    "received": "1",  # Read — safe for inbound historical emails
    "draft":    "0",  # New — safe for draft emails
    # Never map to "3" (Sent) in a migration context
}
email_row["Status"] = STATUS_MAP.get(row['source_status'], "1")
```

**Detection hint:** Search generated code or CSVs for `Status.*=.*3` or `"Status": "3"` or `Status,3` in CSV column patterns.

---

## Anti-Pattern 2: Using Bulk API 2.0 for ContentDocumentLink

**What the LLM generates:**
```python
# LLM incorrectly uses Bulk API 2.0 for ContentDocumentLink
bulk_job = sf.bulk2.ContentDocumentLink.insert(
    [{"ContentDocumentId": doc_id, "LinkedEntityId": case_id, "ShareType": "V"}
     for doc_id, case_id in links]
)
```

**Why it happens:** LLMs generalize from patterns where Bulk API 2.0 works for most standard and custom objects. ContentDocumentLink is the only commonly used standard object that explicitly does not support Bulk API 2.0, and this restriction is often absent from the training context or drowned out by the general pattern.

**Correct pattern:**
```python
import urllib.request, json

def insert_cdl_rest(instance_url, token, content_doc_id, linked_entity_id):
    url = f"{instance_url}/services/data/v62.0/sobjects/ContentDocumentLink"
    data = json.dumps({
        "ContentDocumentId": content_doc_id,
        "LinkedEntityId": linked_entity_id,
        "ShareType": "V"
    }).encode()
    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('Authorization', f'Bearer {token}')
    req.add_header('Content-Type', 'application/json')
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())
```

**Detection hint:** Look for `bulk.*ContentDocumentLink` or `ContentDocumentLink.*bulk` or `sf.bulk2.ContentDocumentLink` in generated code.

---

## Anti-Pattern 3: Attempting to Insert CaseHistory Records Directly

**What the LLM generates:**
```python
# LLM incorrectly tries to insert CaseHistory
case_history_rows = [
    {"CaseId": case_id, "Field": "Status", "OldValue": "New", "NewValue": "In Progress", "CreatedDate": "2024-03-15"}
    for row in audit_log
]
sf.bulk2.CaseHistory.insert(case_history_rows)  # WRONG — will fail
```

**Why it happens:** Practitioners often ask "how do I migrate case history" and LLMs generate a direct insert pattern by analogy with insertable standard objects. The LLM knows CaseHistory exists as a queryable object and conflates read access with write access.

**Correct pattern:**
```python
# Approximate CaseHistory using Task records
task_rows = []
for row in audit_log:
    task_rows.append({
        "WhatId": f"Case.Legacy_Case_Id__c={row['legacy_case_id']}",
        "Subject": f"Historical Change: {row['field']} {row['old_val']} → {row['new_val']}",
        "ActivityDate": row['changed_at'][:10],
        "Status": "Completed",
        "Description": f"Migrated audit record. Field: {row['field']}",
    })
# Load task_rows via Bulk API 2.0 — Tasks are insertable
```

**Detection hint:** Look for `CaseHistory.*insert` or `sf.bulk.*CaseHistory` or `.insert(case_history` in generated code.

---

## Anti-Pattern 4: Skipping EmailMessageRelation and Expecting Auto-Linkage

**What the LLM generates:**
```python
# LLM loads EmailMessage and assumes ToAddress auto-links to Contact
email_row = {
    "ParentId": case_id,
    "ToAddress": "customer@example.com",  # LLM assumes this links to a Contact
    "FromAddress": "support@company.com",
    "Subject": row['subject'],
    "Status": "1",
}
# LLM does not generate EmailMessageRelation rows
```

**Why it happens:** The LLM sees `ToAddress` and `FromAddress` fields and assumes they are the linkage mechanism. The existence of a separate `EmailMessageRelation` junction object is not obvious from the EmailMessage field list alone, and LLMs trained on general CRM patterns assume address fields are the canonical relationship.

**Correct pattern:**
```python
# After loading EmailMessages, load EmailMessageRelation rows
emr_rows = []
for email_id, contact_id, address in email_contact_mapping:
    emr_rows.append({
        "EmailMessageId": email_id,
        "RelationId": contact_id,
        "RelationObjectType": "Contact",
        "RelationAddress": address,
        "Type": "toAddress",
    })
# Load emr_rows via Bulk API 2.0
```

**Detection hint:** If EmailMessage rows are generated without any corresponding EmailMessageRelation rows or queries, the linkage step has been skipped.

---

## Anti-Pattern 5: Pre-Building ContentDocumentLink Before ContentVersion Is Inserted

**What the LLM generates:**
```python
# LLM incorrectly tries to pre-build ContentDocumentLink in the same batch
rows = []
for file in files:
    cv_id = generate_external_id()  # LLM assumes it can pre-assign IDs
    rows.append({
        "ContentVersion": {"Title": file['name'], "VersionData": file['b64']},
        "ContentDocumentLink": {"ContentDocumentId": cv_id, "LinkedEntityId": file['case_id']}
    })
# WRONG — ContentDocumentId does not exist until ContentVersion is inserted
```

**Why it happens:** LLMs familiar with transactional insert patterns (e.g., insert parent and child in the same operation) apply this pattern to ContentVersion/ContentDocumentLink. They do not account for the fact that ContentDocument is auto-created by Salesforce at ContentVersion insert time and its Id is only resolvable via a subsequent query.

**Correct pattern:**
```python
# Step 1: Insert ContentVersion via Bulk API 2.0
cv_ids = bulk_insert_content_versions(files)

# Step 2: Query auto-created ContentDocumentId values
id_map = query_content_document_ids(sf_session, cv_ids)
# id_map = {ContentVersionId: ContentDocumentId}

# Step 3: Build ContentDocumentLink rows using resolved Ids
cdl_rows = []
for cv_id, doc_id in id_map.items():
    case_id = cv_id_to_case_id[cv_id]
    cdl_rows.append({"ContentDocumentId": doc_id, "LinkedEntityId": case_id, "ShareType": "V"})

# Step 4: Insert ContentDocumentLink via REST API (not Bulk API)
for row in cdl_rows:
    insert_cdl_rest(instance_url, token, row['ContentDocumentId'], row['LinkedEntityId'])
```

**Detection hint:** Look for ContentDocumentLink rows being built before any ContentVersion insert operation completes, or any attempt to set ContentDocumentId using a pre-generated value rather than a queried value.

---

## Anti-Pattern 6: Ignoring Load Order and Loading Child Objects Before Parents

**What the LLM generates:**
```python
# LLM loads objects in alphabetical or arbitrary order
objects_to_load = [
    "CaseComment",       # Loaded before Case — will fail
    "Case",
    "ContentDocumentLink",  # Loaded before ContentVersion — will fail
    "ContentVersion",
    "EmailMessage",      # Loaded before Case — will fail
    "EmailMessageRelation",
]
for obj in sorted(objects_to_load):
    bulk_load(obj)
```

**Why it happens:** LLMs sometimes default to alphabetical or arbitrarily-ordered processing of object names. They understand that parent-child relationships exist but do not always infer the correct dependency sequence for objects they have not seen in a migration context together.

**Correct pattern:**
```
REQUIRED LOAD ORDER:
1. Case
2. CaseComment  (ParentId → Case)
3. EmailMessage  (ParentId → Case)
4. EmailMessageRelation  (EmailMessageId → EmailMessage)
5. ContentVersion  (no parent required at insert; FirstPublishLocationId is optional)
6. ContentDocumentLink  (ContentDocumentId → ContentDocument auto-created from ContentVersion; LinkedEntityId → Case or EmailMessage)
```

**Detection hint:** If the generated load sequence does not follow this exact order, or if any child object appears before its parent in the sequence, the load will produce referential integrity failures on child rows.
