# Specialized Platform Features

Coverage for less common but important Salesforce features that appear in debug logs: Platform Cache, Transaction Finalizers, Continuations, Big Objects, Custom Metadata, Omni-Channel, Data Cloud, Einstein, Lightning Message Service, Duplicate Rules, Lead Conversion, and more.

## Platform Cache

In-memory cache for Apex. Org-level (shared across all users) or session-level (per user).

### Log signatures

```
CACHE_GET|<namespace>|<key>
CACHE_PUT|<namespace>|<key>
CACHE_REMOVE|<namespace>|<key>
```

### Gotchas

- Cache misses force the underlying SOQL or calculation. If cache is cold, performance is worse.
- Cache TTL: default 24 hours (session) or org-defined.
- Cache capacity: org has partitioned MB; if full, least-recently-used is evicted.
- Apex cache is not persistent across deployments; new code clears it.

### Diagnostic

```bash
grep "CACHE_" log.log
```

If a transaction is slow on first run but fast on second, Platform Cache is suspected.

## Transaction Finalizers (Summer '21+)

Run cleanup code after an async Apex job completes, regardless of success or failure.

Implement `System.Finalizer`:

```apex
public class MyFinalizer implements System.Finalizer {
  public void execute(System.FinalizerContext ctx) {
    // Runs after queueable completes
  }
}
```

Attached in a queueable via `System.attachFinalizer(new MyFinalizer())`.

### Log signatures

```
CODE_UNIT_STARTED|[EventService.....finalizer]|<class>
```

### Use cases

- Retry on failure.
- Post-completion logging.
- Chain another job on certain outcomes.

## Continuation (Visualforce, async callouts)

Async callouts in Visualforce that do not block the request.

```apex
Continuation con = new Continuation(40);
con.continuationMethod = 'processResponse';
// ...
return con;
```

### Log signatures

```
CONTINUATION_REQUEST|<id>
CONTINUATION_RESPONSE|<id>
```

### Gotchas

- Continuation timeout: 120 seconds max.
- Only works in VF, not LWC or Aura.
- State persists via the continuation object, not through the VF view state.

## Big Objects

Objects designed for millions to billions of rows. Used for archival, audit, historical data.

### Log signatures

Queries on Big Objects (API names ending in `__b`) use async SOQL via `Database.queryAsync()`:

```
ASYNC_SOQL_BEGIN
ASYNC_SOQL_END
```

### Gotchas

- No triggers on Big Objects.
- No standard SOQL (must use async SOQL or specific index-aware queries).
- Inserted via Bulk API or `Database.insertImmediate()`.
- Index defines the access pattern; queries must match the index.

## Custom Metadata Types

Deployable, configurable records. Queried like SObjects but with reduced limits.

### Log signatures

```
SOQL_EXECUTE_BEGIN|[line]|Aggregations:0|SELECT ... FROM My_Setting__mdt
```

### Limits

