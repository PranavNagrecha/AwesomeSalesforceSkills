# LLM Anti-Patterns — CPQ Custom Actions

Common mistakes AI coding assistants make when generating or advising on Salesforce CPQ custom actions. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Claiming Custom Actions Can Call Apex Directly

**What the LLM generates:** Configuration steps that set `SBQQ__Type__c = Apex` or suggest adding an Apex class name to a custom action field, implying a direct Apex execution type exists.

**Why it happens:** LLMs trained on general Salesforce documentation associate "custom button" with Apex class invocation (as in classic Salesforce button overrides). They apply that pattern to CPQ custom actions without recognizing the CPQ managed package's narrower set of supported action types.

**Correct pattern:**

```
Custom actions support these SBQQ__Type__c values only:
- URL
- Flow
- Calculate
- Save
- Add Group

To execute Apex: use Type = Flow, then call an @InvocableMethod from inside the Flow.
Or: use Type = URL pointing to a Visualforce page backed by an Apex controller.
```

**Detection hint:** Flag any output containing `SBQQ__Type__c = Apex` or phrases like "set the Apex class on the custom action."

---

## Anti-Pattern 2: Adding More Than 5 Actions Per Context Without Warning

**What the LLM generates:** A list of six or more `SBQQ__CustomAction__c` records all with the same `SBQQ__Location__c` value, without any note about the hard limit.

**Why it happens:** LLMs do not model CPQ's rendering constraints. They treat the request as a pure data modeling task ("create records for each requirement") without applying the five-action ceiling.

**Correct pattern:**

```
Before creating any new action for a given location, verify:
SELECT COUNT() FROM SBQQ__CustomAction__c
WHERE SBQQ__Location__c = '<target location>'
  AND SBQQ__Active__c = true

If count >= 5: consolidate existing actions or deactivate one before adding.
The limit is 5 per location. Exceeding it causes silent button drops, not an error.
```

**Detection hint:** Count the number of `SBQQ__CustomAction__c` records in the generated output sharing the same `SBQQ__Location__c`. Flag if count > 5.

---

## Anti-Pattern 3: Using Flow Decisions or Apex Triggers to Control Custom Action Visibility

**What the LLM generates:** Instructions to add a Decision element in the Flow, or an `after update` trigger on `SBQQ__Quote__c`, to control whether a custom action button is visible to the rep.

**Why it happens:** LLMs correctly know that Flows and Apex triggers can conditionally execute logic, so they apply that pattern to visibility control without knowing that CPQ custom action visibility is evaluated by the CPQ condition engine at page load — not by Flow outcomes or trigger side effects.

**Correct pattern:**

```
Conditional visibility for CPQ custom actions uses SBQQ__CustomActionCondition__c records.
Set SBQQ__ConditionsMet__c on the parent SBQQ__CustomAction__c to 'All', 'Any', or 'Formula'.
Create child SBQQ__CustomActionCondition__c records specifying:
  - SBQQ__FilterField__c (field API name)
  - SBQQ__FilterOperator__c (Equals, Not Equal, Greater Than, etc.)
  - SBQQ__FilterValue__c (expected value)

Flow decisions and Apex triggers have no effect on button rendering in the QLE.
```

**Detection hint:** Flag any output that suggests modifying Flow decision outcomes or writing Apex trigger logic with the stated goal of hiding or showing a custom action button.

---

## Anti-Pattern 4: Placing a Custom Action on the Quote Lightning Record Page Instead of in the QLE

**What the LLM generates:** Steps to add a Quick Action of type `Flow` to the `SBQQ__Quote__c` Lightning record page's "Highlights Panel" or "Action Bar," presenting this as the way to give reps a button when working in CPQ.

**Why it happens:** LLMs default to the standard Salesforce pattern for object-level buttons (Quick Actions on the record page layout) without knowing that the QLE is a full-page overlay that hides the record page action bar. The standard pattern is technically valid for the record page but inaccessible from within the QLE.

**Correct pattern:**

```
To surface a button inside the Quote Line Editor (QLE), product configurator,
or amendment screen, use SBQQ__CustomAction__c — NOT a Quick Action on the Quote object.

Quick Actions on SBQQ__Quote__c are only accessible from the standard Lightning
record page, which is not visible when the QLE is active.
```

**Detection hint:** Flag any recommendation to add a Quick Action, button, or Lightning Action to the `SBQQ__Quote__c` page layout or record page when the stated goal is to give reps access to the action while editing in the QLE.

---

## Anti-Pattern 5: Referencing a Draft Flow in the Custom Action Without Activating It First

**What the LLM generates:** A deployment plan that creates the `SBQQ__CustomAction__c` record and the Flow in the same change set or SFDX package without verifying the Flow's activation status, or instructions that say "deploy the Flow and the custom action together" without noting that the Flow must be Active.

**Why it happens:** LLMs treat Flow deployment as analogous to Apex class deployment — deploy and it is available. They do not model the Flow activation status requirement or the fact that CPQ silently fails at runtime if the referenced Flow is in Draft state.

**Correct pattern:**

```
Deployment order for Flow-backed custom actions:
1. Deploy and ACTIVATE the Flow first (ensure status = Active in metadata or via post-deploy step).
2. Then deploy or create the SBQQ__CustomAction__c record referencing the activated Flow.

In SFDX: set <status>Active</status> in the Flow metadata XML before packaging.
In Change Sets: activate the Flow in the source org before adding it to the change set.

CPQ does not validate Flow status when the custom action record is saved.
Failure only surfaces when a rep clicks the button at runtime.
```

**Detection hint:** Flag any deployment plan that creates a `SBQQ__CustomAction__c` record referencing a Flow without explicitly confirming or setting the Flow to Active status beforehand.
