# Gotchas — Custom Agent Actions Apex

Sources: Apex Developer Guide (Spring '26 PDF), Metadata API Developer Guide (Spring '26 PDF, GenAiFunction), "Quickstart Your Einstein Generative AI Solution" (Generative AI guide, Spring '26 PDF), and Agentforce Developer Guide pages under `developer.salesforce.com/docs/ai/agentforce/guide/`, read on 2026-10-03.

## Gotcha 1: Empty or Generic Descriptions Leave the Agent Guessing

**What happens:** A developer builds a custom action with a descriptive label ("Get Account Details") but a blank or generic description. The agent calls it for the wrong requests or not at all. The deployed action is a `GenAiFunction` whose `description` field is "a description explaining the general purpose and domain of the action", and each input and output in its `schema.json` has its own `description`.

**When it occurs:** When the Apex annotations, and therefore the generated action, carry placeholder text. Earlier versions of this skill quantified the miss rate (70%); that figure has no source and is removed.

**How to avoid:** Write the method description as a one-sentence directive that starts with "Use when" or "Invoke when", and write every input and output description as an instruction about what value goes there and in what format. Review the generated agent action's descriptions in Agentforce Builder after creation. UNVERIFIED (2026-10-03): whether the reasoning engine weighs `description` over `masterLabel` is not stated in any source read.

**Source:** Metadata API Developer Guide, GenAiFunction (`description`, input and output folder `schema.json` properties).

---

## Gotcha 2: `callout=true` Does Not Enable or Block Callouts

**What happens:** A team adds `callout=true` and still gets "You have uncommitted work pending", or assumes that without it the callout is blocked. The Apex Developer Guide defines the modifier as identifying "whether the method calls to an external system", and its section on invocable callouts says screen flows use it to decide whether the action can run in the current transaction. The uncommitted-work exception comes from DML or queued asynchronous work before the callout in the same transaction.

**When it occurs:** Actions that insert or update a record and then call out, or that are called after other actions performed DML in the same transaction. Earlier versions of this skill said omitting the modifier throws a CalloutException even with no prior DML; the guide does not support that.

**How to avoid:** Set `callout=true` on any action that calls out, so Flow can manage the transaction and readers can see it. Inside the method, perform all callouts before any DML. When work must be written after a slow callout, return a tracking ID and continue in a Queueable.

**Source:** Apex Developer Guide, InvocableMethod Annotation (Supported Modifiers: `callout`); "Making Callouts to External Systems from Invocable Actions"; "Performing DML Operations and Mock Callouts".

---

## Gotcha 3: The Agent User Is Not the Developer

**What happens:** An action works when run as an admin in Developer Console but returns no records when the deployed agent calls it. The agent user "determines what your agent can access and do", and for a Service Agent that is a dedicated user with the Agentforce Service Agent User permission set.

**When it occurs:** Any action tested only as an administrator.

**How to avoid:** Create a test user that matches the agent user's permission sets and run `System.runAs(agentUser)` in unit tests. Use `with sharing` and `WITH USER_MODE` so the agent user's sharing and FLS apply.

**Source:** Generative AI guide, Create an Agent (Define Settings: the agent user); Apex Developer Guide, InvocableMethod Annotation code samples (`WITH USER_MODE`, `AccessLevel.USER_MODE`).

---

## Gotcha 4: Agentforce Apex Actions Support Only Primitive Inputs and Outputs

**What happens:** An action returns `List<Account>` or takes a list field as input and works from Flow but not from the agent. The Generative AI guide states that custom actions that reference an Apex class or flow support only primitive data types, that collections aren't supported, and that custom actions can't accept a list and object as input. Raw sObjects also expose every populated field to the conversation.

**When it occurs:** DTOs reused from Flow-oriented invocable classes, or actions that return records directly.

**How to avoid:** Return a DTO whose `@InvocableVariable` fields are primitives (String, Boolean, Integer, Decimal, Date). Where structure is unavoidable, serialize the minimum fields to a JSON string. Name the fields the agent needs and nothing else.

**Source:** Generative AI guide, What are Agents? (Considerations for Custom Actions).

---

## Gotcha 5: No Output Marked for the Planner Means Random Answers

**What happens:** The action runs, returns data, and the agent's reply ignores it. In the action's output `schema.json`, `copilotAction:isUsedByPlanner` "Indicates whether the property is used by the agent planner. At least one output property must have this value as true or else the planner returns random responses."

**When it occurs:** Hand-edited or deployed `GenAiFunction` output schemas where every property has `isUsedByPlanner` false, often because only `isDisplayable` was set.

**How to avoid:** Set `copilotAction:isUsedByPlanner: true` on every output the agent must reason with, and `copilotAction:isDisplayable: true` only on outputs that should be shown to the user.

**Source:** Metadata API Developer Guide, GenAiFunction, Output Folder (`copilotAction:isUsedByPlanner`).

---

## Gotcha 6: Text Properties Have a 250-Character Ceiling in the Action Schema

**What happens:** A JSON payload or long message returned as a text output is cut short or rejected. The GenAiFunction schema reference lists `lightning__textType` with optional `maxLength` and `minLength` and states "The maximum text type length is 250 characters."

**When it occurs:** Actions that return serialized records or long explanations in a String field typed as text.

**How to avoid:** Keep text outputs short, or type long outputs as `lightning__multilineTextType` or `lightning__richTextType`. Test with realistic output sizes. UNVERIFIED (2026-10-03): the runtime behavior when a value exceeds 250 characters (truncation or error) is not described in the source.

**Source:** Metadata API Developer Guide, GenAiFunction, Input Folder and Output Folder (`lightning:type` values).

---

## Gotcha 7: Outputs Must Match Inputs by Size and Order

**What happens:** An action skips failed inputs and returns fewer outputs, or returns them in a different order. The caller then attaches results to the wrong requests. The guide states inputs and outputs "must match on both the size and the order", and that the method "must run and return the same number of results as inputs received even if errors occur".

**When it occurs:** Error handling that `continue`s past a bad input, or code that builds outputs from a Map.

**How to avoid:** Build exactly one output per input, in input order. Put failures in the output (`success = false`, `errorMessage`) instead of dropping the row.

**Source:** Apex Developer Guide, InvocableMethod Annotation (Inputs and Outputs; exception-handling paragraph and sample).

---

## Gotcha 8: One Invocable Method Per Class, and Packaged Ones Are Permanent

**What happens:** A second `@InvocableMethod` in the same class fails to compile. In a managed package, an invocable method added in one version cannot be removed later, and only global invocable methods appear in subscriber orgs.

**When it occurs:** When an "action utility" class grows several actions, or when an ISV ships actions in a package.

**How to avoid:** One outer class per action, delegating to a shared service class. Decide public or global before the first package version.

**Source:** Apex Developer Guide, InvocableMethod Considerations (Implementation Notes; Managed Packages).

---

## Gotcha 9: Custom Actions Get No Page Context

**What happens:** An action expects to know which record the user is looking at and receives nothing. The Generative AI guide says page context is supported for some standard agent actions, and "Page context isn't supported for custom agent actions."

**When it occurs:** Employee-agent actions that assume the current record ID is passed automatically.

**How to avoid:** Make the record ID an explicit input with a clear description, and let the agent obtain it from the conversation or a standard action.

**Source:** Generative AI guide, Considerations for Agent Conversations.

---

## Gotcha 10: Actions That Change Data Should Ask First

**What happens:** The agent closes a case or cancels an order on a misread request. `GenAiFunction` has an `isConfirmationRequired` field ("Indicates whether confirmation is required for this action").

**When it occurs:** Write actions deployed with the default settings.

**How to avoid:** Set `isConfirmationRequired` to true for actions that create, change, or delete data, or that send messages, and keep it false for read-only lookups.

**Source:** Metadata API Developer Guide, GenAiFunction (`isConfirmationRequired`).

---

## Gotcha 11: Agent-Specific Actions Are Not Retrieved by GenAiFunction

**What happens:** Source control has the asset-library actions but not the ones created inside a particular agent. In Winter '26 orgs and later, actions created within an agent are retrieved through `GenAiPlannerBundle`; `GenAiFunction` retrieves asset-library actions. Deploying to a Summer '25 (API 64.0) org requires retrieving with API 64.0.

**When it occurs:** Pipelines that only list `GenAiFunction` in `package.xml`.

**How to avoid:** Add `GenAiPlannerBundle` for agent-specific actions and pin the API version to the target org.

**Source:** Metadata API Developer Guide, GenAiFunction (Usage).

---

## Gotcha 12: `required` Means Nothing on Outputs, and Clashes With `defaultValue`

**What happens:** An output marked `required=true` is still null at run time, or an input annotated with both `required` and `defaultValue` throws an error. The guide says `required` "is ignored for output variables" and "The defaultValue modifier throws an error when used with required."

**When it occurs:** DTOs where every field gets the same annotation.

**How to avoid:** Use `required` only on inputs. Choose either `required` or `defaultValue` for an input, not both. Validate output completeness in code.

**Source:** Apex Developer Guide, InvocableVariable Annotation (Supported Modifiers).
