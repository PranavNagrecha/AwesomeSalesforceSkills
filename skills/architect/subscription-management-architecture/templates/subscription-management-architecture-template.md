# Subscription Management Architecture — Work Template

Use this template when designing, reviewing, or troubleshooting Salesforce CPQ subscription lifecycle architecture.

## Scope

**Skill:** `subscription-management-architecture`

**Request summary:** (describe what the user asked for — e.g., "Design amendment flow for enterprise contracts with 2,000+ subscription lines")

---

## Context Gathered

Answer these before starting. Refer to SKILL.md → Before Starting for guidance.

- **CPQ package version:** (e.g., 240.x — check Setup > Installed Packages > Salesforce CPQ)
- **Approximate SBQQ__Subscription__c record count on affected contracts:** (< 200 / 200–1,000 / 1,000+)
- **Amendment service mode decision:** [ ] Legacy synchronous  [ ] Large-Scale async  [ ] TBD
- **Bundle products on contracts:** [ ] Yes — Preserve Bundle Structure setting:  [ ] No bundles
- **Combine Subscription Quantities enabled:** [ ] Yes  [ ] No  [ ] Unknown
- **Salesforce Billing installed:** [ ] Yes (blng__BillingSchedule__c expected)  [ ] No
- **Renewal model:** [ ] Auto-renew (both flags true)  [ ] Forecast only (RenewalForecast=true, RenewalQuoted=false)  [ ] Manual
- **Co-termination strategy:** (earliest-end / fixed anchor date / not yet defined)

---

## Amendment Design

### Service Mode Selection

| Factor | Value | Implication |
|---|---|---|
| Subscription line count | | |
| Trigger complexity on SBQQ__Subscription__c | | |
| Async job monitoring infrastructure available | | |
| Billing integration timing requirement | | |

**Selected mode:** [ ] Legacy  [ ] Large-Scale async

**Rationale:** (explain why)

### Downstream Consumers of SBQQ__Subscription__c

List all integrations, reports, triggers, and Flows that read subscription data. Verify each uses aggregation, not single-record lookup.

| Consumer | Current Query Pattern | Aggregation-Safe? | Action Required |
|---|---|---|---|
| (e.g., ERP integration) | (e.g., ORDER BY CreatedDate DESC LIMIT 1) | No | Rewrite to SUM aggregation |
| | | | |

---

## Price Change Design (if applicable)

**Is a mid-contract price change required?** [ ] Yes  [ ] No

If Yes — use the swap pattern:
- [ ] Identify existing subscription line to zero out
- [ ] Confirm "Allow Price Override" is enabled on the product (or Price Rule will enforce new price)
- [ ] Plan credit memo handling for zeroed-out line in billing system
- [ ] Plan new invoice handling for replacement line in billing system

---

## Co-termination Design

**Co-termination anchor date:** ____________________

**Write-once field audit:**

- [ ] SBQQ__SubscriptionStartDate__c — no Flow, trigger, or process writes this post-activation
- [ ] SBQQ__CoTerminationDate__c — no Flow, trigger, or process writes this post-activation
- [ ] Validation rules in place to prevent edits after Contract.Status = 'Activated'

---

## Renewal Automation Configuration

**SBQQ__RenewalForecast__c:** [ ] true  [ ] false
**SBQQ__RenewalQuoted__c:** [ ] true  [ ] false

**Rationale for setting combination:** (e.g., "Enterprise accounts — deferred quoting to prevent price lock")

**Contracted prices required for renewal?** [ ] Yes — SBQQ__ContractedPrice__c records created for: _______  [ ] No

---

## Billing Integration Sequencing (if Salesforce Billing installed)

**Activation sequence documented?** [ ] Yes  [ ] No

Sequence:
1. [ ] CPQ processes amendment/renewal quote
2. [ ] SBQQ__Subscription__c delta records fully written
3. [ ] (If Large-Scale async) AsyncApexJob for SBQQ.AmendmentBatchJob = 'Completed'
4. [ ] Contract Status set to 'Activated'
5. [ ] blng__BillingSchedule__c records generated

**Async monitoring mechanism:** (platform event / scheduled Apex poll / manual check)

---

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] Amendment service mode (Legacy vs Large-Scale) documented and validated against subscription line count
- [ ] All downstream consumers of SBQQ__Subscription__c verified to aggregate delta records
- [ ] Preserve Bundle Structure and Combine Subscription Quantities confirmed NOT both enabled
- [ ] Co-termination start dates confirmed write-once; no automation modifies them post-activation
- [ ] SBQQ__RenewalForecast__c and SBQQ__RenewalQuoted__c set consistently with renewal model
- [ ] If Salesforce Billing: Contract activation sequence confirmed to fire after CPQ subscription write completes
- [ ] For Large-Scale async amendments: AsyncApexJob monitoring in place

---

## Validation Commands

```bash
# Run the subscription architecture checker against retrieved metadata
python3 skills/architect/subscription-management-architecture/scripts/check_subscription_arch.py \
  --manifest-dir force-app/main/default

# Search local knowledge for related guidance
python3 scripts/search_knowledge.py "CPQ subscription amendment renewal architecture"
```

---

## Notes

Record any deviations from the standard patterns documented in SKILL.md and the reason for the deviation.
