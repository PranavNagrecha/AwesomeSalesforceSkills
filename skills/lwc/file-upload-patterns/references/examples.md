# Examples — LWC File Upload Patterns

## Example 1: Simple record attachment

**Context:** Attach PDF to Case

**Problem:** Previous approach uploaded to a temp bucket

**Solution:**

`<lightning-file-upload record-id={caseId} accept=".pdf" multiple>`

**Why it works:** Native ContentDocumentLink, no Apex needed


---

## Example 2: Chunked 50MB upload

**Context:** Legal contract

**Problem:** Apex heap hit at 12MB

**Solution:**

JS chunks 4.5MB → @AuraEnabled appends to ContentBody per chunk → final save

**Why it works:** Respects governor heap limits

