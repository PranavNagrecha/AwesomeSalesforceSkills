# Gotchas — Flow Action Framework

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Apex action not listed despite compiling in the IDE

**What happens:** The Flow author searches the Apex action palette and the class never appears.

**When it occurs:** Common when the running user lacks Apex class access, the method is not `static`, the annotation is missing, the org has an older API version incompatible with the feature set, or the class lives in another namespace and is not `global`.

**How to avoid:** Grant **Apex Class Access** on profiles or permission sets, confirm `@InvocableMethod` on a `public static` or `global static` method, and recompile in the target org. For packaged code, verify the publisher exposed the invocable.

---

## Gotcha 2: Scalar mapping to a list-only invocable input

**What happens:** Flow validates in the builder but fails at runtime, or only the first conceptual row is processed as expected while bulk paths drop data. UNVERIFIED (2026-09-05): this exact runtime symptom is not described in `api_meta.txt` or `apexdev.txt`. What the Apex guide does state is the requirement it violates — "For a correct bulkification implementation, the Inputs and Outputs must match on both the size and the order… the i-th Output entry must correspond to the i-th Input entry. Matching entries are required for data correctness when your action is in bulkified execution, such as when an apex action is used in a record trigger flow" (`apexdev.txt` L5456-5458).

**When it occurs:** Record-triggered after-save paths pass `$Record` while the Flow variable feeding Apex is typed as a single record but the interview is bulk; or a collection is never built before the Apex action.

**How to avoid:** Align variable types with the invocable signature: use SObject collection variables when the Apex input is `List<Wrapper>` representing many rows. Test with multi-record transactions.

---

## Gotcha 3: Unwired Apex action fault path

**What happens:** Any uncaught Apex exception or platform fault terminates the interview with a generic error; screen flows show a poor end-user message.

**When it occurs:** Teams accustomed to fault-tolerant standard actions omit the Apex action’s fault connector.

**How to avoid:** Always connect the fault path, capture `$Flow.FaultMessage`, and route to recovery UI or logging consistent with the automation’s reliability requirements.

---

## Gotcha 4: Subflow input/output renames break parents silently until activation

**What happens:** Child flow variable API names change; parent **Run Subflow** mappings become invalid or default to empty values.

**When it occurs:** Agile renaming of child flow variables without regression-testing all parent flows.

**How to avoid:** Treat child input/output API names as contract; version child flows or communicate breaking changes; run Flow test coverage or manual activation checks for each parent.

---

## Gotcha 5: `flowTransactionModel` is `Required` on every action call, not only on ones that call out

**What happens:** A hand-written or LLM-generated `<actionCalls>` element carries
`actionName`, `actionType` and `inputParameters` and nothing else. The author reasons that
a Chatter post has no transaction concern, so no transaction model is needed.

**When it occurs:** Any time flow XML is authored outside Flow Builder — a migration
script, a template, a generated fragment pasted into an existing flow.

**How to avoid:** `FlowActionCall` marks exactly three fields `Required`: `actionName`,
`actionType`, and `flowTransactionModel` (`api_meta.txt` L68462-68466, L68479-68480). The
guide's own sample flow sets `<flowTransactionModel>CurrentTransaction</flowTransactionModel>`
on both of its action calls, including the `chatterPost` one (L73229, L73259). Pick
deliberately: `Automatic` "Creates a transaction if the invocable action supports it and
there's pending DML"; `CurrentTransaction` "Keeps the invocable action running in the same
transaction"; `NewTransaction` "Creates a transaction before the invocable action is
executed" (L68481-68486). API 51.0 and later — below that the field does not exist, which
is why flows retrieved from very old orgs omit it legitimately.

---

## Gotcha 6: `actionName` is unique only *within* an `actionType`, so the pair is the address

**What happens:** A flow is repointed by editing `actionName` alone, from an Apex action to
a same-named autolaunched flow (or the reverse). It deploys. It calls something else.

**When it occurs:** Renaming or "upgrading" an action in place; search-and-replace across a
flows directory; assuming action names are globally unique the way Apex class names are.

**How to avoid:** "Required. Name for the action. Must be unique across actions with the
same `actionType`" (`api_meta.txt` L68462-68463). Two rows in the action catalogue can
legitimately share a name as long as their `actionType` differs — and the REST catalogue
is shaped the same way, one collection per type: `.../actions/custom/quickAction`,
`/apex`, `/emailAlert`, `/flow`, `/sendNotification` (`api_rest.txt` L13836-13841). Change
`actionName` and `actionType` together, then re-describe
`/services/data/vXX.X/actions/custom/apex/<name>` to confirm the target exists.

---

## Gotcha 7: `actionType` `flow` is illegal from the flow types most likely to want it

