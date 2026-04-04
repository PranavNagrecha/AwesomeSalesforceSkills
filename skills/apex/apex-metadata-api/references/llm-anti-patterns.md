# LLM Anti-Patterns — Apex Metadata API

Common mistakes AI coding assistants make when generating or advising on Apex Metadata API.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating enqueueDeployment as Synchronous and Inspecting a Return Value for Success

**What the LLM generates:** Code that calls `Metadata.Operations.enqueueDeployment()`, then immediately checks the return value or queries the newly-created field/object in the same method, assuming the deployment has completed.

```apex
// WRONG
Id jobId = Metadata.Operations.enqueueDeployment(container, callback);
// This check will always fail — schema is not yet applied
Schema.SObjectField f = Schema.getGlobalDescribe().get('MyObj__c').getDescribe().fields.getMap().get('NewField__c');
if (f != null) { /* ... */ } // Never true here
```

**Why it happens:** LLMs trained on general async patterns assume a return value carries result information (as with `Future` or `Promise` objects in other languages). They also conflate the job ID with a success indicator.

**Correct pattern:**

```apex
// RIGHT — inspect results only inside the callback
public void handleResult(Metadata.DeployResult result, Metadata.DeployCallbackContext ctx) {
    if (result.isSuccess()) {
        // schema is now deployed — act here
    }
}
```

**Detection hint:** Look for schema describe calls or metadata queries immediately after `enqueueDeployment` in the same method body.

---

## Anti-Pattern 2: Attempting to Deploy Unsupported Metadata Types via Apex Metadata API

**What the LLM generates:** Apex code that tries to deploy metadata types not in the supported subset — most commonly `Flow`, `ApexClass`, `PermissionSet`, `Profile`, or `CustomApplication` — by constructing an instance of a class that does not exist in the `Metadata` namespace.

```apex
// WRONG — Flow is not a supported Apex Metadata API type
Metadata.Flow myFlow = new Metadata.Flow(); // Compile error — class does not exist
```

**Why it happens:** LLMs conflate the full SOAP Metadata API type catalog (which includes Flows, ApexClasses, etc.) with the limited Apex Metadata API subset. The SOAP API covers hundreds of types; the Apex API covers around twenty.

**Correct pattern:** Check the Apex Reference Guide for the official list of `Metadata.Metadata` subclasses. For types not on that list, use the SOAP Metadata API or CLI-based deployment (see `apex/metadata-api-and-package-xml`).

**Detection hint:** Any use of `Metadata.<TypeName>` where `TypeName` is not a documented subclass of `Metadata.Metadata` in the Apex Reference Guide.

---

## Anti-Pattern 3: Missing or Incomplete DeployCallback Implementation

**What the LLM generates:** Code that calls `enqueueDeployment` with a `null` callback or with a `handleResult` body that is empty, only prints to debug, or only handles the success branch.

```apex
// WRONG — null callback discards all result information
Metadata.Operations.enqueueDeployment(container, null);

// ALSO WRONG — silent failure
public void handleResult(Metadata.DeployResult result, Metadata.DeployCallbackContext ctx) {
    System.debug('done'); // failures are invisible
}
```

**Why it happens:** LLMs focus on the happy path. The async nature of the callback, combined with its late firing, makes error handling feel optional in generated code. LLMs also sometimes generate `null` as the callback argument when they are unsure of the callback class structure.

**Correct pattern:**

```apex
public void handleResult(Metadata.DeployResult result, Metadata.DeployCallbackContext ctx) {
    if (!result.isSuccess()) {
        for (Metadata.DeployMessage msg : result.details.componentFailures) {
            System.debug(LoggingLevel.ERROR, 'Deploy failure: ' + msg.problem);
        }
        // also persist to a custom object for audit
    }
}
```

**Detection hint:** Search for `enqueueDeployment(container, null)` or `handleResult` bodies with no branching on `result.isSuccess()`.

---

## Anti-Pattern 4: Confusing Apex Metadata API With the SOAP Metadata API

**What the LLM generates:** Advice that mixes concepts from the SOAP/REST Metadata API (XML zip files, `deploy()` and `retrieve()` SOAP methods, `AsyncResult` polling) into Apex code that should be using `Metadata.Operations`.

```apex
// WRONG — MetadataService is a SOAP stub pattern, not Apex Metadata API
MetadataService.MetadataPort service = new MetadataService.MetadataPort();
MetadataService.AsyncResult result = service.deploy(zipFile, options);
```

**Why it happens:** Both APIs share the word "Metadata" and both deploy metadata components. LLMs conflate them because they appear together in practitioner discussions and the SOAP API has more training data coverage.

**Correct pattern:** The Apex Metadata API uses the built-in `Metadata` namespace — no external WSDL stub, no callout, no zip file. The SOAP Metadata API requires a generated stub class, server-to-server callout, and credentials. They are completely different mechanisms.

**Detection hint:** Any reference to `MetadataService`, `deploy()` with a zip file parameter, or `AsyncResult` polling in code that is supposed to use the Apex Metadata API.

---

## Anti-Pattern 5: Ignoring the 10 Concurrent Deployment Limit in Loops or Bulk Operations

**What the LLM generates:** Code that calls `Metadata.Operations.enqueueDeployment()` inside a loop — for example, iterating over a list of fields to create — without any serialization or throttling.

```apex
// WRONG — can easily exceed 10 concurrent deployments
for (String fieldName : fieldNames) {
    Metadata.CustomField f = new Metadata.CustomField();
    f.fullName = 'MyObj__c.' + fieldName;
    // ...
    Metadata.DeployContainer c = new Metadata.DeployContainer();
    c.addMetadata(f);
    Metadata.Operations.enqueueDeployment(c, new MyCallback()); // called N times
}
```

**Why it happens:** LLMs treat `enqueueDeployment` like an ordinary Apex method call that can safely be called in any quantity. The org-wide limit of 10 concurrent deployments is not obvious from the method signature.

**Correct pattern:** Either batch multiple components into one `DeployContainer` per `enqueueDeployment` call (the container accepts multiple `addMetadata()` calls), or serialize deployments by enqueuing the next one from inside the `handleResult()` callback after the previous one completes.

**Detection hint:** `enqueueDeployment` inside a `for` loop, or a list iteration where each iteration creates a new `DeployContainer`.
