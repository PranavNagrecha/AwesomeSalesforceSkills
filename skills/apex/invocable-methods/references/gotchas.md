# Gotchas — Invocable Methods

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.
Line references are into the Apex Developer Guide v67.0 (`apexdev`), the Apex Reference Guide v67.0
(`apexrefguide`), the Metadata API Developer Guide v67.0 (`api_meta`), and the REST API Developer
Guide v67.0 (`api_rest`), all Summer '26.

---

## The Output List Must Match The Input List In Size **And** Position

**What happens:** The action returns fewer results than it received, or returns them in the order
work completed rather than the order the inputs arrived, and the flow attributes outcomes to the
wrong records. Nothing throws — the wrong Case gets marked escalated and the right one does not.

**When it occurs:** The result list is built inside the success branch, or built by iterating a
`Map.values()` / a query result / a `List<Database.SaveResult>` instead of iterating the original
input list. Both are invisible with one input and wrong from the second input on.

**How to avoid:** Seed one result object per input before any work happens, then fill them in by
index. The guide is explicit: "For a correct bulkification implementation, the Inputs and Outputs
must match on both the size and the order. For example, the i-th Output entry must correspond to
the i-th Input entry. Matching entries are required for data correctness when your action is in
bulkified execution, such as when an apex action is used in a record trigger flow"
(apexdev L5456–5458). Its own primitive sample carries the comment "put each name in the output at
the same position as the id in the input" (apexdev L5203–5211). See
`references/code-examples.md` §3 step 1.

---

## One Class, One Invocable Method — There Is No Overloading

**What happens:** A second `@InvocableMethod` is added to the same class to expose a "single-record"
convenience wrapper alongside the bulk one, and the class no longer compiles or the second action
never appears in Flow Builder.

**When it occurs:** Someone treats the annotation like `@AuraEnabled`, which can decorate many
methods on one class.

**How to avoid:** "Only one method in a class can have the InvocableMethod annotation"
(apexdev L5422), and the guide repeats it for packaged agent actions: "Create a separate global
Apex class for each agent action in your managed package" (apexdev L43669–43670). One action per
outer class; share the body through a service. The only annotation you may stack on it is
`@Deprecated`: "The only annotation that can be used with the InvocableMethod annotation is
Deprecated" (apexdev L5430) — so `@TestVisible`, `@AuraEnabled` and `@Future` on the same method
are all rejected. The checker at `scripts/check_invocable_methods.py` flags a class with more than
one.

---

## An Uncaught Exception Faults The Whole Batch Of Interviews, Not One Input

**What happens:** Input 7 of 200 has a null Id, the method throws, and all 200 interviews take the
flow's fault path. The 199 records that would have processed cleanly are not processed, and the
transaction's DML is rolled back with them.

**When it occurs:** The action validates inputs by throwing, or lets a service exception escape,
because that is the normal Apex idiom.

**How to avoid:** Report per-input failure as *data* in that input's result object. The guide states
the rule and shows the pattern: "To handle exceptions within an invocable method, wrap the results
in an Apex object that reports failures. The execution of the invocable method must run and return
the same number of results as inputs received even if errors occur" (apexdev L5318–5319), followed
by `AdjustPositiveValuesAction`, which catches per value and sets `adjustmentSucceeded = false`
rather than propagating (apexdev L5322–5359). Reserve throwing for a failure that genuinely
invalidates the whole call — and when you do throw, make sure the `actionCalls` node has a
`faultConnector`, which "Specifies which node to execute if the action call results in an error"
(api_meta L68479). Fault-path design is `flow/fault-handling`.

---

## `callout=true` Does Not Start A New Transaction Outside A Screen Flow

**What happens:** An action marked `callout=true` is called from a record-triggered flow that has
already saved records, and the callout dies with `System.CalloutException: You have uncommitted
work pending. Please commit or rollback before calling out.` (message text asserted at
apexdev L8768–8769). The developer concludes the modifier is broken.

**When it occurs:** `callout=true` is read as "this action is allowed to call out anywhere",
by analogy with `@Future(callout=true)`.

**How to avoid:** Understand the three-condition gate, which is **screen-flow only**. All three must
hold for a new transaction: "The method's callout modifier is true", "The action's Transaction
Control setting in a screen flow is configured to let the flow decide", "The current transaction has
uncommitted work" (apexdev L26872–26876). If any of "The callout modifier is false", "The action is
executed by a non-screen flow", "The current transaction doesn't have uncommitted work" holds, then
"the flow executes the action in the current transaction" (apexdev L26877–26880). For non-screen
flows the lever is the element's own `flowTransactionModel`: `NewTransaction` "Creates a transaction
before the invocable action is executed" (api_meta L68485–68486). Transaction boundaries in flows
are owned by `flow/flow-transactional-boundaries`.

