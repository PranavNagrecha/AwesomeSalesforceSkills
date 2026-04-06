# LLM Anti-Patterns — Flow for Admins

Common mistakes AI coding assistants make when generating or advising on Salesforce Flows from an admin perspective.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using After-Save Flow for same-record field updates

**What the LLM generates:** "Create a Record-Triggered Flow (After Save) to update the Status field on the same record when the Priority changes."

**Why it happens:** LLMs default to After-Save flows for all record-triggered automation. For same-record field updates, Before-Save flows are more efficient: they execute before the record is committed, do not consume an additional DML operation, and avoid retriggering the flow. After-Save flows that update the triggering record cause an additional DML and can create recursion.

**Correct pattern:**

```
Same-record field updates → Before-Save Flow:
- No DML consumed (the record has not been saved yet).
- Use $Record to read current values.
- Use an Assignment element to set field values directly.
- No risk of re-triggering the flow.

Related-record updates, create child records, callouts → After-Save Flow:
- The triggering record's ID is available.
- DML on other records is allowed.
- Can perform callouts (if configured as async path).
```

**Detection hint:** If the output uses an After-Save flow with an Update Records element targeting `$Record` or the triggering record's ID, it should be a Before-Save flow instead. Search for `After Save` combined with updating `$Record`.

---

## Anti-Pattern 2: Missing fault paths on DML and callout elements

**What the LLM generates:** "Add a Create Records element to create the child task. Then add the email alert."

**Why it happens:** LLMs build the happy path and skip error handling. Every DML element (Create, Update, Delete), callout, or action in a Flow can fail. Without a Fault connector, the entire Flow transaction fails with an unhandled fault error that is difficult for users to understand.

**Correct pattern:**

```
Every DML and action element needs a Fault connector:
1. Add the Create Records element.
2. Connect the Fault output to a fault-handling path:
   a. Log the error: create a custom log record or use Platform Event.
   b. Notify: send an email or post to Chatter with the error details.
   c. User-facing: for Screen Flows, show a friendly error screen.
3. Use {!$Flow.FaultMessage} to capture the error details.
4. In Record-Triggered Flows, an unhandled fault rolls back the
   entire transaction, which may prevent the triggering record from saving.
```

**Detection hint:** If the output adds DML elements (Create, Update, Delete Records) without Fault connectors, the Flow lacks error handling. Search for `Fault` or `fault path` after each DML element.

---

## Anti-Pattern 3: Not considering bulkification in Record-Triggered Flows

**What the LLM generates:** "The flow fires when an Opportunity is updated. It gets the Account and updates a field on the Account."

**Why it happens:** LLMs design flows as if they process one record at a time. Record-Triggered Flows must handle bulk operations (up to 200 records in a single transaction from Data Loader, API, or batch Apex). A flow that performs a Get Records + Update Records per record will hit governor limits in bulk scenarios.

**Correct pattern:**

```
Bulkification considerations for Record-Triggered Flows:
1. Salesforce auto-bulkifies flows since Spring '22:
   - Before-Save: batch of up to 200 records processed together.
   - After-Save: each record's flow interview runs individually but
     DML is batched.
2. Avoid patterns that multiply queries or DML:
   - Do NOT put Get Records inside a Loop element.
   - Collect IDs first, then query once outside the loop.
3. For After-Save flows updating related records:
   - The platform batches DML across interviews.
   - But custom Apex actions called per-record may not batch well.
4. Test with Data Loader (200+ records) to verify the flow does not
   hit SOQL query limits or DML limits.
```

**Detection hint:** If the output places a Get Records or Update Records element inside a Loop, it will fail in bulk. Search for `Get Records` or `Update Records` nested within a `Loop` element.

---

## Anti-Pattern 4: Recommending Process Builder or Workflow Rules for new automation

**What the LLM generates:** "Use Process Builder to update the Account rating when an Opportunity is closed."

**Why it happens:** LLMs trained on pre-2025 data reference Process Builder and Workflow Rules, which are now retired. All new automation should be built with Flow. Existing Process Builder and Workflow Rules should be migrated to Flow.

**Correct pattern:**

```
Automation tool status:
- Workflow Rules: RETIRED (ceased functioning after Dec 2025).
- Process Builder: RETIRED (ceased functioning after Dec 2025).
- Flow: CURRENT and recommended for all new automation.

Migration:
- Use the "Migrate to Flow" tool in Setup for simple processes.
- For complex Process Builder logic, rebuild in Flow manually.
- Test thoroughly — Flow evaluation order differs from Process Builder.
```

**Detection hint:** If the output recommends `Process Builder` or `Workflow Rule` for new automation, it is recommending retired tools. Search for `Process Builder` or `Workflow Rule` as a new build recommendation.

---

## Anti-Pattern 5: Creating Screen Flows without input validation

**What the LLM generates:** "Add a Screen element with a text input for the phone number. On the next screen, create the record."

**Why it happens:** LLMs build functional screens without validation. Screen Flows should validate user inputs before processing: checking for blank required fields, valid formats (email, phone), and business rule compliance. Without validation, bad data enters the system.

**Correct pattern:**

```
Screen Flow input validation:
1. Mark required fields as "Required" in the screen component properties.
2. Add validation formulas on input components:
   - Phone: REGEX({!phoneInput}, "^\\+?[0-9\\-\\(\\)\\s]{7,15}$")
   - Email: NOT(ISBLANK({!emailInput})) &&
            REGEX({!emailInput}, "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$")
3. Use a Decision element after the screen to validate business rules
   before DML (e.g., Amount must be positive, Date must be in the future).
4. If validation fails, loop back to the screen with an error message
   displayed in a Display Text component.
```

**Detection hint:** If the output creates a Screen Flow that goes directly from a screen input to a DML element without validation, input validation is missing. Search for `validation`, `REGEX`, or `Decision` between the screen and the DML element.

---

## Anti-Pattern 6: Setting Flow to run in System Context without considering security implications

**What the LLM generates:** "Set the flow to run in System Context Without Sharing so it can access all records."

**Why it happens:** LLMs solve access errors by escalating privileges. Running a Flow in System Context Without Sharing bypasses all record-level security (OWD, sharing rules, role hierarchy). This may expose data to users who should not see it, especially in Screen Flows where the user interacts with the results.

**Correct pattern:**

```
Flow execution context:
- System Context With Sharing (default for auto-launched flows):
  Runs as the automation user but respects sharing rules.
- System Context Without Sharing: bypasses all record-level security.
  Use ONLY when the flow needs cross-boundary data access for
  legitimate backend processing (not user-facing).
- User Context (Screen Flows default): respects the running user's
  CRUD, FLS, and sharing. Safest for user-facing flows.

If a flow needs elevated access for a specific step, use an
Invocable Apex action with 'without sharing' only for that step.
```

**Detection hint:** If the output sets "System Context Without Sharing" on a Screen Flow or user-facing flow, it is bypassing security inappropriately. Search for `Without Sharing` combined with `Screen Flow`.
