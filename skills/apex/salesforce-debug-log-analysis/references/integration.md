# Integration Patterns in Debug Logs

Salesforce orgs rarely live in isolation. This reference covers callouts, external services, platform events as integration, Change Data Capture, outbound messaging, streaming, and all the ways Salesforce talks to other systems (and they talk back).

## Outbound HTTP Callouts

Apex makes HTTP requests via `HttpRequest` / `Http.send()`.

### Log signatures

```
CALLOUT_REQUEST|[line]|url:https://api.example.com/path|method:GET|headers:...|body:...
CALLOUT_RESPONSE|[line]|status:200|headers:...|body:<size>
```

Timestamp delta between REQUEST and RESPONSE is the callout duration.

### Callout limits

| Limit | Value |
|---|---|
| Max callouts per transaction | 100 |
| Max cumulative callout time | 120 seconds |
| Single callout timeout (default / max) | 10s / 120s |
| Max request body size | 12 MB |
| Max response body size | 6 MB (sync) / 22 MB (async) |

### Async callouts

For long callouts:
- `@future(callout=true)`: simple, fire-and-forget, no retry on failure.
- Queueable with `Database.AllowsCallouts`: can chain and persist state.
- Continuation (VF only): long-running callout without blocking the VF request.

### Common callout errors

- `System.CalloutException: Unauthorized endpoint`: remote site setting missing or named credential misconfigured.
- `System.CalloutException: Read timed out`: remote system too slow.
- `System.CalloutException: SSLPeerUnverifiedException`: cert issue.
- `UNABLE_TO_LOCK_ROW` during callout: cannot have DML before callout, must be reversed.

### Callout from trigger

Direct callouts from triggers are **not allowed** (SF blocks them). The code must go through `@future(callout=true)` or queueable.

If you see a trigger calling `@future`, the log shows:
```
CODE_UNIT_STARTED|[EventService.....trigger]|MyTrigger
...
System.enqueueJob / System.runAs / @future call
CODE_UNIT_FINISHED|MyTrigger
[new log appears later for the async continuation]
```

## Named Credentials

Named Credentials centralize endpoint URL, authentication, and certificate management. Apex uses `callout:<NamedCredential>` as the URL.

### Log signatures

```
NAMED_CREDENTIAL_REQUEST|<credential-name>|<endpoint-resolved>
NAMED_CREDENTIAL_RESPONSE|<credential-name>|<status>
```

Or, older format:
```
CALLOUT_REQUEST|url:callout:MyNamedCredential/resource
```

### Types

