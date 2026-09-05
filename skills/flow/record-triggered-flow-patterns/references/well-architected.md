# Well-Architected Notes — Record Triggered Flow Patterns

## Relevant Pillars

### Reliability

Choosing the right record-triggered pattern keeps transactions predictable and reduces accidental recursion or hidden side effects.

### Scalability

Before-save and after-save have very different scale characteristics, and the trigger model needs to fit the real record volume.

### Operational Excellence

Well-scoped entry criteria and explicit trigger context make record-triggered automation easier to reason about, debug, and hand over.

## Architectural Tradeoffs

- **Before-save efficiency vs after-save flexibility:** Before-save is cheaper, but after-save is necessary for committed side effects and related-record work.
- **Declarative speed vs code-level control:** Flow is easier to maintain for moderate logic, while Apex provides tighter orchestration for complex transaction behavior.
- **Broad starts vs explicit business events:** Broad starts are quicker to configure, but field-change-aware criteria produce more reliable automation.

## Anti-Patterns

1. **After-save used for simple same-record updates** — wastes DML and creates avoidable recursion risk.
2. **Record-triggered flows that run on every edit** — operationally noisy and harder to troubleshoot.
3. **Ignoring mixed automation on the same object** — the flow design fails because validation rules or Apex still shape the transaction.
4. **Entry criteria that test a state where the requirement is a transition** — the flow is correct on the day it ships and wrong the first time a data load touches historical records.
5. **`triggerOrder` left unset on an object that already has a record-triggered flow** — the sequence is undeclared, so identical metadata can behave differently between orgs and nothing in the deploy output says so.
6. **DML elements with no `faultConnector`** — the failure mode is silence, which is strictly worse than an error: nothing to alert on and nothing to query.
7. **Shipping a `flowDefinitions/` directory alongside modern flows** — the definition's `activeVersionNumber` overrides the flow's `status`, so a successful deploy can leave production on an old version.

## Official Sources Used

- **Apex Developer Guide — *Triggers and Order of Execution*** (`apexdev.txt` L15402–15490, PDF: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf) — the 20-step save order: before-save flows at step 3, before triggers at 4, validation at 5, duplicate rules at 6, save at 7, after triggers at 8, after-save flows at 14, commit at 19, asynchronous flow paths at 20. Supports every save-order claim in SKILL.md § *Order Of Execution Still Applies*.
- **Apex Developer Guide — recursive-save note** (`apexdev.txt` L15414–15415) — "During a recursive save, Salesforce skips steps 9 … through 17." Supports `references/gotchas.md` § *A Recursive Save Skips Steps 9 Through 17*, which is the one place the flat step list actively misleads.
- **Apex Developer Guide — versioned behaviour** (`apexdev.txt` L15509 and L44657) — "In API version 53.0 and earlier, after-save record-triggered flows run after entitlements are executed." Supports the gotcha that a flow's own `<apiVersion>` moves it in the save order.
- **Metadata API Developer Guide — `Flow`** (`api_meta.txt` L68065–68470, PDF: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf) — `apiVersion` (L68075), `runInMode` enum (L68374–68390), `status` / `FlowVersionStatus` enum (L68416–68424), `triggerOrder` "from 1 to 2,000", API 54.0+ (L68438–68441). Supports the frontmatter of every flow in `references/metadata-examples.md` and the checker's status/triggerOrder rules.
- **Metadata API Developer Guide — `FlowStart`** (`api_meta.txt` L72279–72580) — `doesRequireRecordChangedToMeetCriteria` (L72322–72325), `filterFormula` (L72390–72392), `recordTriggerType` enum (L72450–72457), `FlowTriggerType` enum including `RecordAfterSave` (L72524), `RecordBeforeDelete` (L72536) and `RecordBeforeSave` (L72539) — and no after-delete value anywhere in it. Supports the entry-criteria and delete-context gotchas.
- **Metadata API Developer Guide — `FlowScheduledPath`** (`api_meta.txt` L71389–71425) — `maxBatchSize` "from 1 to 200. Default is 200" (L71397–71398), `offsetUnit` values (L71405–71411), `pathType` / `AsyncAfterCommit` (L71412–71415), `timeSource` (L71420–71423). Supports the scheduled path in `references/metadata-examples.md` § 2 and the batching gotcha.
- **Metadata API Developer Guide — `FlowDefinition` and the API 44.0 upgrade checklist** (`api_meta.txt` L73186–73201 and L73920–73957) — "the active version numbers in the flow definitions override the status fields in the flows"; "The `flowDefinitions` directory is empty." Supports § 5 of `references/metadata-examples.md` and the stale-activation gotcha.
- **Metadata API Developer Guide — `FlowTest`** (`api_meta.txt` L73959–74380) — suffix and folder (L73976), API 55.0+ (L73980), `testType` API 66.0+ (L74041–74048), `elementApiName` limited to `Start` / `Finish` (L74143–74147), `InputTriggeringRecordInitial` / `InputTriggeringRecordUpdated` / `ScheduledPath` parameter types (L74304–74329), and the guide's own sample definition (L74342–74380). Supports the transition test in `references/metadata-examples.md` § 4.
- **Metadata API Developer Guide — flow record elements** (`api_meta.txt` L70930–71300) — `faultConnector` on `FlowRecordCreate` (L70965), `FlowRecordDelete` (L71046), `FlowRecordLookup` (L71120) and `FlowRecordUpdate` (L71283); `FlowCustomError` "to roll back a change that triggered a flow" (L70006–70008). Supports the fault-path rule the checker enforces.
- **Object Reference — `FlowDefinitionView`** (`object_reference.txt` L139267–139790, PDF: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf) — queryable from API 46.0; `RecordTriggerType` (L139689), `TriggerObjectOrEventLabel` (L139755), `TriggerOrder` (L139763–139769), `TriggerType` (L139772). Supports the verification SOQL in `references/metadata-examples.md` § 8.
- **Salesforce Help — Flow Builder, Flow Reference, and "Guidelines for Defining the Run Order of Record-Triggered Flows for an Object"** — https://help.salesforce.com/s/articleView?id=sf.flow.htm&type=5 and https://help.salesforce.com/s/articleView?id=sf.flow_ref.htm&type=5. Referenced by the Metadata API guide (L68440) for run-order guidance. **Not fetchable from this environment**, which is why the `triggerOrder` tie-break behaviour and the before-save element restrictions carry UNVERIFIED markers rather than confident claims.
