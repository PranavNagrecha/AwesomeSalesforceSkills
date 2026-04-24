# Salesforce Error Codes in Debug Logs

Comprehensive reference for StatusCode values you will see in `EXCEPTION_THROWN`, `FATAL_ERROR`, `FLOW_ELEMENT_FAULT`, and managed package error fields.

Format:
```
STATUS_CODE, human message: [field_or_id]  (line_number);extra context
```

## Access and visibility

### INSUFFICIENT_ACCESS_OR_READONLY
The running user cannot see or edit the record or a related record.

Subvariants:
- `cannot merge with entity that is not accessible: []`: merge failed because a related record (Opportunity, Task, Event, Case, custom lookup) is outside the user's visibility. **Empty brackets are deliberate**: Salesforce refuses to name the blocking record to prevent information disclosure. The log cannot tell you which object is the issue.
- `entity is deleted`: related record was deleted between read and DML.
- Generic: user lacks edit access on a specific field or record.

Investigation path:
1. Identify the running user (`LastModifiedById` on the record).
2. Impersonate and retry in the native UI (the UI error is more specific).
3. Diff child-record counts as admin vs integration user.

### INSUFFICIENT_ACCESS_ON_CROSS_REFERENCE_ENTITY
A field value in the DML points to a record the user cannot see. Error usually names the field.

### FIELD_INTEGRITY_EXCEPTION
Lookup filter or polymorphic reference constraint violated.

### TOO_MANY_RECORDS
Sharing rules or filters created more records than can be processed (e.g., 201 records in a view that only supports 200).

## Validation

### FIELD_CUSTOM_VALIDATION_EXCEPTION
A validation rule rejected the DML. Error names the rule.

### REQUIRED_FIELD_MISSING
A required field was null.

### STRING_TOO_LONG, NUMBER_OUTSIDE_VALID_RANGE, INVALID_EMAIL_ADDRESS, INVALID_URL, INVALID_PHONE, INVALID_DATE, INVALID_CURRENCY_CODE
Data type violations. Self-explanatory.

### INVALID_ID_FIELD
Malformed Salesforce ID.

### INVALID_FIELD_FOR_INSERT_UPDATE
Trying to set a system/formula/rollup field directly.

### INVALID_MASTER_OR_TRANSLATED_SOLUTION
Multilingual Solution object validation.

### INVALID_TYPE
SObject type mismatch.

### DUPLICATE_VALUE
Unique field constraint violated.

### DUPLICATES_DETECTED
Duplicate Rule triggered. Includes the duplicate record IDs.

## Flow errors

### CANNOT_EXECUTE_FLOW_TRIGGER
A record-triggered flow failed without a fault handler.

### FLOW_EXCEPTION
Generic flow failure. Look at `FLOW_ELEMENT_FAULT` for detail.

### INVALID_FLOW_VARIABLE
A flow variable was missing or misconfigured.

## Concurrency

### UNABLE_TO_LOCK_ROW
Two transactions writing to the same record (or a shared lock parent) at once.

Diagnostics:
- Compare timestamps across logs. If two transactions overlap and touch the same parent, contention confirmed.
- Aggregator jobs, bulk API loads, scheduled managed package jobs are common contributors.

Fix: reduce concurrency on the parent, sequence the updates, or increase FOR UPDATE usage inside Apex.

### ROW_LOCKED_BY_ANOTHER_USER_OR_TRANSACTION
Same category.

### LOCK_TIMEOUT
Waited too long for a lock.

## Governor limits

### LIMIT_EXCEEDED
Specific limit hit. Message names it:
- `Too many SOQL queries: 101`
- `Too many DML statements: 151`
- `Too many DML rows: 10001`
- `Apex CPU time limit exceeded`
- `Apex heap size too large`
- `Maximum stack depth reached: 1000`
- `Too many query rows: 50001`
- `Callout time limit exceeded`

Investigation: `CUMULATIVE_LIMIT_USAGE` block shows per-namespace usage. Identify who burned the budget.

### STORAGE_LIMIT_EXCEEDED
Org out of data storage.

### FILE_EXTENSION_NOT_ALLOWED
Uploading a blocked file type.

### CUMULATIVE_LIMIT_USAGE_FOR_NS
Namespace exceeded its limit.

## Merge-specific

### `cannot merge with entity that is not accessible: []`
See above.

### `invalid master record`
Master ID wrong or types do not match.

### `first error: INVALID_ID_FIELD`
Losing record ID malformed.

## Mixed DML

### MIXED_DML_OPERATION
`System.MixedDMLException: DML operation on setup object is not permitted after you have updated a non-setup object (or vice versa)`

Setup objects include: User, Group, GroupMember, PermissionSet, PermissionSetAssignment, Profile, and similar. Resolution: do one operation sync, the other via `@future` or queueable.

## Callouts

### REQUEST_RUNNING_TOO_LONG
HTTP callout exceeded timeout (default 10s, max 120s).

### SESSION_REQUIRED, INVALID_SESSION_ID
Session issues with named credential or OAuth.

### UNAUTHORIZED_ENDPOINT
Remote site setting missing or endpoint not allowed.

### CERTIFICATE_EXPIRED, SSL_HANDSHAKE_FAILED
Cert issues with HTTPS callout.

