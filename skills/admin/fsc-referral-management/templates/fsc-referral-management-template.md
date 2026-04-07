# FSC Referral Management — Work Template

Use this template when working on FSC Referral Management tasks. Fill in each section before beginning implementation work.

## Scope

**Skill:** `fsc-referral-management`

**Request summary:** (describe what the user or project requires — e.g. "Add referral type for Small Business Lending" or "Fix referral routing for Mortgage queue")

---

## Context Gathered

Answer these before proceeding:

- **FSC Referral Management enabled?** (Setup > Financial Services Cloud Settings > Referral Management toggle): Yes / No
- **Referral types in scope:** (list each Lead record type developer name that will be used as a referral type)
- **Partner referrals via Experience Cloud?** Yes / No — if yes, Referrer Score visibility must be validated
- **Einstein Referral Scoring referenced anywhere?** Yes / No — if yes, flag for removal (feature is retiring)
- **Known constraints:** (e.g. sandbox-only deployment window, change freeze, specific queue names required)

---

## ReferralRecordTypeMapping Audit

List each referral type and its metadata status:

| Referral Type (Lead RT Dev Name) | ReferralRecordTypeMapping Entry Exists? | Active? | Target Queue |
|---|---|---|---|
| (e.g. MortgageReferral) | Yes / No | Yes / No | (queue name) |
| (e.g. WealthManagementReferral) | Yes / No | Yes / No | (queue name) |
| (add rows as needed) | | | |

**Action items from audit:** (list any missing or inactive entries that must be created/activated)

---

## Expressed Interest Picklist Audit

List each Expressed Interest value required for routing and confirm it exists in the Lead field metadata:

| Expressed Interest Value (API) | Exists in Picklist? | Assignment Rule Entry Exists? | Routes To |
|---|---|---|---|
| (e.g. Home Loan) | Yes / No | Yes / No | (queue name) |
| (e.g. Retirement Planning) | Yes / No | Yes / No | (queue name) |
| (add rows as needed) | | | |

**Action items:** (list missing picklist values or rule entries)

---

## Partner Referral Visibility (if applicable)

Complete this section only if Experience Cloud partner referrals are in scope.

- **ReferrerScore__c on Experience Builder page layout?** Yes / No
- **FLS for ReferrerScore__c — Community Profile — Read access?** Yes / No
- **ReferredBy__c resolves to Contact for partner referrals?** Yes / No (expected: Yes)
- **Test partner login verified score is visible?** Yes / No

---

## Approach

Which pattern from SKILL.md applies?

- [ ] Registering a New Referral Type End-to-End
- [ ] Enabling Partner Referrer Score Visibility in Experience Cloud
- [ ] Other: (describe)

**Why this pattern:** (brief explanation)

**Deployment sequence:**
1. (e.g. Deploy Expressed Interest picklist values)
2. (e.g. Deploy ReferralRecordTypeMapping__mdt records)
3. (e.g. Update Lead Assignment Rules in target org)
4. (e.g. Update Experience Builder page layout)

---

## Checklist

Copy from SKILL.md Review Checklist and track progress:

- [ ] Every active referral type has a corresponding active ReferralRecordTypeMapping__mdt entry
- [ ] Every Expressed Interest picklist value used in routing exists in Lead field metadata
- [ ] Lead Assignment Rules cover all active referral types with no routing gaps
- [ ] ReferrerScore__c is visible on Experience Cloud pages (if partner referrals in scope)
- [ ] Einstein Referral Scoring is NOT referenced in any new configuration or documentation
- [ ] Test referrals for each type result in correct queue assignment (verified via Lead Assignment Log)
- [ ] FLS for all 11 referral custom fields is correctly set for all relevant profiles

---

## Test Results

Record the outcome of end-to-end routing tests here:

| Referral Type | Expressed Interest Value | Expected Queue | Actual Queue | Pass/Fail |
|---|---|---|---|---|
| (e.g. MortgageReferral) | (e.g. Home Loan) | (e.g. Mortgage Queue) | | |
| (add rows per test case) | | | | |

---

## Notes

Record any deviations from the standard pattern, workarounds applied, or open questions:

- (e.g. Sandbox Lead Assignment Rules cannot be deployed as metadata — must be manually configured in production)
- (e.g. ReferredBy__c FLS was already set correctly; only layout change was needed)