---

## `@InvocableVariable` Silently Rejects Static, Final, Protected And Property Members

**What happens:** A wrapper field is declared `public static final String DEFAULT_REASON` or turned
into a property with `{ get; set; }`, and it never appears in Flow Builder — or the class fails to
save.

**When it occurs:** A constant is added to the wrapper class for tidiness, or `public String x { get;
set; }` is used out of C# habit.

**How to avoid:** "Only global and public variables can be invocable variables" and the invocable
variable "can't be any of these: A non-member variable such as a static or local variable. A
property. A final variable. Protected or private" (apexdev L5718–5723). Plain `public` instance
fields only. Constants belong on the service class, not on the wrapper. And the field name is the
integration contract: "The invocable variable name in Apex must match the name in the flow. The
name is case-sensitive" (apexdev L5731) — renaming `caseId` to `recordId` breaks every flow that
binds it, and the flow does not warn at save time.

---

## `List<List<sObject>>` Is Legal As A Return Type And A Runtime Error As A Wrapper Field

**What happens:** A wrapper class declares `public List<List<SObject>> batches;` to hand a flow
nested collections. It compiles and then fails at runtime.

**When it occurs:** Someone reads the input/output type list, sees `List<List<sObject>>` allowed,
and assumes it is allowed everywhere.

**How to avoid:** The guide draws the line explicitly, twice: "@InvocableVariable fields of type
`List<List<sObject>>` are not supported in user-defined Apex classes and cause a runtime error. Use
`List<List<sObject>>` only as a direct @InvocableMethod return type" (apexdev L5440–5442, repeated
at L5452–5454). The permitted wrapper field types are narrower than the permitted method types:
"A primitive other than Object", "An sObject, either the generic sObject or a specific sObject",
"A list of primitives, sObjects, or objects created from Apex classes", "A list of lists of
primitives or objects created from Apex classes" (apexdev L5725–5729) — note `sObject` is absent
from that last line.

---

## Generic `sObject` Inputs Need `dataTypeMappings` In The Flow, Or The Action Cannot Be Configured

**What happens:** The wrapper declares `public List<SObject> inputCollection` so the action works
for any object. In Flow Builder the admin cannot bind a collection, or the deployed flow fails
because the concrete type was never resolved.

**When it occurs:** A "reusable" generic action is built without the flow-side half of the contract.

**How to avoid:** `List<sObject>` and `List<List<sObject>>` *are* supported input and return types
(apexdev L5435), and the guide ships the `GetFirstFromCollection` sample to prove it
(apexdev L5240–5288). The flow must then carry a `FlowDataTypeMapping` per generic parameter, where
"The `T__` prefix is required for input variables. The `U__` prefix is required for output
variables" and `typeValue` is the "API name of the specific sObject data type that this value maps
to" (api_meta L70192–70203) — the guide's own flow sample shows `T__inputCollection` and
`U__outputMember` both mapped to `Account` (api_meta L73221–73228). Available in API version 48.0
and later (api_meta L70178–70179).

---

## Removing The Annotation Breaks The Flow At Runtime, Not At Deploy Time

**What happens:** An action is retired by deleting `@InvocableMethod` from the class. The deploy
succeeds. Every interview that reaches the action element then fails in production.

**When it occurs:** Rollback or cleanup, where deactivating the flow first feels like the optional
step.

**How to avoid:** "If you add an Apex action to a flow, and then remove the Invocable Method
annotation from the Apex class, a runtime error in the flow occurs" (api_rest L13781–13782).
Deactivate or re-point the flow first, then change the class. In a managed package the constraint
is harder still: "after you add an invocable method you can't remove it from later versions of the
package" (apexdev L5460–5461). Treat the signature as permanent from the first release — that is
the real argument for wrapper DTOs over primitives, since a wrapper can gain a field without
changing the method signature (apexdev L43673–43676).

---

## Apex Class Access Is A Separate Grant, And Its Absence Looks Like A Flow Bug

**What happens:** The flow works for the admin who built it and fails for everyone else, with an
error that names the flow element rather than the permission.

**When it occurs:** The class is deployed but never added to a permission set's `classAccesses`,
because Apex called from a flow feels like platform code rather than user-invoked code.

