# Partner Community Requirements — Work Template

Use this template when gathering and documenting requirements for a Salesforce PRM implementation. Fill each section before handing off to the Experience Cloud configuration team.

## Scope

**Skill:** `partner-community-requirements`

**Request summary:** (describe what the business needs from the partner portal)

**In scope:**
- [ ] Deal registration
- [ ] Lead distribution
- [ ] Partner tier management
- [ ] MDF tracking
- [ ] Co-marketing asset entitlement

**Out of scope (confirm explicitly):**
- [ ] Experience Cloud site builder / technical portal configuration
- [ ] Partner account hierarchy management
- [ ] Channel Revenue Management / rebate programs

---

## License and Org Baseline

| Item | Value |
|---|---|
| Salesforce Edition | |
| Experience Cloud enabled? | Yes / No |
| Partner Community license count | |
| Partner Community Plus license count | |
| Partner Central template available? | Yes / No |
| Channel Revenue Management licensed? | Yes / No (affects MDF options) |

**License decision rationale:** (why Partner Community vs. Partner Community Plus)

---

## Partner Tier Hierarchy

| Tier Name | Tier Rank | Deal Registration | Lead Pool Access | MDF Eligible | Co-Marketing Access | Promotion Criteria |
|---|---|---|---|---|---|---|
| (e.g., Gold) | 1 | Yes | Yes | Yes — $X allocation | All categories | Annual revenue > $X |
| (e.g., Silver) | 2 | Yes | Yes | Yes — $Y allocation | Standard only | Annual revenue > $Y |
| (e.g., Bronze) | 3 | No | No | No | Basic only | Registered partner |

**Tier field location:** `Account.Tier__c` (picklist, stored on partner Account record)

**Public groups required (one per tier):**
- `PG_Gold_Partners`
- `PG_Silver_Partners`
- `PG_Bronze_Partners`

---

## Deal Registration Requirements

**Object model:** Lead-based (standard PRM) / Custom object (specify if custom)

**Deal registration entry criteria:**
- Who can submit: (e.g., Gold and Silver partners only)
- Fields required on submission: (Company, Contact, Estimated Amount, Product, Close Date)
- Status value on submission: `Submitted for Registration`

**Duplicate prevention:**
- Duplicate rule match fields: (e.g., Company [exact] + Email [exact])
- On duplicate detected: Block / Alert (specify)

**Approval chain:**

| Step | Condition | Approver | Auto-approve threshold |
|---|---|---|---|
| Step 1 | Tier = Gold AND Amount < $X | Auto-approve | $X |
| Step 2 | All others | Channel_Manager_Queue | None |

**On approval:** Flow converts Lead to Opportunity; stamps `Partner_Account__c` on Opportunity.

**On rejection:** (notification content, resubmission allowed: Yes/No)

---

## Lead Distribution Requirements

**Distribution model:** Push (assignment rules) / Pull (shared queue / lead pool)

### Push Model — Assignment Rule Criteria

| Priority | Condition | Assigned To | Notes |
|---|---|---|---|
| 1 | Tier = Gold AND State IN (West) | Gold_West_Queue | |
| 2 | Tier = Gold AND State IN (East) | Gold_East_Queue | |
| 3 | Tier = Silver AND State IN (West) | Silver_West_Pool | Pull access only |
| 4 | Default | Unassigned_Channel_Queue | Channel manager reviews |

**Tier stamping mechanism:** Cross-object formula `Lead.Partner_Tier__c = PartnerAccount__r.Tier__c` OR Flow on Lead creation

### Pull Model — Shared Pool Configuration

| Pool Name | Eligible Tiers | Territory | Sharing Rule |
|---|---|---|---|
| Silver_West_Pool | Silver | West | PG_Silver_West → Read/Write on pool leads |

---

## MDF Requirements

**MDF tracking location:** In Salesforce (custom objects) / External system / Not in scope

### If In Salesforce — Custom Object Data Model

| Object | Purpose | Key Fields |
|---|---|---|
| `MDF_Budget__c` | Annual allocation per partner | Partner_Account__c, Fiscal_Year__c, Total_Budget__c, Remaining_Budget__c |
| `MDF_Request__c` | Partner-submitted fund request | Budget__c, Amount_Requested__c, Activity_Type__c, Activity_Date__c, Status__c |
| `MDF_Claim__c` | Post-activity reimbursement claim | Request__c, Amount_Claimed__c, Proof_of_Execution__c, Status__c |

**MDF approval process:** (claim reimbursement approval chain — who approves, SLA)

---

## Co-Marketing Content Entitlement

| Content Category | Gold | Silver | Bronze | Sharing Mechanism |
|---|---|---|---|---|
| Brand assets | Yes | Yes | Yes | Public (all partners) |
| Campaign templates | Yes | Yes | No | PG_Silver_Partners + PG_Gold_Partners share |
| Sales enablement | Yes | No | No | PG_Gold_Partners share |
| Executive briefing decks | Yes | No | No | PG_Gold_Partners share |

**Content storage:** Salesforce CMS / Salesforce Files (specify)

---

## Sharing Model Summary

| Record Type | Default Access | Sharing Rule | Scope |
|---|---|---|---|
| Leads (Gold pool) | Private | PG_Gold_Partners → Read/Write | Queue-owned leads |
| Leads (Silver pool) | Private | PG_Silver_Partners → Read only | Queue-owned leads |
| MDF_Request__c | Private | Owner sharing | Partner sees own records |
| CMS Content (Gold only) | No access | PG_Gold_Partners → View | Gold content category |

---

## Open Decisions

| Decision | Owner | Target Date | Notes |
|---|---|---|---|
| (e.g., MDF in Salesforce vs external) | | | |
| (e.g., auto-approval threshold for Gold) | | | |

---

## Review Checklist

- [ ] Partner Community or Partner Community Plus licenses confirmed — Customer Community explicitly ruled out
- [ ] Partner tier hierarchy documented with names, promotion criteria, and feature access matrix
- [ ] Deal registration object model selected and duplicate rule specified
- [ ] Approval chain mapped per tier with auto-approval thresholds and rejection flow
- [ ] Lead distribution model selected (push or pull) with assignment criteria documented
- [ ] Tier stamping mechanism specified (formula field or Flow) for assignment rule eligibility
- [ ] MDF option selected (Salesforce custom objects, Channel Revenue Management, or external)
- [ ] Co-marketing asset entitlement rules defined per tier
- [ ] Sharing rule model documented — public groups identified for each tier
- [ ] `IsPartner = true` flag requirement documented in partner onboarding runbook
- [ ] Open decisions logged with owner and resolution date

---

## Notes

(Record any deviations from standard PRM patterns and the business justification)
