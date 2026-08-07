# LLM Anti-Patterns — Industries API Extensions

Common mistakes AI coding assistants make when generating or advising on Salesforce Industries-specific API integrations.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using Standard REST CRUD or Apex DML to Create InsurancePolicy Records

**What the LLM generates:**

```apex
InsurancePolicy policy = new InsurancePolicy(
    Name = 'AUTO-2026-00001',
    EffectiveDate = Date.today(),
    InsuranceProductId = productId,
    PolicyOwnerId = accountId
);
insert policy;

InsurancePolicyCoverage cov = new InsurancePolicyCoverage(
    InsurancePolicyId = policy.Id,
    CoverageType = 'Liability',
    CoverageAmount = 100000
);
insert cov;
```

**Why it happens:** The LLM correctly identifies `InsurancePolicy` and `InsurancePolicyCoverage` as standard Salesforce objects queryable via SOQL and concludes they follow standard DML patterns. It extrapolates from Apex training data where standard object creation always uses `insert`. The Insurance Cloud Connect API constraint is not represented in generic Salesforce Apex training material.

**Correct pattern:**

```http
POST /services/data/v67.0/connect/insurance/policies
Content-Type: application/json

{ "<contextIdField>": "<context record Id>" }
```

The body placeholder is intentional — see Anti-Pattern 1b for why filling it in from memory is the *second* failure mode here.

**Detection hint:** Any code that contains `insert InsurancePolicy` or `new InsurancePolicy(` followed by a DML statement for a lifecycle operation (create, modify, cancel) is using the wrong API layer. Read-only Apex that queries `[SELECT Id FROM InsurancePolicy]` is fine.

---

## Anti-Pattern 1b: Pluralising the Lifecycle Verb into a Fake Connect Resource

**What the LLM generates:** Having correctly decided to use the Insurance Policy Business API, the model then invents the resource path by turning each lifecycle operation into its own pluralised collection:

```http
POST /connect/insurance/policy-issuances       <-- does not exist
POST /connect/insurance/policy-endorsements    <-- does not exist
POST /connect/insurance/policy-renewals        <-- does not exist
POST /connect/insurance/policy-cancellations   <-- does not exist
```

It usually also invents the request body — a flat document with `policyName`, `effectiveDate`, `productId` and a nested `coverages` array — assembled from `InsurancePolicy` and `InsurancePolicyCoverage` field names.

**Why it happens:** This is confabulation *inside a correct decision*, which is what makes it so durable. The model has the mechanism right (atomic lifecycle transaction, not DML) and only the identifier wrong, so the surrounding prose reads as authoritative and reviewers accept the path along with the reasoning. The specific shape comes from **REST convention over-generalisation**: "a resource per noun, pluralised" is the dominant pattern in REST training data, so a lifecycle *verb* gets nominalised into a collection ("issue" → "policy-issuances"). Salesforce Connect APIs frequently do the opposite — one collection with verb sub-resources on the member. The body is invented by the same reflex applied to the object model: the model knows the objects, so it assumes the payload mirrors them.

**Correct pattern:**

```text
Insurance Policy Business API — one collection, verb sub-resources:

  POST /connect/insurance/policies
       "Use the context ID provided in the request body to generate a new
        insurance policy."
  GET  /connect/insurance/policies/{policyId}?_qs=contextOnly=true
  POST /connect/insurance/policies/{policyId}/endorse
  POST /connect/insurance/policies/{policyId}/out-of-sequence-endorsement
  POST /connect/insurance/policies/{policyId}/renew
  POST /connect/insurance/policies/{policyId}/cancel
  POST /connect/insurance/policies/{policyId}/reinstate

Multi-root (parent + children of different product types) — ASYNCHRONOUS:

  POST /connect/insurance/policies/multi-root
  POST /connect/insurance/policies/multi-root/endorse
  POST /connect/insurance/policies/multi-root/renew

Request body: context-ID driven. NOT a flat policy document, NOT an sObject
payload. Read the "Requests" section of the reference for exact field names.
```

**Detection hint:** Grep any generated Industries integration code for a `/connect/` path segment containing a **hyphenated noun ending in `s`** that nominalises a verb — `policy-issuances`, `policy-endorsements`, `policy-renewals`, `policy-cancellations`, `asset-activations`, `order-submissions`. Salesforce Connect resources overwhelmingly place lifecycle verbs as bare sub-resources on a member (`/{id}/endorse`), so a nominalised-plural segment is a strong fabrication signal. Second check: any Connect API request body whose field names are camelCased versions of the sObject's own fields is reconstructed rather than recalled — Connect payloads generally do not mirror the object model. Resolve both against the vertical's developer guide before shipping.

---

## Anti-Pattern 2: Passing Product Names or Catalog Codes in TM Forum API Payloads

**What the LLM generates:**

```json
{
  "productOrderItem": [{
    "productOffering": {
      "name": "Broadband-100-Plus",
      "href": "https://catalog.telco.com/offerings/BROAD-100"
    },
    "action": "add"
  }]
}
```

**Why it happens:** The TM Forum specification uses `name` and `href` as optional descriptor fields in its schema, and many non-Salesforce TM Forum implementations resolve products by name or external href. The LLM generalizes from those implementations. The Salesforce-specific constraint that only Salesforce record IDs are valid resolvers is not present in the TM Forum specification itself.

**Correct pattern:**

```json
{
  "productOrderItem": [{
    "productOffering": {
      "id": "0ZaXXXXXXXXXXXXX"
    },
    "action": "add"
  }]
}
```

