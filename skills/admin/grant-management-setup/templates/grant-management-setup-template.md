# Grant Management Setup — Work Template

Use this template when configuring grant tracking in a Salesforce nonprofit org.
Fill in each section before beginning implementation work.

---

## Scope

**Skill:** `grant-management-setup`

**Request summary:** (describe what the org needs — e.g., "Configure multi-tranche grant disbursements for the Smith Foundation capacity-building program")

---

## Platform Path Confirmation

**Step 1: Identify installed platform**

- [ ] NPSP managed package installed? (check Setup → Installed Packages for `npsp` namespace)
  - Installed: Yes / No
- [ ] Outbound Funds Module (OFM) installed? (check for `outfunds` namespace)
  - Installed: Yes / No
- [ ] Nonprofit Cloud (NPC) licensed?
  - Licensed: Yes / No
- [ ] Nonprofit Cloud for Grantmaking separately licensed?
  - Licensed: Yes / No (check Setup → Company Information → Permission Set Licenses)

**Determined platform path:**
- [ ] NPSP + Outbound Funds Module (OFM)
- [ ] Nonprofit Cloud for Grantmaking (FundingAward / FundingDisbursement / FundingAwardRequirement)
- [ ] Undetermined — resolve before proceeding

**Note:** Do not mix guidance between platforms. OFM and NC Grantmaking are architecturally incompatible.

---

## Grant Program Requirements

Answer each question before proceeding to configuration:

| Requirement | Answer |
|---|---|
| Number of grant programs to configure | |
| Single lump-sum disbursement or multi-tranche? | Lump-sum / Multi-tranche |
| Number of tranches per award (if multi-tranche) | |
| Are deliverables / reports required per award? | Yes / No |
| Types of deliverables needed (e.g., Progress Report, Final Report, Site Visit) | |
| Will grantees access Salesforce directly (Experience Cloud portal)? | Yes / No |
| Volume: estimated number of active awards at any time | |
| Integration needed with financial system? | Yes / No / Which system: |

---

## Data Model Configuration (NC Grantmaking Path)

### FundingAward Setup

- Record Types needed: ______________________________
- Key custom fields to add: ______________________________
- Required fields on page layout: AwardAmount__c, AwardDate__c, Status, Grantee__c (Account), FundingProgram__c
- Status picklist values in use: ______________________________

### FundingDisbursement Setup

- Tranche pattern per award: ______ tranches of $______ each (or milestone-based)
- Key fields: ScheduledDate, DisbursementAmount, Status
- Status lifecycle for this org: Draft → Scheduled → Paid (standard) / customized: ______

### FundingAwardRequirement Setup

- Requirement types needed: ______________________________
- Standard status lifecycle: Open → Submitted → Approved
  - Any approved deviations from standard lifecycle: ______________________________
- Disbursement gating: Which disbursement tranches are gated by which requirement types?

| Requirement Type | Gated Disbursement Tranche |
|---|---|
| | |
| | |

---

## Data Model Configuration (OFM Path)

### Outbound Funds Module Objects

- `outfunds__Funding_Request__c` page layout fields: ______________________________
- `outfunds__Disbursement__c` payment tracking approach: ______________________________
- Relationship to Opportunity: ______________________________
- Custom objects needed for deliverable tracking (OFM has no native equivalent): ______

---

## Automation Plan

| Automation | Trigger | Action | Platform |
|---|---|---|---|
| Disbursement reminder | FundingDisbursement.ScheduledDate within 14 days | Email grants manager | NC / OFM |
| Requirements gating | FundingDisbursement Status → Paid | Check all linked requirements are Approved | NC |
| Award closure | All FundingDisbursements = Paid | Update FundingAward.Status = Closed | NC |
| Requirement submission notification | FundingAwardRequirement.Status = Submitted | Email grants manager | NC |
| ______ | ______ | ______ | |

---

## Reporting Requirements

| Report / Dashboard | Object(s) | Key Fields | Audience |
|---|---|---|---|
| Grant pipeline by program | FundingAward | AwardAmount, Status, Program | Grants Director |
| Disbursement schedule (upcoming 90 days) | FundingDisbursement | ScheduledDate, Amount, Status | Finance |
| Requirement completion rate | FundingAwardRequirement | Status, Type, DueDate | Grants Manager |
| ______ | ______ | ______ | ______ |

---

## Review Checklist

Run through these before marking implementation complete:

- [ ] Platform path (OFM vs. NC Grantmaking) confirmed and documented
- [ ] Nonprofit Cloud for Grantmaking license verified (if using NC objects)
- [ ] No OFM API names (`outfunds__`) appear in NC Grantmaking automation, and vice versa
- [ ] FundingDisbursement records created at award setup time (not retroactively)
- [ ] All expected disbursement tranches are created per FundingAward
- [ ] FundingAwardRequirement status lifecycle (Open → Submitted → Approved) is enforced by automation
- [ ] Disbursement gating validation rule tested end-to-end (cannot pay without approved requirements)
- [ ] Reports surface correct totals (no double-counting from incorrect data model choices)
- [ ] Grants staff trained on new data model and page layouts
- [ ] Platform path, customizations, and deviations documented for future administrators

---

## Notes and Deviations

Record any deviations from the standard pattern and the rationale:

- Deviation: ______________________________
  Rationale: ______________________________

- Deviation: ______________________________
  Rationale: ______________________________
