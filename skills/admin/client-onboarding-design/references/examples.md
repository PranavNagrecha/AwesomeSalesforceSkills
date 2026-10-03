# Examples — Client Onboarding Design

## Example 1: Wealth Management New Client Onboarding

**Context:** A regional wealth management firm uses FSC to onboard high-net-worth clients. The process involves an advisor, a compliance officer, and an operations team member. The firm has OmniStudio licensed as part of a Salesforce Industries bundle. Regulatory requirements mandate KYC verification before account funding instructions are sent.

**Problem:** Without a structured process design, the team built the intake form and tasks independently. Advisors were sending welcome emails before compliance had cleared KYC. Document collection tasks had no SLAs and were being missed, causing regulatory audit findings. When the compliance team needed to add a beneficial ownership disclosure step, the admin discovered the Action Plan template was published and could not be edited — forcing an emergency clone-and-republish under time pressure with no versioning convention in place.

**Solution:**

Process design delivered before any re-implementation:

```
Stage 1: Pre-Onboarding (Gate: Identity verification cleared)
  - Task: Collect government-issued ID (owner: Advisor, due: StartDate + 1, required: true)
  - Task: Run KYC check (owner: Compliance, due: StartDate + 2, required: true)
  - Task: Capture beneficial ownership disclosure (owner: Advisor, due: StartDate + 2, required: true)
  Gate condition: KYC task closed AND beneficial ownership task closed

Stage 2: Document Collection (Gate: All required docs received)
  - Task: Collect signed account agreement (owner: Advisor, due: StartDate + 1, required: true)
  - Task: Collect investment policy statement (owner: Advisor, due: StartDate + 3, required: true)
  - Task: Confirm beneficiary designations (owner: Advisor, due: StartDate + 5, required: false)
  Gate condition: Account agreement task closed AND IPS task closed

Stage 3: Compliance Review (Gate: Compliance sign-off)
  - Task: Compliance officer review (owner: Compliance Queue, due: StartDate + 2, required: true)
  Gate condition: Compliance review task closed

Stage 4: Account Activation
  - Task: Send funding instructions (owner: Operations, due: StartDate + 1, required: true)

Stage 5: Welcome Journey Handoff
  Trigger: FinancialAccount Status field = "Active"
  Channel: Marketing Cloud welcome journey (3-email series over 30 days)
  Payload: ClientName, AccountNumber, AdvisorName, AdvisorEmail
```

Governance design: Template owner = Senior Business Analyst. Change requests submitted via internal JIRA project. Naming convention: "Wealth Onboarding v[N]". In-flight plans complete on the version at launch; new version applies to onboardings started after publish date.

**Why it works:** The compliance gate (Stage 3 must complete before Stage 4 begins) is enforced by an item dependency: the "Send funding instructions" item depends on the "Compliance officer review" item with `creationType` `OnPreviousItemCompleted`, so the funding task is not created until compliance signs off. Marking the review item required records that it must be done; the dependency is what enforces the order. The versioning governance gives the beneficial ownership change, and every later change, a documented path that does not need emergency decisions. The deployable template for this design is in `metadata-examples.md`.

---

## Example 2: Insurance Client Onboarding (No OmniStudio License)

**Context:** A mid-size insurance carrier uses FSC but does not have OmniStudio licensed. They need a guided intake process for new policyholders, including consent capture, document submission, and underwriting review, anchored on an InsurancePolicy record.

**Problem:** The team assumed OmniStudio was included with FSC and began designing a multi-step OmniScript intake flow. Three weeks into design, licensing confirmed OmniStudio was not part of the contract. The design had to be restarted from scratch using Screen Flows, causing a significant project delay.

**Solution:**

Process design phase established license facts first:

```
License check result: OmniStudio NOT licensed. Intake tool = Screen Flow (Screen Flow with
multiple screens, decision elements, and record operations on InsurancePolicy and Contact).

Stage 1: Intake (Screen Flow)
  Screen 1: Personal information capture (Name, DOB, address)
  Screen 2: Coverage selection and coverage level
  Screen 3: Consent capture (explicit checkbox components, stored to Contact.HasOptedOutOfEmail
            and a custom consent object record)
  Screen 4: Document upload instructions (links to document portal, not inline upload)
  On completion: creates InsurancePolicy record in status "Pending Underwriting"

Stage 2: Document Collection (Action Plan on InsurancePolicy)
  Template: "Insurance Onboarding Docs v2"
  - Task: Receive signed application form (owner: Operations Queue, due: StartDate + 2, required: true)
  - Task: Receive proof of prior coverage (owner: Operations Queue, due: StartDate + 5, required: false)
  - Task: Confirm medical exam scheduled if required (owner: Advisor, due: StartDate + 3, required: true)

Stage 3: Underwriting Review
  Approval process on InsurancePolicy record (standard Salesforce Approval Process)
  Approver: Underwriting Team Queue
  On approval: InsurancePolicy Status = "Active"

Stage 4: Welcome Journey
  Trigger: InsurancePolicy Status change to "Active" (record-triggered Flow)
  Action: Send welcome email via OrgWideEmailAddress (no Marketing Cloud dependency)
  Timing: Immediately on activation
```

**Why it works:** Replacing OmniStudio with Screen Flow is a straightforward substitution at the process design layer. The phased structure, compliance gates, and welcome journey design are tool-agnostic — the process map does not change; only the intake tool changes. Catching the license gap in the design phase (not mid-implementation) saved the team from building unusable components.

---

## Anti-Pattern: Designing for OmniStudio Without Confirming License

**What practitioners do:** They read FSC documentation describing OmniScripts and OmniStudio as standard FSC capabilities, design a multi-step guided intake using OmniScript components, and hand the design to the implementation team — who then discover OmniStudio requires a separate license that is not in the contract.

**What goes wrong:** OmniStudio FlexCards and OmniScripts are a separately licensed add-on. They are prominently documented in FSC materials because they are commonly purchased together, but they are not automatically included. The implementation team either has to stop work pending a licensing procurement, or substitute Screen Flows last-minute with a design that was not optimized for the standard Flow UI.

**Correct approach:** Confirm OmniStudio license availability as the first step of process design. Check the org's installed packages (Setup > Installed Packages) for the OmniStudio managed package, or confirm with the account executive. Only then select the intake tool. Document the license basis in the technology selection rationale artifact so the decision is traceable.

---

## Example 3: Checking Document Collection Status Before the Compliance Gate

**Context:** The wealth onboarding design in Example 1 tracks the signed account agreement and the investment policy statement as document checklist items on the client's account.

**Problem:** The compliance officer needs one view of every client whose required documents are not yet accepted or waived, before the review task is assigned.

**Solution:** A report or list view built on this query, run against the onboarding parent records:

```sql
SELECT ParentRecordId, Name, DocumentType.MasterLabel, Status, IsRequired
FROM DocumentChecklistItem
WHERE IsRequired = true
  AND Status IN ('New', 'Pending')
ORDER BY ParentRecordId
```

**Why it works:** `Status` takes `Accepted`, `New`, `Pending`, or `Waived`, so "outstanding" is `New` or `Pending`. A document compliance chose not to require for one client is marked `Waived` rather than having `IsRequired` edited, because `IsRequired` is set only at creation. UNVERIFIED (2026-10-03): the `DocumentType` relationship name on `DocumentChecklistItem` is inferred from the `DocumentTypeId` field; adjust if the org's schema differs.

