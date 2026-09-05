# Examples — DevOps Process Documentation

## Example 1: Runbook for a Release Including a Named Credential Update

**Scenario:** A team is deploying a new integration metadata package that includes a `NamedCredential` pointing to an updated external API endpoint. A junior admin will execute the deployment.

**Problem:** The team's prior approach was to list "update Named Credentials" as a single line item at the end of a generic deployment checklist. In three out of the previous five releases, this step was either skipped or done incorrectly because the admin executing the deployment did not know which fields needed to be updated or what the correct values were.

**Solution:**

The runbook adds a Named Credential re-entry section with field-level detail:

```
## Step 7: Re-enter Named Credential — Acme ERP API

Navigate to: Setup > Security > Named Credentials > Acme ERP API

Field                  | Value
-----------------------|--------------------------------------------
Label                  | Acme ERP API
Name                   | Acme_ERP_API
URL                    | https://api.acme.com/v2  (confirm with integration team)
Identity Type          | Named Principal
Authentication Protocol| Password Authentication
Username               | sfdc-integration@acme.com
Password               | [retrieve from LastPass vault: "Acme ERP – SFDC Integration"]
Generate Authorization Header | Checked

After saving: navigate to Setup > Developer Console > Open Execute Anonymous
Run: HttpRequest req = new HttpRequest(); req.setEndpoint('callout:Acme_ERP_API/healthcheck'); req.setMethod('GET'); HttpResponse res = new Http().send(req); System.debug(res.getStatusCode());
Expected result: 200
If result is 401 or 404: stop deployment, escalate to integration owner.
```

**Why it works:** The runbook specifies the exact navigation path, every field that must be set, the secret source (vault entry name), and a verification step with a pass/fail criterion. The admin executing the step does not need prior knowledge of the integration to complete it correctly.

---

## Example 2: Environment Matrix for a Team with Four Sandboxes

**Scenario:** A mid-size ISV has four active sandboxes and a Developer Edition used for spike work. The team has been onboarding contractors who keep running experiments in the UAT sandbox and contaminating test data before customer demos.

**Problem:** There was no written record of what each sandbox was for, what data it contained, or how recently it had been refreshed. Contractors made reasonable-sounding assumptions that turned out to be wrong.

**Solution:**

The team authors a one-page environment matrix stored in the team wiki and linked from every runbook:

```
| Org Name       | Org Type      | Purpose                        | Branch Alignment       | Refresh Cadence | Data Policy                        | Owner           |
|----------------|---------------|--------------------------------|------------------------|-----------------|------------------------------------|-----------------|
| sf-dev-01      | Developer Pro | Individual feature development | feature/* branches     | On demand       | Synthetic only — no prod data      | Dev team lead   |
| sf-int         | Partial Copy  | Integration regression QA      | develop branch         | Monthly (1st)   | Anonymized prod subset — no PII    | QA lead         |
| sf-uat         | Full Copy     | Customer UAT and demos         | release/* branches     | Quarterly       | Anonymized prod — demo accounts OK | Release manager |
| sf-staging     | Full Copy     | Pre-production validation      | main branch            | Before each rel | Full anonymized prod copy          | DevOps lead     |
| sf-spike-01    | Developer Ed  | POC and spike work only        | spike/* (ephemeral)    | Never           | Synthetic only — sandboxed         | Architect       |
| Production     | Production    | Live customer org              | main (source of truth) | N/A             | Live customer data — restricted    | Org owner       |
```

Below the table, the team adds explicit rules:
- "sf-uat must not be used for feature development. Any config change in sf-uat must be tracked in a separate branch and promoted through sf-int first."
- "sf-staging is refreshed before each major release window. Confirm refresh date before running any pre-release validation."

**Why it works:** The data policy column eliminates the ambiguity that caused the contamination problem. The owner column creates accountability for refresh cadence. The branch alignment column prevents deployments targeting the wrong branch.

---

## Anti-Pattern: Writing the Runbook as a Release Plan

**What practitioners do:** They write a single document that combines scope description, stakeholder communication, environment promotion sequence, and execution steps. The document is typically 8–15 pages and is circulated to the project team a week before the release.

**What goes wrong:** During the deployment window, the person executing the deployment cannot navigate the document to find the specific steps for the current phase. They either improvise (creating execution risk) or spend 10–15 minutes scanning the document for the relevant section (creating timeline pressure). Post-deploy issues are harder to reconstruct because actions are not numbered or timestamped. Named Credential steps are buried in a prose description rather than a numbered checklist.

**Correct approach:** Separate the release plan (scope, timeline, approvals, stakeholder comms — authored by the project or release manager, typically a week before the window) from the deployment runbook (numbered execution steps — authored by the deploying admin, reviewed 24 hours before the window). The runbook references the release plan by name or link but does not repeat its content.

**The split, as an artefact.** The two documents share exactly one field — the change-request number —
and nothing else. Written down, the boundary stops being a matter of taste:

```yaml
# release-plan.md  (release manager, ~1 week before the window, prose is fine)
release_plan:
  release: CI-2026.10
  change_requests: [CR-0141, CR-0142, CR-0147]      # <-- the only shared key
  scope_narrative: "Case intake moves off the shared mailbox."
  stakeholders: ["Support ops", "ERP integration team", "Finance (shipment refs)"]
  timeline: {uat_open: "2026-10-06", go_live: "2026-10-17"}
  comms_plan: "Support-wide email 2026-10-14; standup demo 2026-10-16."
  risk_register: [{id: R-3, risk: "ERP sandbox endpoint differs from prod", owner: "integration-lead"}]

# devops-process.yaml -> runbook  (deploying admin, reviewed 24h before, no prose)
runbook:
  release: CI-2026.10                                # <-- joins on the same release / CR ids
  steps:
    - {id: RB-05, phase: validate, action: validate-only, owner: admin,
       duration_minutes: 25, pass_criteria: "status == Succeeded; deploy ids on CR-0141/0142/0147"}
    - {id: RB-07, phase: deploy, action: deploy, owner: admin,
       duration_minutes: 20, pass_criteria: "four deploys Succeeded, in deploy_order sequence"}
```

Anything with a `stakeholders`, `scope_narrative`, `timeline` or `risk_register` key belongs in the
left-hand file. Anything with an `owner`, a `duration_minutes` and a `pass_criteria` belongs in the
right-hand one. `scripts/check_devops_process_documentation.py` enforces the right-hand shape:
a step with no owner or no pass criterion is an ERROR, because those are the two fields that make a
line executable during a window rather than readable a week before it.
