# LLM Anti-Patterns: OmniStudio Debugging

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
   - Read the Data JSON pane, which updates as you fill fields
   - Identify which step fails or produces wrong data

2. Integration Procedure Test Execution:
   - Run IP with sample input directly from the designer
   - View response JSON, step-by-step execution, and timing
   - Identify which step fails without testing from OmniScript

3. DataRaptor Preview:
   - Test Extract/Transform/Load with sample input
   - View mapped output before integrating with IP or OmniScript

4. Action Debugger (designer Preview):
   - Shows request/response for each action; search, copy nodes, clear logs
   - UNVERIFIED (2026-10-03): runtime debug switches such as a URL
     parameter are documented only in Salesforce Help

Use Apex debug logs ONLY when the issue is in Apex code called
by an OmniStudio component (Apex Remote Action, custom LWC controller).
```

**Detection hint:** Flag debugging advice that jumps directly to Apex debug logs for OmniStudio issues. Check for missing OmniStudio-specific debugging tool recommendations.

---

## Anti-Pattern 2: Not Checking the OmniScript Data JSON Between Steps

**What the LLM generates:** "The OmniScript is not working, check the integration" without first inspecting the data JSON that flows between OmniScript steps, which often reveals the actual issue (wrong field mapping, missing data, incorrect merge field path).

**Why it happens:** LLMs troubleshoot by suggesting external checks (API logs, debug logs) rather than the OmniScript's internal data flow. The data JSON is the central debugging artifact in OmniStudio but is not widely discussed in training data.

**Correct pattern:**

```text
OmniScript data JSON debugging:

The OmniScript maintains a JSON data structure that grows as
the user progresses through steps. This JSON is THE source of truth.

How to inspect:
1. In the designer Preview, read the Data JSON pane (it updates as
   you enter values; copy it with one click)
2. Use Reset Data to reload the canvas and refresh the Data JSON and
   the Action Debugger between attempts

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

4. Named Credentials: secrets are not deployed, HTTP Actions will
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

Execute the IP in the designer Preview pane and read Errors/Debug Output.
The structure below is ILLUSTRATIVE ONLY. UNVERIFIED (2026-10-03): the
real per-step keys (for example whether a vlcStatus key appears) depend
on the runtime and are not documented in the fetched sources; read the
actual debug output instead of expecting these names:

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

**What the LLM generates:** "Test the OmniScript in Preview mode, if it works there, deploy it" without noting that Preview mode runs with the designer's permissions, may use different data, and does not reflect the actual runtime context (record page, Experience Cloud, mobile).

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

---

## Anti-Pattern 6: Adding Remote Site Settings for Named Credential Callouts

**What the LLM generates:** "The HTTP action fails in production because the Remote Site Setting is missing; add one for the endpoint."

**Why it happens:** Remote Site Settings are the classic answer to callout failures, and the LLM doesn't check how the endpoint is defined.

**Correct pattern:**

```text
Apex Developer Guide: "If the callout specifies a named credential as the
endpoint, you don't need to configure remote site settings."
- Endpoint is a named credential -> check the credential, its auth, and
  its endpoint in the target org
- Endpoint is a raw URL -> check the RemoteSiteSetting (a deployable
  Metadata API type) and move the call to a named credential
```

**Detection hint:** Remote Site Setting advice for an HTTP action whose endpoint is a named credential.

---

## Anti-Pattern 7: Prescribing `rollbackOnError` on the Integration Procedure Root to Surface Errors

**What the LLM generates:** "Set `rollbackOnError: true` at the IP root so failures reach the OmniScript."

**Why it happens:** `rollbackOnError` is a documented DataRaptor (OmniDataTransform) field, and the LLM transfers it to Integration Procedures and to error surfacing.

**Correct pattern:**

```text
OmniIntegrationProcedure metadata (Summer '26) has no rollbackOnError field.
Documented ways to control what the caller sees:
- Try-Catch Block: "Returns specified output or calls an Apex class if a
  step within it fails" (Trailhead)
- Response Action: decides what data goes back to the caller
For DataRaptor Loads, rollbackOnError decides whether partial work commits;
it does not by itself send an error message to the OmniScript.
```

**Detection hint:** `rollbackOnError` recommended on an Integration Procedure as the fix for silent failures.

