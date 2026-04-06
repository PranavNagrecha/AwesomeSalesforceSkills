# LLM Anti-Patterns — Assignment Rules

Common mistakes AI coding assistants make when generating or advising on Salesforce Lead and Case Assignment Rules.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Suggesting multiple active assignment rules per object

**What the LLM generates:** "Create an assignment rule for web leads and another assignment rule for partner leads. Activate both."

**Why it happens:** LLMs treat assignment rules like sharing rules or validation rules where multiple can be active. In Salesforce, only ONE assignment rule can be active per object (Lead or Case) at a time. Activating a new rule deactivates the previous one.

**Correct pattern:**

```
Only one assignment rule can be active per object at a time.
Create ONE assignment rule with multiple ordered rule entries:
  Rule: Lead Assignment Rule (Active)
    Entry 1: Lead Source = 'Web' AND State = 'CA' → Queue: West Web Leads
    Entry 2: Lead Source = 'Partner' → Queue: Partner Leads
    Entry 3: (Default / catch-all) → Queue: Unassigned Leads
Entries are evaluated top-to-bottom; first match wins.
```

**Detection hint:** If the output suggests creating and activating multiple assignment rules for the same object, the one-active-rule limit is being violated. Search for `activate both` or multiple `assignment rule` creation instructions for one object.

---

## Anti-Pattern 2: Assuming assignment rules fire on all record creation methods

**What the LLM generates:** "Once your assignment rule is active, all new leads will be automatically assigned."

**Why it happens:** LLMs do not distinguish between UI creation and API creation. Assignment rules only fire automatically on records created through the Salesforce UI (with the "Assign using active assignment rules" checkbox checked) or Web-to-Lead/Web-to-Case. For API or Data Loader inserts, the `AssignmentRuleHeader` must be explicitly set in the API call.

**Correct pattern:**

```
Assignment rules fire automatically when:
- Record is created via Salesforce UI with "Assign using active
  assignment rules" checkbox checked (checked by default for Cases).
- Record is created via Web-to-Lead or Web-to-Case.

Assignment rules require explicit opt-in when:
- Record is created via API: set AssignmentRuleHeader in the request.
- Record is created via Data Loader: check "Use Assignment Rules" in Settings.
- Record is created via Apex: set DMLOptions.assignmentRuleHeader.
```

**Detection hint:** If the output says assignment rules fire "automatically on all new records" without mentioning API/Data Loader opt-in, the API behavior is being ignored. Search for `AssignmentRuleHeader` or `DMLOptions`.

---

## Anti-Pattern 3: Recommending native round-robin without clarifying it does not exist

**What the LLM generates:** "Enable round-robin assignment in the assignment rule to distribute leads evenly across your team."

**Why it happens:** LLMs hallucinate a native round-robin feature. Salesforce assignment rules do not support round-robin distribution natively. They assign to a single user or queue based on criteria. Round-robin requires a custom solution using Apex, Flow, or a queue with manual claim.

**Correct pattern:**

```
Native assignment rules do NOT support round-robin.
Options for even distribution:
1. Assign to a Queue → reps manually claim or use Omni-Channel routing.
2. Build a custom round-robin using:
   - A custom counter field on a config object or Custom Metadata Type.
   - An Apex trigger or Flow that increments the counter and assigns
     to the next rep in a list.
   - A scheduled Flow that redistributes unworked records.
3. Use a third-party AppExchange solution (e.g., LeanData, RingLead).
```

**Detection hint:** If the output mentions `round-robin` as a native assignment rule feature, it is hallucinated. Search for `round-robin` without an accompanying custom implementation explanation.

---

## Anti-Pattern 4: Forgetting that assignment rules only exist for Lead and Case

**What the LLM generates:** "Create an assignment rule on the Opportunity object to route new opportunities to the right rep."

**Why it happens:** LLMs generalize assignment rules to any object. Assignment rules are available only for Lead and Case objects. For other objects, routing must be done via Flow, Apex triggers, or Omni-Channel.

**Correct pattern:**

```
Assignment rules are ONLY available for Lead and Case.
For other objects (Opportunity, Account, custom objects):
- Use a Record-Triggered Flow to update OwnerId based on criteria.
- Use an Apex trigger for complex routing logic.
- Use Omni-Channel routing for work-item distribution.
```

**Detection hint:** If the output references creating an assignment rule on any object other than Lead or Case, it is incorrect. Check the object name in the assignment rule instructions.

---

## Anti-Pattern 5: Ignoring rule entry order and the first-match-wins behavior

**What the LLM generates:** "Add all your criteria as rule entries. Salesforce will evaluate all of them and pick the best match."

**Why it happens:** LLMs describe assignment rule evaluation as if it scores all entries. In reality, rule entries are evaluated in order from top to bottom, and the first matching entry wins. Subsequent entries are not evaluated. Poor ordering causes broad catch-all entries to swallow specific entries below them.

**Correct pattern:**

```
Rule entries are evaluated top-to-bottom. First match wins.
Order entries from MOST specific to LEAST specific:
  Entry 1: Lead Source = 'Web' AND State = 'CA' → West Web Queue
  Entry 2: Lead Source = 'Web' → General Web Queue
  Entry 3: (no criteria — catch-all) → Unassigned Queue

If Entry 3 were placed first, every lead would match it
and no other entry would ever fire.
```

**Detection hint:** If the output says Salesforce "evaluates all entries" or "picks the best match," the first-match-wins behavior is being misrepresented. Search for `best match` or `all entries`.