**What happens:** An autolaunched or screen flow needs to call another flow. The author
finds `flow` in the `InvocableActionType` enum, writes an `<actionCalls>` element with
`<actionType>flow</actionType>`, and the flow will not save or run.

**When it occurs:** Reading the enum list top-to-bottom without reading the value's own
sentence; or converting a Process Builder "Flows" action, which really was an action call.

**How to avoid:** The enum entry says it outright: `flow` "Invokes an autolaunched flow.
This action type isn't available for flows with a `processType` of `Flow` or
`AutolaunchedFlow`. To invoke an autolaunched flow from one of those types, use
`FlowSubflow`" (`api_meta.txt` L68749-68753). So there are two mechanisms for calling a
flow and the legal one depends on the *caller's* `processType`, not on the child. Screen
flows (`Flow`) and autolaunched flows use `<subflows>`; other process types (recommendation
strategies, orchestrations, and similar) use the action call. Child-contract design lives
in `flow/subflows-and-reusability`.

---

## Gotcha 8: An async action's timeout does not travel down the fault connector

**What happens:** An action configured to pause the flow until it completes never returns.
The fault path — carefully built, logging `$Flow.FaultMessage` — is never taken, and the
interview stalls or ends somewhere the author did not draw.

**When it occurs:** `isWaitUntilCompleted` is set true (API 61.0+) with `offset` /
`offsetUnit` on an action that supports asynchronous execution, and only a `faultConnector`
was wired.

**How to avoid:** `FlowActionCall` has two distinct escape connectors. `faultConnector`
"Specifies which node to execute if the action call results in an error" (`api_meta.txt`
L68476-68477); `timeoutConnector` "Specifies which node to execute if an async action
execution is timed out", API 62.0 and later (L68532-68534). A timeout is not an error, so
it takes the second one. `timeoutPathUsage` (`DisableTimeoutPath` / `EnableTimeoutPath`,
API 66.0+, L68536-68540) is what turns the path on. Wire both connectors on any action
where `isWaitUntilCompleted` is true, and route them to different log rows so you can tell
"the callee failed" from "the callee never answered".

---

## Gotcha 9: `Order` in an `InvocableActionExtension` is all-or-nothing

**What happens:** Two of an action's six inputs get an `Order` attribute so the important
ones float to the top. The property panel in Flow Builder comes back in an order nobody
asked for, and the two ordered fields are not necessarily where they were put.

**When it occurs:** Ordering is treated as a partial hint rather than a total ordering — the
natural reading, since the file targets one parameter at a time.

**How to avoid:** The Apex guide flags it as an *Important* note: "To sort the order of
input fields, define an `Order` for all input parameters for the action. If you define an
`Order` for at least one parameter, you must define an `Order` for all parameters within
the action to avoid unexpected behavior" (`apexdev.txt` L26985-26986). The default with no
extension at all is alphabetical (L26901-26902). Two related traps in the same file: the
standard key names differ between the two guides — `Group`/`ProvidedValuesList` in the Apex
guide's worked example (L26996-27011, L27048) versus `GroupName`/`ProvidedValueList` in the
Metadata API field table (`api_meta.txt` L82000-82005) — and a static picklist caps at 500
values per input parameter (`apexdev.txt` L27034).

---

## Gotcha 10: Three of the four common action families do not pull their dependencies into a package

**What happens:** A package or change set containing the flow deploys into a clean org and
fails, or installs and then errors at runtime on a missing email template, quick action, or
Apex class.

**When it occurs:** Trusting the dependency crawler, which resolves record types, fields
and objects referenced by a flow but not the things an *action* points at.

**How to avoid:** The REST guide names the exact list: "If any of these elements are used
in a flow, packageable components that reference the elements aren't automatically included
in the package" — *Apex action, Email alerts, Post to Chatter core action, Quick Action
core action, Send Email core action, Submit for Approval core action* — followed by "if you
use an email alert, manually add the email template that's used by that email alert. To
deploy the package successfully, manually add those referenced components to the package"
(`api_rest.txt` L13787-13800). Build the manifest from the flow's action inventory, not
from the flow. `references/metadata-examples.md` § 4 shows the resulting `package.xml`.

---

## Gotcha 11: A `FlowTest` can only assert at `Start` and `Finish`, so it cannot see an action's output

**What happens:** A test is written to assert that the Apex action returned three ranked
Cases. There is nowhere to put the assertion, and the author concludes FlowTest is broken
or that the element API name must be spelled differently.

**When it occurs:** Reasoning by analogy with Apex unit tests, where any intermediate value
is inspectable.

