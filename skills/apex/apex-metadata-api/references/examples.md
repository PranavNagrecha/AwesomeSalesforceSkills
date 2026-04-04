# Examples — Apex Metadata API

## Example 1: ISV Managed Package Creates a Custom Field During Post-Install Setup

**Context:** An ISV managed package needs to add a required tracking field to `Account` in a subscriber org after the admin installs the package. The field is not bundled in the package itself because its existence depends on subscriber-specific conditions detected at install time.

**Problem:** Without Apex Metadata API, the only options are to either ship the field in the package (applies universally) or require the admin to create it manually after installation (poor UX, error-prone).

**Solution:**

```apex
// PostInstallHandler.cls — implements InstallHandler
public class PostInstallHandler implements InstallHandler {
    public void onInstall(InstallContext ctx) {
        // Defer schema creation to a Queueable to avoid DML-before-enqueue issues
        System.enqueueJob(new CreateTrackingFieldQueueable());
    }
}

// CreateTrackingFieldQueueable.cls
public class CreateTrackingFieldQueueable implements Queueable {
    public void execute(QueueableContext ctx) {
        Metadata.CustomField trackingField = new Metadata.CustomField();
        trackingField.fullName    = 'Account.PkgInstallDate__c';
        trackingField.label       = 'Package Install Date';
        trackingField.type        = Metadata.FieldType.DateTime;
        trackingField.description = 'Populated by post-install script.';

        Metadata.DeployContainer mdContainer = new Metadata.DeployContainer();
        mdContainer.addMetadata(trackingField);

        FieldDeployCallback callback = new FieldDeployCallback();
        Metadata.Operations.enqueueDeployment(mdContainer, callback);
    }
}

// FieldDeployCallback.cls — top-level class, not inner class
public class FieldDeployCallback implements Metadata.DeployCallback {
    public void handleResult(
        Metadata.DeployResult result,
        Metadata.DeployCallbackContext context
    ) {
        if (result.isSuccess()) {
            // Log success or update a setup status custom object record
            System.debug('Post-install field deployment succeeded.');
        } else {
            for (Metadata.DeployMessage msg : result.details.componentFailures) {
                System.debug('Deployment error: ' + msg.problem);
            }
        }
    }
}
```

**Why it works:** The deployment is isolated in a Queueable so there is no DML-before-enqueue conflict. The callback handles both success and failure paths and is a named top-level class, which is required for the platform to invoke it correctly in a separate transaction.

---

## Example 2: Admin Tool Adds a Required Field to a Custom Object via Button Click

**Context:** A custom admin console app (LWC + Apex controller) lets system administrators add a pre-defined set of fields to a custom object from a button click. The app is used internally to provision tenant-specific schema in a multi-tenant architecture.

**Problem:** Manually adding fields via Salesforce Setup is slow and error-prone at scale. Wrapping the deployment in a self-service UI with validation and logging is more reliable.

**Solution:**

```apex
// AdminSchemaController.cls
public with sharing class AdminSchemaController {

    @AuraEnabled
    public static String addRequiredField(String objectApiName, String fieldLabel, String fieldApiName) {
        // Basic guard: validate input length and avoid injection in fullName
        if (String.isBlank(objectApiName) || String.isBlank(fieldApiName)) {
            throw new AuraHandledException('Object API name and field API name are required.');
        }

        Metadata.CustomField newField = new Metadata.CustomField();
        newField.fullName    = objectApiName + '.' + fieldApiName;
        newField.label       = fieldLabel;
        newField.type        = Metadata.FieldType.Text;
        newField.length      = 255;
        newField.required    = false; // Required fields must already have data or a default

        Metadata.DeployContainer mdContainer = new Metadata.DeployContainer();
        mdContainer.addMetadata(newField);

        AdminFieldCallback callback = new AdminFieldCallback(objectApiName, fieldApiName);
        Id jobId = Metadata.Operations.enqueueDeployment(mdContainer, callback);

        return jobId;
    }
}

// AdminFieldCallback.cls
public class AdminFieldCallback implements Metadata.DeployCallback {

    private String objectName;
    private String fieldName;

    public AdminFieldCallback(String objectName, String fieldName) {
        this.objectName = objectName;
        this.fieldName  = fieldName;
    }

    public void handleResult(
        Metadata.DeployResult result,
        Metadata.DeployCallbackContext context
    ) {
        SchemaDeployLog__c log = new SchemaDeployLog__c();
        log.ObjectName__c  = objectName;
        log.FieldName__c   = fieldName;
        log.DeployedAt__c  = Datetime.now();
        log.Success__c     = result.isSuccess();

        if (!result.isSuccess()) {
            String errors = '';
            for (Metadata.DeployMessage msg : result.details.componentFailures) {
                errors += msg.problem + '\n';
            }
            log.ErrorDetails__c = errors;
        }

        insert log; // Safe: callback runs in its own transaction
    }
}
```

**Why it works:** The controller validates inputs before constructing the metadata object. The callback writes to a custom audit object (`SchemaDeployLog__c`) so admins can review deployment history. Because the callback fires in a separate transaction, the DML inside it does not conflict with the original button-click request.

---

## Anti-Pattern: Calling enqueueDeployment Inside a Trigger With Prior DML

**What practitioners do:** Add `Metadata.Operations.enqueueDeployment()` at the end of a trigger that also inserts or updates records. This seems natural because it is all "one operation."

**What goes wrong:** The Apex Metadata API does not permit `enqueueDeployment` in the same synchronous execution context as certain DML patterns. At minimum, this produces unexpected exceptions in some orgs. Even when it does not error immediately, the transaction boundary semantics are unpredictable.

**Correct approach:** Move the `enqueueDeployment` call to a Queueable job enqueued from the trigger. The Queueable runs in a separate transaction, satisfying the platform's isolation requirement:

```apex
// In trigger:
System.enqueueJob(new MetadataDeployQueueable(/* params */));

// In Queueable:
public void execute(QueueableContext ctx) {
    Metadata.DeployContainer mdContainer = new Metadata.DeployContainer();
    // ... build metadata ...
    Metadata.Operations.enqueueDeployment(mdContainer, new MyCallback());
}
```
