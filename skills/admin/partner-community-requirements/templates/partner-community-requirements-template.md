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
| `PID_Partner_Community` (member) count — from `UserLicense` | |
| `PID_Partner_Community_Login` count — from `UserLicense` | |
| Legacy `PID_STRATEGIC_PRM` / `POWER_PRM` present? | Yes / No |
| Partner Central template available? | Yes / No |
| `CommunitiesSettings.enableEnablePRM` | true / false |
| `CommunitiesSettings.enablePRMAccRelPref` | true / false |
| `CommunitiesSettings.enableRelaxPartnerAccountFieldPref` | true / false |
| `CommunitiesSettings.enableNetPortalUserReportOpts` | true / false |
| `SharingSettings.enableAccountRoleOptimization` | true / false |
| `SharingSettings.enablePartnerSuperUserAccess` | true / false |
| `SharingSettings.enablePortalUserVisibility` (support-gated to enable) | true / false |

**License decision rationale:** (member vs login per tier, and what the count is sized against)

> Read these from the target org, not from the contract. `Account.IsPartner`,
> `Lead.PartnerAccountId` and `Opportunity.PartnerAccountId` only exist when partner portal
> licences are present.

---

## Partner Tier Hierarchy

| Tier Name | Tier Rank | Licence | Role Depth (1–3) | Deal Registration | Lead Pool Access | Fund Eligible | Co-Marketing Access | Promotion Criteria |
|---|---|---|---|---|---|---|---|---|
| (e.g., Gold) | 1 | Partner Community | 3 | Yes | Yes | Yes — $X allocation | All categories | Annual revenue > $X |
| (e.g., Silver) | 2 | Partner Community | 2 | Yes | Yes | Yes — $Y allocation | Standard only | Annual revenue > $Y |
| (e.g., Bronze) | 3 | Partner Community Login | 1 | No | No | No | Basic only | Registered partner |

**Role depth is capped at 3.** `UserRole.PortalRole` is a restricted picklist — `Executive`,
`Manager`, `User`, `PersonAccount` — so a partner account stacks at most three levels.

**Tier storage decision:** standard `ChannelProgramLevel` + `ChannelProgramMember.LevelId`  /  custom
`Account.Tier__c` picklist. **Reason for the choice:** ______________________

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

**On acceptance (required step):** Lead ownership transfers to the accepting partner user.
`Lead.PartnerAccountId` and `Opportunity.PartnerAccountId` are read-only and derive from the owner —
a Flow cannot write them, so a registration that stays with the approver converts unattributed.

**On conversion:** convert with the partner user as owner so `Opportunity.PartnerAccountId` populates.

**Accepting partner user recorded on:** (name the custom field, if the business also needs a writable one)

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

## Marketing Fund (MDF) Requirements

**Fund tracking location:** Standard partner fund objects / Custom objects / External system / Not in scope

### Option A — Standard objects (evaluate this first)

| Object | Purpose | In scope? |
|---|---|---|
| `PartnerMarketingBudget` | Budget providing funds to channel partners | Yes / No |
| `PartnerFundAllocation` | Allocated funds from a budget, per channel partner | Yes / No |
| `PartnerFundRequest` | Partner-submitted request against an allocation | Yes / No |
| `PartnerFundClaim` | Post-activity reimbursement claim against a request | Yes / No |

All four are available from API version 41.0. Known restriction to check before sign-off:
`ChannelPartnerId` is not supported for formula fields, custom buttons or custom links on
`PartnerFundAllocation`, `PartnerMarketingBudget` or `PartnerFundRequest`.

**Formula / button / link requirements that touch `ChannelPartnerId`:** ______________________

### Option B — Custom object model (only with a stated reason)

**Reason the standard objects do not carry this requirement:** ______________________

| Object | Purpose | Key Fields |
|---|---|---|
| `MDF_Budget__c` | Annual allocation per partner | Partner_Account__c, Fiscal_Year__c, Total_Budget__c, Remaining_Budget__c |
| `MDF_Request__c` | Partner-submitted fund request | Budget__c, Amount_Requested__c, Activity_Type__c, Activity_Date__c, Status__c |
| `MDF_Claim__c` | Post-activity reimbursement claim | Request__c, Amount_Claimed__c, Proof_of_Execution__c, Status__c |

**Fund approval process:** (claim reimbursement approval chain — who approves, SLA)

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

One mechanism per object, from the documented set: `sharing-set`,
`partner-account-role-hierarchy`, `account-relationship-share-rule`, `sharing-rule-portal-role`,
`folder-share`, `record-ownership`, `apex-managed-sharing`, `not-exposed`. A sharing set **cannot**
target Lead.

| Object | External OWD | Mechanism | Scope | Owner |
|---|---|---|---|---|
| Lead (Gold pool) | Private | sharing-rule-portal-role or account-relationship-share-rule | Queue-owned leads | |
| Lead (Silver pool) | Private | sharing-rule-portal-role | Queue-owned leads | |
| Opportunity | Private | partner-account-role-hierarchy | Same partner account | |
| Account | Private | sharing-set (`userField` Account, `objectField` Id) | Own firm | |
| `PartnerFundRequest` | Private | account-relationship-share-rule or record-ownership | Partner sees own records | |
| CMS Content (Gold only) | n/a | folder-share / content library share | Gold content category | |
| Contract | Private | not-exposed | — | |

---

## Open Decisions

| Decision | Owner | Target Date | Notes |
|---|---|---|---|
| (e.g., MDF in Salesforce vs external) | | | |
| (e.g., auto-approval threshold for Gold) | | | |

---

## Review Checklist

- [ ] Partner licence keys read from `UserLicense` in the target org — Customer Community explicitly ruled out
- [ ] Role depth per tier is between 1 and 3
- [ ] Ownership-transfer (acceptance) step present between approval and conversion
- [ ] Partner tier hierarchy documented with names, promotion criteria, and feature access matrix
- [ ] Deal registration object model selected and duplicate rule specified
- [ ] Approval chain mapped per tier with auto-approval thresholds and rejection flow
- [ ] Lead distribution model selected (push or pull) with assignment criteria documented
- [ ] Tier stamping mechanism specified (formula field or Flow) for assignment rule eligibility
- [ ] Fund option selected: standard partner fund objects, custom (with reason), or external
- [ ] Every exposed object has one mechanism from the documented set — none is a sharing set on Lead
- [ ] Offboarding sequenced reassign → deactivate → group/queue → permission sets → `IsPartner` last
- [ ] `partner-portal-design.yaml` written and `scripts/check_partner_community_requirements.py` exits 0
- [ ] Co-marketing asset entitlement rules defined per tier
- [ ] Sharing rule model documented — public groups identified for each tier
- [ ] `IsPartner = true` flag requirement documented in partner onboarding runbook
- [ ] Open decisions logged with owner and resolution date

---

## Notes

(Record any deviations from standard PRM patterns and the business justification)
