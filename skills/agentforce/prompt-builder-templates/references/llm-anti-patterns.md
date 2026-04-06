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
- Field Generation → populates a specific field via Einstein button on record page
- Record Summary → generates a summary panel on the record page
- Sales Email → drafts emails in the activity composer
- Flex → general-purpose for agent actions, quick actions, screen flows

Using Flex when Field Generation is correct means:
- The Einstein button for field population will not appear.
- Additional wiring (quick action, agent action) is needed unnecessarily.
- The template cannot be bound directly to the target field.

Match the template type to the intended deployment surface.
```

**Detection hint:** If the advice creates a Flex template for a use case that is field population on a record page, Field Generation is the correct type.

---

## Anti-Pattern 3: Assuming Flow Grounding Errors Surface in Prompt Builder

**What the LLM generates:** "If the Flow fails, Prompt Builder will show an error" or debugging advice that checks only the Prompt Builder UI.

**Why it happens:** LLMs assume errors propagate visually. Template-Triggered Prompt Flows that fail at runtime (invalid SOQL, governor limit, null variable) fail SILENTLY — the merge field returns an empty string.

**Correct pattern:**

```
If a Template-Triggered Prompt Flow errors at runtime, the merge field that
references the flow returns an EMPTY STRING — not an error message. The
resolved prompt appears valid but the grounded data is missing, causing the
LLM to hallucinate or produce generic output.

Debugging Flow-grounded templates:
1. Test the underlying flow independently in Flow Builder.
2. Check for SOQL errors, governor limit hits, and null variable assignments.
3. Only after the flow passes independently, test it through the template.
4. Compare the Resolved Prompt output against expected data to confirm the
   flow merge field is populated.
```

**Detection hint:** If the advice assumes Flow errors will be visible in Prompt Builder, it will miss silent failures that cause blank or hallucinated output.

---

## Anti-Pattern 4: Ignoring the Manage Prompt Templates Permission in Package Subscriber Orgs

**What the LLM generates:** "Package the prompt template and install it in the subscriber org" without mentioning the permission requirement.

**Why it happens:** LLMs describe packaging steps without covering subscriber-side prerequisites. The package installs successfully without the permission — the failure is at invocation time, not install time.

**Correct pattern:**

```
When prompt templates are distributed via a managed package:
- The package installs successfully WITHOUT the subscriber having the Manage
  Prompt Templates permission.
- The templates exist in the subscriber org but CANNOT be invoked.
- No error appears during installation — the failure surfaces only when users
  try to use the template.

Document the Manage Prompt Templates permission requirement as a prerequisite
in package installation instructions. Verify the permission is assigned in the
subscriber org before marking the deployment complete.
```

**Detection hint:** If the advice packages prompt templates without documenting the subscriber permission requirement, post-deployment support escalations are inevitable.

---

## Anti-Pattern 5: Mismatching Apex Capability Type with Template API Name

**What the LLM generates:** An @InvocableMethod with a capability type that does not exactly match the template type identifier.

**Why it happens:** LLMs generate Apex annotations from general patterns without verifying the exact capability type string format, which differs by template type.

**Correct pattern:**

```
The capability type in the @InvocableMethod annotation must EXACTLY match the
template type identifier:
- Flex template: FlexTemplate://your_template_api_name
- Sales Email: PromptTemplateType://einstein_gpt__salesEmail
- Other types have their own format

A single character mismatch causes the Apex data to be SILENTLY excluded from
the resolved prompt. No error appears in Prompt Builder or debug logs.

After creating the Apex class:
1. Verify the capability type string character by character.
2. Test with Save & Preview to confirm the Apex data appears in the Resolved
   Prompt panel.
```

**Detection hint:** If the advice creates an @InvocableMethod for Apex grounding without verifying the exact capability type string format, the grounding data will be silently excluded.

---

## Anti-Pattern 6: Not Accounting for Newly Created Fields Being Unavailable in the Session

**What the LLM generates:** "Create the custom field, then immediately add it as a merge field in Prompt Builder."

**Why it happens:** LLMs present configuration as a linear sequence. They do not model session caching behavior in the Salesforce UI.

**Correct pattern:**

```
Newly created custom objects and custom fields do NOT appear in the Prompt
Builder Insert Resource panel until the admin logs out and logs back in.

If you create a field and immediately try to add it as a merge field in the
same session, it will not appear in the picker. This is a session cache issue,
not a permissions or configuration problem.

Workflow:
1. Create the custom field.
2. Log out and log back in (or open a new session).
3. Navigate to Prompt Builder and the field will appear in the Insert Resource
   panel.
```

**Detection hint:** If the advice creates a field and immediately uses it in Prompt Builder without mentioning the session refresh requirement, the field will not appear and the practitioner will waste time troubleshooting.
