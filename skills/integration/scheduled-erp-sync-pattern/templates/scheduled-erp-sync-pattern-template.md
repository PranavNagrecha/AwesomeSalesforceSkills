# Scheduled ERP Sync Pattern — implementation template

Use this as the starting point when wiring a Salesforce ↔ ERP scheduled sync. Replace placeholders in `{{...}}` with org-specific values.

## Architecture

```
+-------------------+    Scheduled (15 min / hourly / nightly)
| Schedulable class | --> System.scheduleBatch(...) or System.enqueueJob(new {{Sync}}Queueable())
+-------------------+
            |
            v
+-------------------+    callout via Named Credential
| Queueable         | -->  http(s)://{{erp-named-credential}}/{{endpoint}}
| (AllowsCallouts)  |
+-------------------+
            |
            +--> upsert into staging custom object {{ERP_Staging__c}}
            +--> publish PE on partial success: {{ERP_Sync_Failure__e}}
            +--> increment watermark on Custom Metadata Type {{Watermark__mdt}}
```

## Watermark CMD

Custom Metadata Type `{{ERP_Sync_Watermark__mdt}}` with fields:

- `Object__c` (text) — sync target object name
- `Last_Successful_Run__c` (datetime)
- `Last_Cursor__c` (text) — opaque cursor returned by ERP, NULL on first run
- `Mode__c` (picklist: `timestamp`, `cursor`, `full-refresh`)

## Named Credential

Setup → Named Credentials → New, type "External Credential". Configure:

- Authentication: `JWT Bearer Flow` (preferred) or `Password` (legacy ERP only).
- Service Account: a non-human user with read-only access to the ERP source feed.
- Scopes: minimal — read on sync objects, no admin scopes.

## Failure Handling

- In-cycle: try-catch around each callout with exponential backoff (1s, 4s, 16s).
- Cycle-level: catch unhandled exceptions in `Schedulable.execute()`, write to `{{Sync_Failure_DLQ__c}}` custom object, publish `{{ERP_Sync_Failure__e}}` event.
- Multi-cycle: scheduled monitor that queries `{{Sync_Failure_DLQ__c}}` for N consecutive failures and pages an admin via Custom Notification.

## Volume thresholds — switch from this pattern to:

- **>50k records per cycle** → Bulk API 2.0 ingest
- **<5 minute SLA** → Change Data Capture (CDC) or Pub/Sub API
- **Bi-directional sync** → Add SF→ERP path with Platform Events + Apex publisher; otherwise this pattern is one-way pull only.
