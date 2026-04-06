# Retry and Backoff Patterns — Work Template

Use this template when designing or reviewing retry logic for an Apex callout integration.

## Scope

**Skill:** `retry-and-backoff-patterns`

**Request summary:** (fill in what the user asked for — e.g., "Add retry logic to the order sync Queueable")

## Context Gathered

Answer the Before Starting questions from SKILL.md before proceeding:

- **Execution context of callout:** [ ] Synchronous (trigger/controller — must move to Queueable first) / [ ] Queueable / [ ] Batch
- **Idempotency requirement:** [ ] Target system is idempotent (safe to retry same payload) / [ ] Not idempotent (External_Id__c + upsert guard required)
- **Current async Apex usage:** ___% of daily Queueable limit consumed (check AsyncApexJob)
- **Target system error behavior:** HTTP codes returned on failure: ___

## Retry Configuration

| Parameter | Value | Source |
|---|---|---|
| `maxRetries` | e.g., 4 | `Retry_Config__mdt.Max_Retries__c` |
| `baseDelaySeconds` | e.g., 2 | `Retry_Config__mdt.Base_Delay_Seconds__c` |
| `maxDelaySeconds` | e.g., 60 | `Retry_Config__mdt.Max_Delay_Seconds__c` |
| Retriable status codes | e.g., 429, 503, 500 | Agreed with API owner |
| Non-retriable codes | e.g., 400, 401, 403, 404 | Dead-letter immediately |

## Pattern Selection

Which pattern from SKILL.md applies?

- [ ] **Queueable Retry Chain** — callout fails with transient error, needs automatic re-attempt
- [ ] **Circuit Breaker** — external system has extended outages; need operator-controlled halt
- [ ] **Idempotency Key Guard** — downstream system does not deduplicate; POST/PUT/PATCH retries
- [ ] **Native Platform Retry** — using Outbound Messages or Platform Events (no Apex retry needed)

**Justification:** (explain why this pattern applies)

## Implementation Checklist

- [ ] Callout is in Queueable or Batch context (not synchronous)
- [ ] `maxRetries` read from `Retry_Config__mdt` — not hardcoded
- [ ] Exponential backoff formula: `baseDelay * 2^retryCount + (Math.random() * baseDelay)`
- [ ] Idempotency key field (`External_Id__c`) exists on driving SObject
- [ ] Key generated before first enqueue and passed unchanged through constructor on re-enqueue
- [ ] `X-Idempotency-Key` header set on every callout attempt
- [ ] DML (logging, status update) occurs AFTER the callout block — not before
- [ ] Dead-letter path inserts `Failed_Integration_Log__c` when `retryCount >= maxRetries`
- [ ] Circuit breaker CMDT checked at start of `execute()`
- [ ] Only 429, 5xx (excluding 501), and `CalloutException` trigger retry — 4xx goes to dead-letter
- [ ] Apex tests mock HTTP 429, 503, and timeout — assert retry counter and dead-letter creation
- [ ] `Failed_Integration_Log__c` does not store PII or credential fields

## Dead-Letter Record Fields

Confirm `Failed_Integration_Log__c` captures:

| Field | Type | Purpose |
|---|---|---|
| `Record_Id__c` | Lookup/Text | Links log to driving record |
| `Error_Message__c` | Long Text | Raw error or HTTP body |
| `HTTP_Status__c` | Number | HTTP status code (0 for timeout) |
| `Retry_Count__c` | Number | Number of attempts made |
| `Idempotency_Key__c` | Text | Key used — enables tracing |
| `Status__c` | Picklist | Retrying / Dead Letter / Resolved |
| `Timestamp__c` | DateTime | Time of final failure |

## Notes

(Record any deviations from the standard pattern and why — e.g., "Circuit breaker is manual-only because the team does not have an automated health-check mechanism.")
