# Pub/Sub API Patterns — Work Template

## Scope

**Skill:** `pub-sub-api-patterns`

**Request summary:** (fill in: subscribe to events, publish events, or Managed Subscription setup)

## Connection Details

- **Topic name:** `/event/<EventName>__e` or `/data/<ObjectName>ChangeEvent`
- **Access token:** (from standard Salesforce OAuth)
- **Instance URL:**
- **Tenant ID (18-char Org ID):** (verify 18 chars via `SELECT Id FROM Organization`)

## RPC Method Selection

- **Subscribe** — stateful consumer, client-side replay ID tracking
- **ManagedSubscribe** — stateless consumer, server-side replay tracking (200-subscription org limit)
- **Publish / PublishStream** — outbound event publishing

## Replay Strategy

- **Replay preset:** [ ] LATEST (new events only)  [ ] EARLIEST (from 3 days back)  [ ] CUSTOM (specify ID)
- **Last known replay ID:**
- **Replay ID persistence store:** [ ] Redis  [ ] Database  [ ] N/A (ManagedSubscribe)

## Subscription Configuration

- **FetchRequest num_requested:** ___ (max 100 per request)
- **For ManagedSubscribe:** Subscription name:
- **Token refresh interval:** < 2 hours (pre-emptive, before session expiry)

## Publish Configuration (if applicable)

- **Batch size:** ___ events (max 200) / ___ MB (max 4 MB per batch)
- **Streaming or unary:** [ ] Publish  [ ] PublishStream

## Checklist

- [ ] tenantid is 18-character Org ID (confirmed via SOQL)
- [ ] Proto stubs generated from official Salesforce Pub/Sub API proto file
- [ ] Token refresh implemented (< 2-hour pre-emptive refresh)
- [ ] Replay ID persisted after each processed batch
- [ ] FetchRequest num_requested ≤ 100
- [ ] Publish batches ≤ 200 events and ≤ 4 MB
- [ ] 3-day event retention window factored into downtime SLA

## Notes

(Record Managed Subscription name, consumer lag monitoring approach, dead-letter strategy)
