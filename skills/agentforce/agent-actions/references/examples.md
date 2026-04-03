# Agent Actions — Examples

## Example 1: Narrowly Named Mutation Action

**Context:** An agent needs to reschedule an appointment.

**Problem:** The initial action is called `handleAppointment` and can create, cancel, or reschedule depending on hidden flags.

**Solution:**

```text
Use a specific action such as:
- Reschedule appointment

With explicit inputs:
- appointment id
- requested new time
- confirmation flag
```

**Why it works:** The agent can choose the action for the right reason and understand the expected parameters.

---

## Example 2: Apex Invocable Action With Structured Result

**Context:** The action needs strict service-layer validation before writing data.

**Problem:** The invocable method throws raw exceptions for business-rule failures.

**Solution:**

```text
Return a result DTO with:
- success flag
- user-safe message
- machine-readable status or code
```

**Why it works:** The agent can explain failure and decide whether to recover, retry, or hand off.

---

## Anti-Pattern: Too Many Generic Actions

**What practitioners do:** Add many broad actions like `executeFlow`, `runTool`, or `processCase`.

**What goes wrong:** Tool selection quality drops because the action set is large and semantically muddy.

**Correct approach:** Keep the action set small, clearly named, and capability-specific.
