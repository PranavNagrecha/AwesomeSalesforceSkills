# Idempotent Integration Patterns — Work Template

Use this template when designing or auditing idempotency in a Salesforce integration.

## Scope

**Skill:** `idempotent-integration-patterns`

**Integration name/system:** ___

**Integration direction:** [ ] Inbound (external → Salesforce)  [ ] Outbound (Salesforce → external)  [ ] Both

**Mechanism:** [ ] REST API  [ ] Bulk API  [ ] Platform Events  [ ] Outbound Messages  [ ] Multiple

## Inbound Idempotency Design

**Idempotency mechanism selected:**
- [ ] External ID Upsert (preferred)
- [ ] Idempotency key log in Salesforce
- [ ] External system handles retries idempotently (document how)

### External ID Upsert (if selected)

| Setting | Value |
|---|---|
| Object | |
| External ID Field API Name | |
| Field marked as External ID? | [ ] Yes |
| Field marked as Unique? | [ ] Yes — REQUIRED |
| API call type | PATCH (not POST) |
| External ID path | /sobjects/{Object}/{Field}/{value} |

### Idempotency Key Log (if selected)

| Setting | Value |
|---|---|
| Key generation timing | Once before first attempt (not per retry) |
| Key storage location | |
| Check-before-process logic location | |
| Log purge policy | After ___ days |

## Outbound Idempotency Design

**Platform Events:**
- [ ] Publish After Commit configured for all transactional events
- [ ] Subscriber implements deduplication on CorrelationId or equivalent
- [ ] ReplayId persisted for subscriber recovery

**Outbound Messages:**
- [ ] External system implements deduplication on Salesforce record ID
- [ ] Duplicate window defined: ___ minutes

## Idempotency Key Review

- [ ] Key generated ONCE before first attempt (not inside the retry loop)
- [ ] Key reused for all retries of the same logical operation
- [ ] Key is opaque (UUID or hash, not plaintext business data)

## Testing

| Test Scenario | Expected Result | Actual Result |
|---|---|---|
| Same API call sent twice | Single record created | |
| Platform Event published, transaction rolled back | No subscriber processing | |
| Outbound Message delivered twice | Single processing in external system | |

## Checklist

- [ ] Inbound: PATCH with External ID (not POST)
- [ ] Inbound: External ID field is Unique
- [ ] Inbound: Idempotency key generated once (not per retry)
- [ ] Platform Events: Publish After Commit for transactional events
- [ ] Platform Events: Subscriber deduplication implemented
- [ ] Outbound: External system deduplicates on record ID
- [ ] All retry scenarios tested with duplicate-prevention verified

## Notes

(Record design decisions and any exceptions with justification.)
