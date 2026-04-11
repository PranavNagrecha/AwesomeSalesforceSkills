# Wealth Management Requirements — Work Template

Use this template when conducting requirements discovery for an FSC wealth management implementation.

---

## Scope

**Skill:** `wealth-management-requirements`

**Engagement summary:** (describe the client, the project, and the wealth management capabilities in scope)

**Salesforce org model:** (managed package with FinServ__ namespace / FSC Core, Winter '23+, no namespace / not yet confirmed)

---

## Architecture Determination (Complete First)

Before documenting any FSC object names or workflows, confirm the architecture:

| Question | Answer |
|---|---|
| Is this a new or existing FSC org? | |
| Setup > Installed Packages: is "Financial Services Cloud" with namespace "FinServ" listed? | Yes (managed package) / No (FSC Core) / Not yet checked |
| Confirmed architecture | Managed Package / FSC Core / Pending |
| Naming convention for this project | FinServ__ prefix / No prefix |
| Third-party ISV packages in scope | (list each) |
| Each ISV package validated for FSC Core? | (list package + certification status) |

**Architecture decision rationale:** (document why managed package or FSC Core was chosen)

---

## FSC Object Scope

Check each object as in-scope or out-of-scope for this engagement. Use the confirmed API name format.

| Object | Confirmed API Name (for this org) | In Scope? | Notes |
|---|---|---|---|
| Financial Account | `FinancialAccount` / `FinServ__FinancialAccount__c` | Yes / No | Types needed: investment, deposit, insurance, loan |
| Financial Account Role | `FinancialAccountRole` / `FinServ__FinancialAccountRole__c` | Yes / No | Role types needed: |
| Financial Account Party | `FinancialAccountParty` (Core only) | Yes / No | Required if >2 owners per account |
| Financial Goal | `FinancialGoal` / `FinServ__FinancialGoal__c` | Yes / No | Goal types: retirement, education, home, other |
| Financial Plan | `FinancialPlan` / `FinServ__FinancialPlan__c` | Yes / No | License confirmed? Yes / No / Pending |
| Action Plan | `ActionPlan` | Yes / No | Which workflows? |
| Action Plan Template | `ActionPlanTemplate` | Yes / No | Templates needed: |
| Account Financial Summary | `AccountFinancialSummary` (Core only) | Yes / No | PSL integration user requirement noted? |
| Financial Holding | `FinancialHolding` / `FinServ__FinancialHolding__c` | Yes / No | Custodian feed in scope? |

---

## Volume and Frequency Data

Capture during requirements discovery. Required before architecture sign-off.

| Metric | Value | Notes |
|---|---|---|
| Number of client households | | |
| Average financial accounts per household | | |
| Maximum financial accounts per household | | |
| Number of FinancialHolding positions per account (avg) | | |
| Number of active advisors | | |
| Advisor reviews per year per client | | |
| ActionPlan instances created per year (est.) | advisors × clients × review frequency | |
| Custodian data feed frequency | | Daily / Weekly / Manual |
| Records per custodian data load (est.) | | |
| Peak concurrent users (advisors) | | |

**Volume risk flags:** (document any metrics that exceed thresholds: >100k holdings, >50k ActionPlan instances/year, >50k custodian feed records)

---

## Financial Planning Workflow (Separate from Portfolio Review)

Document the financial planning lifecycle — goal-based, client-centric.

### As-Is Process

(Describe how the firm currently manages financial planning — goals, plans, advisor involvement)

### To-Be Process (mapped to FSC features)

| Step | Salesforce Feature | FSC Object(s) | Owner | Notes |
|---|---|---|---|---|
| Client goal discovery | | FinancialGoal | Advisor | |
| Goal prioritization | | FinancialGoal | Advisor + Client | |
| Financial plan creation | | FinancialPlan + FinancialGoal | Advisor | License required |
| Annual plan review | | ActionPlan + ActionPlanTemplate | Advisor | Recurrence trigger needed |
| Life event plan update | | FinancialGoal | Advisor | Trigger: what events? |

---

## Portfolio Review Workflow (Separate from Financial Planning)

Document the portfolio review cycle — performance-based, position-centric.

### As-Is Process

(Describe how advisors currently review portfolios — custodian portals, spreadsheets, manual steps)

### To-Be Process (mapped to FSC features)

| Step | Salesforce Feature | FSC Object(s) | Owner | Notes |
|---|---|---|---|---|
| Custodian data load | Integration — see integration requirements | FinancialHolding | System | Source: |
| Portfolio analysis | CRM Analytics / Reports | FinancialHolding, AccountFinancialSummary | Advisor | |
| Review meeting prep | ActionPlan task | ActionPlan | Advisor | |
| Meeting documentation | Activity / Notes | Account | Advisor | |
| Post-meeting actions | ActionPlan task | ActionPlan | Advisor / Ops | |

---

## Advisor Tooling Requirements

User stories for advisor-facing FSC features.

### Story: [Advisor Role] — [Feature Name]

**As a** [advisor persona with Salesforce role context],
**I want** [specific FSC feature or action involving named objects/fields],
**So that** [business outcome].

**Acceptance Criteria:**
- [ ] If [condition], then [observable outcome in Salesforce] for [profile/permission set]
- [ ] If [condition], then [field/automation] behaves as: [expected]

**FSC Objects referenced:** (list objects by confirmed API name)
**Volume note:** (estimated records this story creates)
**License dependency:** (any FSC add-on required?)

---

## Integration Requirements

Document custodian data feed and other integration requirements separately.

| Integration | Source System | Direction | Format | Frequency | Fields Mapped | Error Handling |
|---|---|---|---|---|---|---|
| Custodian feed | | Inbound to SF | | | | |
| | | | | | | |

---

## Fit-Gap Analysis

| Requirement | Standard FSC Feature | Configuration | Custom Dev | Integration | Process Gap | Notes |
|---|---|---|---|---|---|---|
| | | | | | | |

**Summary:**
- Standard FSC: ___ requirements
- Configuration: ___ requirements
- Custom Development: ___ requirements
- Integration: ___ requirements
- Process Gap (stakeholder decision needed): ___ requirements

---

## Open Items and Risks

| Item | Type (Risk / Decision / Dependency) | Owner | Target Resolution Date | Status |
|---|---|---|---|---|
| ISV package FSC Core certification: [package name] | Risk | | | Pending |
| FinancialPlan license entitlement confirmation | Dependency | | | Pending |
| FSC PSL integration user setup (if AccountFinancialSummary in scope) | Dependency | | | Pending |
| Custodian data feed format and frequency confirmation | Dependency | | | Pending |

---

## Review Checklist

Run through before handing requirements to the build team.

- [ ] FSC architecture (managed package vs. FSC Core) is confirmed and documented
- [ ] All FSC object API names in requirements match the confirmed architecture (no namespace mixing)
- [ ] FinancialAccount types in scope are listed with record type implications noted
- [ ] Ownership model confirmed: two-owner (managed package) vs. unlimited via FinancialAccountParty (Core)
- [ ] Financial planning workflow and portfolio review workflow are documented separately
- [ ] ActionPlan template requirements captured: task list, owners, due date offsets, record association
- [ ] All third-party ISV packages validated for FSC Core compatibility (if Core is chosen)
- [ ] AccountFinancialSummary PSL integration user requirement noted (if in scope)
- [ ] Custodian data feed requirements documented as integration scope
- [ ] Volume data captured for all data-intensive features
- [ ] FinancialPlan license entitlement confirmed or flagged as pending
