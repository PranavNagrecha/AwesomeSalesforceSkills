# LLM Anti-Patterns — DevOps Process Documentation

Common mistakes AI coding assistants make when generating or advising on Salesforce DevOps process documentation.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Generating a Release Plan When a Runbook Was Requested

**What the LLM generates:** A multi-section document covering scope, stakeholder communication, environment promotion sequence, testing strategy, go-live timeline, and risk register — presented as a "deployment runbook."

**Why it happens:** LLMs are trained on project management templates and release planning content, which are more common in training data than execution-level runbooks. The distinction between "release plan" and "runbook" is not prominent in general DevOps literature, so the model collapses them.

**Correct pattern:**

```
A deployment runbook is scoped to a single deployment event.
It contains:
- Numbered execution steps (not prose descriptions)
- A single responsible person per step
- An expected duration and pass/fail outcome per step
- Pre-deploy gate, deploy execution, post-deploy validation, and rollback decision gate sections

It does NOT contain: scope narrative, stakeholder lists, project timeline, or risk register.
```

**Detection hint:** If the generated document includes a section titled "Scope," "Timeline," "Stakeholders," or "Risk Register," it is a release plan, not a runbook. Flag and regenerate with the correct scope.

---

## Anti-Pattern 2: Omitting Named Credential Re-entry Steps

**What the LLM generates:** A deployment runbook or deployment checklist that includes "deploy metadata package" and "run smoke tests" but has no step for re-entering Named Credential or External Credential values after the deployment.

**Why it happens:** LLMs understand that Named Credentials are a metadata type and assume they deploy completely. The gap (secret values are not transferred by the Metadata API) is a platform-specific behavior that requires Salesforce-specific knowledge to know. General DevOps training data does not cover this.

**Correct pattern:**

```
## Step N: Re-enter Named Credential — [Integration Name]

Navigate to: Setup > Security > Named Credentials > [NamedCredential API Name]

Field                          | Value
-------------------------------|------------------------------------------
URL                            | [endpoint URL — confirm with integration owner]
Identity Type                  | [Named Principal / Per User / Anonymous]
Authentication Protocol        | [Password / JWT / OAuth / Custom]
Username                       | [integration username]
Password                       | [retrieve from [vault/secret source]]

After saving, verify connectivity:
- Run test callout to [endpoint/healthcheck path]
- Expected response: HTTP 200
- If not 200: escalate to [integration owner name]
```

**Detection hint:** Search the generated runbook for the words "Named Credential" or "ExternalCredential". If they appear in the metadata scope list but not in a post-deploy step, the credential re-entry is missing.

---

## Anti-Pattern 3: Generating an Environment Matrix Without a Data Policy Column

**What the LLM generates:** An environment matrix table with columns for org name, org type, purpose, and refresh cadence — but no column capturing what data the environment contains or whether production data is permitted.

**Why it happens:** Generic environment matrix templates from non-Salesforce DevOps literature rarely include a data policy column because most non-Salesforce environments are not populated with copies of production CRM data. Salesforce sandboxes are commonly Full Copy or Partial Copy sandboxes containing real customer records, making data policy a critical operational distinction.

**Correct pattern:**

```
| Org Name | Org Type    | Purpose         | Branch Alignment | Refresh Cadence | Data Policy                     | Owner      |
|----------|-------------|-----------------|------------------|-----------------|---------------------------------|------------|
| sf-uat   | Full Copy   | Customer UAT    | release/*        | Quarterly       | Anonymized prod — demo accounts OK | Rel. mgr  |
| sf-dev   | Developer   | Feature dev     | feature/*        | On demand       | Synthetic only — no prod data   | Dev lead   |
```

Data policy column must specify: production data present / anonymized / synthetic / prohibited.

**Detection hint:** Check the generated matrix for a "Data Policy" or "Data" column. If absent, add it before using the matrix. If present, verify each row states more than "no PII" — the full data category must be explicit.

---

## Anti-Pattern 4: Writing Rollback as a Single Checklist Item

**What the LLM generates:** A runbook that includes "rollback if needed" or "revert changes if deployment fails" as a single line item, without specifying the rollback procedure, the decision owner, the time estimate, or the go/no-go threshold.

**Why it happens:** LLMs model rollback as a single atomic operation ("undo the deployment") rather than a decision gate with multiple possible paths (metadata restore, feature toggle, hotfix, data reversal). The nuance of who owns the call and under what conditions is not captured by generic rollback language.

**Correct pattern:**

```
## Rollback Decision Gate

Go/No-Go threshold: If post-deploy smoke tests fail within 30 minutes of deployment completion,
or if any P1/P2 incident is raised within 2 hours of go-live, initiate rollback.

Decision owner: [Release manager name] — must be reachable during the deployment window.

Rollback procedure:
1. [If metadata rollback] Deploy previous package version: sf project deploy start --manifest previous-manifest.xml
2. [If feature toggle] Disable custom setting: Setup > Custom Settings > [Name] > set Active = false
3. [If data reversal required] Execute data restore script: see runbook attachment [filename]

Estimated rollback time: 20 minutes for metadata restore / 5 minutes for feature toggle

After rollback: confirm smoke tests pass, notify stakeholders, file incident report within 24 hours.
```

**Detection hint:** Search the generated runbook for "rollback". If it appears exactly once as a checklist item with no sub-steps, escalation path, or time estimate, the rollback section is incomplete.

---

## Anti-Pattern 5: Using a Prior Environment's Runbook as the Production Runbook with Only the Org Name Changed

**What the LLM generates:** When asked to "create a production runbook based on the staging runbook," the model produces an identical document with "staging" replaced by "production" throughout, including sections that reference staging-specific Named Credential values, staging test user accounts, and staging smoke test endpoints.

**Why it happens:** LLMs perform textual substitution when asked to adapt one document for another context. They do not distinguish between environment-independent content (deploy commands, metadata scope, Flow activation steps) and environment-specific content (credential values, user accounts, URLs, IP allowlists).

**Correct pattern:**

```
When adapting a runbook across environments, explicitly audit each section:

Environment-INDEPENDENT (carry forward unchanged):
- Metadata scope / manifest
- Deploy command structure
- Flow version verification steps
- Permission set assignment verification steps

Environment-SPECIFIC (must be re-authored for production):
- Named Credential values and secret sources
- Test user accounts and login credentials
- Smoke test URLs and endpoints
- IP allowlist values
- External system integration contacts
- Go/no-go threshold and rollback decision owner (may differ between environments)
```

**Detection hint:** Search the adapted runbook for staging-specific values (sandbox org name, staging API URLs, sandbox-user email addresses). Any staging reference that survives into the production runbook is a carry-over error.
