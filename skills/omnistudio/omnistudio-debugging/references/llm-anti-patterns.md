# LLM Anti-Patterns — OmniStudio Debugging

Common mistakes AI coding assistants make when generating or advising on debugging OmniStudio components.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using Apex Debug Logs Instead of OmniStudio Debug Mode

**What the LLM generates:** "Check the Apex debug logs to see why the OmniScript is failing" without mentioning OmniStudio's built-in debug tools: Preview mode with debug console, Action Debugger, and Integration Procedure test execution.

**Why it happens:** Apex debug logs are the most familiar debugging tool in Salesforce. OmniStudio's specialized debugging tools have less training data coverage.

**Correct pattern:**

```text
OmniStudio debugging tools (use before debug logs):

1. OmniScript Preview Mode:
   - Test OmniScript without publishing or deploying
   - View data JSON at each step in the browser console
   - Identify which step fails or produces wrong data

2. Integration Procedure Test Execution:
   - Run IP with sample input directly from the designer
   - View response JSON, step-by-step execution, and timing
   - Identify which step fails without testing from OmniScript

3. DataRaptor Preview:
   - Test Extract/Transform/Load with sample input
   - View mapped output before integrating with IP or OmniScript

4. Action Debugger (browser console):
   - Enable in OmniScript runtime: add ?debug=true to URL
   - Shows request/response for each server action

Use Apex debug logs ONLY when the issue is in Apex code called
by an OmniStudio component (Apex Remote Action, custom LWC controller).
```

**Detection hint:** Flag debugging advice that jumps directly to Apex debug logs for OmniStudio issues. Check for missing OmniStudio-specific debugging tool recommendations.

---

## Anti-Pattern 2: Not Checking the OmniScript Data JSON Between Steps

**What the LLM generates:** "The OmniScript is not working — check the integration" without first inspecting the data JSON that flows between OmniScript steps, which often reveals the actual issue (wrong field mapping, missing data, incorrect merge field path).

**Why it happens:** LLMs troubleshoot by suggesting external checks (API logs, debug logs) rather than the OmniScript's internal data flow. The data JSON is the central debugging artifact in OmniStudio but is not widely discussed in training data.

**Correct pattern:**

```text
OmniScript data JSON debugging:

The OmniScript maintains a JSON data structure that grows as
the user progresses through steps. This JSON is THE source of truth.

How to inspect:
1. In Preview mode: open browser Developer Console
2. At each step transition, log the OmniScript data:
   - React-based OmniScript: inspect component state
   - LWC-based OmniScript: use the OmniStudio debug panel

What to check in the data JSON:
- Is the field value present under the expected key?
- Is the key path correct? (e.g., Step1.AccountName vs AccountName)
- Are prefill values populated before the step renders?
- Are Integration Procedure responses merged correctly?
- Are null values present where data is expected?

Common root causes found in data JSON:
- Field name mismatch between OmniScript element and IP output
- Nested JSON path not matching the expected structure
- Prefill action running after the step renders (timing issue)
```

**Detection hint:** Flag OmniScript debugging advice that does not mention inspecting the data JSON. Check for missing browser console or debug panel recommendations.

---

## Anti-Pattern 3: Assuming Sandbox Behavior Matches Production for OmniStudio Components

**What the LLM generates:** "It works in sandbox so it should work in production" without noting that OmniStudio components can behave differently between environments due to version differences, data differences, permission differences, and activation state.

**Why it happens:** LLMs treat sandbox-to-production promotion as a deployment concern. Environment-specific OmniStudio issues (different active versions, missing dependencies, user permission gaps) are operational problems not covered in feature documentation.

**Correct pattern:**

```text
Environment differences that affect OmniStudio:

1. Version activation: a different version may be active in production
   than in sandbox (check activation status after deployment)

2. Data dependencies: OmniScript may reference records (IDs, values)
   that exist in sandbox but not in production

3. Permissions: guest users or external users in production may lack
   permissions that sandbox test users have

4. Named Credentials: secrets are not deployed — HTTP Actions will
   fail if credentials are not configured in target org

5. Custom Metadata / Custom Settings: values may differ between environments

6. OmniStudio package version: sandbox and production may run different
   OmniStudio managed package versions

Debugging production issues:
- Compare active version numbers between environments
- Check Named Credential connectivity in production
- Test with a production-equivalent user profile in sandbox
```

**Detection hint:** Flag debugging advice that does not consider environment-specific differences. Check for missing version activation verification and credential configuration checks.

---

## Anti-Pattern 4: Not Using the Integration Procedure Response for Error Diagnosis

**What the LLM generates:** "The Integration Procedure is failing" as a vague diagnosis without inspecting the actual response JSON from the IP execution, which contains step-level status, error messages, and execution timing.

**Why it happens:** LLMs provide generic troubleshooting steps. The IP response structure (which includes per-step success/failure, error messages, and the data transformation chain) is specific to OmniStudio.

**Correct pattern:**

```text
Integration Procedure response diagnosis:

Execute IP in test mode and inspect the response:

{
  "IPResult": {
    "Step1_Extract": {
      "vlcStatus": "success",
      "records": [...]
    },
    "Step2_HTTPAction": {
      "vlcStatus": "error",
      "errorMessage": "Connection refused: api.example.com",
      "HTTPStatusCode": 0,
      "responseTime": "30002ms"
    }
  }
}

Key fields to check:
- vlcStatus: "success" or "error" per step
- errorMessage: specific error text
- HTTPStatusCode: for HTTP Actions (0 = timeout/connection failure)
- responseTime: identify slow steps
- Empty results: DataRaptor returned no records (check filter criteria)
```

**Detection hint:** Flag IP debugging advice that does not mention inspecting the response JSON. Check for missing per-step status analysis.

---

## Anti-Pattern 5: Confusing Preview Mode Behavior with Runtime Behavior

**What the LLM generates:** "Test the OmniScript in Preview mode — if it works there, deploy it" without noting that Preview mode runs with the designer's permissions, may use different data, and does not reflect the actual runtime context (record page, Experience Cloud, mobile).

**Why it happens:** Preview mode is convenient and LLMs treat it as equivalent to production testing. The differences between Preview and runtime are subtle but important.

**Correct pattern:**

```text
Preview mode vs Runtime differences:

Preview mode:
- Runs as the current designer user (admin permissions)
- No record context (unless manually provided)
- No Experience Cloud theme or guest user context
- May use different Named Credential scope
- Skips some Lightning runtime behaviors

Runtime:
- Runs as the actual end user (may have restricted permissions)
- Has record context from the embedding page
- Applies Experience Cloud theme and guest user security
- Named Credential runs in the user's context
- Subject to Lightning runtime quirks and caching

Testing checklist:
1. Preview mode: verify basic functionality and data flow
2. Sandbox runtime: test embedded on a record page as end user
3. Permission testing: test with a restricted user profile
4. Mobile testing: verify on Salesforce mobile if applicable
5. Experience Cloud testing: test in portal context if applicable
```

**Detection hint:** Flag OmniScript testing plans that only include Preview mode without runtime testing. Check for missing user permission and context testing.