**How to avoid:** "If a flow invokes Apex, the running user must have the corresponding Apex class
security set in their user profile or permission set" (apexdev L5172); the REST guide repeats it
for the API path — "Describe and invoke for an Apex action respect the profile access for the Apex
class. If you don't have access, an error is issued" (api_rest L13780). Ship the permission set in
the same manifest as the class; `references/code-examples.md` §7 shows it.

---

## Public vs Global Decides Whether A Subscriber Ever Sees The Action

**What happens:** A managed package ships an action that works in the packaging org and is invisible
in every subscriber org's Flow Builder.

**When it occurs:** The class and method were left `public`, which is correct for an unpackaged org
and wrong for a package.

**How to avoid:** "Public invocable methods can be referred to by flows and processes within the
managed package. Global invocable methods can be referred to anywhere in the subscriber org. Only
global invocable methods appear in Flow Builder and Process Builder in the subscriber org"
(apexdev L5462–5465), and the same split applies to the variables: "Only global invocable variables
appear in Flow Builder and Process Builder in the subscriber org" (apexdev L5733–5735). Agentforce
actions in a package add a further requirement: "Your Apex method must be global static"
(apexdev L43653).

---

## `defaultValue` And `required` Cannot Be Combined

**What happens:** `@InvocableVariable(required=true defaultValue='High')` is added so the field is
both mandatory and pre-filled, and the class fails to save.

**When it occurs:** The two modifiers read as complementary.

**How to avoid:** "The defaultValue modifier throws an error when used with required"
(apexdev L5693). Pick one: `required=true` to force the admin to bind something, or `defaultValue`
to supply a fallback the admin may leave alone. Note also that `required` is meaningless on the way
out — "The value is ignored for output variables" (apexdev L5691) — so a `required=true` on a
result field promises the flow builder nothing. `defaultValue` is a **string** in every case, even
for numeric types, with type-specific suffix rules: Double needs the `d` suffix, Long needs `l`,
Decimal and Integer must have none (apexdev L5656–5682).

---

## API 66.0 Added A No-Argument-Constructor Requirement To Parameter Classes

**What happens:** A wrapper class that only has a convenience constructor —
`public Request(Id caseId) { … }` — worked for years and starts failing once the class is saved at
API version 66.0 or later.

**When it occurs:** A class is bumped to a newer API version during an unrelated refactor, or a new
class is written with a parameterised constructor and no default one.

**How to avoid:** "Starting in API version 66.0, Apex classes used for invocable action parameters
must have a visible no-argument constructor. Use the default constructor or add your own
constructor. The constructor must be public for non-packaged classes or global for packaged classes
invoked from outside the package" (apexdev L5737–5739). Declaring any constructor removes the
implicit default one, so a wrapper with a convenience constructor must declare the empty one too.

---

## `Invocable.Action.getDescribe()` Is Expensive And Easy To Put In A Loop

**What happens:** Apex that calls standard or custom actions describes the action once per record,
and the transaction slows down or trips limits for reasons that do not show up as SOQL or DML.

**When it occurs:** A generic dispatcher builds an `Invocable.Action`, describes it to discover
parameter names, then invokes — all inside a `for` loop over records.

**How to avoid:** The reference guide warns directly: `getDescribe()` "returns detailed metadata
about an invocable action, including its inputs, outputs, and configuration. Because this method
retrieves comprehensive describe information, it can have performance implications. Use
`getDescribe()` judiciously, especially in performance-sensitive contexts such as loops or
frequently executed code paths" (apexrefguide L160648–160652). Describe once, cache the parameter
names, then loop. Results come back as `List<Invocable.Action.Result>` (apexrefguide L160993–160997)
whose entries answer `isSuccess()`, `getErrors()` and `getOutputParameters()`
(apexrefguide L162561–162573) — read those instead of assuming the call succeeded.

---

## The REST Invocation Path Accepts Only Primitives, So It Cannot Prove A Complex Contract

**What happens:** A team tests an action over REST, gets a clean response, and ships. The flow then
fails on a wrapper field the REST call never exercised.

**When it occurs:** `/services/data/vXX.X/actions/custom/apex/<Class>` is used as the smoke test for
an action whose wrapper carries sObject or collection fields.

**How to avoid:** "When invoking an Apex action using the POST method and supplying the inputs in
the request, only the following primitive types are supported as inputs: Blob, Boolean, Date,
Datetime, Decimal, Double, ID, Integer, Long, String, Time" (api_rest L13767–13779). REST is a good
proof of registration, access and index alignment — not of the full contract. Anything involving
sObject or collection inputs has to be proved by an Apex test at 200 inputs
(`references/code-examples.md` §4) and by an actual flow run.