### BAD_GATEWAY_502, SERVICE_UNAVAILABLE_503
Remote system issues.

## Apex-specific exceptions

### System.NullPointerException
Object reference is null. Log shows the line number and often the variable name.

### System.TypeException
Type mismatch or cast failure.

### System.StringException
String operation invalid.

### System.MathException
Division by zero, etc.

### System.QueryException
SOQL-related. "List has no rows for assignment to SObject" is the most common: `.get()` on a list that is empty, or `[SELECT ...][0]` where the query returned zero.

### System.DmlException
DML failed. Wraps status codes above.

### System.LimitException
Governor limit. Wraps LIMIT_EXCEEDED.

### System.AuraHandledException
Handled and shown to the LWC/Aura user. Clean-looking error in UI.

### System.CalloutException
HTTP callout failure.

### System.AsyncException
Queueable/future/batch async failure.

### System.EmailException
Email send failed.

### System.JSONException
JSON parse failure.

### System.SecurityException
Security check failed (stripInaccessible, WITH SECURITY_ENFORCED).

## Specific contextual errors

### DELETE_FAILED
Cascade delete blocked by a related record. Often because the related record has a lookup that cannot be set to null or a master-detail that would orphan it.

### ENTITY_IS_LOCKED
Record is in an approval process and cannot be modified.

### CIRCULAR_DEPENDENCY
Lookup creates a cycle.

### CANNOT_DISABLE_LAST_ADMIN
Attempted to deactivate the only admin.

### DEPENDENCY_EXISTS
Trying to delete a record that is referenced elsewhere.

### INVALID_SHARING_MODE
Sharing mode conflict in `with sharing` context.

### ENTITY_FAILED_IFLASTMODIFIED_ON_UPDATE
Optimistic lock: record was modified by someone else since you loaded it.

### CANNOT_CASCADE_PRODUCT_ACTIVE
CPQ-specific: product deletion blocked.

## Platform events and CDC

### HANDLED_EXCEPTION in subscriber
Apex trigger on `__e` object threw. The event is retried up to 5 times automatically, then dropped.

### EVENT_PUBLISH_FAILURE_OUTBOUND
Outbound event publish failed.

### INVALID_REPLAY_ID
Replay ID not found (past retention window).

## Legacy automation errors

### CANNOT_EXECUTE_FLOW_TRIGGER
Flow failure (covered above).

### WORKFLOW_FIELD_UPDATE_FAILED
Workflow rule field update failed.

### APPROVAL_PROCESS_FIELD_UPDATE_FAILED
Approval process field update failed.

### INVALID_OPERATION_WITH_EXPIRED_PASSWORD
User password expired, they cannot execute.

## Experience Cloud / Community

### INVALID_COMMUNITY
Community not published or user lacks access.

### INVALID_NETWORK
Network (site) not accessible.

## Bulk API

### BULK_API_ERROR
Bulk API job failed. Specific error in job detail.

### INVALID_BATCH
Batch file malformed.

### TIMEOUT_PROCESSING
Bulk API batch timed out.

## How to decode an unfamiliar error

1. Read the status code. It tells you the category.
2. Read the brackets. Content = specific thing that failed; empty = Salesforce hiding details for security.
3. Read the line number. Find that line in the class. For managed packages, the line number identifies the specific operation within the package but you cannot see the source.
4. Look at 20 lines before the error in the log for context (record, flow, user, DML op).
5. Check `CUMULATIVE_LIMIT_USAGE` if the error is limit-related.
6. Check `VALIDATION_FAIL` if the error names a rule.
7. If caught by a managed package and rewritten to a field, the log shows the caught text but not always the raw Salesforce error. Try to trigger the operation as a user you control to see the raw error.

## What errors cannot tell you

`INSUFFICIENT_ACCESS_OR_READONLY` tells you the user cannot access something. It does not tell you why. Configuration that could cause it:

- Profile-level object permissions (Profile or Permission Set)
- Field-level security (FLS)
- Record-level sharing (OWD, sharing rules, manual shares)
- Role hierarchy (for owner-based sharing)
- Criteria-based sharing
- Territory management
- Restriction rules
- Implicit sharing (Account/Contact/Opportunity parent-child)
- Experience Cloud Guest User profile configuration

If the error is access-related and the log does not have detail, you must check the user's access configuration outside the log.

## Error-handling patterns in Apex

Code that catches and rewrites errors loses fidelity. When you see a managed package field like `TracRTC__Realtime_Clean_Error_Message__c` containing a sanitized error, the raw Salesforce error had more detail.

To see the raw error:
1. Try the operation yourself as a user with the same profile.
2. Enable `APEX_CODE,FINEST` on the service user.
3. Look at Setup > Apex Exception Email or ApexLog for the raw exception.

## Errors that look scary but are often benign

- `INSUFFICIENT_ACCESS` on a formula recalc: sometimes a formula references a field the user cannot see. Depending on context, this might be intentional restriction, not a bug.
- `DUPLICATE_VALUE` on upsert: often handled by the calling code; look at whether the exception was caught.
- `REQUEST_RUNNING_TOO_LONG` on a callout: retry usually succeeds.
- `UNABLE_TO_LOCK_ROW` once: retry usually succeeds. Repeated locks = real contention.