- **Legacy Named Credential**: single URL and auth.
- **External Credential + Named Credential (Winter '23+)**: external credential holds auth, named credential holds URL. More composable.
- **Per-User Named Credential**: each user authenticates separately (OAuth).

### Debugging

```bash
grep "NAMED_CREDENTIAL" log.log
```

Common issues:
- 401 Unauthorized: auth expired (for per-user NCs) or misconfigured.
- Username-password NC with MFA enabled remote: fails because MFA requires interactive auth.
- OAuth token expired: SF auto-refreshes for some NCs, not all.

## External Services

External Services let you register a REST API's OpenAPI (Swagger) spec and generate Apex wrappers or Flow invocable actions automatically.

### Log signatures

```
EXTERNAL_SERVICE_REQUEST|<service-name>|<operation>
EXTERNAL_SERVICE_RESPONSE|<service-name>|<status>
```

### Gotchas

- External Services-generated code is read-only and auto-updates when the schema changes.
- Call limits: 50 per transaction.
- Not all OpenAPI specs are supported (some auth types excluded).

## Connect API (internal SF API)

Apex can call `ConnectApi` methods to interact with Chatter, Communities, Files, etc.

### Log signatures

Treated as Apex method calls, not callouts. No `CALLOUT_REQUEST`.

## REST API (inbound)

Custom Apex REST services (`@RestResource`) respond to external HTTP requests.

### Log signatures

```
EXECUTION_STARTED
CODE_UNIT_STARTED|[EventService.....apex]|<MyRestService>.<method>
...
```

The entry point is the Apex method. Running user is the authenticated API user.

Response size limit: 15 MB. Response time limit: 60 seconds.

## SOAP API (inbound)

Apex classes annotated with `webservice` expose SOAP methods. Legacy; most modern integrations use REST or bulk.

### Log signatures

Similar to REST but the entry is the SOAP method.

## Bulk API v1 and v2

For mass data operations.

### Log signatures

Bulk API operations do not log per-record; they log per-job:
```
EXECUTION_STARTED
CODE_UNIT_STARTED|[BulkAPI....]|<job-id>
...
```

### Gotchas

- Bulk API uses `Parallel` mode by default; can cause row-lock contention if records share locks (e.g., multiple updates to children of the same Account).
- Switching to `Serial` mode avoids contention but is slower.
- Bulk API v2 is simpler and recommended for new integrations.

## Platform Events as Integration

Platform Events decouple producers and consumers. An external system can publish an event via REST, and Apex/Flow triggers react.

### Publishing from external system

External POSTs to `/services/data/vXX.X/sobjects/MyEvent__e/` create an event. No triggers fire on the publisher side.

### Subscribing

Apex trigger on `MyEvent__e` fires after commit, in Automated Process user context. In the log, the trigger shows up as a normal after-insert trigger.

### Replay ID

Each event has a ReplayId. Events are retained 72 hours (or 24 for some event types). Subscribers can replay from a specific ReplayId after downtime.

## Change Data Capture (CDC)

CDC publishes events when records change. External systems or Apex can subscribe.

### Configuration

Setup > Change Data Capture > select objects to track.

### Log signatures

When CDC fires:
```
CODE_UNIT_STARTED|[EventService.....trigger]|MyCdcTrigger on Account__ChangeEvent trigger event AfterInsert
```

The event payload includes:
- `ChangeType`: CREATE, UPDATE, DELETE, UNDELETE, GAP_OVERFLOW
- `ChangedFields`: fields that changed
- `RecordIds`: affected record IDs

### Gotchas

- Bulk DML produces one event with multiple record IDs. Trigger must handle the array.
- `GAP_OVERFLOW` indicates the subscriber missed events (fell behind the 72-hour retention).
- CDC respects entitlements: only tracked objects emit events.

## Outbound Messaging (legacy)

Part of Workflow Rules. Fires a SOAP message to an external endpoint.

### Log signatures

```
WF_OUTBOUND_MSG|<endpoint>
```

### Gotchas

- Not retried indefinitely; messages age out of the queue.
- Only SOAP. Modern alternatives: Platform Events or callouts from Apex.

## Streaming API (CometD) / Change Data Capture over Streaming

Long-poll connection for real-time updates. Used by internal UI and external subscribers.

### Log signatures

Streaming is server-to-client; subscribers do not appear in publisher logs. Push Topics (SOQL-based) do, if a client is subscribed:

```
PUSH_TRACE_FLAGS|...
```

## Salesforce Connect (External Objects)

Federated queries against external systems via OData or custom adapters. External data appears as `__x` objects.

### Log signatures

Queries on external objects show up as normal SOQL but with the external namespace/provider.

### Gotchas

- No DML support on most external objects.
- Query performance depends entirely on the external system.
- SOSL queries can federate across external objects.

## MuleSoft / Boomi / iPaaS

These are external integration platforms that use Salesforce's APIs (REST, SOAP, Streaming, Bulk).

### Identifying them in logs

- Running user named like "Mulesoft Integration", "Boomi Service User".
- Custom fields prefixed with package name: `BOOMI_*__c`.
- Incoming traffic in REST API logs.
- Outbound messaging targets with their endpoints.

### Gotchas

- iPaaS tools can hammer Salesforce with high-frequency API calls; monitor daily API usage.
- Some iPaaS tools create their own queues inside SF (custom objects) for retry; if one is stuck, check those.

## OAuth and Connected Apps

External systems authenticate via Connected Apps using OAuth flows.

### Log signatures

Initial OAuth does not appear in Apex logs. The resulting session does: running user is the authenticated user, with client info available via `UserInfo.getClientAppId()`.

### Flows supported

- OAuth 2.0 Authorization Code (web app)
- OAuth 2.0 Username-Password (legacy, deprecated)
- OAuth 2.0 JWT Bearer (server-to-server)
- OAuth 2.0 Client Credentials (machine-to-machine, newer)
- OAuth 2.0 Device Flow (for IoT)

### Common issues

- Refresh token revoked: subsequent calls fail with 401.
- App not enabled for user: `invalid_client` error.
- IP restrictions on Connected App.

## Outbound email

Apex can send email via `Messaging.SingleEmailMessage` or `Messaging.MassEmailMessage`.

### Log signatures

```
EMAIL_QUEUE|<to>|<subject>
TOTAL_EMAIL_RECIPIENTS_QUEUED|<count>
```

### Limits

- 10 email invocations per transaction.
- 5,000 external email recipients per day (paid orgs).
- Mass emails retired in some orgs; use Marketing Cloud or Pardot.

## Inbound email (Email Services)

Email addresses configured to route to an Apex class (`implements Messaging.InboundEmailHandler`).

### Log signatures

```
EXECUTION_STARTED
CODE_UNIT_STARTED|[EmailService]|<class-name>.handleInboundEmail
```

Running user is the "Automated Process" user.

## Diagnostic grep recipes

```bash
# All outbound HTTP
grep "CALLOUT_REQUEST" log.log

# All named credential resolutions
grep "NAMED_CREDENTIAL" log.log

# All external service calls
grep "EXTERNAL_SERVICE" log.log

# All platform event publishes
grep "EVENT_SERVICE_PUB" log.log

# All platform event subscribes
grep "EVENT_SERVICE_SUB" log.log

# All CDC events
grep "ChangeEvent" log.log

# All outbound messages (legacy)
grep "WF_OUTBOUND_MSG" log.log

# Email queuing
grep "EMAIL_QUEUE\|TOTAL_EMAIL_RECIPIENTS" log.log
```

## Common integration failure modes

1. **Callout after DML without async**: SF blocks this. Need to flip: async first, then DML, or callout in queueable.
2. **Expired OAuth token**: refresh token revoked or expired. Requires re-authentication.
3. **Cert expired**: HTTPS callout fails on TLS handshake. Update cert.
4. **Remote endpoint changed**: 404 or connection refused. Named credential URL is stale.
5. **Response parse error**: external system returned HTML error page instead of JSON/XML. Apex tries to parse, throws.
6. **Partial success on bulk**: some records succeed, some fail, but the calling code does not handle. Data split.
7. **Orphaned records after failure**: callout succeeded, but downstream DML failed, leaving the external system updated and SF not.
8. **Event subscriber falls behind**: CDC/platform event retention (72h) exceeded, events lost.
9. **Outbound messaging silently failing**: rotated endpoint URL, OM still points to old one, no visible failure.
10. **Race condition in async**: two queueable jobs enqueued for the same record from different contexts, neither checks if the other already did the work.

## Debugging integration patterns

1. Identify the direction: inbound (external calls SF) or outbound (SF calls external).
2. For outbound, grep `CALLOUT_REQUEST` and check status.
3. For inbound, check Setup > Environments > Apex Jobs (for @future/queueable) or event subscribers.
4. For CDC, check Setup > Change Data Capture: is the object enabled? Event subscription active?
5. For callouts that seem to work but produce bad data, compare request body vs response body vs downstream DML.
6. For OAuth, check Setup > Connected Apps OAuth Usage for error codes.
7. For Platform Events, check Setup > Event Manager for publish success rates.
