# Examples: OmniStudio Integration Procedures

---

## Example 1: Root propertySetConfig — Mandatory Configuration

Every Integration Procedure must start with this root configuration. Open the IP in OmniStudio Designer → Properties panel:

```json
{
  "propertySetConfig": {
    "rollbackOnError": true,
    "chainableQueriesLimit": 50,
    "chainableCpuLimit": 2000
  }
}
```

**How to set it:**
1. Open the Integration Procedure in OmniStudio Designer
2. Click the root node (the IP name at the top)
3. In the Properties panel, set the three values above
4. Verify in the JSON export that they appear at the root level

If `rollbackOnError` is missing or false, and Step 3 of 5 fails, Steps 1 and 2 have already written data — partial write. No rollback. Silent data corruption.

---

## Example 2: HTTP Action — Named Credential + Timeout + Failure Response

**Scenario:** Integration Procedure calls an external address validation API.

Step configuration:
```
Step Type: HTTP Action
Name: PKG_InvokeAddressValidation
Description: POST address to USPS validation endpoint via Named Credential. Returns validated address or error.

method: POST
namedCredential: USPS_AddressValidation_Production
path: /address/v1/validate
restOptions:
  timeout: 15000          ← 15 seconds; USPS API SLA is <5s, 15s gives headroom
  headers:
    Content-Type: application/json
    Accept: application/json
body: {
  "street": "{addressLine1}",
  "city": "{city}",
  "state": "{state}",
  "zip": "{postalCode}"
}

failureResponse: "Address validation is temporarily unavailable. Your application has been saved. Our team will verify your address within 1 business day."
failOnStepError: true
```

**What NOT to put in failureResponse:**
- ❌ "USPS API returned HTTP 503" — internal detail, not user-friendly
- ❌ "Put Business approved verbiage here" — placeholder, will ship to prod
- ❌ "Error" — zero information
- ✅ "Address validation is temporarily unavailable. [What user should do.]"

---

## Example 3: Null Guard Pattern — After HTTP Response

**Problem:** The address validation API sometimes returns `{"status": "ERROR"}` with no address fields. Directly mapping `response.address.street` throws a null error.

**Pattern: Decision step after HTTP action**

```
Step 1: PKG_InvokeAddressValidation [HTTP Action]
         ↓ success
Step 2: PKG_CheckValidationStatus [Decision]
         Condition: {response.status} = "SUCCESS"
         ├── TRUE → Step 3: PKG_ExtractValidatedAddress [DataRaptor Transform]
         └── FALSE → Step 4: PKG_HandleValidationFailure [Set Values]
                      Set: outputStatus = "VALIDATION_FAILED"
                      Set: outputMessage = "Address could not be validated. Please check and resubmit."
         ↓
Step 5: PKG_OutputResult [Response Action]
```

**Formula-level null guard (in DataRaptor or Set Values step):**
```
IF(ISBLANK({response.address.street}), "Unknown", {response.address.street})
```

Never assume the external API returns all fields on every call. Structure changes, optional fields, and partial responses are common. Guard everything you map.

---

## Example 4: Input/Output Contract Documentation

Before building any IP, document its contract. This goes in the IP description field AND in your team's documentation.

```
IP Name: PKG_InvokeAddressValidation
Purpose: Validates a US postal address against USPS API. Called from PKG_ApplyForAssistance OmniScript.

INPUT VARIABLES:
  addressLine1  (String, required): Street address line 1
  city          (String, required): City name
  state         (String, required): 2-letter state code
  postalCode    (String, required): 5-digit ZIP or ZIP+4

OUTPUT VARIABLES:
  validationStatus  (String): "SUCCESS" | "VALIDATION_FAILED" | "SERVICE_UNAVAILABLE"
  validatedStreet   (String): Corrected street address from USPS (populated on SUCCESS)
  validatedCity     (String): Corrected city from USPS (populated on SUCCESS)
  validatedState    (String): Corrected state from USPS (populated on SUCCESS)
  validatedZip      (String): Corrected ZIP from USPS (populated on SUCCESS)
  errorMessage      (String): User-friendly message (populated on non-SUCCESS)

INTERNAL FIELDS (not in output contract):
  response.rawBody    — never expose to OmniScript
  response.statusCode — internal use only
```

**Why define this before building:** The OmniScript that calls this IP is being built in parallel. Without a contract, both teams make assumptions and discover the mismatch in testing.
