# Well-Architected Notes — Apex Metadata API

## Relevant Pillars

- **Operational Excellence** — Apex Metadata API deployments are asynchronous, fire-and-forget operations. Operational excellence requires that every deployment logs its result, handles failure, and provides visibility into deployment state. Without a `DeployCallback` that writes structured audit records, failed deployments are invisible.
- **Scalability** — The 10 concurrent deployment limit per org constrains how this pattern scales. Any scenario that involves multiple simultaneous deployments must account for this limit explicitly, either through serialization queues or throttling logic.
- **Reliability** — The callback-based delivery model means that failures are discovered late — after the transaction has returned to the caller. Reliable implementations must store job IDs, implement failure handling, and design for the case where the callback never fires (platform disruption, org lock).

## Architectural Tradeoffs

**Apex Metadata API vs SOAP/REST Metadata API:** The Apex Metadata API is in-platform, does not require callout credentials or external connectivity, and respects Apex sharing and security context. The tradeoff is a far smaller supported type catalog and the 10-deployment concurrent limit. The SOAP Metadata API supports every metadata type but requires external server-to-server configuration and cannot run natively inside a transaction.

**Runtime Schema Creation vs Package Deployment:** Creating metadata at runtime via Apex allows per-subscriber customization without a new package version. The tradeoff is that runtime-created schema is harder to audit, version-control, or roll back compared to metadata bundled in a package. Only use runtime creation where subscriber-specific conditions genuinely require it.

**Synchronous Feedback vs Asynchronous Callback:** There is no synchronous path for Apex Metadata API deployments. If a UI or process flow requires immediate confirmation, it must poll or use a platform event pattern to signal completion. Design for async from the start rather than retrofitting later.

## Anti-Patterns

1. **Silent Callback — no logging in handleResult()** — implementing `Metadata.DeployCallback` with an empty or debug-only body means failures disappear. Production implementations must write structured audit records (custom object insert in the callback is safe since it runs in its own transaction).
2. **Looping enqueueDeployment calls without serialization** — deploying many components by calling `enqueueDeployment` in a loop hits the 10-deployment limit and causes unhandled `LimitException`. Always chain deployments through the callback rather than in bulk.
3. **Assuming Apex Metadata API covers all types** — generating code for types not in the supported subset (such as `Flow`, `ApexClass`, `PermissionSet`) leads to runtime failures that are hard to trace because they surface in the async callback, not at the call site.

## Official Sources Used

- Apex Reference Guide — Metadata namespace, Metadata.Operations class, Metadata.DeployCallback interface, supported metadata type subclasses
  URL: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_ref_guide.htm
- Apex Developer Guide — asynchronous Apex patterns, Queueable, transaction boundaries, post-install scripts
  URL: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm
- Salesforce Well-Architected Overview — Operational Excellence and Scalability pillar framing
  URL: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Metadata API Developer Guide — metadata type catalog reference; used to understand type support boundaries between SOAP Metadata API and Apex Metadata API
  URL: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
