# Apex Metadata API — Deployment Pattern Template

Use this template when implementing a `Metadata.Operations.enqueueDeployment` workflow with a callback stub. Fill in every section before shipping.

---

## Scope

**Skill:** `apex/apex-metadata-api`

**Request summary:** (fill in what the user asked for — e.g., "create a custom field on Account during post-install")

**Target metadata type:** (e.g., `Metadata.CustomField`, `Metadata.CustomObject`, `Metadata.CustomLabel`)

**Triggering context:** (e.g., post-install script, Queueable, LWC controller action)

---

## Context Gathered

Answer before writing any code:

- Target metadata type confirmed in Apex Metadata API supported type list? [ ] Yes / [ ] No — if No, use SOAP Metadata API instead
- DML performed before this enqueue call in the same transaction? [ ] Yes → isolate in Queueable / [ ] No
- Concurrent deployment limit concern? [ ] High-frequency scenario → add serialization layer / [ ] Low-frequency → single enqueue is fine
- Callback class name: _______________
- Audit / logging mechanism for callback results: _______________

---

## Deployment Class

```apex
// [YourDeploymentClass].cls
// Purpose: Constructs and enqueues a metadata deployment for [describe what is being deployed].
// Context: Run from [post-install script / Queueable / controller].

public class [YourDeploymentClass] {

    public static Id deploy() {
        // Step 1: Construct the metadata component
        Metadata.[MetadataType] component = new Metadata.[MetadataType]();
        component.fullName = '[ObjectApiName].[ComponentApiName]'; // e.g., 'Account.MyField__c'
        component.label    = '[Human-Readable Label]';
        // Set type-specific required attributes:
        // component.type   = Metadata.FieldType.[FieldType]; // for CustomField
        // component.length = 255;                            // for Text fields

        // Step 2: Build the deploy container
        Metadata.DeployContainer container = new Metadata.DeployContainer();
        container.addMetadata(component);

        // Step 3: Enqueue deployment with callback
        [YourCallbackClass] callback = new [YourCallbackClass]();
        Id jobId = Metadata.Operations.enqueueDeployment(container, callback);

        // Step 4: Log or store the job ID for tracking
        System.debug('Metadata deployment enqueued. Job ID: ' + jobId);
        return jobId;
    }
}
```

---

## Callback Class

```apex
// [YourCallbackClass].cls
// Purpose: Handle the result of the async metadata deployment.
// IMPORTANT: Must be a top-level class, not an inner class.

public class [YourCallbackClass] implements Metadata.DeployCallback {

    public void handleResult(
        Metadata.DeployResult result,
        Metadata.DeployCallbackContext context
    ) {
        if (result.isSuccess()) {
            // Deployment succeeded — perform post-setup logic here
            // e.g., update a setup status record, send a platform event
            System.debug('Metadata deployment succeeded.');
            // [Your post-success logic]

        } else {
            // Deployment failed — log all component failure messages
            System.debug(LoggingLevel.ERROR, 'Metadata deployment failed.');
            for (Metadata.DeployMessage msg : result.details.componentFailures) {
                System.debug(LoggingLevel.ERROR,
                    'Component: ' + msg.fullName + ' | Problem: ' + msg.problem
                );
            }
            // [Your failure handling: write to audit object, send alert, etc.]
        }
    }
}
```

---

## Queueable Wrapper (use when DML precedes this deployment)

```apex
// [YourDeploymentQueueable].cls
// Use when the calling context has already performed DML in the same transaction.

public class [YourDeploymentQueueable] implements Queueable {

    // Store any parameters needed to construct the metadata component
    private String targetObjectApiName;
    private String fieldApiName;

    public [YourDeploymentQueueable](String targetObjectApiName, String fieldApiName) {
        this.targetObjectApiName = targetObjectApiName;
        this.fieldApiName        = fieldApiName;
    }

    public void execute(QueueableContext ctx) {
        Metadata.CustomField field = new Metadata.CustomField();
        field.fullName = targetObjectApiName + '.' + fieldApiName;
        field.label    = fieldApiName.replace('__c', '').replace('_', ' ');
        field.type     = Metadata.FieldType.Text;
        field.length   = 255;

        Metadata.DeployContainer container = new Metadata.DeployContainer();
        container.addMetadata(field);

        [YourCallbackClass] callback = new [YourCallbackClass]();
        Metadata.Operations.enqueueDeployment(container, callback);
    }
}
```

---

## Checklist

Copy from SKILL.md — tick each item before marking complete:

- [ ] Target metadata type confirmed in the official Apex Metadata API supported type list
- [ ] `Metadata.DeployCallback` implemented in a named top-level class
- [ ] `handleResult()` covers both success and failure branches with structured logging
- [ ] Transaction boundary verified — no unguarded DML before `enqueueDeployment` in same transaction
- [ ] Concurrent deployment limit (10/org) accounted for if high-frequency
- [ ] Job ID returned by `enqueueDeployment` is stored or logged
- [ ] Integration test performed in sandbox or scratch org (unit tests cannot invoke this)

---

## Notes

Record deviations from the standard pattern here:

- Deviation: _______________
- Reason: _______________
