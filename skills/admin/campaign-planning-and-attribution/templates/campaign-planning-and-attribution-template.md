# Campaign Planning And Attribution — Work Template

Use this template when designing Campaign Hierarchy structures, configuring Customizable Campaign Influence (CCI), or planning multi-touch attribution reporting.

## Scope

**Skill:** `campaign-planning-and-attribution`

**Request summary:** (fill in what the user asked for — e.g., "design campaign hierarchy for Q2 pipeline program" or "configure CCI first-touch and last-touch models")

---

## Context Gathered

Answer these before proceeding (from SKILL.md Before Starting section):

- **CCI enabled in org?** [ ] Yes [ ] No — Check: Setup > Campaign Influence > Customizable Campaign Influence
- **Standard Campaign Influence auto-association rules active?** [ ] Yes [ ] No — if yes, disable before configuring CCI
- **MCAE B2B Marketing Analytics Plus licensed?** [ ] Yes [ ] No — required for time-decay / U-shaped models
- **Maximum hierarchy levels needed:** _______ (must be ≤ 5)
- **Attribution models in scope:** [ ] First Touch [ ] Last Touch [ ] Even Distribution [ ] Time-Decay [ ] U-Shaped (position-based)
- **Contact Role population enforced on Opportunities?** [ ] Yes [ ] No [ ] Partial — CCI requires this

---

## Campaign Hierarchy Design

| Level | Campaign Name (example) | Campaign Type | Purpose |
|-------|------------------------|---------------|---------|
| 1 (Root) | | Program | Program-level ROI aggregation |
| 2 | | | Channel or sub-program |
| 3 | | | Tactic |
| 4 | | | (if needed) |
| 5 | | | (if needed — maximum level) |

**Budgeted Cost owner (which level carries budget?):** Level ___

**ExpectedRevenue owner (which level carries forecast?):** Level ___

**Additional dimensions encoded as Campaign fields (not hierarchy levels):**
- Region field: ___________
- Product Line field: ___________
- Other: ___________

---

## Campaign Member Status Configuration

For each Campaign Type in scope, document the required status values:

| Campaign Type | Status Value | Responded? | Notes |
|---------------|-------------|-----------|-------|
| Email | Sent | No | |
| Email | Opened | No | Required for MCAE |
| Email | Clicked | No | Required for MCAE |
| Email | Responded | Yes | |
| Email | Unsubscribed | No | |
| Event | Invited | No | |
| Event | Registered | No | |
| Event | Attended | Yes | |
| Event | No-Show | No | |
| (add rows as needed) | | | |

---

## Customizable Campaign Influence Model Plan

| Model Name | Model Type | Primary Model? | Use Case |
|------------|-----------|----------------|----------|
| | First Touch | [ ] Yes | Awareness channel credit |
| | Last Touch | [ ] Yes | Conversion channel credit |
| | Even Distribution | [ ] Yes | Equal credit across all touches |
| | Custom (Apex) | [ ] Yes | (describe custom logic) |

**Contact Role enforcement approach:**
- [ ] Validation rule on Opportunity (prevents advance without Contact Role)
- [ ] Flow automation (auto-creates Contact Role on Opportunity creation)
- [ ] Manual process / sales team checklist
- [ ] None — RISK: CCI will produce no records for Opportunities missing Contact Roles

---

## Attribution Reporting Plan

| Report / Dashboard | Object | Filter | Attribution Model | Consumer |
|-------------------|--------|--------|-------------------|---------|
| Program ROI Summary | Campaign (Hierarchy) | Parent Campaign | N/A — rollup fields | Marketing leadership |
| First-Touch Attribution | CampaignInfluence | ModelId = First Touch | First Touch | Revenue ops |
| Last-Touch Attribution | CampaignInfluence | ModelId = Last Touch | Last Touch | Revenue ops |
| Time-Decay (if MCAE) | CRM Analytics dataset | CloseDate range | Time-Decay | Demand gen team |

**Rollup field refresh lag acknowledged?** [ ] Yes — stakeholders informed that parent Campaign fields update on a batch schedule, not in real time.

---

## Checklist

Before marking this work complete:

- [ ] Campaign Hierarchy does not exceed 5 levels
- [ ] Parent Campaign records have Budgeted Cost and Expected Revenue set
- [ ] CCI is enabled in Setup before any CCI model is referenced
- [ ] Standard Campaign Influence auto-association rules disabled (if CCI is active)
- [ ] At least one CCI model fully configured
- [ ] Contact Roles enforced on Opportunities via validation rule or automation
- [ ] Campaign Member Status picklist includes all required values per Campaign Type
- [ ] MCAE required statuses present if MCAE is in use: Sent, Opened, Clicked, Responded
- [ ] Attribution model choices documented with rationale
- [ ] Rollup field lag communicated to dashboard consumers
- [ ] Reporting layer built and validated with sample data

---

## Notes

Record any deviations from the standard pattern and the reason:

- 
- 
