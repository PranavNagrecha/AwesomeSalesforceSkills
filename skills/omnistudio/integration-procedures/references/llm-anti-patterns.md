# LLM Anti-Patterns — Integration Procedures

Common mistakes AI coding assistants make when generating or advising on OmniStudio Integration Procedures.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Not Using Named Credentials for HTTP Actions

**What the LLM generates:** HTTP Action steps with hardcoded endpoint URLs and authentication headers, bypassing Named Credentials and exposing secrets in the Integration Procedure configuration.

**Why it happens:** Direct URL and header configuration is simpler. LLMs follow the shortest path to a working callout without applying the Salesforce security pattern of Named Credentials for external authentication.

**Correct pattern:**

```text
HTTP Action authentication:

WRONG — hardcoded credentials:
  URL: https://api.example.com/v1/data
  Headers: Authorization: Bearer sk-12345abcdef

CORRECT — Named Credential:
  URL: callout:My_Named_Credential/v1/data
  Authentication: handled automatically by the Named Credential

Benefits:
- Credentials encrypted at rest and managed in Setup
- Environment-specific (different credential per sandbox)
- Credential rotation without changing the Integration Procedure
- Audit trail for credential usage
```

**Detection hint:** Flag HTTP Actions with full URLs (https://...) instead of callout: prefix. Look for Authorization headers with literal tokens in HTTP Action configuration.

---

## Anti-Pattern 2: Ignoring Error Handling in Integration Procedure Steps

**What the LLM generates:** Integration Procedures that call DataRaptors and HTTP Actions without configuring failure responses, continue-on-error settings, or conditional paths for error scenarios.

**Why it happens:** Success-path designs dominate OmniStudio training examples. Error handling in Integration Procedures (ResponseAction, Continue on Step Error, conditional error paths) is more complex and less documented.

**Correct pattern:**

```text
Integration Procedure error handling:

1. Per-step error configuration:
   - "Continue on Step Error": set to true for non-critical steps
   - "Show Error in Response": true for debugging
   - ResponseAction: configure for each step

2. Error path pattern:
   - Step 1: HTTP Action (may fail)
   - Step 2: Conditional Block: check if Step 1 succeeded
     - Success path: process response
     - Failure path: set default values or retry

3. HTTP Action error handling:
   - Check response status code (200, 4xx, 5xx)
   - Map error response body to output for caller visibility
   - Set a failure flag for downstream conditional logic

4. DataRaptor error handling:
   - Extract may return empty results (not an error — check count)
   - Load may fail on validation rules — capture the error message
```

**Detection hint:** Flag Integration Procedures with 5+ steps and no error handling configuration. Look for missing "Continue on Step Error" settings and absent conditional error paths.

---

## Anti-Pattern 3: Calling Integration Procedures Synchronously When Async Is Appropriate

**What the LLM generates:** OmniScript designs that call a long-running Integration Procedure synchronously, blocking the user interface while waiting for an external API response that may take 5-10 seconds.

**Why it happens:** Synchronous execution is the default and simpler to implement. LLMs do not evaluate the expected response time and recommend async patterns (fire-and-forget IP, queueable processing) less frequently.

**Correct pattern:**

```text
Sync vs Async Integration Procedure execution:

Synchronous (default):
- User waits for the IP to complete
- Appropriate when: response time < 3 seconds, user needs the result
- OmniScript blocks on the step until IP returns

Asynchronous options:
1. Fire-and-forget IP: OmniScript continues without waiting
   - Use when: the result is not needed immediately
   - Example: logging, audit record creation, non-blocking notifications

2. Polling pattern: launch async IP, then poll for completion
   - Use when: long-running external process (5-30 seconds)
   - OmniScript shows a spinner and checks periodically

3. Platform Event pattern: IP publishes event when done
   - Use when: result must be pushed back to the UI
   - Requires event listener in OmniScript or LWC

User experience: never make users wait >3 seconds synchronously.
```

**Detection hint:** Flag synchronous IP calls from OmniScripts where the HTTP Action has a timeout configured for >5 seconds. Check for missing async patterns on long-running operations.

---

## Anti-Pattern 4: Overloading a Single Integration Procedure with Too Many Responsibilities

**What the LLM generates:** A single Integration Procedure that fetches data from 3 sources, transforms it, calls 2 external APIs, writes back to Salesforce, and sends a notification — creating a monolithic, hard-to-debug procedure.

**Why it happens:** LLMs consolidate logic into a single unit for convenience. The OmniStudio best practice of composing smaller, focused Integration Procedures that can be called from a parent IP is underrepresented in training data.

**Correct pattern:**

```text
Integration Procedure composition pattern:

MONOLITHIC (avoid):
  IP_DoEverything:
    Step 1: Extract Account data
    Step 2: Extract Contact data
    Step 3: Call External API 1
    Step 4: Transform response
    Step 5: Call External API 2
    Step 6: Load data back
    Step 7: Send notification

COMPOSED (recommended):
  IP_Orchestrator:
    Step 1: Call IP_FetchData (extracts from Salesforce)
    Step 2: Call IP_EnrichFromExternal (calls external APIs)
    Step 3: Call IP_SaveResults (loads data back)
    Step 4: Call IP_Notify (sends notification)

Benefits:
- Each sub-IP is testable independently
- Errors are isolated to specific sub-procedures
- Sub-IPs are reusable across multiple orchestrations
- Easier to debug (test each sub-IP in isolation)
```

**Detection hint:** Flag Integration Procedures with more than 10 steps. Check whether the procedure can be decomposed into smaller, reusable sub-procedures.

---

## Anti-Pattern 5: Not Activating the Correct Version of the Integration Procedure

**What the LLM generates:** "Save and activate the Integration Procedure" without addressing version management — that only one version can be active at a time, and activating a new version immediately deactivates the previous one.

**Why it happens:** Version management is an operational concern. LLMs focus on building and testing without covering the activation workflow and its impact on running OmniScripts.

**Correct pattern:**

```text
Integration Procedure version management:

Rules:
- Only ONE version of an IP can be active at any time
- Activating a new version immediately deactivates the previous version
- ALL calling OmniScripts and FlexCards immediately use the new active version
- There is no gradual rollout or A/B testing for IP versions

Safe activation workflow:
1. Create new version with changes
2. Test in Preview mode (does not affect active version)
3. Test from calling OmniScript in a sandbox
4. Activate the new version only after testing passes
5. Monitor for errors after activation
6. If issues: activate the previous version to roll back

Naming: use Type and SubType carefully — calling components
reference IP by Type/SubType, not by internal version number.
```

**Detection hint:** Flag Integration Procedure deployment instructions that do not mention version activation impact on calling components. Check for missing rollback strategy.
