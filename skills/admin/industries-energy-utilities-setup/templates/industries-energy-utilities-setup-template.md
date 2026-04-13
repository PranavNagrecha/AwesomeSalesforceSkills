# Industries Energy Utilities Setup — Work Template

Use this template when working on an E&U Cloud setup task. Fill in each section before beginning configuration work.

## Scope

**Skill:** `industries-energy-utilities-setup`

**Request summary:** (fill in what the user asked for — e.g., "configure ServicePoints and rate plans for a new regulated electricity utility org")

---

## Pre-Flight Context

Answer these before starting any configuration:

- **E&U Cloud license confirmed?** [ ] Yes — verified in Setup > Installed Packages
- **Market type:** [ ] Regulated utility  [ ] Competitive/deregulated market
- **Service types in scope:** [ ] Electricity  [ ] Gas  [ ] Water  [ ] Other: ________
- **CIS/billing system vendor and integration type:**
- **RatePlan sync confirmed (SOQL verified)?** [ ] Yes — record count: ____  [ ] No — integration not yet operational
- **Known constraints or regulatory requirements:**

---

## Approach

Which pattern from SKILL.md applies?

- [ ] New customer ServicePoint provisioning (Example 1 pattern)
- [ ] Rate plan change via service order (Example 2 pattern)
- [ ] Other: ________

**Reason this pattern applies:**

---

## Setup Sequence Checklist

Work through these in order. Do not skip steps.

### Phase 1 — License and Permissions

- [ ] E&U Cloud managed package confirmed installed (Setup > Installed Packages)
- [ ] E&U Cloud permission set license assigned to all relevant users
- [ ] E&U Cloud managed package feature permission sets assigned (Standard User / Admin)
- [ ] Validated: ServicePoint object accessible in Object Manager for a test user

### Phase 2 — CIS Integration Validation

- [ ] CIS/billing integration confirmed operational
- [ ] RatePlan records present in Salesforce — SOQL result:
  ```
  SELECT Id, Name, RatePlanCode__c, ServiceType__c, MarketSegment__c FROM RatePlan
  ```
  Record count: ____ (must match expected tariff class count from CIS)
- [ ] If record count is zero or mismatched — STOP. Do not proceed to Phase 3 until resolved.

### Phase 3 — ServicePoint and Meter Configuration

- [ ] Market segment picklist values on ServicePoint configured to match CIS tariff classes
- [ ] OWD sharing settings reviewed for ServicePoint, Meter, ServiceContract, RatePlan
- [ ] ServicePoint records created with:
  - [ ] AccountId linked to customer Account
  - [ ] ServiceType set (Electricity / Gas / Water)
  - [ ] MarketSegment set (matches CIS tariff class)
  - [ ] Status = Active
  - [ ] Address fields populated
- [ ] Meter records created for each ServicePoint with:
  - [ ] ServicePointId linked to parent ServicePoint
  - [ ] MeterType set (AMI / AMR / Analog)
  - [ ] Status = Active
  - [ ] InstallDate populated

### Phase 4 — ServiceContract Configuration

- [ ] For each ServicePoint, ServiceContract created with:
  - [ ] AccountId linked to customer Account
  - [ ] ServicePointId linked to ServicePoint
  - [ ] RatePlanId linked to CIS-synchronized RatePlan (non-null)
  - [ ] StartDate populated
  - [ ] Status = Active (confirmed after save — not just Draft)
- [ ] Any ServiceContracts in Draft status investigated and resolved

### Phase 5 — Service Order Workflow Testing

- [ ] Service order workflow tested in sandbox for: Connect
- [ ] Service order workflow tested in sandbox for: Disconnect
- [ ] Service order workflow tested in sandbox for: Rate Change
- [ ] CIS notification confirmed for each service order type
- [ ] ServiceContract updates confirmed after service order completion

---

## Market Type Configuration Notes

**For regulated market:**
- MarketSegment values must match legally mandated tariff classes from CIS
- Rate plan assignment is automatic — do not expose customer-facing plan selection
- Rate plan changes require a service order (may require regulatory approval)
- Document: which tariff classes are in scope and their CIS codes

**For competitive market:**
- ServicePoint requires: retailer identifier and DSO identifier fields populated
- Rate plan assignment is customer-driven — confirm selection UI or process
- Rate plan changes are initiated by customer request via retailer change service order
- Document: retailer and DSO identifiers in scope

---

## Deviations from Standard Pattern

Record any deviations from the standard setup sequence and the reason for each:

| Deviation | Reason | Risk |
|---|---|---|
| (fill in) | (fill in) | (fill in) |

---

## Sign-Off

- [ ] All Phase 1–5 checklist items completed
- [ ] No ServiceContracts in Draft status with null RatePlanId
- [ ] Service order workflows tested and confirmed operational in sandbox
- [ ] Market type configuration documented and confirmed
- [ ] Reviewed against references/gotchas.md — no known gotchas unmitigated
