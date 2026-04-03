# Examples — Requirements Gathering for Salesforce

## Example 1: Lead Management Requirements for a Sales Team Migration

**Context:** A company is migrating from a spreadsheet-based lead tracking process to Salesforce Sales Cloud. The BA is conducting discovery with the inside sales team lead.

**Problem:** Without structured requirements, the admin builds a generic Lead layout. Sales reps complain they cannot see the "Industry Vertical" and "Competitor" fields they always tracked in the spreadsheet. Managers cannot see the pipeline report they used for weekly reviews. Adoption drops because the tool does not match how the team works.

**Solution:**

Discovery interview surfaces:
- Reps track 8 fields not in standard Salesforce Lead: Industry Vertical, Competitor, Annual Contract Value, Decision Maker Name, Decision Timeline, Next Step, Last Contact Method, Source Campaign
- Reps need the "Last Contact Method" field to be required when updating a lead — they currently miss it
- Managers need a weekly "Leads by Rep by Stage" report filtered by their team's region
- Integration with the marketing automation platform sends new leads via API — these must run assignment rules automatically

The resulting user stories:

```
Story 1:
As a sales rep (with Standard User profile + Sales permission set),
I want to see and edit Lead Vertical, Competitor, and ACV on the Lead record page,
So that I can track qualification context without switching to a spreadsheet.

Acceptance Criteria:
- [ ] Three custom fields exist on Lead: Industry_Vertical__c (picklist), Competitor__c (text), ACV__c (currency)
- [ ] All three fields are visible and editable on the Lead page layout for Standard User profile
- [ ] All three fields appear in the Lead list view "My Open Leads"

Story 2:
As a sales rep updating a lead's stage,
I want Last_Contact_Method__c to be required when Lead Status = "Contacted",
So that we capture contact data consistently for reporting.

Acceptance Criteria:
- [ ] Validation rule fires if Last_Contact_Method__c is blank and Lead Status = "Contacted"
- [ ] Error message reads: "Please enter the last contact method before updating this lead"
- [ ] Rule is bypassed for System Administrator profile (for data imports)
```

**Why it works:** By mapping each current-state spreadsheet column to a specific Salesforce field and attaching acceptance criteria to each story, the BA eliminates ambiguity before the build starts. The integration requirement (API-created leads must run assignment rules) is captured explicitly, preventing the silent failure where API leads land with no owner.

---

## Example 2: Fit-Gap Analysis for a Case Management Enhancement

**Context:** A service team wants to add SLA tracking to their existing Salesforce Case setup. The BA conducts a fit-gap workshop before sprint planning.

**Problem:** Without a fit-gap analysis, the team assumes all requirements are Salesforce configuration work. Two sprints in, the dev team discovers that the "customer tier" SLA field lives in an external billing system, not Salesforce — requiring an integration that was never scoped. The sprint is blocked.

**Solution:**

The fit-gap table produced in the workshop:

| Requirement | Salesforce Capability | Fit Type | Notes |
|---|---|---|---|
| Track case priority (High/Medium/Low) | Standard Case Priority picklist | Standard Fit | Available OOTB |
| Auto-escalate case after 4 hours if unresolved | Escalation Rules with business hours | Configuration Gap | Admin config, no code |
| Show SLA countdown timer on agent console | Entitlements and Milestones | Configuration Gap | Admin config, no code |
| Set SLA tier based on customer contract level | Contract__c field on Account | Configuration Gap | Requires custom field + formula |
| Pull customer tier from billing system | No native connector exists | Customization Gap | Requires API integration |
| Notify VP of Support if a P1 case ages past 8 hours | Escalation Rule + email alert | Configuration Gap | Admin config |
| Dashboard showing SLA breach rate by team | Standard Reports + Dashboard | Configuration Gap | Admin config |

The integration requirement is surfaced in the workshop, not mid-sprint. The team scopes the integration separately, with appropriate effort.

**Why it works:** A fit-gap analysis forces explicit classification of every requirement before any build work starts. Requirements that have no native Salesforce solution are surfaced as decisions for the business — not as surprises for the development team.

---

## Anti-Pattern: Gathering Requirements Only from the Project Sponsor

**What practitioners do:** The BA schedules one meeting with the VP of Sales, collects high-level requirements, and begins writing user stories based on that single session.

**What goes wrong:** The VP describes the reporting and forecast visibility they want. They do not describe what a sales rep sees when they open a lead record, what fields they need to enter, or what error messages they encounter. The resulting build optimizes for manager reporting and ignores rep workflow. Adoption drops — reps continue using email and spreadsheets, and the reports the VP needs are never populated accurately because reps don't enter data into the tool.

**Correct approach:** Interview the actual end users doing the daily work. Observe them performing their current process if possible. Interview the manager separately to capture reporting and oversight requirements. Reconcile the two perspectives explicitly in the requirements document. Tag each story with its primary persona so the build team knows whose workflow it supports.
