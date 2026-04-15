# Examples — Industries API Extensions

## Example 1: Issuing a New Insurance Policy via Connect API

**Context:** An Insurance Cloud org has a new customer application intake OmniScript. After the underwriter approves the application, the system must create an `InsurancePolicy` record together with three `InsurancePolicyCoverage` records (liability, collision, comprehensive) in a single atomic operation.

**Problem:** The initial implementation used direct Apex DML:

```apex
// WRONG — do not do this
InsurancePolicy policy = new InsurancePolicy(
    Name = 'POL-2026-00123',
    EffectiveDate = Date.today(),
    ExpirationDate = Date.today().addYears(1),
    InsuranceProductId = productId,
    PolicyOwnerId = accountId
);
insert policy;

List<InsurancePolicyCoverage> coverages = new List<InsurancePolicyCoverage>();
// ... build coverage list
insert coverages;  // If this fails, orphaned InsurancePolicy record is left behind
```

When the coverage insert fails (for example, due to a missing required coverage field), the `InsurancePolicy` record is committed but the coverages are not, leaving the policy in an invalid state that the UI cannot display and the business cannot process.

**Solution:**

Call the Insurance Policy Business Connect API instead. The request is a single HTTP POST that creates the policy and all coverages atomically:

```http
POST /services/data/v62.0/connect/insurance/policy-issuances
Content-Type: application/json
Authorization: Bearer {access_token}

{
  "policyName": "POL-2026-00123",
  "effectiveDate": "2026-04-15",
  "expirationDate": "2027-04-15",
  "productId": "01tXXXXXXXXXXXXX",
  "policyHolderId": "001XXXXXXXXXXXXXXX",
  "coverages": [
    {
      "coverageType": "Liability",
      "coverageAmount": 100000,
      "deductibleAmount": 500
    },
    {
      "coverageType": "Collision",
      "coverageAmount": 50000,
      "deductibleAmount": 1000
    },
    {
      "coverageType": "Comprehensive",
      "coverageAmount": 50000,
      "deductibleAmount": 500
    }
  ]
}
```

A successful response returns HTTP `201 Created` with the new `InsurancePolicy` ID:

```json
{
  "id": "7eXXXXXXXXXXXXXX",
  "success": true,
  "policyNumber": "POL-2026-00123"
}
```

If any validation fails (missing coverage type, invalid product ID, duplicate policy detection), the API returns a non-2xx status and no records are created. Check for `409 Conflict` on duplicate detection and `400 Bad Request` for schema validation failures.

**Why it works:** The Connect API wraps all DML in a single managed transaction within the Insurance Cloud service layer. Rollback on any failure is guaranteed — the API cannot emit a partial success for a policy issuance operation. Manual DML sequences in Apex have no such guarantee across separate `insert` statements even when called from the same Apex transaction if savepoints are not used correctly.

---

## Example 2: Submitting a TM Forum Commercial Order (Communications Cloud — Direct Access)

**Context:** A BSS provisioning system submits an order for a broadband bundle to Communications Cloud after a customer selects products in an external web portal. The integration team initially tried to pass the product catalog item code in the request.

**Problem:** The TMF622 request was constructed using catalog codes:

```json
// WRONG — product names and catalog codes are not valid identifiers in this API
{
  "productOrderItem": [{
    "productOffering": {
      "name": "BROADBAND-100-BUNDLE",
      "href": "https://catalog.example.com/offerings/BROADBAND-100-BUNDLE"
    },
    "action": "add"
  }]
}
```

This results in a `404 Not Found` or a validation error because the TM Forum API implementation in Salesforce resolves product offerings by Salesforce record ID, not by external catalog code or name.

**Solution:**

First, resolve the Salesforce record ID for the product offering (this lookup can be done via SOQL or a separate product catalog search API):

```soql
SELECT Id, Name FROM ProductOffering__c WHERE CatalogItemCode__c = 'BROADBAND-100-BUNDLE'
```

