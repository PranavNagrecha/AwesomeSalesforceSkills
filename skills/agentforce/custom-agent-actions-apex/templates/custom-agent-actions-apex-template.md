# Custom Agent Actions Apex — Action Design Template

Use this template when designing a new custom Apex action for an Agentforce agent.

## Action Identity

**Action Name (method name):** ________________________________
**Label (shown in Agentforce Builder):** ________________________________
**Description (for Atlas Reasoning Engine — start with "Invoke when..."):**

> Invoke when ________________________________________________________________
> ____________________________________________________________________________

**Agent Type:** [ ] Employee Agent (runs as logged-in user) [ ] Service Agent (runs as service agent user)
**Requires External Callout:** [ ] Yes — add callout=true [ ] No

---

## Input Schema

| Field Name | Type | Required | Label | Description (for agent) |
|---|---|---|---|---|
| | | [ ] Yes [ ] No | | |
| | | [ ] Yes [ ] No | | |
| | | [ ] Yes [ ] No | | |

---

## Output Schema

Always include success (Boolean) and errorMessage (String).

| Field Name | Type | Label | Description |
|---|---|---|---|
| success | Boolean | Success | True if action completed successfully. |
| errorMessage | String | Error Message | Human-readable error if success is false. Empty string if success is true. |
| | | | |
| | | | |

---

## Security Model

- Sharing enforcement: [ ] with sharing (recommended) [ ] without sharing (document reason below)
- Reason if without sharing: _______________________________________________
- SOQL uses WITH USER_MODE: [ ] Yes [ ] No — add if querying records
- External auth uses Named Credential: [ ] Yes — name: ________________ [ ] No callouts needed

---

## Error Handling

What errors can this action encounter?

| Error Condition | Response (always set success=false + errorMessage) |
|---|---|
| Required input missing | success=false, errorMessage='[FieldName] is required.' |
| Record not found | success=false, errorMessage='No [object] found for [criteria].' |
| Callout failure | success=false, errorMessage='External system returned HTTP [status]: [message].' |
| | |

---

## Test Plan

| Scenario | Expected Output |
|---|---|
| Happy path with valid inputs | success=true, [expected output fields populated] |
| Missing required input | success=false, errorMessage contains field name |
| Record not found | success=false, appropriate message |
| Callout failure (mock 500 response) | success=false, HTTP error in message |

---

## Review Checklist

- [ ] `@InvocableMethod` has both `label` and `description`
- [ ] Every `@InvocableVariable` has `label` and `description`
- [ ] Method signature is `List<Input>` → `List<Output>`
- [ ] Output includes `success` (Boolean) and `errorMessage` (String)
- [ ] No `throw` statements — all errors return structured output
- [ ] `with sharing` on the class (or documented exception)
- [ ] `callout=true` if HTTP requests are made
- [ ] Named Credentials for authentication — no hardcoded credentials
- [ ] Unit tests cover success and failure paths
