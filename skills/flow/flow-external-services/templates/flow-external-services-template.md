# Flow External Services — Work Template

Use this template when designing, reviewing, or troubleshooting a Flow that calls an external REST API via External Services or the HTTP Callout action.

---

## Scope

**Skill:** `flow-external-services`

**Request summary:** (fill in what the user asked for)

**Integration direction:** Salesforce → External API (outbound callout)

---

## Context Gathered

Answer these before starting any design or review work.

| Question | Answer |
|---|---|
| External API endpoint (base URL) | |
| Authentication type (OAuth 2.0, API key, basic auth, JWT) | |
| Named Credential exists? (Yes / No / TBD) | |
| OpenAPI spec available? (Yes / No / Version: 2.0 or 3.0) | |
| Flow type (screen, autolaunched, record-triggered, scheduled) | |
| Trigger context (user action, platform event, schedule, record save) | |
| Expected response structure (flat JSON, nested, array) | |
| Error handling requirement (user message, log, retry, escalate) | |
| Volume context (single record, batch, high-volume data load) | |

---

## Registration Method Selection

Choose one:

- [ ] **External Services** — Use when an OpenAPI 2.0/3.0 spec is available and multiple operations need to be accessible in Flow Builder as typed actions.
- [ ] **HTTP Callout action** — Use when no spec is available, only one endpoint is needed, or speed of setup is prioritized over type safety.

**Reason for choice:** _______________

---

## Named Credential Configuration

| Field | Value |
|---|---|
| Named Credential Developer Name | |
| External Credential Developer Name | |
| Base URL (no trailing slash) | |
| Authentication Protocol | |
| Principal Type (Named Principal / Per User / Anonymous) | |
| Permission Set(s) assigned to principal | |

Named Credential ready for callout? [ ] Yes [ ] No — blocked by: _______________

---

## External Service Registration (if applicable)

| Field | Value |
|---|---|
| Service Name | |
| Spec Source (URL / file upload) | |
| Named Credential linked | |
| Operations imported | |
| Spec warnings reviewed | [ ] Yes — warnings: ___ [ ] No warnings |
| Generated action parameters verified in Flow Builder | [ ] Yes |

---

## HTTP Callout Action Configuration (if applicable)

| Field | Value |
|---|---|
| Named Credential | |
| Invocable Action Name (label) | |
| HTTP Method | |
| Path | |
| Request Headers | Content-Type: application/json |
| Request Body Variable | |
| Response_Body variable name | |
| Response_Status_Code variable name | |

---

## Output Variable Mapping

| API Response Field | Flow Variable Name | Flow Variable Type |
|---|---|---|
| | | |
| | | |
| | | |

For External Service action outputs — explicit Assignment element used to map to sObject variables? [ ] Yes [ ] N/A

For HTTP Callout action — Transform element or Apex parsing method used? [ ] Transform [ ] Apex InvocableMethod [ ] N/A (simple response)

---

## Error Handling Design

**Fault connector wired on all callout actions?** [ ] Yes

**For HTTP Callout action — Decision element checking `Response_Status_Code >= 400`?** [ ] Yes [ ] N/A (External Services only)

**`$Flow.FaultMessage` captured in a variable?** [ ] Yes — variable name: _______________

**On fault, user sees:** _______________

**On fault, logging/notification:** _______________

---

## Async Dispatch (required for record-triggered flows)

Is the callout triggered from a record save? [ ] Yes [ ] No

If yes, async dispatch mechanism:
- [ ] Platform Event published from record-triggered flow → Platform Event-Triggered autolaunched flow contains callout
- [ ] Scheduled Path within record-triggered flow
- [ ] Apex `@future` / Queueable invoked from record-triggered flow

**Event / mechanism name:** _______________

---

## Checklist

Copy from SKILL.md Review Checklist and tick as you complete:

- [ ] Named Credential exists and has Permission Set assigned to the External Credential principal
- [ ] Flow type is not record-triggered (or async dispatch is in place)
- [ ] Every External Service action and HTTP Callout action has a fault connector wired
- [ ] `$Flow.FaultMessage` is captured on the fault path
- [ ] HTTP Callout action responses include a Decision element checking `Response_Status_Code >= 400`
- [ ] No raw API error text is displayed directly to end users
- [ ] Collection variables for array responses are initialized before loop elements
- [ ] Callout volume is within the 100-callout-per-transaction limit
- [ ] External Service spec version recorded; team knows the update procedure
- [ ] Test covers both success and failure paths with real credentials

---

## Notes

Record any deviations from the standard pattern and why:

_______________