Then construct the TMF622 request with the Salesforce ID:

```http
POST https://<instance>.my.salesforce.com/services/apexrest/tmf-api/productOrderingManagement/v4/productOrder
Content-Type: application/json
Authorization: Bearer {access_token}

{
  "description": "Customer broadband order",
  "relatedParty": [{
    "@type": "RelatedParty",
    "id": "001XXXXXXXXXXXXXXX",
    "role": "Customer"
  }],
  "productOrderItem": [{
    "@type": "ProductOrderItem",
    "id": "1",
    "action": "add",
    "productOffering": {
      "id": "0ZaXXXXXXXXXXXXX"
    }
  }]
}
```

Successful response returns HTTP `201` with a Salesforce order record ID and initial state `acknowledged`:

```json
{
  "id": "8OXXXXXXXXXXXXXXX",
  "state": "acknowledged",
  "href": ".../.../productOrder/8OXXXXXXXXXXXXXXX"
}
```

Poll `GET .../productOrder/8OXXXXXXXXXXXXXXX` for state transitions to `inProgress` and then `completed` or `failed`.

**Why it works:** Direct Access routes the TMF622 POST directly to the Salesforce platform, which resolves all references against live Salesforce records. The ID-based resolution is deterministic and version-stable. Name-based lookup is not part of the TM Forum API implementation contract in Salesforce Industries and has no fallback behavior.

---

## Example 3: Updating Energy Asset Status via E&U Connect API

**Context:** A field operations system needs to mark a ServicePoint as `Inactive` after a customer requests disconnection.

**Problem:** A developer updated the `ServicePoint.Status` field directly via REST:

```http
// WRONG — bypasses business rule validation
PATCH /services/data/v62.0/sobjects/ServicePoint__c/a0XXXXXXXXXXXXXXXNNN
Content-Type: application/json

{ "Status__c": "Inactive" }
```

This bypasses the `sfiEnergy_UpdateAssetStatus` Integration Procedure, which enforces disconnection sequencing rules and creates a `StatusChange__c` audit record. Compliance reporting fails because the required audit trail is missing.

**Solution:**

Use the E&U Update Asset Status Connect API:

```http
POST /services/data/v62.0/connect/energy/asset-status-updates
Content-Type: application/json
Authorization: Bearer {access_token}

{
  "assetId": "a0XXXXXXXXXXXXXXXNNN",
  "newStatus": "Inactive",
  "reason": "CustomerRequest",
  "effectiveDate": "2026-04-15"
}
```

The API delegates to `sfiEnergy_UpdateAssetStatus`, which validates the transition (`Active` → `Inactive` is permitted; invalid transitions return `422 Unprocessable Entity`), updates the `ServicePoint.Status` field, and creates the required `StatusChange__c` record.

**Why it works:** The Connect API preserves the Integration Procedure delegation chain that embeds E&U business rules. The `sfiEnergy_UpdateAssetStatus` IP is the enforcement point for transition validity, notification sequencing, and audit record creation. Bypassing it via direct DML removes all three guarantees.

---

## Anti-Pattern: Using Standard DML or REST CRUD for Industry Object Lifecycle Operations

**What practitioners do:** A practitioner sees that `InsurancePolicy` is a standard Salesforce object queryable via SOQL and concludes that standard REST CRUD (`POST /sobjects/InsurancePolicy`) or Apex `insert` DML is the correct way to create or update it.

**What goes wrong:** The Insurance Cloud consistency guarantee requires that policy, coverage, and participant records are created or modified together in a single managed transaction. Standard CRUD does not coordinate across these objects. A partial failure leaves orphaned policy records. Additionally, Insurance Cloud calculates certain computed fields (premium totals, coverage indices) as part of the Connect API processing chain; these calculations are skipped when records are inserted via raw DML.

**Correct approach:** Always use the Insurance Policy Business Connect API for lifecycle operations. Use standard SOQL and REST `GET` for read-only access to existing policy records — reads are safe; writes are not.
