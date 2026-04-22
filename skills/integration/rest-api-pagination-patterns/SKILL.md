---
name: rest-api-pagination-patterns
description: "REST API pagination for inbound and outbound integrations: Salesforce QueryMore, cursor-based, offset-based, Link header, page-size tuning, rate limit interaction. NOT for Bulk API (use bulk-api-patterns). NOT for GraphQL connection pagination (use graphql-api-patterns)."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Reliability
tags:
  - rest
  - pagination
  - querymore
  - cursor
  - offset
  - link-header
triggers:
  - "salesforce querymore nextrecordsurl pagination apex callout"
  - "rest api cursor based vs offset pagination"
  - "link header pagination github style rfc5988"
  - "rate limit interaction with pagination loop"
  - "offset pagination drift on insert delete"
  - "batch size tuning for inbound rest integration"
inputs:
  - Integration direction (inbound to Salesforce, outbound from Salesforce)
  - API style (cursor, offset, Link header, custom)
  - Total result magnitude
  - Rate limit profile
outputs:
  - Pagination loop pattern
  - Termination condition
  - Retry / rate-limit interaction
  - Volume test plan
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-21
---

# REST API Pagination Patterns

Activate when integrating with a paginated REST API — either consuming an external API from Apex or serving a paginated endpoint from Salesforce. Pagination mistakes cause three classic failures: infinite loops, missed records, and duplicate records due to concurrent writes between page fetches.

## Before Starting

- **Identify pagination style.** Cursor / Next-link / Offset / Link-header / Token-based — all have different termination semantics.
- **Plan termination.** Every pagination loop needs a safety cap (max iterations) plus the documented termination signal.
- **Respect rate limits.** Back off on 429; implement exponential backoff.

## Core Concepts

### Salesforce QueryMore (outbound to external consumer)

```
/services/data/v60.0/query?q=SELECT+Id+FROM+Account
→ { "done": true, "nextRecordsUrl": "/services/data/v60.0/query/01g...", "records": [...] }
```

Loop: fetch `nextRecordsUrl` until `done == true`.

### Cursor-based (opaque token)

Response includes a cursor string; pass back as `?cursor=<value>` until the server returns an empty cursor or explicit end-of-stream flag.

### Offset / limit

Classic `?offset=0&limit=100`. Simple but vulnerable to drift: records inserted/deleted between pages cause missed or duplicate rows.

### Link header (RFC 5988)

```
Link: <https://api/x?page=2>; rel="next", <https://api/x?page=10>; rel="last"
```

Parse headers; loop until no `rel="next"` present.

### Rate limit headers

`X-RateLimit-Remaining`, `Retry-After` — consult before issuing the next page.

## Common Patterns

### Pattern: QueryMore loop in Apex

```
HttpResponse resp = http.send(req);
Map<String,Object> body = (Map<String,Object>) JSON.deserializeUntyped(resp.getBody());
List<Object> all = new List<Object>();
all.addAll((List<Object>) body.get('records'));
while (body.get('done') == false) {
    String nextUrl = (String) body.get('nextRecordsUrl');
    HttpRequest r2 = new HttpRequest();
    r2.setEndpoint(base + nextUrl);
    // auth ...
    resp = http.send(r2);
    body = (Map<String,Object>) JSON.deserializeUntyped(resp.getBody());
    all.addAll((List<Object>) body.get('records'));
}
```

### Pattern: Cursor loop with safety cap

```
String cursor = null;
Integer safetyCap = 1000; // max pages
for (Integer i = 0; i < safetyCap; i++) {
    // fetch with cursor
    if (cursor == null || cursor == '') break;
}
if (i == safetyCap) throw new IntegrationException('Pagination safety cap hit');
```

### Pattern: Rate-limit-aware pagination

Check `X-RateLimit-Remaining`; if < threshold, sleep per `Retry-After` before next page. In Apex: use Queueable chaining for long-running paginations (cannot `Thread.sleep`).

## Decision Guidance

| Situation | Pagination style |
|---|---|
| Salesforce inbound data | QueryMore |
| Large stable dataset | Cursor |
| Small dataset, admin UI | Offset/limit |
| Complex filter with stable ordering | Cursor |
| Lots of concurrent writes | Cursor with created-since filter |

## Recommended Workflow

1. Identify the source API's pagination style from documentation.
2. Implement the loop with an explicit termination signal AND a safety cap.
3. For offset/limit: either confirm dataset is stable or add resume tokens.
4. Parse rate-limit headers; back off on 429.
5. For long paginations in Apex, chain Queueables — each handles one page batch.
6. Persist intermediate results in case of mid-stream failure.
7. Write integration test that mocks 3+ pages including empty-tail.

## Review Checklist

- [ ] Termination signal matches API spec
- [ ] Safety cap on page count (avoid infinite loops)
- [ ] Rate-limit headers honored
- [ ] Apex: long paginations chained via Queueable (callout limit: 100/transaction)
- [ ] Resume/checkpoint on mid-stream failure
- [ ] Test mocks multi-page and empty-tail
- [ ] No blind offset pagination on mutable data

## Salesforce-Specific Gotchas

1. **Apex has a 100-callout-per-transaction limit.** Paginating over thousands of pages requires Queueable chaining.
2. **QueryMore cursor expires after ~15 minutes.** Long paginations need restart logic if they straddle the expiry.
3. **`Test.setMock` supports only one response per request.** Multi-page tests need a mock class tracking call count.

## Output Artifacts

| Artifact | Description |
|---|---|
| Pagination helper Apex class | Reusable loop with safety cap |
| Rate-limit-aware http wrapper | Backoff + retry |
| Integration test fixtures | Multi-page mocks |

## Related Skills

- `integration/bulk-api-patterns` — for large-volume data operations
- `integration/rate-limit-handling` — backoff strategies
- `apex/apex-queueable-patterns` — chaining for long-running callouts