**How to avoid:** `FlowTestPoint.elementApiName` is "Required. The element API names for
the start of the flow and the end of the flow. Possible values are: `Start`, `Finish`"
(`api_meta.txt` L74140-74146). Design for it: route whatever you want to assert into a flow
variable and assert on that variable at `Finish`. Two more boundaries in the same type —
FlowTest covers "a record-triggered, autolaunched, or Data Cloud-triggered flow"
(L73961-73962), so an action wired into a screen flow gets none; and
`FlowTestPoint.isUseMockOuput` is "Reserved for future use" (L74148), so the test really
invokes the action, really sends the email alert, and really posts to Chatter. Broader
FlowTest technique is `flow/flow-testing`.

---

## Gotcha 12: A legacy Apex action is a different element type, and no `actionType` edit converts it

**What happens:** An org retrieved from a long-lived tenant contains `<apexPluginCalls>`
elements. Someone "modernises" them by changing them to `<actionCalls>` with
`<actionType>apex</actionType>`, and nothing binds — or the element is dropped in
Flow Builder's auto-layout canvas and cannot be added back.

**When it occurs:** Classes implementing `Process.Plugin` predate `@InvocableMethod` and
still appear in Flow Builder "as a legacy Apex action" (`apexdev.txt` L27272-27273).

**How to avoid:** `FlowApexPluginCall` is its own metadata type with its own field set —
`apexClass`, `connector`, `faultConnector`, `inputParameters`, `outputParameters`
(`api_meta.txt` L69680-69702) — and it keys on `apexClass`, not `actionName`/`actionType`.
It has no `flowTransactionModel`, no `dataTypeMappings`, and no `storeOutputAutomatically`.
Migrating means rewriting the Apex to `@InvocableMethod` and rebuilding the element, and
there is a real reason to do it: the interface "doesn't support Blob, Collection, and
sObject, data types, and it doesn't support bulk operations. After you implement the
interface on a class, the class can be referenced only from flows", while the annotation
"supports all data types and bulk operations… can be referenced from flows, processes, and
the Custom Invocable Actions REST API endpoint" (`apexdev.txt` L27262-27265). Meanwhile
"Legacy Apex actions aren't supported in auto-layout in Flow Builder. Legacy Apex actions
are only available to be added in free-form in Flow Builder. Existing actions can be edited
in both auto-layout and free-form mode" (L27266-27267) — which is why the element survives
retrieval but resists editing.

---

## Gotcha 13: LWC local actions are screen-flow-only and abandon their work after 120 seconds

**What happens:** An `lwcComponent` action works in a screen flow and then does nothing —
or cannot be selected at all — when the same logic is needed in a record-triggered path.
Separately, a long client-side call "fails" but the remote system still processes it.

**When it occurs:** Treating a local action as just another action in the palette;
`InvocableActionType` lists `lwcComponent` alongside `apex` with no runtime caveat
(`api_meta.txt` L68830-68832).

**How to avoid:** The LWC guide sets both boundaries. "Lightning web components require a
browser context to run, so flow local action components are supported only in screen flows"
and "Flows that include Lightning web components are supported only in Lightning runtime"
(`lwc_guide.txt` L8810-8811). On timeout: "By default, requests time out after 120 seconds"
and "If an asynchronous request times out, the flow executes the local action's fault
connector and sets the error message to `$Flow.FaultMessage`. However, the original request
isn't automatically canceled. To abort an asynchronous request, use the `cancelToken`
parameter available in the `invoke()` method" (L8863). Note this is the one action family
where the guide *does* state that a timeout goes down the fault connector — the opposite of
the async `timeoutConnector` behaviour in Gotcha 8. The default message is "An error
occurred when the *elementName* element tried to execute the *c-myComponent* component"
(L8840), which is why an unhandled local-action fault reads like a component bug to the end
user rather than an integration outage.

---

## Gotcha 14: An HTTP Callout action is not its own metadata type

**What happens:** A flow built with Flow Builder's HTTP Callout wizard is put into a
manifest as some `HttpCallout` member. There is no such type, so the action arrives in the
target org unbound.

**When it occurs:** The Flow Builder UI presents HTTP Callout as a distinct thing to
create, so it reads like a distinct thing to deploy.

**How to avoid:** The schema the wizard infers is stored as an `ExternalServiceRegistration`
whose `registrationProviderType` is `SchemaInferred` — "The API specification was provided
during the HTTP Callout configuration process. Available in API version 57.0 and later"
(`api_meta.txt` L64091-64093). That type carries the `namedCredential` and the OpenAPI
`schema` (L64024, L64096-64097) and lives in `externalServiceRegistrations`
(L64006-64008). Ship the registration and its Named Credential alongside the flow.
UNVERIFIED (2026-09-05): the guide does not state in one place which `actionType` the
resulting flow element carries; `externalService` is the only enum value describing an
"External Service schema registered through Setup" (L68739-68742), so that is the expected
value — retrieve one working HTTP Callout flow and confirm before templating it. Callout
design itself is `flow/flow-http-callout-action` and
`flow/flow-external-services`.
