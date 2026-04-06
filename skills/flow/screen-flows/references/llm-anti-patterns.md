# LLM Anti-Patterns — Screen Flows

Common mistakes AI coding assistants make when generating or advising on interactive screen flow design.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Performing DML on every screen instead of at the end

**What the LLM generates:**

```
Screen 1: Collect Account info --> [Create Account]
Screen 2: Collect Contact info --> [Create Contact]
Screen 3: Collect Opportunity info --> [Create Opportunity]
```

**Why it happens:** LLMs save data immediately after each screen. If the user abandons the flow on Screen 3, orphaned Account and Contact records exist with no Opportunity.

**Correct pattern:**

```
Screen 1: Collect Account info --> [Assignment: Store in variables]
Screen 2: Collect Contact info --> [Assignment: Store in variables]
Screen 3: Collect Opportunity info --> [Assignment: Store in variables]
Screen 4: Review all data
[Create Account] --> [Create Contact] --> [Create Opportunity]
```

Batch all DML at the end after the user confirms. This makes the flow transactional and avoids orphaned records.

**Detection hint:** DML elements (Create/Update/Delete Records) between Screen elements instead of after the last screen.

---

## Anti-Pattern 2: Not handling the Back button and data state

**What the LLM generates:**

```
Screen 1: [Input fields]
Screen 2: [More input fields]
// No consideration for what happens when user clicks Back on Screen 2
```

**Why it happens:** LLMs design the forward path only. When users click Back, input values from the current screen may be lost if they are not stored in flow variables.

**Correct pattern:**

- Store all screen input values in flow variables immediately via component default values
- Set default values on screen components to the flow variable, so values persist on Back navigation
- Test the flow by navigating forward and backward to ensure no data loss

```
Screen Component: Account Name
  Default Value: {!varAccountName}
  Store Output: {!varAccountName}
```

**Detection hint:** Screen flow with multiple screens but no default values set on input components for Back navigation persistence.

---

## Anti-Pattern 3: Using a single screen with too many fields instead of multi-step wizard

**What the LLM generates:**

```
Screen 1:
  - Account Name, Industry, Phone, Website, Billing Address,
    Contact First Name, Contact Last Name, Contact Email, Contact Phone,
    Opportunity Name, Amount, Close Date, Stage
```

**Why it happens:** LLMs put all fields on one screen for simplicity. This creates an overwhelming user experience, especially on mobile.

**Correct pattern:**

Break into logical steps:

```
Screen 1: Account Information (Name, Industry, Phone)
Screen 2: Contact Information (First Name, Last Name, Email)
Screen 3: Opportunity Details (Name, Amount, Stage)
Screen 4: Review and Confirm
```

Keep 3-5 fields per screen. Group by logical entity or step.

**Detection hint:** Screen element with more than 7-8 input fields.

---

## Anti-Pattern 4: Not adding validation before navigation

**What the LLM generates:**

```
Screen: [Email input] --> [Next button]
// No validation — user can proceed with invalid email
```

**Why it happens:** LLMs rely on the input component's built-in validation (if any) but do not add explicit validation rules for business logic like format checks, cross-field rules, or duplicate detection.

**Correct pattern:**

Use validation on screen components:

```
Screen Component: Email
  Required: Yes
  Validation Formula: REGEX({!Email}, "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$")
  Error Message: "Please enter a valid email address."
```

For custom LWC screen components, implement the `validate()` method.

**Detection hint:** Screen flow with input fields but no validation formulas, required flags, or custom component validation.

---

## Anti-Pattern 5: Not providing a Cancel or Exit path

**What the LLM generates:**

```
Screen 1 --> Screen 2 --> Screen 3 --> Done
// No way for the user to cancel or exit mid-flow
```

**Why it happens:** LLMs design the linear happy path. Without a cancel option, users are forced to complete or abandon the browser tab, leaving paused flow interviews.

**Correct pattern:**

Add navigation options:
- Enable the "Pause" button if the flow supports resumption
- Add a custom "Cancel" button or link on each screen
- Configure the flow's "Show Cancel" option in Flow Builder settings
- Handle cancellation by cleaning up any partial data

**Detection hint:** Multi-screen flow with no mention of Cancel, Pause, or early exit handling.

---

## Anti-Pattern 6: Ignoring mobile layout and responsiveness

**What the LLM generates:**

```
Screen:
  Section with 3 columns
    Column 1: Name, Phone
    Column 2: Email, Title
    Column 3: Address fields
```

**Why it happens:** LLMs design for desktop-width screens. Three-column layouts collapse poorly on mobile devices, creating a cramped and confusing experience.

**Correct pattern:**

Design for mobile-first:
- Use 1 or 2 column layouts for screen flows
- Test in the Salesforce mobile app
- Avoid horizontal scrolling
- Keep field labels short
- Place action buttons at the bottom where thumbs can reach

```
Screen:
  Section with 2 columns (stacks to 1 on mobile)
    Column 1: Name, Email
    Column 2: Phone, Title
```

**Detection hint:** Screen flow sections with 3+ columns without mobile layout consideration.
