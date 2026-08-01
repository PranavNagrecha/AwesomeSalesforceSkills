# Pub/Sub API Error Codes — Decoder

**Open this file on a symptom. Do not preload it.**

Pub/Sub API returns a gRPC status *and*, separately, a Salesforce-specific error code: "Pub/Sub API adds a custom error code in the Trailers section of the exception. You can retrieve the custom error code by calling `getTrailers()` on the exception." The gRPC status alone is not actionable — the same `UNAVAILABLE` or `INTERNAL` status maps to several different recovery actions. Branch on the `sfdc.platform.eventbus.grpc.*` string.

The exception also carries a support correlation ID: "the exception contains an RPC ID that the Pub/Sub API appends to the error message after the `rpcId:` prefix." Capture it in your log line — Salesforce Customer Support cannot trace the failure without it.

Codes below are shown with the `sfdc.platform.eventbus.grpc.` prefix stripped for width; the literal string always carries it.

## Service, connection, and auth

| Code (suffix) | What happened | Retry? | Action |
|---|---|---|---|
| `service.unavailable` | Pub/Sub API service unavailable | Yes | Retry later with exponential backoff |
| `service.auth.error` | Authentication exception. Also fires on IP session locking and across Salesforce release windows | Yes, after re-auth | Verify credentials, check IP session settings, fetch a new session token after a major release |
| `service.auth.headers.invalid` | Auth header value invalid or blank | No | Supply valid `accesstoken` / `instanceurl` / `tenantid` (18-char org ID) |
| `service.auth.refresh.invalid` | Auth refresh token invalid | No | Supply a valid refresh token |
| `service.protection.stream.limit.triggered` | Too many PublishRequests or FetchRequests on the stream | Yes, slower | Reduce request frequency; this is client-side pacing, not a quota |
| `service.protection.triggered` | Excessive connections or requests | Yes, slower | Retry with reduced load |
| `service.tenant.license` | Org is not licensed for Pub/Sub API | No | Contact Salesforce to enable; retry only once enabled |
| `concurrent.client.limit.exceeded` | Maximum concurrent clients across all topics exceeded | No | Reduce the number of active publisher/subscriber clients |

## Topic and schema

| Code (suffix) | What happened | Retry? | Action |
|---|---|---|---|
| `topic.not.found` | The topic does not exist | **Never** | Permanently fatal for that name — retrying is an infinite loop. Confirm the topic name and that the entity is CDC-enabled or the platform event is deployed |
| `topic.meta.permission` | Topic metadata access error | No | Verify credentials and topic name |
| `topic.api.unavailable` | Topic information temporarily unavailable | Yes | Retry |
| `topic.validation.empty` | Topic name blank | No | Provide a topic name |
| `schema.meta.permission` | Schema access error | No | Verify the schema ID and the credentials used to fetch it |
| `schema.api.unavailable` | Schema information unavailable | Yes | Retry |
| `schema.validation.failed` | Schema ID blank or missing | No | Provide a non-blank schema ID |

## Subscribe

| Code (suffix) | What happened | Retry? | Action |
|---|---|---|---|
| `subscription.fetch.replayid.corrupted` | Replay ID invalid or outside the retention window | Not as-is | Resubscribe with a different `ReplayPreset` — see the trade-off in `references/gotchas.md` before reflexively choosing EARLIEST |
| `subscription.fetch.replayid.validation.failed` | `ReplayPreset` is CUSTOM but no replay ID was supplied | No | Supply the replay ID, or use LATEST/EARLIEST |
| `subscription.fetch.replay.repeated` | An event arrived with a lower replay ID than the previous one | No | Restart the subscription |
| `subscription.limit.exceeded` | The org's 24-hour event delivery allocation is exhausted | **Never** | Retrying burns nothing and fixes nothing — the allocation is org-wide and rolling. Wait for the next 24-hour period, cut subscriber count, or buy the add-on |
| `subscription.fetch.overflow` | The client requested more events than it drained | No | Process the outstanding events before issuing the next FetchRequest |
| `subscription.fetch.requested.events.invalid` | `num_requested` not greater than zero | No | Request > 0 events |
| `subscription.fetch.topic.mismatch` | Topic name differs between requests on the same stream | No | Keep the topic constant for the life of the stream |
| `subscription.fetch.request.invalid` | Fetch request missing auth refresh | No | Include the auth refresh |
| `subscription.topic.cannot.subscribe` | Insufficient permissions for the topic | No | Grant the subscribing user read access to the platform event / change event |
| `subscription.internal.error` | Internal subscription error | Yes | Restart the subscription |

## Publish

| Code (suffix) | What happened | Retry? | Action |
|---|---|---|---|
| `publish.stream.sweeper.timeout` | No publish request sent during the 1,800-second window | Yes | Reopen the stream; send a keepalive publish or accept periodic reconnects |
| `publish.auth.refresh.invalid` | A refresh token was present in the **initial** publish request, where it is not allowed | No | Remove it from the first request; send it on subsequent requests only |
| `publish.event.count.invalid` | Request contained no events | No | Include at least one event |
| `publish.topic.mismatch` | Topic name mismatch between requests | No | Keep the topic constant |
| `publish.topic.validation.empty` | Topic name blank | No | Provide a topic name |

## Managed Subscribe (Beta)

| Code (suffix) | What happened | Retry? | Action |
|---|---|---|---|
| `managed.subscription.already.active` | An active subscription with the same ID already exists | Yes, later | Wait for the prior subscription to expire before reconnecting |
| `managed.subscription.config.stopped` | The `ManagedEventSubscription` state is STOP | No | Change the state to RUN — this is a metadata fix, not a client fix |
| `managed.subscription.config.deleted` | The subscription configuration was deleted | No | Recreate or point at an existing configuration |
| `managed.subscription.developer.name.not.found` | No configuration for that developer name | Yes if just created | Verify the developer name; a freshly deployed record may need a moment |
| `managed.subscription.subscription.id.not.found` | No configuration for that subscription ID | Yes if just created | Verify the ID |
| `managed.subscription.subscription.id.invalid` | Subscription ID is the wrong length | No | Use a 15- or 18-character ID |
| `managed.subscription.id.or.developer.name.empty` | Both ID and developer name supplied | No | Supply exactly one identifier |
| `managed.subscription.fetch.request.events.invalid` | Requested events not >= 0 | No | Request >= 0 |
| `managed.subscription.fetch.request.invalid` | Missing `CommitReplayRequest` or auth refresh | No | Include the required element |
| `managed.subscription.fetch.request.commit.request.restricted` | `CommitReplayRequest` present in the initial request | No | Exclude it from the first fetch |
| `managed.subscription.fetch.request.auth.request.restricted` | Auth refresh present in the initial request | No | Exclude it from the first fetch |

Managed Subscribe commit failures are different in kind: they arrive inside `CommitResponse` and **do not terminate the connection**. The documented cases are a missing replay ID, an invalid or out-of-retention replay ID, a commit issued before the event was delivered, a generic commit failure, and a request whose replay ID is older than the currently committed one. Handle them on the response, not in the stream's error path.

## Official Sources Used

- Pub/Sub API — Handle Errors (full error-code table, `getTrailers()`, `rpcId:` prefix): https://developer.salesforce.com/docs/platform/pub-sub-api/guide/handling-errors.html
- Pub/Sub API — Retry Long-Lived RPC Calls After an Error Occurs: https://developer.salesforce.com/docs/platform/pub-sub-api/guide/retry-rpc-calls.html
- Pub/Sub API — Event Message Durability: https://developer.salesforce.com/docs/platform/pub-sub-api/guide/event-message-durability.html
