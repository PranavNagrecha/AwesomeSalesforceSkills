# Gotchas: OmniStudio Integration Procedures

---

## `rollbackOnError: false` Is the Silent Default — Partial Writes Are Not Reported

**What happens:** A 5-step Integration Procedure: Step 1 creates a Case, Step 2 creates a Contact, Step 3 calls an external API and fails. `rollbackOnError` is not configured (defaults to false). Salesforce creates the Case (Step 1) and the Contact (Step 2), then the API call fails. The IP returns the `failureResponse` from Step 3. The OmniScript shows the error. But the Case and Contact were already written. No rollback. The user tries again — now there are duplicate Cases and Contacts.

**When it bites you:** Multi-step IPs that create or update records before a callout. Common in intake forms, application processes, and any IP that mixes DML with external API calls.

**How to avoid it:**
- Set `rollbackOnError: true` on every IP. Always. No exceptions.
- Test specifically for partial failure: mock the external API to return an error, verify no records were created

---

## HTTP Status 200 Does Not Mean Business Success

**What happens:** The external API returns HTTP 200 with this body: `{"status": "FAILED", "errorCode": "DUPLICATE_APPLICATION", "message": "An application already exists for this user."}`. The IP's HTTP action step succeeds (status 200 = HTTP success). `failOnStepError` doesn't fire. The next step tries to map `response.applicationId` — which doesn't exist in an error response. Null error. The user sees a generic error message with no explanation.

**When it bites you:** Any integration with APIs that use HTTP 200 for business-level errors (extremely common in REST APIs).

**How to avoid it:**
- After every HTTP action: add a Decision step checking the business-level status field
- Route error responses to a Set Values step that sets your output `status` and `errorMessage`
- Never assume the next DataRaptor step will have valid data just because the HTTP step succeeded

---

## Named Credentials Are Not Available in Every Sandbox by Default

**What happens:** An IP is built and tested in a full sandbox using `PaymentGateway_Production` Named Credential. The IP is deployed to a new Developer sandbox for a new team member. The IP fails immediately with `Invalid named credential`. The Named Credential wasn't deployed to the new sandbox. There's no Named Credential in that org for that name.

**When it bites you:** First deployment to any new environment (new sandbox, production go-live, org merge).

**How to avoid it:**
- Include Named Credentials in your deployment package/changeset
- Document all Named Credentials required by each IP in the IP description
- In the deployment runbook: "Before running IPs, verify Named Credentials exist: [list]"
- Consider using a sandbox-specific Named Credential (`PaymentGateway_Sandbox`) that points to a mock/test endpoint

---

## Placeholder `failureResponse` Text Ships to Production

**What happens:** Developer creates an IP, sets `failureResponse` to "Put Business approved verbiage here" as a placeholder. Business hasn't approved the text yet. Deploys to UAT. UAT testers don't test the error path. Deploys to production. First real error: users see "Put Business approved verbiage here."

**When it bites you:** Standard IP development workflow when error paths aren't tested.

**How to avoid it:**
- Make every `failureResponse` value a required review item before any deployment to UAT
- Run a pre-deployment check: grep the IP JSON for "verbiage", "TBD", "placeholder", "TODO"
- Default `failureResponse` should always be a real message, even if it's generic: "An error occurred. Please try again or contact support."

---

## FlexCards Don't Show IP Errors Without Explicit Error State Configuration

**What happens:** An IP fails and returns a `failureResponse`. The FlexCard that calls the IP doesn't have an error state configured. The FlexCard shows... nothing. Blank. No error. The user doesn't know what happened. They try again. Support tickets arrive: "The page is just blank sometimes."

**When it bites you:** Any FlexCard that calls an IP without configuring error/loading states.

**How to avoid it:**
- Every FlexCard has three states: Loading, Data (success), Error
- Error state checks `{IPResponse.error}` or your output `status` variable
- Error state shows a user-friendly message, not the raw IP response
- Test the error state explicitly: use the FlexCard preview with a mocked error response
