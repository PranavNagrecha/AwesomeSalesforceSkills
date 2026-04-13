# Change Advisory Board Process — Work Template

Use this template when designing, implementing, or reviewing a CAB process for Salesforce deployments.

---

## Scope

**Skill:** `change-advisory-board-process`

**Request summary:** (fill in what the user asked for — e.g., "Define a CAB process for our Salesforce DevOps team," "Review our existing CAB classification matrix," "Design an Emergency CAB procedure")

---

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md:

- **ITSM platform in use:** (ServiceNow / Jira Service Management / Freshservice / none — specify)
- **Deployment toolchain:** (Salesforce CLI / Copado / Gearset / DevOps Center / GitHub Actions / other)
- **Org type / regulatory context:** (standard / GovCloud / HIPAA / SOX / FedRAMP — specify any)
- **Current change volume:** (estimated deployments per month — e.g., "~5/month" or "daily")
- **Next Salesforce upgrade window:** (check trust.salesforce.com — record sandbox preview start + production wave dates)
- **Known high-risk metadata types in scope:** (list which of: Profiles, PermissionSets, SharingRules, Flows, NamedCredentials, ConnectedApps are in play)

---

## Change Classification Matrix

Complete this table for the organization's context:

| Metadata Type | Default Tier | Override Conditions | Required Approvers |
|---|---|---|---|
| Profile | Normal | None — always Normal | Admin + Security + Business Owner |
| PermissionSet | Normal | None — always Normal | Admin + Security |
| SharingRules / OWD | Normal | None — always Normal | Admin + Security + Data Owner |
| Flow / ProcessBuilder | Normal | Standard if: cloning existing Flow with no logic change and Business Owner pre-approves the type | Admin + Business Owner |
| NamedCredential / RemoteSiteSetting | Normal | None | Admin + Security |
| Connected App OAuth scopes | Normal | None | Admin + Security + IT |
| Apex classes (no sharing/access changes) | Standard | Escalate to Normal if: touching Batch/Queueable that processes >10k records | Admin (peer review) |
| Custom Object / Field (non-critical) | Standard | Escalate to Normal if: field is on a regulated data object | Admin |
| Report / Dashboard | Standard | None | None (pre-authorized) |
| Email Template | Standard | None | None (pre-authorized) |
| ValidationRule (critical object) | Normal | Standard if: org-wide Business Owner pre-authorization exists for the rule type | Admin + Business Owner |
| CustomMetadata / CustomSetting | Normal | None | Admin + relevant system owner |

---

## Approval Workflow Definition

### Standard Change
- **Approvers required:** None (pre-authorized runbook applies)
- **Advance notice:** Same-day acceptable
- **Deployment window:** Any scheduled deployment window
- **Evidence required:** Runbook reference number, sandbox test log

### Normal Change
- **Approvers required:** Minimum 2 of: Salesforce Admin / Release Manager, Business Process Owner, Security/IT (mandatory for access/integration changes)
- **Advance notice:** Minimum 48 hours before planned deployment
- **Deployment window:** Within approved CAB-assigned window
- **Evidence required:** Change ticket (Approved status), sandbox deployment log, test class results (≥75% coverage), rollback plan

### Emergency Change (ECAB)
- **Approvers required:** Minimum 2 of named ECAB quorum:
  - ECAB Member 1: [Name/Role] — e.g., Release Manager
  - ECAB Member 2: [Name/Role] — e.g., Head of IT or on-call Architect
  - ECAB Member 3 (optional backup): [Name/Role]
- **Advance notice:** As soon as incident is identified — ticket opened before deployment
- **Deployment window:** Immediate, with post-deploy monitoring
- **Evidence required:** Change ticket (Emergency-Approved status), rollback plan, post-implementation review scheduled within 5 business days

---

## Deployment Freeze Calendar

| Period | Freeze Type | Reason | Exceptions |
|---|---|---|---|
| Sandbox preview start — Production upgrade Wave 1 | Soft freeze for Normal changes | Platform drift risk (sandbox on new release, production on old) | Emergency changes only; or Normal with explicit CAB acknowledgment of drift risk |
| 7 days before each production upgrade wave | Enhanced review required | Elevated deployment risk near upgrade | Emergency and Standard only; all Normals require additional sign-off |
| [Organization-specific dates — e.g., fiscal year close, peak season] | Org-defined freeze | Business risk | Emergency only |

**Next Salesforce upgrade dates:** (fill from trust.salesforce.com)
- Spring '25 Sandbox Preview: ___________
- Spring '25 Production Wave 1: ___________
- Spring '25 Production Wave 2: ___________
- Spring '25 Production Wave 3: ___________

---

## ITSM Integration Specification

**ITSM platform:** ___________

**Change ticket required fields:**
- [ ] Change title and description
- [ ] Affected metadata types (list)
- [ ] Change classification tier (Standard / Normal / Emergency)
- [ ] Rollback procedure
- [ ] Planned deployment window (date + time + timezone)
- [ ] Test evidence (sandbox log URL or attachment)
- [ ] Impacted business processes
- [ ] Approver assignments

**Pipeline gate configuration:**
```
# Required pipeline environment variables
ITSM_API_ENDPOINT=https://[your-itsm]/api/change
ITSM_API_TOKEN=${{ secrets.ITSM_TOKEN }}
CHANGE_REQUEST_NUMBER=${{ inputs.change_request_number }}  # required input

# Gate logic (before production deploy step)
STATUS=$(curl -s -H "Authorization: Bearer $ITSM_API_TOKEN" \
  "$ITSM_API_ENDPOINT/$CHANGE_REQUEST_NUMBER/status" | jq -r '.status')

if [[ "$STATUS" != "Approved" && "$STATUS" != "Emergency-Approved" ]]; then
  echo "ERROR: Change request $CHANGE_REQUEST_NUMBER not in Approved state (current: $STATUS)"
  exit 1
fi
```

---

## Post-Deployment Requirements

### Normal Change
- [ ] Deployment log attached to change ticket
- [ ] Smoke test results documented
- [ ] Change ticket marked Implemented
- [ ] Any unintended impacts reported within 24 hours

### Emergency Change
- [ ] Deployment log attached to change ticket
- [ ] Change ticket marked Implemented (Emergency)
- [ ] Post-implementation review scheduled (≤5 business days)
- [ ] Root cause of incident documented in review

---

## Notes

(Record any deviations from the standard pattern, regulatory-specific additions, or decisions made during this CAB design engagement and their rationale.)