- Queries on Custom Metadata do NOT count against the SOQL limit (since Spring '19).
- Limited DML: can be inserted/updated via Metadata API, not via standard DML (well, with exceptions).
- `Custom_Metadata_Type.getAll()` method for fast access (cached).

### Gotchas

- Protected Custom Metadata records visible only within their package context.
- Hierarchy custom metadata: user → profile → org defaults.

## Custom Settings

Similar to Custom Metadata but older. Hierarchy (per user/profile) or list (org-wide).

### Log signatures

```
SOQL_EXECUTE_BEGIN|... FROM MyCustomSetting__c
```

Or via `MyCustomSetting__c.getInstance()` which is cached:
```
(no SOQL event, cache hit)
```

### Gotchas

- `getInstance()` returns hierarchy cascade.
- `getAll()` returns all list custom setting records.
- DML on Custom Settings counts against DML limits.

## Duplicate Rules

Fire during DML to detect and block duplicates.

### Log signatures

```
DUPLICATE_DETECTION_BEGIN
DUPLICATE_DETECTION_RULE_INVOCATION|<rule-name>|<match-count>
DUPLICATE_DETECTION_END
```

### Gotchas

- Fires on DML, not just UI save.
- Can be bypassed via `DMLOptions.DuplicateRuleHeader.allowSave = true` in Apex.
- Matching Rules underlie Duplicate Rules.
- Fuzzy matching is expensive; heavy orgs should limit rule scope.

## Matching Rules

Define what counts as a duplicate. Referenced by Duplicate Rules.

### Log signatures

Visible as part of `DUPLICATE_DETECTION_RULE_INVOCATION`.

## Lead Conversion

Converting a Lead creates an Account, Contact, and optionally Opportunity.

### Log signatures

```
CODE_UNIT_STARTED|[LeadConvertService]|<lead-id>
DML_BEGIN|Op:Insert|Type:Account|Rows:1
DML_BEGIN|Op:Insert|Type:Contact|Rows:1
DML_BEGIN|Op:Update|Type:Lead|Rows:1
```

All triggers fire for each object. This is a known source of cascading automation.

### Gotchas

- Lead custom fields map to Contact/Account via "Lead Field Mapping".
- Custom validation on Contact can block conversion.
- Large orgs have many converting triggers; can hit governor limits.

## Case Merge

Salesforce Cases can be merged via the UI or API.

### Log signatures

```
DML_BEGIN|Op:Merge|Type:Case|Rows:1
```

Same mechanics as Contact/Lead merge. Same access issues (blocking related records with empty brackets).

## Omni-Channel

Routes work items (Cases, Leads, custom objects) to agents based on skills and availability.

### Log signatures

```
CODE_UNIT_STARTED|[OmniChannel]|<routing-config>
OMNI_ROUTING_DETAIL|<routing-type>|<result>
```

Agents see queued work items in the Omni-Channel widget. Log shows routing decisions.

### Gotchas

- Skills-based routing requires SkillRequirement records.
- Presence Status determines agent availability.
- Push Timeout kicks work back if agent does not accept in time.

## Einstein Bots

Chatbot framework. Bots can invoke Apex.

### Log signatures

```
CODE_UNIT_STARTED|[EinsteinBots]|<bot-name>.<dialog>.<step>
```

Invocable Apex actions from bots appear as normal Apex calls.

## Einstein Next Best Action

Strategies that recommend actions based on data and rules.

### Log signatures

```
NBA_STRATEGY_BEGIN
NBA_NODE_BEGIN|<node-name>
NBA_NODE_DETAIL|...
NBA_NODE_END|<result>
NBA_STRATEGY_END
```

### Gotchas

- Strategies use `Strategy Builder` in Setup.
- Branches can include Apex, Flow, ML predictions, or filters.
- NBA_NODE_ERROR if a branch fails.

## Einstein Activity Capture

Syncs emails and events from Gmail/Outlook into Salesforce.

### Log signatures

EAC runs through its own infrastructure; not fully visible in Apex logs. Visible as:
- `EmailMessage` and `Event` inserts by the EAC service user.
- SOQL on `EmailMessage` from various Apex that processes EAC data.

## Lightning Message Service (LMS)

Cross-frame communication between Aura/LWC/Visualforce.

### Log signatures

Not visible as distinct events in Apex logs. LMS is entirely client-side.

## Lightning Data Service (LDS) via uiRecordApi

LWC's preferred way to read/write records.

### Log signatures

LDS writes trigger standard Apex triggers on the object, visible as:
```
CODE_UNIT_STARTED|[EventService.....trigger]|<Trigger> on <Object> trigger event BeforeUpdate
```

The entry point is different from Apex DML: typically `[UIAPI Service]` or similar.

### Gotchas

- LDS uses the UI API, which has different FLS enforcement than direct Apex DML.
- Some fields unsupported by UI API are silently skipped.
- Cache management: `refreshApex`, `notifyRecordUpdateAvailable`, and `getRecordNotifyChange` are needed to propagate changes.

## Salesforce Functions (deprecated 2024)

Ran Node.js / Java functions on Heroku-like infrastructure. Deprecated.

If you see references in older logs:
```
CODE_UNIT_STARTED|[FunctionsService]|<function-name>
FUNCTIONS_INVOCATION_REQUEST
FUNCTIONS_INVOCATION_RESPONSE
```

Alternative in 2024+: Apex + callouts to external services.

## Heroku Connect

Bi-directional sync between Salesforce and a Postgres database on Heroku.

### Log signatures

Heroku Connect runs via an integration user (named "Heroku Connect"). DML by that user on synced objects is Heroku Connect activity.

## Salesforce CDP / Data Cloud

Unified customer data platform.

### Log signatures

Complex. Data Cloud runs as its own Apex context:
```
CODE_UNIT_STARTED|[DataCloud]|<operation>
```

Data streams, identity resolution, and calculated insights have their own events (less standardized, varies by release).

## Slack integration

Slack-Salesforce native integration fires callouts to Slack.

### Log signatures

```
CALLOUT_REQUEST|url:https://slack.com/api/...
```

Slack-initiated actions (from slash commands, messages) come in as Connected App sessions on the Salesforce side.

## Quip integration (deprecated)

Quip was retired. Historical orgs may have Quip-related fields like `QuipSalesforceLink__c`.

## Apex Event Recorder (Event Monitoring, distinct from debug logs)

Shield Event Monitoring captures production activity for compliance/security. Not the same as debug logs but often conflated.

Access via:
- REST API: `/services/data/vXX.X/sobjects/EventLogFile`
- Event Monitoring Analytics App.

Categories include: API, Login, Report, Logout, UI Tracking, Apex Execution, Apex SOAP, Content Transfer, and many more.

## Transaction Security Policies (Shield)

Policies that block or notify on specific events (e.g., user downloading 1000 records).

### Log signatures

Not in Apex logs. Visible in Event Monitoring and Setup > Transaction Security.

## Enhanced Domains, My Domain, and URL context

Orgs with Enhanced Domains see URLs like `<domain>.my.salesforce.com`. Old URLs redirect.

### Log signatures

None distinct, but callouts and REST responses reference full domain.

## Encryption at rest (non-Shield)

Salesforce encrypts data at rest by default. Classic Encryption (for Name fields) and Shield Platform Encryption are separate features.

### Log signatures

None distinct. Encrypted fields appear normally unless masked.

## Event Monitoring metrics for performance tuning

For slow transactions, Event Monitoring's `ApexExecution` event captures:
- Execution time
- CPU time
- DB time
- Callout time
- Run time across many executions (aggregate trend)

Check Event Monitoring Analytics App for trends that debug logs cannot show (one log is one transaction).

## Experience Cloud / Communities deep dive

### Guest User specifics

The Guest User is an automated account the community uses for unauthenticated visitors.

Limits:
- Cannot own records unless set as owner explicitly.
- Cannot use private sharing model; records need explicit Guest User Sharing Rules.
- Limited object access via Profile.
- No "Update Records" on standard objects by default.

### Customer/Partner community users

Authenticated external users. Have limited record access:
- Can see records owned by them.
- Can see records shared via Sharing Sets (for high-volume community users) or Sharing Rules.
- Cannot see internal user-owned records by default.

### Super User access

Delegates community user access up the hierarchy of the external organization. Set via `User.IsPortalEnabled` and partner account user management.

### Navigation in logs

Community navigation is mostly client-side. Server calls appear as LWC @AuraEnabled calls or REST API calls.

## Approval Process automation patterns

Beyond the basic log signatures in legacy-automation.md:

### Locking and unlocking

```apex
Approval.LockResult lr = Approval.lock(recordId);
```

Log:
```
CODE_UNIT_STARTED|[ApprovalLocking]|<record-id>
```

### Submit for approval via Apex

```apex
Approval.ProcessSubmitRequest req = new Approval.ProcessSubmitRequest();
req.setObjectId(recordId);
Approval.ProcessResult result = Approval.process(req);
```

Log:
```
CODE_UNIT_STARTED|[ApprovalProcessService]|<request>
WF_APPROVAL_SUBMIT|...
```

### Approve/reject via Apex

`Approval.ProcessWorkitemRequest` similar pattern.

## Formula fields and logs

Formulas recalculate on read. Not visible as distinct events.

But when a formula field is included in a SOQL select, the platform computes it. If the formula is expensive (cross-object, nested), the query runs longer.

Can you see formula recalc in the log? No. But you can see:
- Slow SOQL that selects many formula fields.
- Formula-based validation rules appearing as `VALIDATION_FORMULA`.

## Account Teams, Opportunity Teams, Case Teams

Team members get defined access to the parent record.

### Log signatures

DML on `AccountTeamMember`, `OpportunityTeamMember`, `CaseTeamMember` objects.

### Gotchas

- Default team members can be auto-added via User settings.
- Sharing from team membership shows up as implicit access; not a distinct share record in `__Share`.

## Record Types

Record types control picklist values and page layouts but not sharing or security.

### Log signatures

Record type assignments visible in record dumps:
```
RecordTypeId=012XXXXXXXXXX
```

### Gotchas

- Different record types can share the same object; user permissions specify which types are accessible.
- Record type picklist values are enforced at UI layer, not platform. Apex can set an invalid value.

## Person Accounts

Hybrid Account/Contact. Appear as Accounts with `IsPersonAccount = true`.

### Gotchas

- All Contact operations work but target Account records.
- Triggers fire on both Account and Contact contexts.
- SOQL queries must account for the hybrid nature.

## Metadata API operations in logs

Metadata changes (deploy, retrieve) are visible in Apex logs only indirectly. Deployment triggers recompilation of Apex, which appears as:

```
(no specific event; recompiled classes run from their new source on next invocation)
```

Metadata deploys themselves are logged in Setup > Deployment Status.

## Tooling API operations

Queries against tooling objects (ApexClass, ApexTrigger, CustomField, etc.) use a separate API:

```
SOQL_EXECUTE_BEGIN|... FROM ApexClass
```

### Gotchas

- Tooling API SOQL has different limits.
- Some objects are only queryable via Tooling API, not REST API.

## Debug logs for specific user contexts

To debug as a specific user, set up Trace Flags in Setup > Debug Logs:

- User Trace Flag: log for a specific user.
- Class/Trigger Trace Flag: log only for specific classes/triggers (useful for production).

Log levels specified in the trace flag override the developer console defaults.

## AppExchange package install/uninstall

Installing or uninstalling packages is logged in Setup > Installed Packages. During install, many schema changes may occur; the install log (different from Apex debug logs) shows them.

## Salesforce to Salesforce (S2S)

Federation between two orgs. Record-level sharing across orgs.

### Log signatures

Fields like `ConnectionReceivedId` and `ConnectionSentId` on records. S2S publisher records changes via platform events or queued jobs.

## Salesforce Mobile App debugging

LWC/Aura/VF in the mobile app run through a compatibility layer. Debug logs capture the Apex backend as normal, but the entry point may differ:
```
EXECUTION_STARTED|[MobileService]|...
```

## Advanced grep recipes

```bash
# Platform Cache usage
grep "CACHE_" log.log

# Duplicate detection events
grep "DUPLICATE_" log.log

# NBA strategies
grep "NBA_" log.log

# Omni-Channel routing
grep "OMNI_" log.log

# Approval process
grep "WF_APPROVAL\|WF_PROCESS_NODE" log.log

# Lead conversion
grep "LeadConvertService" log.log

# Record type assignments
grep "RecordTypeId=" log.log | sort -u

# Person Accounts
grep "IsPersonAccount" log.log

# Einstein Bots
grep "EinsteinBots" log.log

# Continuations
grep "CONTINUATION_" log.log

# Transaction Finalizers
grep "finalizer" log.log -i
```
