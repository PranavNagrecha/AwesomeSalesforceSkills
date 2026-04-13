# LLM Anti-Patterns — Change Advisory Board Process

Common mistakes AI coding assistants make when generating or advising on Change Advisory Board Process for Salesforce.
These patterns help the consuming agent self-check its own output.

---

## Anti-Pattern 1: Recommending Salesforce Approval Processes to Implement CAB

**What the LLM generates:** "Create a custom object `Deployment_Request__c` with fields for Change Type, Description, and Approver. Configure a Salesforce Approval Process with two approval steps (Manager and Release Manager). Only proceed with deployment once the record is in 'Approved' status."

**Why it happens:** LLMs are trained on Salesforce documentation where Approval Processes appear as the canonical "how to get something approved" mechanism. The training data conflates business-process approvals (record-level) with deployment governance (pipeline-level). The LLM does not model the fact that the deployment pipeline lives outside the Salesforce org.

**Correct pattern:**

```
CAB enforcement must live in the deployment toolchain — not inside Salesforce.
The pipeline (GitHub Actions, Copado, Gearset, Salesforce CLI wrapper) must call the 
ITSM tool's API (ServiceNow, Jira SM) to verify change request status before
allowing the production deploy step.

A Salesforce Approval Process cannot gate a `sf project deploy start` command 
run from a developer's terminal or a CI runner.
```

**Detection hint:** Look for phrases like "Approval Process," "Deployment_Request__c," or "custom object approval" in proposed CAB designs. Any design where the enforcement mechanism is a Salesforce record state is this anti-pattern.

---

## Anti-Pattern 2: Treating All Changes as Requiring Full CAB Board Review

**What the LLM generates:** "Every change to the Salesforce org — including report updates, dashboard modifications, and email template changes — must go through the Change Advisory Board meeting, which convenes weekly. Submit a change request at least 5 business days in advance for any modification."

**Why it happens:** LLMs default to conservative, comprehensive recommendations when given a governance topic. Without modeling the operational cost of over-governance, the LLM applies maximum review to every change type.

**Correct pattern:**

```
CAB governance must use tiered change classification:
- Standard (pre-authorized): reports, dashboards, email templates, list views — no CAB meeting required
- Normal (full CAB review): Profiles, Permission Sets, Sharing Rules, Flows, Named Credentials
- Emergency (ECAB, expedited): P1 production incidents requiring immediate fix

Applying full CAB to every change creates a governance bottleneck that drives 
teams to route around the process or declare false emergencies.
```

**Detection hint:** If the generated process has a single change category with no tiers and requires the same approval process for every change type, flag it as this anti-pattern.

---

## Anti-Pattern 3: Ignoring the Salesforce Seasonal Release Upgrade Window

**What the LLM generates:** A CAB process, deployment calendar, and change management plan with no mention of Salesforce platform upgrade windows, sandbox preview periods, or production upgrade wave dates.

**Why it happens:** LLMs model generic ITIL/ITSM change management patterns and apply them to Salesforce without accounting for the platform-specific constraint that Salesforce itself upgrades the underlying runtime three times per year, creating windows where sandbox and production are on different platform versions.

**Correct pattern:**

```
The CAB change calendar must incorporate:
1. Salesforce sandbox preview start date (~4-6 weeks before production upgrade)
2. Production upgrade wave dates (Wave 1, 2, 3 — staggered across weekends)
   Source: trust.salesforce.com

During the sandbox-preview/production-old-release overlap window:
- Require explicit CAB sign-off acknowledging platform drift risk
- Recommend deferring Normal changes to post-production-upgrade where possible
- Never treat sandbox test evidence as sufficient validation if the sandbox is on
  a newer release than production
```

**Detection hint:** Search generated CAB templates for any mention of "trust.salesforce.com," "sandbox preview," or "upgrade window." If absent from a deployment calendar or freeze policy section, flag as this anti-pattern.

---

## Anti-Pattern 4: Assuming Permission Set Deployment Is a Complete Replacement

**What the LLM generates:** "Deploy the updated Permission Set XML to production. Once deployed, the Permission Set in production will exactly match your source control version."

**Why it happens:** LLMs model Salesforce CLI deployments as idempotent full-replace operations (analogous to Terraform apply producing a known state). The Metadata API's actual behavior for Permission Sets is additive — it does not remove entries absent from the deployed XML that were added manually in the target org.

**Correct pattern:**

```
Permission Set deployment via Metadata API is ADDITIVE for entries present in the XML.
It does NOT remove permission entries that:
- Were manually added in Setup after the last source-tracked retrieval
- Exist in the org but were not included in the retrieved XML scope

CAB process for Permission Set changes MUST include:
1. Pre-deployment: retrieve current live Permission Set from production and diff against source
2. Post-deployment: audit effective permissions (PermissionSetAssignment + object permissions)
   and confirm no unexpected grants remain

Do not claim the deployment produces a known final state without this audit.
```

**Detection hint:** Any CAB procedure for Permission Set or Profile changes that does not include a pre-deployment diff step and a post-deployment permission audit is exhibiting this anti-pattern.

---

## Anti-Pattern 5: Specifying Only a CAB Meeting Process Without Pipeline Enforcement

**What the LLM generates:** A detailed CAB meeting agenda, attendee list, change request form, and approval sign-off template — but no specification of how the deployment toolchain verifies that approval was obtained before executing the production deploy.

**Why it happens:** LLMs excel at generating process documentation (meeting agendas, forms, checklists) and may not model the critical connection between the approval record and the deployment execution. The generated CAB is complete as a governance document but has no teeth — a developer can bypass it entirely by deploying directly.

**Correct pattern:**

```
Every CAB process design must include a deployment gate specification:

1. The deployment pipeline must have a step that calls the ITSM API before 
   the production deploy step executes.
2. The API call verifies that a change request exists with:
   - Matching deployment scope (environment, change description)
   - Status = "Approved" or "Emergency-Approved"
3. If the check fails, the pipeline exits with a non-zero code and does not deploy.
4. The change request number must be a required input to the pipeline run
   (not optional or post-hoc).

Without this gate, the CAB documentation is a compliance artifact with no 
operational enforcement. Motivated developers will bypass it under pressure.
```

**Detection hint:** If the generated output includes CAB forms, meeting templates, and approval checklists but no description of how the deployment tool verifies approval status before executing, flag as this anti-pattern.

---

## Anti-Pattern 6: Conflating ECAB With "Skipping CAB"

**What the LLM generates:** "For emergency changes, the normal CAB process can be bypassed. Have the on-call manager verbally approve the change and proceed immediately. Document the change after the fact."

**Why it happens:** LLMs interpret "emergency" as an exception to governance rather than a fast path through governance. Verbal after-the-fact approvals appear in some generic ITSM documentation and bleed into Salesforce-specific guidance.

**Correct pattern:**

```
Emergency changes use an Emergency CAB (ECAB) — a smaller, faster quorum —
NOT a bypass of the change process.

ECAB requirements:
- Named ECAB quorum (minimum 2 approvers, pre-defined by role)
- Formal change ticket opened in ITSM tool BEFORE deployment (even if minutes before)
- Rollback plan documented in the ticket
- Post-implementation review mandatory within 5 business days
- ECAB approval recorded in the ITSM tool (machine-readable status)

"Verbal approval" + "document later" creates no audit trail and fails
compliance audits. The change ticket must exist and be approved in the system
of record before the deployment executes, even for emergencies.
```

**Detection hint:** Look for phrases like "verbal approval," "bypass for emergencies," "document after the fact," or "skip the CAB for urgent changes." Any of these signal this anti-pattern.
