# UI Frameworks in Debug Logs: LWC, Aura, Visualforce, Experience Cloud

User-facing layers do not directly produce debug logs, but their server-side Apex calls do. This reference covers what each framework looks like when its backend hits Apex.

## Lightning Web Components (LWC)

LWC calls Apex three ways: imperative calls, wire adapters, and Lightning Data Service (LDS). Each leaves a different log signature.

### Imperative Apex calls

JS calls an @AuraEnabled method directly.

```javascript
import getSomething from '@salesforce/apex/MyController.getSomething';
getSomething({ param: 'x' }).then(...);
```

Log signature:
```
EXECUTION_STARTED
...
CODE_UNIT_STARTED|[EventService.....apex]|<class-id>|MyController.getSomething
```

Running user is the logged-in user (not automated process).

The method must be `public` (or `global`), `static`, and `@AuraEnabled`.

### Wire adapters (cacheable Apex)

```javascript
@wire(getSomething, { param: '$propValue' })
```

Requires the Apex method to be `@AuraEnabled(cacheable=true)`.

**Critical gotcha**: cacheable methods are cached by the Lightning platform. If the data is in the client cache, Apex is not called and there is NO debug log. Refreshing the page clears the cache. When debugging "why is my wire returning stale data", it is the cache, not the method.

Cacheable methods:
- Cannot do DML.
- Cannot do callouts.
- Cannot modify state.
- Can only do SOQL and return data.

### Lightning Data Service (LDS)

```javascript
import { getRecord, updateRecord } from 'lightning/uiRecordApi';
```

LDS uses the UI API, not Apex. It does not hit custom Apex. It does, however, fire triggers when it updates records.

Log signature when LDS updates a record:
- Entry point is `CODE_UNIT_STARTED|[UIAPI Service....]` or similar.
- Triggers on the object fire as normal.
- Running user is the logged-in user.

LDS is the preferred way to update records from LWC because it plays nicely with caching and real-time updates via Change Data Capture.

### LWC calling Apex that does DML

```javascript
import updateThing from '@salesforce/apex/MyController.updateThing';
updateThing({ recordId: id, newValue: val });
```

Log signature: normal imperative call followed by DML, triggers, flows, etc., all inside the Apex execution.

Gotcha: the user needs FLS edit access on the fields being updated. If the Apex class is `with sharing`, the user's sharing is enforced. If `without sharing`, it is not.

### LWC error handling

Unhandled Apex exceptions in an LWC controller method come back to JS as `AuraHandledException` or `System.DmlException`. In the log, you see:
```
EXCEPTION_THROWN|...|System.AuraHandledException: ...
```

In the UI, the user sees an error toast. Whatever message the Apex method threw is displayed.

### Server errors

When an @AuraEnabled method throws without catching, the log shows `FATAL_ERROR`. The JS promise rejects. Networks tab in browser shows 500.

## Aura Components

Older framework, still widely used. Uses `<aura:component>` and server-side actions.

### Server-side action

```javascript
var action = component.get('c.myMethod');
action.setParams({ param1: 'x' });
action.setCallback(this, function(response) { ... });
$A.enqueueAction(action);
```

Log signature:
```
CODE_UNIT_STARTED|[EventService.....apex]|<class-id>|<Controller>.<method>
```

Same as LWC imperative. The Apex method must be `@AuraEnabled`.

### Aura-specific events

| Log event | Meaning |
|---|---|
| `AURA_HANDLED_EXCEPTION` | Exception that was caught and returned to Aura client as a handled error. |
| `AURA_UNHANDLED_EXCEPTION` | Uncaught, returned as a 500 to Aura. |

### @AuraEnabled access rules

For Aura and LWC, methods must be `@AuraEnabled`. If they are not, the call fails with `No APEX action instance for c.myMethod found`.

For Guest Users (Experience Cloud unauthenticated), the class and method must be exposed via the Guest User profile's Apex Class Access.

## Visualforce

Older UI framework. Uses controllers/extensions.

### Page load

Log signature:
```
EXECUTION_STARTED
...
VF_PAGE_MESSAGE|...  (if any messages are on the page)
CODE_UNIT_STARTED|[Visualforce....]|<controller-id>|<Controller>.<Constructor>
```

Visualforce controllers run their constructor on page load. This is where SOQL typically lives. Governor limits apply to the constructor + page render.

### Getter/setter execution

