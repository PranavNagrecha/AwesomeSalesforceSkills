# Analytics Adoption Strategy — Work Template

Use this template when planning or executing a CRM Analytics adoption initiative.

---

## Scope

**Skill:** `analytics-adoption-strategy`

**Request summary:** (fill in what the user asked for — e.g., "Drive adoption of the new Sales Pipeline dashboard for 30 reps" or "Measure who is using the analytics apps we launched last quarter")

**Org edition and CRM Analytics license type:** (e.g., Sales Cloud Enterprise + CRM Analytics Growth)

---

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md:

- **Analytics Adoption Metadata managed package installed?** [ ] Yes / [ ] No / [ ] Not checked
  - If No: install from AppExchange before proceeding with Adoption App creation
- **Target user personas:**
  - (list each persona — e.g., Sales Rep, Service Agent, Operations Manager, Executive)
- **Adoption problem type:**
  - [ ] Discoverability — users cannot find dashboards
  - [ ] Relevance — users open but do not use (escalate to analytics-dashboard-design)
  - [ ] Trust — users do not trust the data (escalate to data quality skills)
- **Existing analytics assets:**
  - Apps: (list app names)
  - Key dashboards: (list dashboard names and their current app)

---

## Persona-to-Discovery-Path Mapping

| Persona | Count | Primary Discovery Path | Recommended Intervention |
|---------|-------|----------------------|--------------------------|
| (e.g., Sales Rep) | (e.g., 35) | (e.g., Record page) | (e.g., Embed pipeline dashboard on Opportunity list view) |
| (e.g., Executive) | | (e.g., Analytics home) | (e.g., Share exec app; onboarding favoriting exercise) |
| (e.g., Ops Analyst) | | (e.g., Analytics Studio) | (e.g., Editor access + lens training session) |

---

## Analytics Adoption App Configuration

**Prerequisites:**
- [ ] Analytics Adoption Metadata managed package confirmed installed
- [ ] Creating user has Viewer+ access to all apps to be tracked

**Configuration decisions:**
- Scope: [ ] All apps / [ ] Specific apps (list: __________________)
- Dataflow schedule: (e.g., daily at 2 AM)
- Who gets access to the Adoption App: (e.g., Analytics Admin group as Manager; Dept Heads as Viewer)

---

## Embedded Analytics Plan

For each Lightning page where embedding is planned:

| Lightning Page | Dashboard to Embed | Filter Attribute Name | Filter Value Token |
|---------------|-------------------|----------------------|-------------------|
| (e.g., Opportunity List View) | (e.g., Pipeline Health Overview) | (e.g., OwnerFilter) | (e.g., {!currentUser.Id}) |
| (e.g., Account Record Page) | (e.g., Account Health) | (e.g., AccountFilter) | (e.g., {!recordId}) |

**Pre-activation checklist for each embedded dashboard:**
- [ ] Filter pass-through configured (not left as unfiltered)
- [ ] Tested with a non-admin test user on multiple records
- [ ] Test user sees only that record's data, not all-org data
- [ ] Row-level security verified for the underlying dataset

---

## Access Model Decisions

| User Group | App | Access Level | Rationale |
|------------|-----|-------------|-----------|
| (e.g., Sales Reps) | Sales Pipeline App | Viewer | View-only via embedded dashboard |
| (e.g., Ops Analysts) | Operations App | Editor | Self-service lens creation |
| (e.g., Analytics Lead) | All apps | Manager | App management and governance |

**Self-service users receiving Editor access:**
- [ ] Briefed: use Save As to personal lens, never Save on shared dashboard
- [ ] Onboarding session scheduled: lens creation walkthrough (45–60 min)
- [ ] Chatter group created for self-service questions: (group name: _______________)

---

## Success Metrics

| Metric | Baseline | Target | Measurement Method | Review Date |
|--------|---------|--------|-------------------|-------------|
| Dashboard open rate | (current %) | (target %) | Adoption App — Dashboard Usage Detail | (date) |
| Repeat weekly usage | — | 50% of initial openers return in week 2 | Adoption App — User Engagement | (date) |
| Self-service lens creation | 0 | 20% of Editor-access users create a lens within 60 days | Adoption App — Lens Usage | (date) |
| Embedded dashboard open rate | (baseline before embedding) | 3x pre-embedding baseline | Adoption App filtered to embedded dashboard name | (date) |

---

## Approach

**Which pattern from SKILL.md applies?**

- [ ] New Analytics App Rollout with Adoption Tracking
- [ ] Embedded Analytics for Record-Context Insight
- [ ] Self-Service Enablement for Operations Managers
- [ ] Combination (describe: _______________)

**Key decisions made:**
(Fill in any deviations from the standard pattern and the reason)

---

## Implementation Checklist

Copy and tick as steps are completed:

- [ ] Adoption App prerequisite (managed package) verified
- [ ] Analytics Adoption App created and dataflow scheduled
- [ ] Adoption App shared with appropriate stakeholders
- [ ] User personas mapped to discovery paths
- [ ] Embedded dashboards configured with filter pass-through (if applicable)
- [ ] Embedded dashboard pages activated for correct profiles
- [ ] App sharing set: each persona has correct access level (Viewer/Editor/Manager)
- [ ] Row-level security verified for all embedded and self-service datasets
- [ ] Editor-access users briefed on shared dashboard governance
- [ ] Collections configured in apps to organize dashboards by role
- [ ] Success metrics agreed with stakeholders and documented above
- [ ] 30-day and 60-day adoption review meetings scheduled
- [ ] Onboarding favoriting exercise included in user onboarding (if no embedded dashboard)

---

## Notes

(Record any deviations from the standard pattern, open questions, or decisions to revisit at the 30-day review)
