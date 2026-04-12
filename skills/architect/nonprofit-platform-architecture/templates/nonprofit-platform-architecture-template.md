# Nonprofit Platform Architecture — Work Template

Use this template when designing or evaluating the end-to-end platform architecture for a Nonprofit Cloud (Agentforce Nonprofit) implementation.

---

## Scope

**Skill:** `nonprofit-platform-architecture`

**Organization name:** ___________________________

**Request summary:** (fill in what the user asked for — e.g., "design module adoption strategy," "review proposed architecture," "advise on phasing")

---

## Platform Foundation Confirmation

Before proceeding with any architecture work, confirm:

- **Platform type:** [ ] Nonprofit Cloud (native, NPC) [ ] NPSP (managed package) — if NPSP, use `npsp-vs-nonprofit-cloud-decision` skill first
- **Person Accounts enabled:** [ ] Yes (confirmed in Setup > Account Settings) [ ] No — must be enabled before module configuration
- **Person Accounts enabled in sandbox first:** [ ] Yes [ ] No — required before production enablement
- **NPC org provisioned (not NPSP):** [ ] Yes [ ] No
- **API version of existing integrations:** _________________ (must be 59.0+ for Fundraising Connect API)

---

## Licensed Modules Inventory

Mark each module's status:

| Module | Licensed | In Scope (This Phase) | Deferred (Future Phase) | Out of Scope |
|---|---|---|---|---|
| Fundraising | [ ] | [ ] | [ ] | [ ] |
| Program and Case Management | [ ] | [ ] | [ ] | [ ] |
| Outcome Management | [ ] | [ ] | [ ] | [ ] |
| Volunteer Management | [ ] | [ ] | [ ] | [ ] |
| Grantmaking | [ ] | [ ] | [ ] | [ ] |
| AI / Agentforce Agents | [ ] | [ ] | [ ] | [ ] |
| Data Cloud (Agentforce prerequisite) | [ ] | [ ] | [ ] | [ ] |

**Rationale for in-scope decisions:**

- Fundraising:
- Program and Case Management:
- Outcome Management:
- Volunteer Management:
- Grantmaking:
- AI / Agentforce:

---

## Person Account Data Model Design

| Decision | Answer |
|---|---|
| Primary constituent record type(s) | |
| Record type for individual constituents | |
| Record type for organizational constituents | |
| Constituent deduplication strategy (matching rules) | |
| Who can create constituent records | |
| Who can merge duplicate constituent records | |
| Integration compatibility confirmed for Person Accounts | |

**Cross-module constituent role notes:**
(e.g., "The same Person Account will serve as donor in Fundraising AND program participant in Program Management — confirmed no record type conflicts")

---

## Cross-Module Data Model Dependency Map

Document how key SIDM objects link across modules:

| Object | Module | Links To | Dependency Type |
|---|---|---|---|
| Person Account | All modules | Fundraising: Donor; Program: Participant; Volunteer: Shift Worker | Foundation |
| Gift Transaction | Fundraising | Designation, Gift Commitment | Fundraising internal |
| Benefit Assignment | Program Management | Person Account, Benefit | Cross-module to constituent |
| Volunteer Shift Worker | Volunteer Management | Person Account, Volunteer Shift | Cross-module to constituent |
| Outcome Result | Outcome Management | Program Cohort, Indicator | Cross-module to Program |
| Funding Request | Grantmaking | Account (external org), Funding Opportunity | Grantmaking internal |
| (add rows as needed) | | | |

---

## Integration Architecture

| System | Integration Type | NPC Module | Direction | API Version / Pattern |
|---|---|---|---|---|
| Payment Processor (name: ________) | REST / Connect API | Fundraising | Inbound (payments to NPC) | v59.0+ Connect API |
| Marketing Automation (name: ________) | | | | |
| ERP / Finance System (name: ________) | | | | |
| External Volunteer Platform (if any) | | | | |
| Data Cloud (if AI/Agentforce in scope) | | | | |
| (add rows as needed) | | | | |

**Integration notes:**
- Payment processor routes through Fundraising Connect API (v59.0+): [ ] Confirmed
- No integration uses direct DML on Gift Transaction objects: [ ] Confirmed

---

## Phased Implementation Roadmap

### Phase 1

**Modules in scope:** ___________________________

**Duration:** ___ weeks / months

**Phase entry criteria (must be true before Phase 1 begins):**
- [ ] Person Accounts enabled and validated in sandbox
- [ ] Constituent data loaded and deduplicated
- [ ] ___________________________

**Phase exit criteria (must be true before Phase 2 begins):**
- [ ] Gift transactions processing successfully via Connect API
- [ ] Finance reconciliation process validated
- [ ] ___________________________

---

### Phase 2

**Modules in scope:** ___________________________

**Duration:** ___ weeks / months

**Phase entry criteria:**
- [ ] Phase 1 exit criteria met
- [ ] ___________________________

**Phase exit criteria:**
- [ ] ___________________________

---

### Phase 3 (if applicable)

**Modules in scope:** ___________________________

**Duration:** ___ weeks / months

**Phase entry criteria:**
- [ ] ___________________________

---

## Risk Register

| Risk | Module(s) Affected | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| Person Account enablement error in production before sandbox validation | All | Medium | High | Enable in sandbox first; document decision record |
| No in-place upgrade path from NPSP — timeline underestimated | All | High (if NPSP) | High | Scope as net-new org + full data migration project |
| Volunteer Management scoped as 3 weeks without 19-object review | Volunteer | High | Medium | Conduct object-level scoping before committing timeline |
| Agentforce agents licensed without Data Cloud | AI/Agentforce | Medium | High | Confirm Data Cloud in contract before AI module scoping |
| Payment processor targets API version < 59.0 | Fundraising | Medium | High | Verify API version in integration spec |
| Grantmaking licensed for grant-receiving org | Grantmaking | Low | Medium | Confirm direction of grant flow in requirements |
| (add rows as needed) | | | | |

---

## Architecture Review Checklist

Run through these before marking architecture work complete:

- [ ] Platform confirmed as Nonprofit Cloud (native) — not NPSP
- [ ] Person Accounts confirmed enabled; record type strategy documented
- [ ] All licensed NPC modules inventoried; module adoption map produced
- [ ] Cross-module data model dependencies documented
- [ ] Fundraising Connect API version (59.0+) specified for all integrations
- [ ] Payment processor integration routes through Connect API, not direct DML
- [ ] Grantmaking module correctly scoped (grant-givers only, not grant-receivers)
- [ ] Volunteer Management scoped as 19-object domain with adequate timeline
- [ ] AI/Agentforce module prerequisites confirmed: Data Cloud in scope and licensed
- [ ] Phased roadmap includes phase entry/exit criteria for each phase
- [ ] Risk register created with at least one risk per licensed module
- [ ] Architecture validated against Salesforce Well-Architected Framework pillars

---

## Notes and Deviations

(Record any decisions that deviate from the standard patterns in SKILL.md and the reason for each)