Every property on a Visualforce controller (`public String foo { get; set; }`) runs its getter/setter as the page renders.

Log signature:
```
VF_APEX_CALL|<method>|<controller>
```

Each get/set is a separate call, which can drive up SOQL count if getters do queries. This is why VF performance tuning often requires caching values in member variables.

### Action methods

Button clicks, `<apex:commandButton action="{!save}">`, call controller methods.

Log signature:
```
VF_APEX_CALL|save|<Controller>
CODE_UNIT_STARTED|[Visualforce action....]|...
```

### Remote Actions (JS Remoting)

```javascript
Visualforce.remoting.Manager.invokeAction(
  '{!$RemoteAction.MyController.myMethod}',
  param1, param2,
  function(result, event) { ... }
);
```

Log signature:
```
CODE_UNIT_STARTED|[VF Remoting....]|<Controller>.<method>
```

Remote actions are similar to @AuraEnabled: static, annotated with `@RemoteAction`, work around page postbacks.

### Visualforce gotchas

- Multiple getters calling SOQL = many queries on page load.
- View state size limits (170 KB) not visible in the log; manifests as page load errors.
- `rerender` attribute on command buttons causes partial page re-execution; sometimes less of the controller runs than you expect.

## Experience Cloud / Communities / Sites

User-facing portals that can be authenticated or unauthenticated (Guest User).

### Authenticated community user

Running user is the community user (`005...`). Sharing model, profile, permission sets apply.

Log signature: normal Apex execution, but the user context has limited record access.

### Guest User (unauthenticated)

Running user is the Guest User assigned to the community. Major constraints:
- Guest users cannot see records they do not own unless sharing is explicit.
- Guest User profile has to grant object + field access.
- Guest User cannot update records without explicit permissions.
- Sharing via Sharing Rules for Guest User.

Log signature: running user is the Guest User, which is easy to miss. Any permissions error in an Experience Cloud log often traces back to Guest User misconfiguration.

## Connect/Chatter

Feed items, comments, and Chatter posts are records and can have triggers.

Log signatures:
- Trigger on `FeedItem` or `FeedComment`.
- `ConnectApi.ChatterFeeds.postFeedElement()` as an Apex method call.

## OmniStudio / Vlocity UI

Vlocity (now Salesforce Industries Cloud) has its own UI layer: OmniScripts, FlexCards, Data Raptors.

Log signatures:
- Namespace: `vlocity_cmt`, `vlocity_ins`, `vlocity_ps`, depending on the industry.
- `OmniScript` invocations appear as `CODE_UNIT_STARTED|[EventService....apex]|vlocity_*.OmniScript.<method>`.
- `DataRaptor` (DR) calls: `vlocity_cmt.DRRunnerImpl.run`.

Performance gotcha: OmniScripts can be very SOQL-heavy. One OmniScript step can do dozens of queries.

## LWC/Aura-specific grep recipes

```bash
# Every AuraEnabled method call
grep -oE "CODE_UNIT_STARTED\|\[[^]]+\]\|[^|]+\|[A-Za-z_]+\.[A-Za-z_]+" log.log | grep -vE "trigger|Visualforce|Batch" | sort -u

# Aura-specific events
grep "AURA" log.log

# Visualforce events
grep "VF_" log.log

# Remote actions
grep "RemoteAction\|VF Remoting" log.log

# Experience Cloud context (if any)
grep -i "community\|network\|guest\|site" log.log | head
```

## Common UI framework gotchas

1. **LWC wire not firing Apex**: cache hit. Refresh page, rerun.
2. **"No APEX action instance found"**: method is not `@AuraEnabled` or class is not accessible to the user's profile.
3. **Guest User sees blank page**: Guest User lacks FLS/CRUD on the object. Check Guest User profile.
4. **Updated field not reflected in LWC**: cache is stale. Call `refreshApex` or use `notifyRecordUpdateAvailable` from the uiRecordApi.
5. **Heavy VF page**: too many getters doing SOQL. Cache values in member variables.
6. **LWC @AuraEnabled cacheable on a user-specific value returns another user's data**: caching is per-user, but shared across tabs/sessions. Not quite a bug but can surprise.
7. **Community user lacks access in Apex**: `with sharing` is enforcing community sharing which is very restrictive. Consider `without sharing` where appropriate, with careful CRUD/FLS checks.
8. **Remote Action cannot bind to visualforce page rerender**: Remote Actions are outside the page state machine.
