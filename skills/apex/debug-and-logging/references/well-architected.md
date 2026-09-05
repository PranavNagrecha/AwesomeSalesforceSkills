# Well-Architected Notes — Debug And Logging

## Relevant Pillars

### Operational Excellence

This skill is primarily about making Apex supportable. Teams cannot operate what they cannot observe.

Tag findings as Operational Excellence when:
- failures leave no durable record
- debug output is noisy or unstructured
- async processes cannot be traced from business action to job failure

### Reliability

Observability supports reliable systems because silent failures and opaque async behavior delay remediation.

Tag findings as Reliability when:
- exceptions are swallowed with only debug output
- support cannot distinguish transient versus systemic failures
- batch or queueable processing lacks failure visibility

## Architectural Tradeoffs

- **Rich logs vs minimal logs:** more detail helps diagnosis until it overwhelms support or leaks data.
- **Debug logs vs structured logs:** debug logs are fast to add; structured logs are what production support needs.
- **Central logger vs ad hoc logging:** centralization adds discipline and correlation, but only if teams use it consistently.

## Anti-Patterns

1. **Production observability built on `System.debug`** — transient and weak.
2. **Secret-bearing logs** — useful in the moment, harmful in operation.
3. **No async correlation** — async failures become disconnected from business impact.

## Sink Selection

| Failure you must still be able to explain tomorrow | Sink | Why this one |
|---|---|---|
| A breadcrumb in a transaction that commits | `Application_Log__c` via `ApplicationLogger` | One buffered DML; rolls back with the transaction, which is fine because the transaction succeeded |
| An exception that rolls the transaction back | `Log_Event__e` with `publishBehavior` `PublishImmediately` | Published "regardless of whether the transaction succeeds" (api_meta L42225–42227) |
| A Queueable that died on a limit exception | Finalizer, flushing both sinks | The finalizer runs on `SUCCESS` and `UNHANDLED_EXCEPTION` alike (Apex Developer Guide L16337–16340) |
| A one-off reproduction in a sandbox | Debug log, class-scoped trace flag | Free, immediate, expires on its own — which is the point |
| Cross-request correlation for a support ticket | `ApexLog.RequestIdentifier` joined to `Request_Id__c` | The request identifier "correlate[s] multiple debug logs triggered by the same request" (Object Reference, ApexLog) |

## Cost Of The Choice

- Publish-immediately events are metered separately at **150 `EventBus.publish` calls** per transaction
  (Apex Developer Guide L19598–19599), so they cannot be the sink for per-record breadcrumbs.
- Publish-after-commit events are metered as **DML statements** against the same 150 the business logic
  is spending (Apex Reference Guide L214524–214528).
- Debug logs are metered by volume, not by count: 20 MB per log, 1,000 MB per org before trace-flag
  edits are blocked (Apex Developer Guide L38115–38126).

## Official Sources Used

- Apex Developer Guide, "Debug Log Limits" (L38115–38126) — the 20 MB per-log truncation, the 24-hour /
  seven-day retention split, and the 1,000 MB trace-flag disable thresholds cited in gotchas.md.
- Apex Developer Guide, "Debug Log Categories" / "Debug Log Levels" / "Debug Log Order of Precedence"
  (L38341–38400, L39539–39575) — the eight cumulative levels, the seven categories, the `FINEST`
  sensitive-data and deployment warnings, and the precedence of trace flags over API header and
  entry-point levels.
- Apex Reference Guide, `System.debug` and `LoggingLevel` Enum (L238857–238914, L222081–222114) — that
  the no-level overload uses `DEBUG`, that filtering happens at write time, and that `System.debug`
  calls are not counted toward code coverage.
- Apex Reference Guide, `Limits` Class (L220152–220290) and `EventBus` Class (L214496–214600) — the
  `Limits` getters used in `LogService.limitsSnapshot()`, and the `Database.SaveResult` contract
  including that a failed publish never throws.
- Metadata API Developer Guide, `CustomObject.publishBehavior` / `eventType` (L42091–42097,
  L42206–42229) and `PlatformEventSubscriberConfig` (L96385–96497) — the `PublishImmediately` semantics,
  the deprecation of `StandardVolume`, and the Automated Process running-user behaviour that makes the
  subscriber config mandatory for a logging trigger.
- Metadata API Developer Guide, `ApexEmailNotifications` (L22368–22500) — the deployable exception-email
  fence, its destructive replace-on-deploy behaviour, and its exclusion from `destructiveChanges.xml`.
- Object Reference, `ApexLog` (L31266–31380) and `AsyncApexJob` (L42262+) — the queryable log fields
  (`RequestIdentifier`, `LogLength`, `Location`, `Status`), the read/delete-only access rule, and the
  async job fields used for correlation.
- Salesforce Well-Architected Overview — operational excellence and reliability framing for the
  pillar tags above.
