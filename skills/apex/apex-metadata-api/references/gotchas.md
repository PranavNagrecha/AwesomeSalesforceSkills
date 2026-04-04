# Gotchas — Apex Metadata API

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: enqueueDeployment Is Asynchronous — Callback May Arrive Minutes Later

**What happens:** `Metadata.Operations.enqueueDeployment()` returns a job ID immediately, but the actual metadata deployment runs asynchronously in a separate transaction. The `Metadata.DeployCallback.handleResult()` method fires only after the deployment engine processes the job, which can be seconds or minutes after the initial call.

**When it occurs:** Any time a practitioner or AI assistant assumes the deployment is complete by the time the calling method finishes. Code that reads back the new field or object immediately after `enqueueDeployment` will find that the schema change has not yet applied.

**How to avoid:** Design the post-deployment logic entirely inside `handleResult()`. Never assume schema changes are visible in the same request or even in the next few seconds. Use a status-tracking custom object or platform event if the caller needs to know when the deployment completed.

---

## Gotcha 2: Not All Metadata Types Are Supported — Failure Is Runtime, Not Compile-Time

**What happens:** The Apex Metadata API supports only a subset of the full Metadata API type catalog. Attempting to deploy an unsupported type (for example, `ApexClass`, `Flow`, `PermissionSet`, `Profile`) does not cause a compilation error. It fails at runtime — inside the deployment, which means the failure surfaces in the callback, not at the `enqueueDeployment` call site.

**When it occurs:** When code is written based on SOAP Metadata API documentation (which covers far more types) rather than the Apex Reference Guide's list of `Metadata.Metadata` subclasses.

**How to avoid:** Before building any implementation, verify the target metadata type appears in the Apex Reference Guide under the `Metadata` namespace subclasses. If it is not listed there, use the SOAP or REST Metadata API instead (see the `apex/metadata-api-and-package-xml` skill).

---

## Gotcha 3: DML Before enqueueDeployment in the Same Synchronous Transaction Causes Errors

**What happens:** Calling `Metadata.Operations.enqueueDeployment()` in a synchronous execution context that has already performed DML (insert, update, delete, upsert on sObjects) can cause a `System.SObjectException` or unexpected behavior. The platform enforces isolation around the Apex Metadata API deployment enqueue.

**When it occurs:** In triggers, controllers, or Visualforce action methods that insert records and then attempt to call `enqueueDeployment` in the same call stack.

**How to avoid:** Isolate `enqueueDeployment` in a Queueable job. The Queueable runs in a fresh transaction, so there is no prior DML state to conflict with the metadata enqueue. In post-install scripts, use a Queueable to perform the deployment.

---

## Gotcha 4: Callback Class Cannot Be an Inner Class in All Contexts

**What happens:** Defining the `Metadata.DeployCallback` implementation as an inner class of another Apex class sometimes prevents the platform from invoking it correctly. The callback fires in a separate transaction, and the platform must be able to instantiate the class independently — inner class instantiation semantics can break this.

**When it occurs:** When developers try to keep the callback co-located with the deploy logic by nesting it inside another class, or inside an interface implementation.

**How to avoid:** Always define the `Metadata.DeployCallback` implementation as a top-level, named Apex class with a no-argument constructor (or only serializable constructor arguments). This ensures the platform can instantiate it correctly during callback dispatch.

---

## Gotcha 5: 10 Concurrent Deployment Limit Is Org-Wide

**What happens:** Salesforce enforces a limit of 10 concurrent Apex-initiated metadata deployments per org. If a 11th `enqueueDeployment` call is made while 10 others are still running, the platform throws a `System.LimitException`. There is no graceful waiting — the exception must be caught and handled.

**When it occurs:** In high-volume admin tooling apps, in scenarios where multiple users trigger deployments simultaneously, or in automated setup flows that loop and call `enqueueDeployment` in rapid succession.

**How to avoid:** Build a serialization layer — enqueue a Queueable or schedule a batch that processes one or a small number of deployments at a time. Track pending deployments in a custom object and only enqueue the next one after the callback for the previous one fires successfully. Wrap `enqueueDeployment` calls in try/catch for `System.LimitException` and handle failures gracefully.
