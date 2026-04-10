# Gotchas — CPQ Custom Actions

Non-obvious Salesforce CPQ platform behaviors that cause real production problems when working with custom actions.

## Gotcha 1: Five-Action Hard Limit Is Enforced Silently Per Location

**What happens:** Salesforce CPQ enforces a maximum of five active `SBQQ__CustomAction__c` records per `SBQQ__Location__c` value (e.g., five for Line Item, five for Group, five for Global). When the count exceeds five, the QLE renders only five buttons and silently discards the rest. No error is thrown in the UI, in logs, or in the browser console. Reps simply report that a button "disappeared" with no explanation.

**When it occurs:** Any time a new active custom action is added for a location that already has five active records. This most commonly surfaces after an org migration, a CPQ upgrade, or when multiple teams independently add actions to the same location without coordinating.

**How to avoid:** Before creating any new custom action, run this SOQL query and count the results:
```sql
SELECT Id, Name, SBQQ__Location__c
FROM SBQQ__CustomAction__c
WHERE SBQQ__Location__c = 'Line Item'
  AND SBQQ__Active__c = true
```
If the count is at 5, either deactivate an existing action or consolidate multiple actions into a single Flow that presents a choice screen to the rep.

---

## Gotcha 2: Custom Actions Cannot Directly Execute Apex — No Apex Action Type Exists

**What happens:** Practitioners expect to configure a custom action that calls an Apex class directly, similar to how Lightning quick actions can invoke Apex. No such action type exists on `SBQQ__CustomAction__c`. The valid `SBQQ__Type__c` values are: `URL`, `Flow`, `Calculate`, `Save`, and `Add Group`. Attempting to set an unsupported type value causes the record to save but the button to fail silently or not render.

**When it occurs:** Whenever a business requirement involves Apex logic (custom validation, external callouts, complex data manipulation) triggered from a QLE button.

**How to avoid:** Use one of two supported workarounds:
1. **Flow bridge** — Set `SBQQ__Type__c = Flow`, build an Autolaunched or Screen Flow, and call the Apex logic via an `@InvocableMethod` action element inside the Flow.
2. **URL to Visualforce** — Set `SBQQ__Type__c = URL` pointing to a Visualforce page that runs an Apex controller. Pass context (Quote ID, Line ID) via CPQ merge field tokens in the URL.

---

## Gotcha 3: Conditional Visibility Uses the CPQ Condition Engine Evaluated at Page Load, Not Flow or Apex

**What happens:** Custom action visibility conditions are evaluated by the CPQ managed package's condition evaluation engine when the QLE page loads. They are not re-evaluated dynamically as a rep edits fields in the QLE. If a rep changes a field value that would satisfy a condition (e.g., changing Status from `Draft` to `Approved`), the button visibility does not update until the page is fully reloaded.

**When it occurs:** Any time a stakeholder expects the button to appear or disappear in real time as reps edit quote fields in the QLE. This creates a confusing experience if the business process assumes the button is always visible in the correct state.

**How to avoid:** Design visibility conditions around fields that are set before the QLE is opened, not fields the rep edits inside the QLE. Document the "reload to see updated button visibility" behavior in rep training materials. If real-time toggling is a hard requirement, consider using a Global location button (always visible) that internally checks the condition at the start of the Flow and presents an informative message if the condition is not met.

---

## Gotcha 4: URL Merge Field Tokens Resolve to the Record Type Matching the Location

**What happens:** The `{!FieldName}` token syntax in `SBQQ__URL__c` resolves fields from different parent records depending on the `SBQQ__Location__c` value. For `Location = Line Item`, `{!Id}` resolves to the quote line record ID. For `Location = Global`, `{!Id}` resolves to the quote record ID. Cross-referencing the wrong location produces a broken or mismatched URL at runtime.

**When it occurs:** When a URL action is configured at the `Global` location but the URL template includes line-level field tokens like `{!SBQQ__ProductCode__c}`. The token resolves to blank because global actions do not have a line item context.

**How to avoid:** Match the field tokens in the URL to the record type that the location context provides. For line-level data in a Global action, use related field traversal syntax: `{!SBQQ__Quote__r.FieldName__c}` does not work for line-level fields from a global context — in that case, switch to a Flow action that can query the lines programmatically.

---

## Gotcha 5: Flow Must Be Activated Before the Custom Action Record Is Saved (or the Button Fails at Runtime)

**What happens:** If a `SBQQ__CustomAction__c` record references a Flow by API name and that Flow is in Draft status, the CPQ package does not validate the Flow status at record save time. The action record saves successfully. However, when a rep clicks the button in the QLE, CPQ attempts to launch the Flow, finds it is not active, and displays a generic runtime error to the rep. The error message does not indicate the Flow status is the cause.

**When it occurs:** During development when a Flow is still being built and the custom action record is created in parallel. Also surfaces after a deployment if the Flow is deployed in Draft state (which is the default deploy behavior unless the package explicitly activates it).

**How to avoid:** Activate the Flow before creating or deploying the custom action record. In CI/CD pipelines, include a post-deploy step that activates the Flow. If deploying both together via a Change Set or SFDX package, ensure the Flow version being deployed has `status = Active` in the metadata.
