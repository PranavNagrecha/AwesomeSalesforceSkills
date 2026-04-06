# LLM Anti-Patterns — Flow Debugging

Common mistakes AI coding assistants make when generating or advising on diagnosing Flow issues.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Suggesting debug logs for Flow troubleshooting as the first step

**What the LLM generates:**

```
"Enable debug logs for the running user to trace the Flow execution."
```

**Why it happens:** LLMs default to Apex-style debugging. For Flow, the built-in Debug mode in Flow Builder and the Flow interview log are the primary tools — they show the exact path, variable values, and fault details without requiring debug log parsing.

**Correct pattern:**

1. Open the Flow in Flow Builder
2. Click Debug, set input variables, and run
3. Review the debug output panel for each element's path and variable values
4. For production issues, check Setup > Flows > View Flow Interviews for paused or failed interviews

Use Apex debug logs only when the issue involves Apex invocable actions called by the Flow.

**Detection hint:** Advice to "enable debug logs" as the primary debugging approach for a Flow issue.

---

## Anti-Pattern 2: Not checking entry conditions when a record-triggered flow does not fire

**What the LLM generates:**

```
"The flow might not be active. Go to Setup > Flows and activate it."
```

**Why it happens:** LLMs check the most obvious cause (inactive flow) but skip the more common cause: entry conditions that do not match the record being saved.

**Correct pattern:**

Debugging checklist for "flow not firing":
1. Is the flow active? (Check Setup > Flows)
2. Do the entry conditions match? (Check field values vs. conditions)
3. Is the trigger type correct? (Create vs. Update vs. Create or Update)
4. Does the "When to Run" setting match? (Every time vs. Only when changed to meet conditions)
5. Is there another flow or process on the same object that might be interfering?

**Detection hint:** Debugging advice for "flow not firing" that only checks activation status without mentioning entry conditions.

---

## Anti-Pattern 3: Recommending adding Screen elements for debugging in production

**What the LLM generates:**

```
"Add a Screen element before the Update Records element to display
the variable values so you can see what the flow is doing."
```

**Why it happens:** LLMs suggest adding visible debug output because it is intuitive. This approach is inappropriate for record-triggered flows (which have no UI), and adding temporary screens to production screen flows is risky.

**Correct pattern:**

- Use Flow Builder's Debug mode with test inputs
- Use the Flow Test framework to create repeatable assertions
- For record-triggered flows, check Paused and Failed Flow Interviews in Setup
- For temporary production debugging, create an Error_Log__c record with variable values

**Detection hint:** Advice to add Screen elements for debugging purposes in non-screen flow types.

---

## Anti-Pattern 4: Not considering the running user's permissions when debugging access issues

**What the LLM generates:**

```
"The flow works in my sandbox. It must be a deployment issue."
```

**Why it happens:** LLMs test against admin-level access and do not consider that the running user in production may lack field-level security, object permissions, or record access that the flow requires.

**Correct pattern:**

Debug with the correct user context:
1. In Flow Builder Debug, use "Run flow as another user" to test with a non-admin profile
2. Check that the running user has CRUD on all objects the flow accesses
3. Check FLS on all fields the flow reads or writes
4. For record-triggered flows, the running user is the user who saved the record
5. For scheduled flows, the running user is the flow creator or the context user

**Detection hint:** Debugging advice that does not mention checking the running user's profile, permission sets, or sharing rules.

---

## Anti-Pattern 5: Confusing flow versions when diagnosing production issues

**What the LLM generates:**

```
"Open the flow and check the logic in the current version."
```

**Why it happens:** LLMs reference "the flow" as a single artifact. In Salesforce, flows have multiple versions. The active version in production may differ from the latest version in the builder.

**Correct pattern:**

1. Go to Setup > Flows
2. Identify which version number is currently active
3. Open that specific version to review the logic
4. Check if a recent activation changed the version
5. Compare the active version with the previous version if the issue started after a deployment

**Detection hint:** Debugging instructions that do not specify checking the active version number.

---

## Anti-Pattern 6: Not using Flow Tests for repeatable regression verification

**What the LLM generates:**

```
"Manually test the flow by creating a record and checking the result."
```

**Why it happens:** LLMs suggest manual testing because it is the simplest approach. Flow Tests (Setup > Flow Tests) provide automated, repeatable assertions that catch regressions across deployments.

**Correct pattern:**

1. Create a Flow Test for each critical path (happy path, fault path, edge cases)
2. Define test inputs and expected assertions
3. Run Flow Tests after every deployment
4. Include Flow Tests in your CI/CD pipeline where possible

```
Flow Test: "Closed Won Opportunity creates Task"
  Input: Opportunity with StageName = "Closed Won"
  Assert: Task created with correct Subject and WhatId
```

**Detection hint:** Debugging or testing advice that relies entirely on manual record creation without mentioning Flow Tests.
