# /score-deployment — Risk-score a change set before deploy

Wraps [`agents/deployment-risk-scorer/AGENT.md`](../agents/deployment-risk-scorer/AGENT.md). Compares a change set against a live target org via MCP and returns HIGH / MEDIUM / LOW risk with a breaking-change list.

---

## Step 1 — Collect inputs (ask all three)

Ask:

```
1. Path to the change set?
   Example: force-app/main/default/ or a package.xml path

2. Target-org alias? (must be authenticated via sf CLI)
   Example: uat, prod

3. Change scope?
   full / delta (since last successful deploy) / a commit range
```

If any required input is missing, STOP.

---

## Step 2 — Load the agent

Read `agents/deployment-risk-scorer/AGENT.md` fully + the devops skills and decision trees it cites.

---

## Step 3 — Execute

Follow the 5-step plan:
1. Enumerate metadata changes (objects, fields, Apex, LWC, Flows, VRs, profiles, sharing rules)
2. Live-org probes (`describe_org`, `list_custom_objects`, `list_flows_on_object`, `validate_against_org`)
3. Risk checks (field-deleted-in-use, required-field-added, VR-stricter, picklist-value-removed, API-version-downgrade, permission-revoked, trigger-added-to-covered-object, managed-package-field-override, sharing-rule-widened, flow-activated-in-deploy, test-coverage-unknown)
4. Remediation hints per risk
5. Pre-deploy smoke plan

---

## Step 4 — Deliver

- Risk score (HIGH / MEDIUM / LOW) with confidence
- Summary table (change counts + finding counts)
- Per-finding row (severity, item, description, remediation, skill citation)
- Pre-deploy checklist (ordered TODOs)
- Post-deploy smoke steps
- Citations + any MCP tool output

---

## Step 5 — Recommend follow-ups

- `/scan-security` if any security-related finding surfaced
- `/consolidate-triggers` if a new trigger was flagged for co-existence risk
- `/detect-drift` after deploy to confirm the org matches the library

---

## What this command does NOT do

- Does not deploy.
- Does not validate-only — recommends the user run `sf project deploy validate` themselves.
- Does not override HIGH risk warnings.
