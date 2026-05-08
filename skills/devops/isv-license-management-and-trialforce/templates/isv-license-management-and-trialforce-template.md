# ISV License Management and Trialforce — Work Template

Use this template when designing or auditing the LMA, Trialforce, Feature Parameter, or AppExchange Checkout surface of a managed package.

## Scope

**Skill:** `isv-license-management-and-trialforce`

**Request summary:** (fill in what the user asked for — e.g. "register v3.0 of AnalyticsPro with the LMA", "add a SubscriberToLmo FP for forecast usage", "set up Trialforce for a CRM-overlay package")

## Org Inventory

Label every relevant org explicitly. Half of all ISV-licensing tickets resolve once this is filled in correctly.

| Role | Org Name | Org ID | Edition | Owner |
|---|---|---|---|---|
| Partner Business Org (PBO) | | | | |
| License Management Org (LMO) | | | | |
| Trialforce Management Org (TMO) | | | | |
| Trialforce Source Org (TSO) | | | | |
| Packaging org (1GP) / DX hub (2GP) | | | | |
| Test subscriber org | | | | |

## Package Context

- [ ] Generation: 1GP managed / 2GP managed / unlocked
- [ ] Namespace: `____________________`
- [ ] Package version under discussion: `04t...`
- [ ] Released or beta: ____________
- [ ] Currently registered with LMA: yes / no
- [ ] AppExchange Checkout in scope: yes / no

## LMA Wiring Checklist

- [ ] LMA managed package installed in LMO
- [ ] `sfLma__Package__c` record exists for every released version
- [ ] Default License Type set (not blank)
- [ ] Default Seats set (not blank)
- [ ] Default Expiration set (for trial-mode packages)
- [ ] Test install creates `sfLma__License__c` row within 5 minutes
- [ ] Suspension-monitoring scheduled job is wired in the LMO
- [ ] Subscriber Support Console configured (for managed-package debug access)

## Trialforce Inventory (if applicable)

| Template ID | Source TSO | Edition | Approval status | Last refresh date | Used by listing? |
|---|---|---|---|---|---|
| | | | | | |

## Feature Parameter Inventory

| FP name | Type | Direction | Default | Reader location | Operational owner | Notes |
|---|---|---|---|---|---|---|
| | | | | | | |

Validate each row:
- [ ] Direction is `LmoToSubscriber` or `SubscriberToLmo` (exact spelling)
- [ ] Default value is set (not blank)
- [ ] Reader Apex passes namespace as first argument to `checkPackage*Value`
- [ ] Set/check pair is not in the same transaction (no synchronous-FP assumption)
- [ ] FP is not used as an authorization decision (only as configuration)

## Approach

Which pattern from SKILL.md applies?

- [ ] Pattern 1 — Register-then-track LMA wiring
- [ ] Pattern 2 — Trialforce template lifecycle
- [ ] Pattern 3 — LmoToSubscriber Feature Parameter for one-customer feature flip
- [ ] Other (describe):

## Decisions

| Choice | Selected | Reasoning |
|---|---|---|
| LMA in PBO vs dedicated LMO | | |
| TMO with branding vs Environment Hub TSO | | |
| FP direction (LmoToSubscriber / SubscriberToLmo) | | |
| Trial method (AppExchange listing / SignupRequest API / free install) | | |
| AppExchange Checkout vs partner-owned billing | | |

## Review Checklist

Copy from SKILL.md and tick items as completed.

- [ ] Org roles labeled and not conflated
- [ ] LMA registered for every released version
- [ ] Default License Type and Seats set on every package row
- [ ] FPs have confirmed readers (no zombies)
- [ ] Beta versions not relied on for SubscriberToLmo testing
- [ ] Trialforce templates re-snapshotted after UX-changing releases
- [ ] License-suspension monitoring wired
- [ ] Checkout renewal-event handler verified end-to-end (if used)
- [ ] FP propagation latency documented; no transactional gates on just-flipped FPs

## Notes / Deviations

(Record any deviations from the standard pattern and why.)
