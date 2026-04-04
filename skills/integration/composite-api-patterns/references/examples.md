# Examples — Composite API Patterns

## Example 1: Create Account, Contact, and Opportunity in One Composite Call

**Context:** An external CRM sync integration needs to create a new Account with an associated primary Contact and an initial Opportunity in Salesforce. None of the Salesforce IDs are known in advance. The caller requires all three records to be created atomically — if the Opportunity insert fails due to a validation rule, the Account and Contact must not be persisted.

**Problem:** Without the Composite API, the caller would need three separate REST calls. The Account ID from call 1 must be stored and passed to calls 2 and 3. If call 3 fails, the caller must compensate by deleting the Account and Contact already created — adding complexity, extra API calls, and a time window where orphaned records exist in Salesforce.

**Solution:**

```json
POST /services/data/v63.0/composite
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "allOrNone": true,
  "compositeRequest": [
    {
      "method": "POST",
      "url": "/services/data/v63.0/sobjects/Account/",
      "referenceId": "NewAccount",
      "body": {
        "Name": "Acme Corp",
        "BillingCity": "San Francisco",
        "BillingState": "CA",
        "Industry": "Technology"
      }
    },
    {
      "method": "POST",
      "url": "/services/data/v63.0/sobjects/Contact/",
      "referenceId": "NewContact",
      "body": {
        "LastName": "Smith",
        "FirstName": "Jane",
        "Email": "jane.smith@acmecorp.com",
        "AccountId": "@{NewAccount.id}"
      }
    },
    {
      "method": "POST",
      "url": "/services/data/v63.0/sobjects/Opportunity/",
      "referenceId": "NewOpportunity",
      "body": {
        "Name": "Acme Corp — Q3 Expansion",
        "AccountId": "@{NewAccount.id}",
        "StageName": "Prospecting",
        "CloseDate": "2025-09-30",
        "Amount": 75000
      }
    }
  ]
}
```

**Response inspection (required — outer HTTP 200 is not sufficient):**

```json
{
  "compositeResponse": [
    {
      "referenceId": "NewAccount",
      "httpStatusCode": 201,
      "body": { "id": "001XXXXXXXXXXXX", "success": true, "errors": [] }
    },
    {
      "referenceId": "NewContact",
      "httpStatusCode": 201,
      "body": { "id": "003XXXXXXXXXXXX", "success": true, "errors": [] }
    },
    {
      "referenceId": "NewOpportunity",
      "httpStatusCode": 201,
      "body": { "id": "006XXXXXXXXXXXX", "success": true, "errors": [] }
    }
  ]
}
```

**Why it works:** The `@{NewAccount.id}` reference is resolved server-side before the Contact and Opportunity subrequests execute. `allOrNone: true` ensures database-level atomicity — a validation failure on the Opportunity rolls back all three records. One API call replaces three, and no compensating delete logic is required.

**Key notes:**
- `referenceId` values are case-sensitive. `@{NewAccount.id}` will not resolve if the referenceId was declared as `"newaccount"`.
- The outer `httpStatusCode` is always 200 even if subrequests fail. Inspect each `compositeResponse` entry individually.
- With `allOrNone: true`, a failed Opportunity subrequest causes the Account and Contact entries to report `"httpStatusCode": 400` with `"errorCode": "PROCESSING_HALTED"`.

---

## Example 2: Upsert 150 Contact Records Using sObject Collection

**Context:** A nightly data sync from an external HR system sends up to 150 employee records that need to be created or updated in Salesforce as Contacts. Each record carries an external system ID (`HR_Employee_Id__c`) that is defined as an External ID field on Contact.

**Problem:** Using individual PATCH upsert calls against `/sobjects/Contact/HR_Employee_Id__c/{value}` for 150 records requires 150 HTTP round trips and counts as 150 API calls against the org's daily limit. An Enterprise Edition org with 1,000 API calls per license per day would burn 150 calls on a single sync batch.

**Solution:**

```json
PATCH /services/data/v63.0/composite/sobjects/Contact/HR_Employee_Id__c
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "allOrNone": false,
  "records": [
    {
      "attributes": { "type": "Contact" },
      "HR_Employee_Id__c": "EMP-001",
      "LastName": "Adams",
      "FirstName": "Alice",
      "Email": "alice.adams@company.com",
      "Title": "Senior Engineer",
      "Department": "Engineering"
    },
    {
      "attributes": { "type": "Contact" },
      "HR_Employee_Id__c": "EMP-002",
      "LastName": "Brown",
      "FirstName": "Bob",
      "Email": "bob.brown@company.com",
      "Title": "Product Manager",
      "Department": "Product"
    }
  ]
}
```

**Response parsing (inspect every record — allOrNone is false):**

```json
[
  { "id": "003XXXXXXXXXXXX", "success": true, "errors": [], "created": false },
  { "id": null, "success": false, "errors": [
    {
      "statusCode": "REQUIRED_FIELD_MISSING",
      "message": "Required fields are missing: [LastName]",
      "fields": ["LastName"]
    }
  ]}
]
```

**Why it works:** The sObject Collection PATCH with an External ID field name in the URL tells Salesforce to upsert each record — create if the `HR_Employee_Id__c` value does not exist, update if it does. `allOrNone: false` allows 149 records to succeed even if one has a validation error. The response array is index-aligned with the request `records[]` array — index 0 in the response corresponds to index 0 in the request, regardless of success or failure.

**Key notes:**
- The response array is always the same length as the request `records[]`. Use the index to correlate failures back to specific input records.
- `allOrNone: false` requires the caller to iterate all results and act on failures (retry, log to DLQ, alert).
- `"created": true` means a new record was inserted; `"created": false` means an existing record was updated.
- All records in a single sObject Collection DML call must be the same object type.

---

## Anti-Pattern: Using Composite Batch When Requests Have Dependencies

**What practitioners do:** Use `/composite/batch/` to bundle a parent record creation followed by a child record creation, and attempt to hardcode a placeholder for the parent ID or make two separate calls anyway.

**What goes wrong:** `/composite/batch/` subrequests cannot reference each other's results. There is no `@{referenceId.field}` resolution in batch requests. If the caller hardcodes the parent ID, the integration breaks if the ID is unknown at call time. If the caller falls back to two separate calls, the batch provides no benefit and partial failure handling becomes more complex.

**Correct approach:** Use `/composite/` (not `/composite/batch/`) whenever subrequests have ordering dependencies or need to pass results between each other. Reserve `/composite/batch/` for genuinely independent operations — for example, updating three unrelated records of different types in one round trip.
