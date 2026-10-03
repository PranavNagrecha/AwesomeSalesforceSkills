# LLM Anti-Patterns — Prompt Builder Templates

Common mistakes AI coding assistants make when generating or advising on Salesforce Prompt Builder template creation and configuration.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Activating a Template Without Preview Testing

**What the LLM generates:** Template creation steps that go straight from authoring to activation without using Save and Preview against a real record.

**Why it happens:** LLMs generate step-by-step instructions that prioritize completion. Preview testing is a validation step that training data often omits or treats as optional.

**Correct pattern:**

```
ALWAYS use Save & Preview with a real record before activating a template.
Preview shows two critical panels:
1. Resolved Prompt — the prompt with all merge fields substituted.
2. Generated Response — the LLM output from the resolved prompt.

Activating without preview is the primary cause of blank output in production.
Merge fields that look correct in the editor often fail to resolve against
real records if the field API name, relationship traversal, or data population
is wrong.
```

**Detection hint:** If the advice activates a template without an explicit preview-and-validate step against a real record, blank or incorrect output in production is likely.

---

## Anti-Pattern 2: Using Flex Template When Field Generation Is Correct

**What the LLM generates:** "Create a Flex template to populate the Case Summary field" when a Field Generation template is the correct choice.

**Why it happens:** LLMs default to Flex because it is the most general-purpose template type. They do not consistently match the template type to the deployment surface.

**Correct pattern:**

```
Each template type has a specific deployment surface:
- Field Generation → users click a button on a record field to run it (added to the
  field on a Lightning record page)
- Record Summary → used by the Summarize Record invocable action and agent action
- Sales Email → drafts emails in Einstein Sales Emails
- Flex → content other types don't cover; you define the resources (flows, actions)

Using Flex when Field Generation is correct means:
- The Einstein button for field population will not appear.
- Additional wiring (quick action, agent action) is needed unnecessarily.
- The template cannot be bound directly to the target field.

Match the template type to the intended deployment surface.
```

**Detection hint:** If the advice creates a Flex template for a use case that is field population on a record page, Field Generation is the correct type.

---

## Anti-Pattern 3: Debugging a Template-Triggered Prompt Flow in Flow Builder Debug

**What the LLM generates:** "Open the flow in Flow Builder and click Debug to see why the prompt is empty."

**Why it happens:** Debug is the standard flow troubleshooting step, so the model assumes it works for every flow type.

**Correct pattern:**

```
Flow Builder's Debug option isn't available for a Template-Triggered Prompt
Flow (GenAI guide, Flow Changes After the Pilot).

Debugging Flow-grounded templates:
1. Preview the template in Prompt Builder with a real record and read the
   resolution: the flow merge field shows the text the Create Prompt
   Instructions elements produced.
2. Check that every flow input is present in the template; for flows,
   all inputs are required.
3. Check that nobody changed the flow's inputs after the template was built;
   that breaks the template and blocks new versions.
```

UNVERIFIED (2026-10-03): the earlier claim that a failing flow returns an empty string with no error was not found in a fetched source.

**Detection hint:** Advice to "Debug" a Template-Triggered Prompt Flow in Flow Builder.

---

## Anti-Pattern 4: Ignoring Permission Sets in the Target Org

**What the LLM generates:** "Package the prompt template and install it in the subscriber org" without mentioning permission sets.

**Why it happens:** LLMs describe packaging steps without covering target-side prerequisites.

**Correct pattern:**

```
Prompt Builder access is granted by permission sets (GenAI guide, Enable
Prompt Builder):
- Prompt Template Manager: create and manage templates (needs Setup access)
- Prompt Template User: run templates
Metadata API: GenAiPromptTemplate is available only if Prompt Builder is
enabled and the deploying user has Prompt Template Manager.

Document both permission sets as installation prerequisites and assign
them before marking the deployment complete.
```

UNVERIFIED (2026-10-03): the earlier claim that a managed package installs without the permission and templates then fail silently at invocation was not found in a fetched source.

**Detection hint:** A deployment plan for prompt templates that names neither permission set.

---

## Anti-Pattern 5: Forcing a CapabilityType Onto Every Apex Grounding Class

**What the LLM generates:** `@InvocableMethod(capabilityType='FlexTemplate://Renewal_Outreach')` with a warning that any mismatch silently drops the data.

**Why it happens:** Older Prompt Builder guidance required a CapabilityType (Spring '24 pilot changes), and models repeat it.

**Correct pattern:**

```
CapabilityType is optional and ties the class to ONE template type
(GenAI guide, Ground with Apex Merge Fields):
- Sales Email:          PromptTemplateType://einstein_gpt__salesEmail
- Field Generation:     PromptTemplateType://einstein_gpt__fieldCompletion
- Record Summary:       PromptTemplateType://einstein_gpt__recordSummary
- Record Prioritization PromptTemplateType://einstein_gpt__recordPrioritization
- Flex:                 FlexTemplate://template_API_Name  (no longer needed;
                        the guide recommends removing CapabilityType=FlexTemplate://*)
- einstein_gpt__caseEmailDraft: don't specify a CapabilityType

Contract either way:
- Input:  List<Request>; only the first element has data
- Output: List<Response> with one @InvocableVariable String Prompt
- Flex:   Request variable API names match the template input API names
          for String inputs and for object types used more than once
```

**Detection hint:** `FlexTemplate://` in new Apex, or a claim that a mismatch drops data "silently."

---

## Anti-Pattern 6: Not Accounting for Newly Created Fields Being Unavailable in the Session

**What the LLM generates:** "Create the custom field, then immediately add it as a merge field in Prompt Builder."

**Why it happens:** LLMs present configuration as a linear sequence. They do not model session caching behavior in the Salesforce UI.

**Correct pattern:**

```
Newly created custom objects and custom fields do NOT appear in the Prompt
Builder Resource picker until the admin logs out and logs back in.

If you create a field and immediately try to add it as a merge field in the
same session, it will not appear in the picker. This is a session cache issue,
not a permissions or configuration problem.

Workflow:
1. Create the custom field.
2. Log out and log back in (or open a new session).
3. Navigate to Prompt Builder and the field will appear in the Resource picker.
```

**Detection hint:** If the advice creates a field and immediately uses it in Prompt Builder without mentioning the session refresh requirement, the field will not appear and the practitioner will waste time troubleshooting.

---

## Anti-Pattern 7: Using Flow Merge Syntax in a Prompt Template

**What the LLM generates:** A template body with `{!$Record.Subject}` or `{!Flow:MyFlow.prompt}`.

**Why it happens:** The model mixes Flow Builder formula syntax with Prompt Builder merge fields.

**Correct pattern:** Record merge fields use the template input: `{!$Input:Case.Subject}`, `{!$Input:Account.Name}`. Flow merge fields use `{!$Flow:FlowApiName.Prompt}` as in the Metadata API sample (`{!$Flow:Fetch_Products.Prompt}`). Insert merge fields from the Resource picker instead of typing them.

**Detection hint:** `$Record.` or `{!Flow:` (without `$`) inside a prompt template body.

