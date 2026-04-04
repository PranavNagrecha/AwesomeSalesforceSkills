# Gotchas — Integration Framework Design

Non-obvious Salesforce platform behaviors that cause real production problems when building a centralized integration framework.

---

## `Type.forName()` Requires Fully Qualified Class Name in Managed Packages

**What happens:** `Type.forName('MyService')` returns `null` in a managed package context. `null` causes `NullPointerException` when the factory calls `newInstance()`.

**When it occurs:** When the integration framework is packaged as a managed package and subscriber orgs install it. The subscriber org's class namespace differs from the package namespace.

**Fix:** Store the fully-qualified class name including namespace prefix in `Service_Class__c` on `Integration_Service__mdt`: e.g. `mynamespace.KycIntegrationService`. The factory should guard against a `null` return from `Type.forName()` and throw `IntegrationException` with `SERVICE_DISABLED` code so the failure is explicit and traceable rather than a bare NPE.

---

## Custom Metadata Records Are NOT Auto-Included in `package.xml` Deploys

**What happens:** `Integration_Service__mdt` records exist in the source org. A standard `sfdx force:source:push` or metadata retrieve without explicit `CustomMetadata` entries in `package.xml` does not include them. The target org deploys the Custom Metadata Type definition but has zero records.

**When it occurs:** First deployment to a new sandbox or production via Salesforce CLI without explicit record inclusion. The factory resolves no records and every `resolve()` call throws a query exception or `SERVICE_DISABLED` error.

**Fix:** Explicitly add `CustomMetadata` members to `package.xml` for each record: `Integration_Service__mdt.Payment_US`, etc. In sfdx project format, Custom Metadata records live under `force-app/main/default/customMetadata/` and are tracked as source. Confirm all records are tracked in version control and included in every deployment set. Consider a post-deployment validation script that queries CMDT counts and alerts on zero-record deployments.

---

## Synchronous Logging Hits DML Limits in Trigger Context

**What happens:** `IntegrationLog__c` insert inside the dispatcher runs synchronously. If the dispatcher is called from a trigger context (e.g., a callout queued via a trigger on an async context), DML operations count against governor limits that are already partially consumed by the triggering transaction's DML.

**When it occurs:** When the integration framework is called from a Queueable or Batch that was enqueued from a trigger, logging DML is safe. But if someone calls the dispatcher inline from a trigger (which is itself a DML-before-callout violation), the entire transaction fails with uncommitted-work callout exceptions long before logging limits are hit.

**Correct approach:** Never make synchronous callouts from triggers. Use Platform Events to decouple trigger-initiated integration: the trigger inserts a Platform Event, a subscribing Queueable picks it up, calls the dispatcher, and the logger writes `IntegrationLog__c` in the Queueable's clean transaction.

**Alternative for high-volume logging:** If every callout generating a synchronous `IntegrationLog__c` insert approaches DML limits in batch or Queueable chains, switch `IntegrationLogger` to publish a `Integration_Log_Event__e` Platform Event. A separate trigger on that event writes `IntegrationLog__c` in its own transaction, keeping the callout transaction clean.

---

## `Type.forName()` Returns `null` for Abstract and Inner Classes

**What happens:** The factory instantiates service classes using `Type.forName()`. Abstract classes and non-public inner classes cannot be instantiated this way. `Type.forName()` returns non-null for the type but `newInstance()` throws an `IllegalAccessException` or returns an unusable object.

**When it occurs:** When a developer registers an abstract base class or a private inner class name in `Integration_Service__mdt` by mistake.

**Fix:** Enforce in code review that only top-level, non-abstract, public classes implementing `IIntegrationService` are registered in CMDT. Consider adding a validation check in the factory: after `newInstance()`, verify the object implements `IIntegrationService` using an `instanceof` check before returning it.

---

## Retry Logic Without Budget Tracking Triggers Apex CPU and Callout Limits

**What happens:** A naive retry loop in `HttpCalloutDispatcher` retries on 429 or 503 up to N times without checking remaining governor limits. Three synchronous retries with a 1-second sleep between them can exhaust the CPU time limit (10,000 ms per transaction). Salesforce does not allow `Thread.sleep()` in Apex — workarounds using busy-loops are worse.

**When it occurs:** When retry is implemented as a loop inside a synchronous callout context. Apex has a governor limit of 10 synchronous callout attempts per transaction regardless of retry logic design.

**Fix:** In synchronous contexts, limit retry to 1 immediate retry on transient failure (to handle a single network blip). For durable retry with backoff, write failed requests to a `Dead_Letter_Queue__c` object or publish a `Retry_Event__e` Platform Event and process retries in a scheduled Queueable that respects a configurable retry count and exponential backoff via sequential Queueable chaining.
