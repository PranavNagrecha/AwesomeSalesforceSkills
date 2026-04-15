# Industries API Extensions — Work Template

Use this template when designing or reviewing an integration against Salesforce Industries-specific API extensions.

## Scope

**Skill:** `industries-api-extensions`

**Request summary:** (fill in the specific integration being designed or reviewed)

---

## 1. Vertical and Operation Identification

| Question | Answer |
|---|---|
| Industry vertical | _____ (Insurance Cloud / Communications Cloud / Energy and Utilities Cloud / Cross-vertical) |
| API operation | _____ (policy issuance / endorsement / renewal / cancellation / asset status update / TM Forum order / service process execution) |
| API family | _____ (Insurance Policy Business Connect API / TM Forum Open APIs / E&U Update Asset Status API / Service Process Studio Connect API) |
| Target API version | _____ (e.g., v62.0) |

---

## 2. License and Access Model Verification

| Check | Status |
|---|---|
| Industry Cloud license confirmed in org | [ ] Yes / [ ] No — License: _____ |
| For Comms Cloud: Direct Access enabled in Setup | [ ] Yes / [ ] No / [ ] N/A |
| For Comms Cloud: MuleSoft gateway dependency identified and flagged | [ ] Yes / [ ] No / [ ] N/A |
| IP version confirmed (E&U / Service Process) | [ ] Yes / [ ] No / [ ] N/A — Version: _____ |

---

## 3. Request Payload Specification

**Endpoint:**
```
{HTTP_METHOD} {BASE_URL}/services/data/{API_VERSION}/{ENDPOINT_PATH}
```

**Required headers:**
```
Content-Type: application/json
Authorization: Bearer {access_token}
```

**Request body (fill in per operation):**

For Insurance policy issuance:
```json
{
  "policyName": "___________",
  "effectiveDate": "YYYY-MM-DD",
  "expirationDate": "YYYY-MM-DD",
  "productId": "{InsuranceProduct_Salesforce_ID}",
  "policyHolderId": "{Account_Salesforce_ID}",
  "coverages": [
    {
      "coverageType": "___________",
      "coverageAmount": 0,
      "deductibleAmount": 0
    }
  ]
}
```

For TM Forum TMF622 order:
```json
{
  "description": "___________",
  "relatedParty": [{
    "@type": "RelatedParty",
    "id": "{Account_Salesforce_ID}",
    "role": "Customer"
  }],
  "productOrderItem": [{
    "@type": "ProductOrderItem",
    "id": "1",
    "action": "add",
    "productOffering": {
      "id": "{ProductOffering_Salesforce_ID}"
    }
  }]
}
```

For E&U asset status update:
```json
{
  "assetId": "{ServicePoint_Salesforce_ID}",
  "newStatus": "___________",
  "reason": "___________",
  "effectiveDate": "YYYY-MM-DD"
}
```

For Service Process execution:
```json
{
  "inputParameters": {
    "paramName1": "value1",
    "paramName2": "value2"
  }
}
```

---

## 4. ID Resolution Map

| External identifier | Resolution method | Salesforce ID field | Notes |
|---|---|---|---|
| _____ | SOQL: `SELECT Id FROM _____ WHERE _____ = '___'` | _____ | _____ |
| _____ | SOQL: `SELECT Id FROM _____ WHERE _____ = '___'` | _____ | _____ |

---

## 5. Error Handling Matrix

| HTTP Status | Meaning | Action |
|---|---|---|
| 201 Created | Success — record(s) created | Extract record ID from response, proceed |
| 400 Bad Request | Schema validation failure in request payload | Log full response body, fix payload, retry |
| 404 Not Found | Referenced entity ID does not exist | Re-resolve Salesforce IDs; do not retry with same payload |
| 409 Conflict | Duplicate detection (Insurance issuance) | Check for existing policy; escalate or surface to user |
| 422 Unprocessable Entity | Business rule validation failure (E&U transition rules) | Log error code from response, surface to user for manual resolution |
| 503 Service Unavailable | Platform or endpoint unavailable | Retry with exponential backoff; alert if persistent |

TM Forum error response shape:
```json
{
  "code": "___________",
  "reason": "___________",
  "message": "___________"
}
```

---

## 6. Review Checklist

- [ ] All entity references in request payload use Salesforce record IDs (not names, codes, or external keys)
- [ ] For Comms Cloud: Direct Access confirmed as the integration path; no MuleSoft gateway URL in configuration
- [ ] No direct DML or REST CRUD on InsurancePolicy, InsurancePolicyCoverage, or ServicePoint Status field
- [ ] Error handling reads the full response body on non-2xx responses; does not search DB for partial records
- [ ] Tested against an industry-licensed org or scratch org with the industry feature flag enabled
- [ ] Service Process response schema validated against process output parameter contract
- [ ] E&U: Confirmed asset status transition is valid (e.g., Active → Inactive permitted)

---

## 7. Notes

(Record any deviations from the standard pattern and why, version constraints, or org-specific configuration details.)
