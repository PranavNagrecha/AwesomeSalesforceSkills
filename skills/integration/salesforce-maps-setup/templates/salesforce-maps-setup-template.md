# Salesforce Maps Setup — Work Template

Use this template when scoping a Salesforce Maps deployment. Fill it in collaboratively with the customer; archive the completed copy in the implementation folder.

---

## Scope

**Skill:** `salesforce-maps-setup`

**Customer / Org:**
**Implementation owner:**
**Target go-live date:**

**Salesforce Maps license tier (check all that apply):**
- [ ] Salesforce Maps (base)
- [ ] Salesforce Maps Advanced
- [ ] Salesforce Maps Routing
- [ ] Salesforce Maps Live Tracking

**User cohort size:** ___ reps
**Primary persona:** Outside sales / Inside sales / Service field / Other: ___

---

## Phase 0 — Discover

- [ ] License tier confirmed (matches the work plan)
- [ ] Source object(s) to plot identified:
  - [ ] Account
  - [ ] Lead
  - [ ] Opportunity
  - [ ] Case
  - [ ] Custom object: ___________
- [ ] Address-source field mapping documented per source object
- [ ] Existing geocode coverage measured (sample query: `SELECT COUNT() FROM Account WHERE Geocode__c != null`)
- [ ] Confirmed Maps is the right product (not FSL — work-order dispatch — and not Consumer Goods Cloud — retail-execution)

---

## Phase 1 — Sandbox Install

- [ ] Salesforce Maps base package installed in sandbox
- [ ] (If Advanced licensed) Salesforce Maps Advanced installed
- [ ] (If Routing licensed) Salesforce Maps Routing installed
- [ ] Post-install wizard completed for each package
- [ ] Sandbox refresh path documented (Maps may require re-config after sandbox refresh)

---

## Phase 2 — Geocoding Configuration

For each source object:

| Object | Address Fields | Real-Time Geocode | Initial Batch Run | Failure Rate |
|---|---|---|---|---|
| Account | BillingStreet, City, State, PostalCode, Country | ON / OFF |  | ___% |
|  |  |  |  |  |

- [ ] Initial batch geocode completed for all source objects
- [ ] Failure rate < 10% (acceptable) — if higher, investigate root causes (missing State, free-text Country, PO Box only)
- [ ] Geocode failure log monitoring configured (weekly review or admin alert above N% threshold)

---

## Phase 3 — Visualization Configuration

- [ ] `MapsLayer__c` definitions created:
  - [ ] Layer name: ___________ Filter: ___________
  - [ ] Layer name: ___________ Filter: ___________
- [ ] Lightning Maps component placed on:
  - [ ] App home page
  - [ ] Account record page
  - [ ] Custom tab
- [ ] Mobile use case validated (if Maps Mobile in scope)

---

## Phase 4 — Territory Plan (if Maps Advanced)

- [ ] Territory model selected: Polygon / ZIP / Hierarchical
- [ ] `MapsTerritoryPlan__c` created: ___________ (FY___)
- [ ] Polygons drawn (count: ___) or ZIP rules defined
- [ ] Assignment batch run; coverage validated (target: 99%+ Accounts assigned)
- [ ] Territory coverage report built

---

## Phase 5 — Routing (if Maps Routing)

- [ ] Routing parameters configured per cohort:
  - Max stops per day: ___
  - Service time per stop: ___ min
  - Start/end location: home / office / configurable
  - Travel mode: driving / walking
- [ ] Optimization tested with real records (sample rep's day)
- [ ] User training scheduled

---

## Phase 6 — Live Tracking (if Live Tracking licensed)

- [ ] HR/legal approval recorded; cohort regions noted
- [ ] Ping interval agreed: ___ min (longer = lower volume)
- [ ] Retention policy: hot for ___ days, archive for ___ days/years
- [ ] Big Object archival schema defined and Batch Apex archival job scheduled
- [ ] Privacy notice / consent flow (per region) deployed

---

## Phase 7 — Permission Sets

- [ ] `Salesforce Maps` PermissionSetAssignment for cohort users (count: ___)
- [ ] `Salesforce Maps Advanced` PermissionSetAssignment (if applicable)
- [ ] `Salesforce Maps Routing` PermissionSetAssignment (if applicable)
- [ ] PermissionSetGroup considered for the bundle (better long-term ergonomics)

---

## Phase 8 — Production Cutover

- [ ] Sandbox UAT signed off
- [ ] Production install (same package order as sandbox)
- [ ] Production geocoding configured (mirror of sandbox)
- [ ] Production initial batch geocode completed; failure rate matches sandbox
- [ ] Production permission-set assignments
- [ ] Day-1 training completed for cohort
- [ ] Day-7 telemetry review: log review (geocode failures), user adoption (active Maps users), support tickets

---

## Notes

Record deviations from the standard pattern and why:
