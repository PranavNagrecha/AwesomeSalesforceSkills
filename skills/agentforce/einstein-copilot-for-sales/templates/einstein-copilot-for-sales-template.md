# Einstein Copilot for Sales — Work Template

Use this template when enabling, reviewing, or troubleshooting Einstein Sales AI features in a Sales Cloud org. Fill in each section before beginning work.

---

## Scope

**Org:** (name and type: Production / Full Sandbox / Partial Sandbox / Developer)

**Einstein Sales features in scope:**

- [ ] Einstein Opportunity Scoring
- [ ] Einstein Activity Capture (EAC)
- [ ] Pipeline Inspection AI Insights
- [ ] Einstein Generative Email (AI email drafting)
- [ ] Einstein Email Recommendations (template-based reply suggestions)
- [ ] Einstein Relationship Insights

**Task type:** (enable from scratch / review and optimize / troubleshoot)

---

## License and Edition Verification

| License / Entitlement | Required By | Status (Confirmed / Not Confirmed) |
|---|---|---|
| Einstein for Sales add-on OR Einstein 1 Sales edition | Opportunity Scoring, EAC, Pipeline Inspection, Email Recommendations, Relationship Insights | |
| Einstein Generative AI (Einstein GPT) | Generative Email Drafting / AI email composition | |
| Sales Cloud Einstein | Pipeline Inspection (specifically) | |

**How to verify:** Setup > Company Information > Feature Licenses

---

## Data Readiness Check (Opportunity Scoring)

| Requirement | Threshold | Current Count | Pass / Fail |
|---|---|---|---|
| Closed opportunities with CloseDate in last 2 years | >= 200 | | |
| Mix of Won and Lost opportunities | Both types present | | |

**SOQL to run in production:**
```text
SELECT COUNT() FROM Opportunity WHERE IsClosed = true AND CloseDate >= LAST_N_DAYS:730
```

If count < 200: Do NOT enable Opportunity Scoring yet. Document plan for reaching threshold.

---

## Einstein Activity Capture Prerequisites

**Email/calendar system in use:** (Microsoft Exchange / Office 365 / Google Workspace / Other)

**EAC exclusion domains to configure (must be done before go-live):**

| Domain | Reason for Exclusion |
|---|---|
| (example: personal.com) | Personal email |
| (example: legal-counsel.com) | Legal communications |
| | |

**EAC configuration profile settings:**

| Setting | Planned Value |
|---|---|
| Sync direction — Email | (Inbound only / Bidirectional) |
| Sync direction — Calendar | (Inbound only / Bidirectional) |
| Object scope | (Contacts, Leads, Opportunities — select all that apply) |
| Users / profiles assigned to profile | |

---

## Opportunity Scoring — Configuration Notes

**Model training status (check Setup > Einstein > Opportunity Scoring):**
- [ ] Not yet enabled
- [ ] In Progress (training underway — do not present to users yet)
- [ ] Insufficient Data (< 200 closed opps — feature deferred)
- [ ] Active (scores being generated — ready for user rollout)

**Custom fields added to scoring model (optional — high-signal fields only):**

| Field API Name | Object | Rationale |
|---|---|---|
| | | |

**Score fields to add to Opportunity page layout:**
- [ ] `Opportunity Score` field
- [ ] `Score Change` field (direction indicator)
- [ ] Score factor fields (optional — top positive/negative drivers)

---

## Pipeline Inspection Setup

**Dependency check:** Opportunity Scoring model status must be Active before enabling Pipeline Inspection AI insights.

- [ ] Opportunity Scoring confirmed Active
- [ ] Pipeline Inspection enabled in Setup > Sales > Pipeline Inspection
- [ ] `Sales Cloud Einstein` or `Einstein Analytics for Sales` permission set assigned to forecast managers
- [ ] Pipeline Inspection component added to Forecast page layout

---

## Einstein Email Features Setup

**Feature type in scope:**

- [ ] Einstein Email Recommendations (included with Einstein for Sales — no additional license)
- [ ] Einstein Generative Email / AI Email Drafting (requires Einstein Generative AI license)

**Trust Layer review completed before enabling generative email:**
- [ ] Einstein Trust Layer audit trail reviewed
- [ ] Data masking rules validated for email context (no PII in prompts without masking)
- [ ] See `einstein-trust-layer` skill for full Trust Layer configuration guidance

---

## Permission Set Assignment Tracker

| Permission Set | Users / Roles Assigned | Date Assigned | Verified in Org |
|---|---|---|---|
| Sales Cloud Einstein | | | |
| Einstein for Sales User | | | |
| Einstein Email Recommendations | | | |

---

## Rollout Sequence (Recommended Order)

Follow this sequence to avoid blank panels and user trust issues:

1. Configure EAC exclusion rules (before any sync begins)
2. Enable EAC and connect user accounts — allow 24 hours to confirm sync
3. Enable Opportunity Scoring — wait 24–72 hours for model training to complete
4. Confirm model status is Active (Setup > Einstein > Opportunity Scoring)
5. Enable Pipeline Inspection — confirm AI insights panel is populated
6. Enable Einstein email features (confirm license before step)
7. Enable Einstein Relationship Insights — communicate 30-day warm-up period to users

---

## Review Checklist

- [ ] License manifest confirms required entitlements for all features in scope
- [ ] Closed opportunity count >= 200 in production (or Opportunity Scoring deferred)
- [ ] EAC exclusion domains configured before email sync started
- [ ] EAC configuration profile assigned to all target users with correct object scope
- [ ] Opportunity Scoring model status is Active before user rollout
- [ ] Opportunity Score and Score Change fields on Opportunity page layout and list views
- [ ] Pipeline Inspection AI insights visible in Forecast page (not empty panel)
- [ ] Einstein Generative AI license confirmed if generative email drafting is in scope
- [ ] Einstein Trust Layer reviewed before enabling generative email
- [ ] Einstein Relationship Insights warm-up period communicated to users
- [ ] `python3 check_einstein_sales.py --manifest-dir path/to/metadata` passes with no issues

---

## Notes and Deviations

(Record any deviations from the standard rollout sequence, stakeholder decisions that override defaults, or known issues to monitor post-launch.)
