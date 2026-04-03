# Integration Procedure Design Template

Complete this before building. Aligns the team on inputs, outputs, and error handling before any OmniStudio Designer work begins.

---

## Overview

| Property | Value |
|----------|-------|
| **IP Name (API)** | TODO: e.g. `PKG_InvokeAddressValidation` |
| **IP Name (Label)** | TODO: e.g. "Invoke Address Validation" |
| **Purpose** | TODO: One sentence — what does this IP do? |
| **Called From** | TODO: OmniScript / FlexCard / Apex / another IP |
| **External System(s)** | TODO: e.g. USPS API, Payment Gateway |
| **Named Credential(s)** | TODO: Name of each Named Credential used |
| **Author** | TODO |
| **Date** | TODO: YYYY-MM-DD |

---

## Root propertySetConfig (Mandatory — verify before build)

```json
{
  "propertySetConfig": {
    "rollbackOnError": true,
    "chainableQueriesLimit": 50,
    "chainableCpuLimit": 2000
  }
}
```

- [ ] `rollbackOnError: true` configured
- [ ] `chainableQueriesLimit: 50` configured
- [ ] `chainableCpuLimit: 2000` configured

---

## Input Contract

| Variable Name | Type | Required? | Description |
|--------------|------|-----------|-------------|
| TODO | String | Required | TODO |
| TODO | String | Optional | TODO: default if blank |

---

## Output Contract

| Variable Name | Type | Values | Description |
|--------------|------|--------|-------------|
| `status` | String | SUCCESS / ERROR / SERVICE_UNAVAILABLE | Overall result |
| `errorMessage` | String | — | Populated on non-SUCCESS; user-friendly text |
| TODO | TODO | TODO | TODO |

**Internal fields NOT in output** (do not expose to caller):
- TODO: e.g. `response.rawBody`, `response.statusCode`, internal IDs

---

## Step Design

| Step # | Step Name | Type | Description | Can Fail? | Fault Handling |
|--------|-----------|------|-------------|-----------|---------------|
| 1 | `PKG_Extract[InputData]` | DataRaptor Extract | Pull [data] from Salesforce | Yes — SOQL | Set error output + return |
| 2 | `PKG_Invoke[ExternalSystem]` | HTTP Action | POST to [system] via NC | Yes — HTTP | Set SERVICE_UNAVAILABLE |
| 3 | `PKG_Check[SystemResponse]Status` | Decision | HTTP 200 ≠ business success | N/A | Route to error on bad status |
| 4 | `PKG_Transform[Response]` | DataRaptor Transform | Parse response to output vars | Yes | Set error output |
| 5 | `PKG_Output` | Response Action | Return output contract | — | — |

---

## HTTP Action Configuration

For each HTTP action:

| Property | Value |
|----------|-------|
| **Step Name** | TODO: `PKG_Invoke[SystemNoun]` |
| **Method** | TODO: POST / GET / PUT |
| **Named Credential** | TODO |
| **Path** | TODO: e.g. `/api/v1/validate` |
| **Timeout (ms)** | TODO: e.g. `30000` |
| **failureResponse** | TODO: User-friendly error text (NO placeholders) |
| **failOnStepError** | `true` |

---

## Error Response Messages

All `failureResponse` values must be approved before deployment:

| Step | failureResponse Text | Approved By | Date |
|------|---------------------|-------------|------|
| `PKG_Invoke...` | TODO | TODO | TODO |
| `PKG_Transform...` | TODO | TODO | TODO |

**Check:** No `failureResponse` contains "verbiage", "TBD", "placeholder", "TODO", or "error" alone.

---

## Null Guard Checklist

For each field accessed from an external response:

| Field Path | Null Guard In Place? | Guard Formula |
|-----------|---------------------|--------------|
| `{response.data.fieldName}` | ☐ | `IF(ISBLANK({response.data.fieldName}), "default", {response.data.fieldName})` |

---

## Testing Plan

| Scenario | Input | Expected Output | Tested By | Date |
|----------|-------|----------------|-----------|------|
| Happy path | Valid inputs | `status = SUCCESS` | TODO | |
| External API failure | Valid inputs, API returns 500 | `status = SERVICE_UNAVAILABLE`, `errorMessage` populated | TODO | |
| Business error response | Valid inputs, API returns `{"status":"ERROR"}` | `status = ERROR`, `errorMessage` populated | TODO | |
| Missing required input | Blank required field | Error before HTTP call | TODO | |
| Named Credential missing | Deploy to new env | Meaningful error, not NPE | TODO | |

---

## Deployment Checklist

- [ ] Named Credentials deployed to target environment
- [ ] All `failureResponse` text approved (no placeholders)
- [ ] IP tested in sandbox with happy path and error path
- [ ] OmniScript/FlexCard error state configured for this IP's error outputs
- [ ] `rollbackOnError: true` verified in deployed IP
