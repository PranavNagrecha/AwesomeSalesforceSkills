# Examples — Wealth Management Requirements

## Example 1: Architecture Determination Before Object Scoping

**Context:** A regional wealth management firm is migrating from Redtail CRM to Salesforce FSC. The implementation partner's BA begins requirements discovery with the client, who says "we want to track client portfolios, financial goals, and annual reviews in Salesforce."

**Problem:** The BA immediately begins writing user stories that reference `FinServ__FinancialGoal__c` and `FinServ__FinancialPlan__c` based on documentation found online. The Salesforce admin assigned to the project has provisioned an FSC Core org (Winter '23+ GA). When the developer later tries to build the SOQL queries and Flow references using the requirements document, the object names do not resolve — because FSC Core uses `FinancialGoal` and `FinancialPlan` without the `FinServ__` namespace.

**Solution:**

The requirements discovery session should begin with an explicit architecture determination step:

```
Architecture Determination Checklist (capture before writing any object names):

1. Is this a new FSC org provisioned after Winter '23?
   → If yes, confirm whether it was provisioned as FSC Core (no namespace) or managed package.
   → Check: go to Setup > Installed Packages. If "Financial Services Cloud" appears with a namespace of "FinServ", this is the managed package. If FSC features are present but no FinServ package appears, this is FSC Core.

2. Are third-party custodian/portfolio management packages installed?
   → List each package. Validate AppExchange listing for "Works with FSC Core" certification.

3. Does the client need more than two named owners on any financial account?
   → If yes, FSC Core with FinancialAccountParty junction is required.

Architecture Decision (document in requirements):
- Org model: FSC Core (no namespace) / Managed Package (FinServ__ namespace)
- Object naming convention for this project: [no prefix] / [FinServ__ prefix]
- All requirements, user stories, and acceptance criteria will use: [confirmed convention]
```

Once the architecture is confirmed, every subsequent object reference in the requirements document is unambiguous.

**Why it works:** The architecture determination is a one-time, low-cost activity that eliminates an entire class of requirements-to-build translation errors. It also surfaces ISV package incompatibilities before the client has committed to FSC Core — not after.

---

## Example 2: Mapping the Annual Client Review Workflow to FSC Features

**Context:** A wealth management firm's advisors conduct annual reviews with every client. The current process is managed via email reminders and a spreadsheet checklist. The firm wants to standardize and automate this in FSC. The BA is gathering requirements for the review workflow.

**Problem:** The BA documents the requirement as "the system should automatically create a review task for each advisor's clients every year." This requirement is ambiguous — it does not specify the FSC mechanism, the task structure, the record association, the responsible party per task, or the trigger timing. The developer later builds a record-triggered Flow that creates a single Task record, which fails to capture the multi-step nature of the review process.

**Solution:**

The BA should use structured discovery to map the workflow step-by-step and then match each step to an FSC feature:

```
Annual Client Review — Requirements Discovery Output

Business Workflow (As-Is):
1. Operations team manually emails advisor 6 weeks before review anniversary
2. Advisor manually prepares performance report from custodian portal
3. Advisor schedules meeting with client (manual calendar invite)
4. Advisor documents meeting notes in Outlook
5. Advisor updates investment policy statement (IPS) in SharePoint
6. Operations team logs meeting as completed in spreadsheet

FSC Feature Mapping (To-Be):
1. ActionPlanTemplate: "Annual Review — Standard"
   Tasks (in order):
   a. [Auto-created, Owner: Advisor] Prepare performance summary — due: 30 days before review date
   b. [Auto-created, Owner: Advisor] Schedule client review meeting — due: 21 days before review date
   c. [Auto-created, Owner: Advisor] Send pre-meeting questionnaire — due: 14 days before review date
   d. [Auto-created, Owner: Advisor] Conduct review meeting — due: review date
   e. [Auto-created, Owner: Advisor] Document meeting notes on Account — due: 2 days after review date
   f. [Auto-created, Owner: Operations] Update IPS in Salesforce Files — due: 5 days after review date

   ActionPlan association: Account (Household record)
   Trigger: Annual — recurrence managed by Process Automation or Scheduler flow

2. AccountFinancialSummary (FSC Core) or custom rollup: performance summary data source
   → Confirm architecture: if Core, populate via FSC PSL integration user before review tasks begin.

Requirements notes:
- ActionPlanTemplate requires FSC license; confirm entitlement before scoping.
- Task recurrence at annual cadence is not a native ActionPlan feature — a separate scheduled Flow or Apex Scheduler is needed to create new ActionPlan instances each year.
- Volume: 400 advisors × 250 clients = 100,000 ActionPlan instances per year. Flag as data volume concern for architecture review.
```

**Why it works:** Mapping each step to a specific FSC feature (ActionPlan, ActionPlanTemplate, AccountFinancialSummary) gives the build team clear implementation targets. Flagging the recurrence gap prevents the developer from discovering the limitation mid-sprint. The volume calculation surfaces a potential performance risk early.

---

## Anti-Pattern: Scoping Financial Planning Features Without Confirming License Entitlement

**What practitioners do:** BAs gather requirements for FinancialPlan and FinancialGoal features, write user stories for goal-based planning workflows, and include these in the sprint backlog — without checking whether the client's FSC license tier includes the financial planning module.

**What goes wrong:** The admin begins configuration work, attempts to enable the Financial Plans and Goals feature, and discovers it requires an add-on FSC license that was not in the contract. The client must either purchase the additional license (unplanned cost) or descope the feature mid-project, causing stakeholder trust issues.

**Correct approach:** During requirements scoping, explicitly confirm the client's FSC license tier and list of enabled feature modules. Check: Setup > Company Information > Feature Licenses, and review the Salesforce order form for FSC add-ons. Document confirmed vs. unconfirmed license entitlements in the requirements package. Mark any requirements that depend on unconfirmed licenses as "pending license validation" in the fit-gap analysis.
