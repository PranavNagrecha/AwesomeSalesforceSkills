# Well-Architected Notes — FSL Integration Patterns

## Relevant Pillars

- **Reliability** — FSL integration reliability depends on idempotent operations. ProductConsumed upserts to ERP must use External IDs to prevent duplicate consumption records on retry. Platform Events with dead-letter queuing or replay handles transient integration failures.
- **Performance** — Outbound polling to GPS/fleet APIs at high frequency exhausts Daily API limits. Integration design must account for Salesforce's per-org API limit as a finite shared resource. Inbound push from external systems is architecturally preferable to outbound polling.
- **Security** — ERP and IoT integrations use Named Credentials for outbound authentication. External system credentials must not be stored in Apex code or custom settings. FSL Mobile status transitions that trigger customer-facing notifications must validate the notification is appropriate for the appointment context before sending.

## Architectural Tradeoffs

**Platform Events vs. Outbound Messages vs. Callouts:** Platform Events are the preferred mechanism for event-driven integrations from FSL. They are async, scalable, and have replay capability. Outbound Messages (SOAP) are legacy and synchronous. Direct Apex callouts from triggers are synchronous and subject to callout-DML constraints — use Queueable for any Apex-based outbound integration.

**Real-time vs. near-real-time vs. batch for ERP sync:** Real-time (on-event) parts consumption sync to ERP is architecturally clean but adds latency to the FSL Mobile record-save path. Near-real-time (Platform Event, 1–5 minute lag) is the best balance for most implementations. Batch (nightly) creates inventory discrepancies during the work day that affect dispatch decisions.

## Anti-Patterns

1. **FSL scheduling callouts inside Platform Event handlers** — Platform Event handlers have DML-before-callout constraints. Always queue scheduling in a Queueable from the event handler.
2. **Missing ERP feedback loop for ProductConsumed** — Inbound-only ERP integration creates phantom stock in ERP. The outbound consumption feedback must be explicitly designed and implemented.
3. **High-frequency outbound GPS polling** — Consumes Daily API limits disproportionately. Fleet systems must push to Salesforce, not be polled by Salesforce.

## Official Sources Used

- Field Service Developer Guide v66.0 (developer.salesforce.com) — https://developer.salesforce.com/docs/atlas.en-us.field_service_dev.meta/field_service_dev/fsl_dev_guide.htm
- Field Service Inventory Management Data Model — https://developer.salesforce.com/docs/atlas.en-us.field_service_dev.meta/field_service_dev/fsl_dev_data_model_inventory.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
