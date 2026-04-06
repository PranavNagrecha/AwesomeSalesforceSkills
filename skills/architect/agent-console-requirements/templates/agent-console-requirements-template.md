# Agent Console Requirements — Work Template

Use this template when gathering and documenting requirements for a Lightning Service Console deployment.

## Scope

**Skill:** `agent-console-requirements`

**Request summary:** (fill in what the stakeholder asked for — e.g., "Design the agent console for our 40-person Tier-1 support team handling email and chat cases")

---

## Context Gathered

Answer these before proceeding:

- **Salesforce licenses confirmed:** (Service Cloud User / Service Cloud Einstein — count: ___)
- **Omni-Channel licensed and active?** (Yes / No / In scope for this project?)
- **Telephony integration:** (None / Open CTI — adapter name: ___ / Service Cloud Voice)
- **Number of support tiers sharing this console:** ___
- **Case record types in scope:** (list each record type and the team that handles it)
- **Expected cases per agent per day:** ___
- **Maximum simultaneous open cases per agent:** ___
- **Knowledge in use?** (Yes / No — affects Knowledge Accordion placement)

---

## Agent Workflow Mapping

For each support tier, document the typical case lifecycle from queue pickup to resolution:

**Tier: ___**

1. Agent picks up case from: (queue name / split-view list view)
2. First action: (review case details / call customer / send acknowledgment email)
3. Typical lookups during case work: (Account / Contact / Asset / Other)
4. Most frequent repeated actions (top 5):
   - ___
   - ___
   - ___
   - ___
   - ___
5. Resolution action: (status update / email / close case / escalate)

---

## Page Template Selection

For each case record type:

| Record Type | Page Template | Highlights Panel Fields | Right Sidebar Component | Notes |
|---|---|---|---|---|
| ___ | Pinned Header | Case Number, Status, Priority, Subject, ___ | Knowledge Accordion / None | ___ |
| ___ | Pinned Header | ___ | ___ | ___ |

---

## Subtab Objects

Objects that should open as subtabs under a Case primary tab:

- [ ] Account
- [ ] Contact
- [ ] Asset
- [ ] (Custom object): ___
- [ ] (Custom object): ___

---

## Utility Bar Specification

| Component | Required? | Justification | Notes |
|---|---|---|---|
| Omni-Channel | Yes / No | Agents accept routed work | Only if Omni-Channel licensed |
| History | Yes | Return to closed tabs | — |
| Macros | Yes | Macro runner access | Requires Run Macros perm set |
| Open CTI Softphone | Yes / No | Phone integration | Only if CTI adapter installed |
| Notes | Yes / No | Cross-case note-taking | — |
| ___ | ___ | ___ | ___ |

**Total components:** ___ (cap at 6-8 for performance)

---

## Macro Catalog

For each candidate macro, fill in the details:

| # | Macro Name | Trigger Scenario | Steps (in order) | Record Types | Sharing Scope |
|---|---|---|---|---|---|
| 1 | ___ | ___ | 1. ___ 2. ___ 3. ___ | ___ | All agents / Profile: ___ |
| 2 | ___ | ___ | 1. ___ 2. ___ | ___ | All agents |
| 3 | ___ | ___ | 1. ___ 2. ___ 3. ___ | ___ | ___ |
| 4 | ___ | ___ | 1. ___ 2. ___ | ___ | ___ |
| 5 | ___ | ___ | 1. ___ 2. ___ 3. ___ | ___ | ___ |
| 6 | ___ | ___ | ___ | ___ | ___ |
| 7 | ___ | ___ | ___ | ___ | ___ |
| 8 | ___ | ___ | ___ | ___ | ___ |
| 9 | ___ | ___ | ___ | ___ | ___ |
| 10 | ___ | ___ | ___ | ___ | ___ |

**Macros requiring conditional logic (route to Flow):**
- ___

---

## Split-View List View Definitions

For each agent tier, define the default list view in the split-view panel:

**Tier / Queue: ___**
- Object: Case
- Filter: Status != Closed AND RecordType = ___ AND ___
- Sort: ___ (ascending / descending)
- Key fields to display: Case Number, Status, Priority, Subject, Created Date
- Expected max records in this view: ___ (must be < 200)

---

## License and Permission Matrix

| Role / Team | Salesforce License | Console App Perm Set | Run Macros Perm Set | Manage Macros Perm Set | CTI Call Center Assignment |
|---|---|---|---|---|---|
| Tier-1 Agent | Service Cloud User | Agent Console Access | Yes | No | Yes / No |
| Tier-2 Agent | Service Cloud User | Agent Console Access | Yes | No | No |
| Team Lead | Service Cloud User | Agent Console Access | Yes | Yes | Yes / No |
| Admin | Sys Admin | N/A (full access) | Yes | Yes | As needed |

---

## Review Checklist

- [ ] Every agent role has a confirmed Service Cloud User license
- [ ] Omni-Channel widget included in utility bar if Omni-Channel is licensed
- [ ] Open CTI prerequisites confirmed before including Softphone component
- [ ] All case page layouts use Pinned Header template with Highlights Panel in header region
- [ ] Knowledge Accordion included in right sidebar for knowledge-intensive record types
- [ ] Utility bar capped at 6-8 components
- [ ] Primary tab and subtab objects explicitly defined
- [ ] Split-view list view filters prevent 200-record overflow
- [ ] Macro catalog has at least 10 candidates with full step definitions
- [ ] Run Macros and Manage Macros permission set assignments documented
- [ ] Console requirements document reviewed by lead admin before build begins

---

## Notes

Record any deviations from the standard pattern, open questions, or decisions deferred to the admin:

- ___
