# Request Examples: An Idempotent Order Sync Over REST

A complete request sequence for a middleware job that syncs orders into Salesforce: check the allocation, upsert the parent by External ID, write dependent records atomically with Composite, and read back with pagination. Endpoints, headers, and response shapes come from the REST API Developer Guide, Version 67.0; limits from the Salesforce Developer Limits and Allocations Quick Reference, release 262. The token comes from the client credentials flow described in `integration/oauth-flows-and-connected-apps`.

## 1. Check the remaining allocation before a large run

```bash
curl -s https://MyDomainName.my.salesforce.com/services/data/v67.0/limits/ \
  -H "Authorization: Bearer $SF_TOKEN" | jq '.DailyApiRequests'
```

Every REST response also carries the header `Sforce-Limit-Info: api-usage=10018/100000`. Stop or slow the job when usage approaches the limit; the allocation is shared by every integration in the org.

## 2. Upsert the account by External ID (idempotent)

```bash
curl -s -X PATCH \
  "https://MyDomainName.my.salesforce.com/services/data/v67.0/sobjects/Account/ERP_Customer_Number__c/C-1001" \
  -H "Authorization: Bearer $SF_TOKEN" -H "Content-Type: application/json" \
  -d '{ "Name": "Acme Corporation", "BillingCountry": "US" }'
```

Responses the client must handle:

| Status | Body | Meaning |
|---|---|---|
| 201 | `{"id": "...", "success": true, "errors": [], "created": true}` | Created |
| 200 | `{"id": "...", "success": true, "errors": [], "created": false}` | Updated (API 46.0+) |
| 300 | List of matching records | The External ID matched more than one record; nothing changed |
| 404 | `{"message": "The requested resource does not exist", "errorCode": "NOT_FOUND"}` | Wrong External ID field name |

Add `?updateOnly=true` to the URL when the job must never create accounts.

## 3. Write the order and its line atomically with Composite

```http
POST /services/data/v67.0/composite HTTP/1.1
Host: MyDomainName.my.salesforce.com
Authorization: Bearer <token>
Content-Type: application/json
```

```json
{
  "allOrNone": true,
  "compositeRequest": [
    {
      "method": "GET",
      "url": "/services/data/v67.0/sobjects/Account/ERP_Customer_Number__c/C-1001?fields=Id",
      "referenceId": "Customer"
    },
    {
      "method": "POST",
      "url": "/services/data/v67.0/sobjects/Order",
      "referenceId": "NewOrder",
      "body": {
        "AccountId": "@{Customer.Id}",
        "EffectiveDate": "2026-10-03",
        "Status": "Draft"
      }
    },
    {
      "method": "POST",
      "url": "/services/data/v67.0/sobjects/Task",
      "referenceId": "FollowUp",
      "body": {
        "WhatId": "@{NewOrder.id}",
        "Subject": "Confirm ERP order BK-1001"
      }
    }
  ]
}
```

The whole series counts as one API call, all subrequests run as the same user, and later subrequests reference earlier results with `@{referenceId.field}`. Up to 25 subrequests are allowed, at most 5 of them sObject Collections or queries. Read every entry of `compositeResponse`:

```json
{
  "compositeResponse": [
    { "body": { "attributes": { "type": "Account" }, "Id": "001xx000003DGb2AAG" }, "httpHeaders": {}, "httpStatusCode": 200, "referenceId": "Customer" },
    { "body": [ { "errorCode": "PROCESSING_HALTED", "message": "The transaction was rolled back since another operation in the same transaction failed." } ], "httpHeaders": {}, "httpStatusCode": 400, "referenceId": "NewOrder" },
    { "body": [ { "errorCode": "REQUIRED_FIELD_MISSING", "message": "Required fields are missing: [Subject]", "fields": [ "Subject" ] } ], "httpHeaders": {}, "httpStatusCode": 400, "referenceId": "FollowUp" }
  ]
}
```

The outer status of that response is 200. UNVERIFIED (2026-10-03): the exact error bodies above are illustrative of the documented per-subrequest shape (`body`, `httpHeaders`, `httpStatusCode`, `referenceId`); the wording Salesforce returns for rolled-back siblings can differ. Required fields on `Order` (for example a price book or contract) depend on the org's configuration.

## 4. Read back with pagination

```bash
next="/services/data/v67.0/query/?q=SELECT+Id,Status+FROM+Order+WHERE+LastModifiedDate=TODAY"
while [ -n "$next" ]; do
  page=$(curl -s "https://MyDomainName.my.salesforce.com$next" \
    -H "Authorization: Bearer $SF_TOKEN" -H "Sforce-Query-Options: batchSize=2000")
  echo "$page" | jq -c '.records[]'
  if [ "$(echo "$page" | jq -r '.done')" = "true" ]; then next=""; else next=$(echo "$page" | jq -r '.nextRecordsUrl'); fi
done
```

`nextRecordsUrl` is a path; the loop prepends the host. The batch size header accepts 200 to 2,000 and is not guaranteed.

## 5. Back off on the documented limit error

```json
[
  {
    "message": "TotalRequests Limit exceeded.",
    "errorCode": "REQUEST_LIMIT_EXCEEDED"
  }
]
```

The REST guide returns this with HTTP 403. UNVERIFIED (2026-10-03): the `message` text is illustrative; branch on `errorCode`, never on the message. Retry with exponential backoff and alert the owner of the call budget.

## 6. Create a parent and children in one tree, in XML

The sObject Tree resource accepts JSON or XML. This XML body follows the REST guide's own sObject Tree example: one Account with two Contacts, all committed together or not at all.

```http
POST /services/data/v67.0/composite/tree/Account HTTP/1.1
Host: MyDomainName.my.salesforce.com
Authorization: Bearer <token>
Content-Type: application/xml
Accept: application/xml
```

```xml
<SObjectTreeRequest>
    <records type="Account" referenceId="acct1">
        <name>Acme Corporation</name>
        <phone>4155550100</phone>
        <industry>Manufacturing</industry>
        <Contacts>
            <records type="Contact" referenceId="con1">
                <lastname>Smith</lastname>
                <title>President</title>
            </records>
            <records type="Contact" referenceId="con2">
                <lastname>Evans</lastname>
                <title>Vice President</title>
            </records>
        </Contacts>
    </records>
</SObjectTreeRequest>
```

A successful response returns `<SObjectTreeResponse>` with `<hasErrors>false</hasErrors>` and one `<results>` element per record (`<id>` and `<referenceId>`). If any record fails, the whole request fails and the response contains only the failing record's reference ID and error. Triggers and flows fire for the Account first, then for both Contacts together.
