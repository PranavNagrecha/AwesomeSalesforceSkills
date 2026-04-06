# LLM Anti-Patterns — Global Actions and Quick Actions

Common mistakes AI coding assistants make when generating or advising on Salesforce Global Actions and Quick Actions.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Confusing global actions with object-specific quick actions

**What the LLM generates:** "Create a global action to update the Opportunity Stage from the Opportunity record page."

**Why it happens:** LLMs conflate the two action types. Global actions live in the global publisher layout (header, home page) and are not tied to a specific object context. Object-specific quick actions are tied to a specific object and appear on that object's record page. An "Update Opportunity Stage" action should be an object-specific quick action on Opportunity, not a global action.

**Correct pattern:**

```
Action type decision:
- Global Action: appears in the global header and home page.
  No parent object context. Use for: create a new Task from anywhere,
  log a call from the home page, or launch a Flow from the header.
  Setup: Setup → Global Actions → New Action.

- Object-Specific Quick Action: appears on a specific object's record page.
  Has parent object context and can pre-fill fields from the current record.
  Use for: update fields on the current record, create a related child record.
  Setup: Setup → Object Manager → [Object] → Buttons, Links, Actions → New Action.

Key difference: object-specific actions can use predefined field values
from the parent record. Global actions cannot.
```

**Detection hint:** If the output creates a global action for a task that requires parent record context (updating a field on the current record), it should be an object-specific action. Search for `global action` combined with record-specific operations.

---

## Anti-Pattern 2: Forgetting to add the action to the page layout

**What the LLM generates:** "Create the quick action and it will automatically appear on the record page."

**Why it happens:** LLMs skip the page layout assignment step. After creating a quick action, it must be added to the object's page layout in the "Salesforce Mobile and Lightning Experience Actions" section. If this section has been customized, new actions do not appear automatically.

**Correct pattern:**

```
After creating the action:
1. Go to Setup → Object Manager → [Object] → Page Layouts.
2. Edit the relevant page layout.
3. In the "Salesforce Mobile and Lightning Experience Actions" section:
   - If this section shows "override the predefined actions":
     it has been customized. You must manually add the new action.
   - If it shows the default predefined actions:
     the action may appear automatically, but verify.
4. Drag the new action from the palette into the action section.
5. Save the page layout.
6. Repeat for each page layout that should show the action.
```

**Detection hint:** If the output creates an action without adding it to the page layout's action section, users will not see it. Search for `page layout` or `Salesforce Mobile and Lightning Experience Actions` after the action creation step.

---

## Anti-Pattern 3: Not configuring the action layout (showing too many or too few fields)

**What the LLM generates:** "Create a 'Log a Call' quick action on the Contact object."

**Why it happens:** LLMs create the action but do not configure its action layout. The action layout controls which fields appear in the quick action popup. By default, it may include fields the user does not need or exclude fields they do. A poorly configured action layout forces users to fill in unnecessary fields or miss important ones.

**Correct pattern:**

```
After creating the action, configure its layout:
1. Go to Setup → Object Manager → [Object] → Buttons, Links, Actions.
2. Click the action name → Edit Layout.
3. The Action Layout Editor shows fields in the popup:
   - Remove fields that are not relevant to this action's purpose.
   - Add fields that are essential (keep it to 3-5 fields maximum).
   - Mark fields as required if they must be filled.
4. For "Create" actions: only show the minimum fields needed.
   Users can fill in the rest after creation.
5. Test the action from a record page to verify the popup shows
   the correct fields in the correct order.
```

**Detection hint:** If the output creates an action without editing its action layout, the popup may show default fields that are irrelevant. Search for `action layout` or `Edit Layout` after the action creation.

---

## Anti-Pattern 4: Ignoring predefined field values for create-type actions

**What the LLM generates:** "Create a quick action to create a new Case from the Account page. The user will fill in all the fields."

**Why it happens:** LLMs create the action without leveraging predefined field values. For object-specific quick actions that create related records, predefined field values can auto-populate fields from the parent record (e.g., Account Name, Contact, Phone) reducing user effort and ensuring data consistency.

**Correct pattern:**

```
Configure predefined field values for create actions:
1. Go to Setup → Object Manager → [Object] → Buttons, Links, Actions.
2. Click the action name → Predefined Field Values.
3. Set values that should auto-populate:
   - AccountId: {!Account.Id} (links the Case to the current Account).
   - ContactId: {!Account.Primary_Contact__c} (if a primary contact field exists).
   - Origin: "Phone" (if this action is for phone-logged cases).
   - Priority: "Medium" (default priority).
4. Predefined values reduce data entry errors and enforce consistency.
5. Users can still override predefined values unless the field is
   removed from the action layout.
```

**Detection hint:** If the output creates a "Create Record" quick action without configuring predefined field values, the action misses an efficiency opportunity. Search for `predefined` or `Predefined Field Values` after create-action setup.

---

## Anti-Pattern 5: Using quick actions for complex multi-step processes instead of Screen Flows

**What the LLM generates:** "Create a quick action with 10 fields to capture the full case escalation details including manager approval, reassignment, and notification preferences."

**Why it happens:** LLMs try to fit complex processes into a single quick action popup. Quick actions are designed for simple, fast interactions (3-5 fields). For multi-step processes with conditional logic, validation, and branching, a Screen Flow launched via a quick action is the correct pattern.

**Correct pattern:**

```
Action complexity guide:
- 1-5 fields, no conditional logic → Quick Action (field update or record create).
- Multi-step process, conditional fields, branching logic →
  Screen Flow launched via a Flow quick action.

To launch a Flow from a quick action:
1. Create a Screen Flow with the multi-step logic.
2. Create an object-specific quick action:
   - Action Type: Flow.
   - Flow: select the Screen Flow.
3. The Flow receives the record ID as input and can read/update
   the record with full conditional logic.
4. Add the Flow action to the page layout's action section.
```

**Detection hint:** If the output creates a quick action with more than 5-6 fields or describes conditional logic within the action layout, a Screen Flow is more appropriate. Count the number of fields in the action layout.