The `id` field must be the Salesforce `ProductOffering__c` record ID. Resolve it via SOQL before constructing the request.

**Detection hint:** Any TM Forum JSON payload that populates `"name":` or `"href":` in a `productOffering`, `productSpecification`, or `productCharacteristic` block without also including `"id":` is likely using the wrong resolution strategy for Salesforce Communications Cloud.

---

## Anti-Pattern 3: Routing Communications Cloud TM Forum API Calls Through a MuleSoft Gateway URL

**What the LLM generates:**

```
Base URL: https://my-mulesoft-gateway.cloudhub.io/communications-cloud/tmf-api/...
```

Or a recommendation to set up a MuleSoft gateway as the API entry point for Communications Cloud TM Forum integrations.

**Why it happens:** The MuleSoft gateway was the documented and supported path for Communications Cloud TM Forum API access prior to Direct Access being generally available. Older documentation, blog posts, and training material references the gateway path. The LLM reproduces this historical guidance because it dominated the training corpus for this topic.

**Correct pattern:**

```
Base URL: https://<instance>.my.salesforce.com/services/apexrest/tmf-api/...
```

Direct Access routes TM Forum API calls directly to the Salesforce org instance. Enable it in Setup > Communications Cloud > TM Forum API Settings. Do not configure a MuleSoft gateway as an intermediary.

**Detection hint:** Any Communications Cloud TM Forum integration specification that references a non-`my.salesforce.com` base URL, a MuleSoft CloudHub subdomain, or recommends MuleSoft gateway as the access layer is describing the deprecated path.

---

## Anti-Pattern 4: Updating ServicePoint Status via Direct PATCH on the sObject Endpoint

**What the LLM generates:**

```http
PATCH /services/data/v62.0/sobjects/ServicePoint__c/{id}
Content-Type: application/json

{ "Status__c": "Inactive" }
```

Or an equivalent Apex `update` DML on a `ServicePoint__c` record's status field.

**Why it happens:** The LLM treats `ServicePoint__c` as a regular custom object and applies the standard Salesforce pattern for field updates. The constraint that status changes must go through the `sfiEnergy_UpdateAssetStatus` Integration Procedure via the Connect API is an E&U Cloud-specific requirement invisible to generic Salesforce training data.

**Correct pattern:**

```http
POST /services/data/v62.0/connect/energy/asset-status-updates
Content-Type: application/json

{
  "assetId": "{ServicePoint_Id}",
  "newStatus": "Inactive",
  "reason": "CustomerRequest"
}
```

**Detection hint:** Any code that writes to `Status__c` on a `ServicePoint__c` record directly (via REST PATCH, Flow record update, or Apex DML) without going through the E&U Connect API is bypassing E&U business rules.

---

## Anti-Pattern 5: Assuming Insurance Connect API Returns a Partial Success or Commits the Parent Record on Coverage Failure

**What the LLM generates:**

```python
# LLM-generated error handling code
response = requests.post(policy_issuance_url, json=payload)
if response.status_code != 201:
    # Try to find the policy that was created before the coverage failed
    policy_id = find_partial_policy(account_id, effective_date)
    if policy_id:
        # Retry coverage creation separately
        create_coverages(policy_id, coverage_data)
```

**Why it happens:** Many Salesforce APIs return partial success responses (e.g., Bulk API, Composite API with `allOrNone: false`). The LLM generalizes this behavior to the Insurance Connect API and assumes the parent policy record may be committed even if coverage creation fails. This leads to integration logic that searches for orphaned policy records as a recovery strategy.

**Correct pattern:**

```python
response = requests.post(policy_issuance_url, json=payload)
if response.status_code != 201:
    # The transaction was fully rolled back — no policy record exists.
    # Read the error body for diagnostic information.
    error_detail = response.json()
    log_error(error_detail)
    raise PolicyIssuanceError(error_detail.get("message", "Unknown error"))
    # Do NOT search for orphaned records — the rollback guarantees none exist.
```

**Detection hint:** Integration error-handling code that attempts to query for a partially-created `InsurancePolicy` record after a non-2xx Insurance Connect API response is based on the incorrect assumption. The rollback is total. Check for `SELECT Id FROM InsurancePolicy WHERE ... AND CreatedDate = TODAY` queries in error recovery code paths.

---

## Anti-Pattern 6: Hardcoding Service Process Connect API Response Field Names Without Contract Testing

**What the LLM generates:**

```python
response = requests.post(service_process_url, json=input_params)
result = response.json()
# LLM hardcodes field names from one-time observation
policy_number = result["outputParameters"]["policyNumber"]
approval_status = result["outputParameters"]["approvalStatus"]
```

**Why it happens:** The LLM treats the Service Process Connect API as if it has a fixed, documented response schema at the endpoint level (like a standard Salesforce REST API). In reality, the response schema is defined by the Service Process definition's output parameters, which can change when the process is updated.

**Correct pattern:**

```python
response = requests.post(service_process_url, json=input_params)
result = response.json()
output_params = result.get("outputParameters", {})

# Validate expected fields are present before accessing them
required_fields = ["policyNumber", "approvalStatus"]
missing = [f for f in required_fields if f not in output_params]
if missing:
    raise SchemaError(f"Service Process response missing expected fields: {missing}")

policy_number = output_params["policyNumber"]
approval_status = output_params["approvalStatus"]
```

Include a contract test that runs against the Service Process API after any process definition change and validates the response schema before promoting to production.

**Detection hint:** Integration code that accesses Service Process API response fields by hardcoded key path without any presence check or schema validation is fragile against process definition updates.
