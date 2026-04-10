# Agentforce Service AI Setup — Work Template

Use this template when planning or executing an Einstein for Service AI feature enablement engagement.

## Scope

**Skill:** `agentforce-service-ai-setup`

**Request summary:** (fill in what the customer or project asked for)

**Features in scope for this engagement:**
- [ ] Case Classification
- [ ] Article Recommendations
- [ ] Reply Recommendations
- [ ] Work Summaries (After-Visit Summary)
- [ ] Service Replies with Einstein
- [ ] Other: _______________

---

## License Verification

| License / Entitlement | Required For | Present in Org? | Verified In |
|---|---|---|---|
| Service Cloud Einstein or Einstein 1 Service | Case Classification, Article Recommendations, Reply Recommendations | Yes / No / Not checked | Setup > Company Information > Feature Licenses |
| Einstein Generative AI PSL or Einstein 1 Service | Work Summaries, Service Replies | Yes / No / Not checked | Setup > Company Information > Permission Set Licenses |
| Data Cloud entitlement | Work Summaries (many configurations) | Yes / No / Not checked | Setup > Data Cloud |

**License gap summary:** (document any missing entitlements and the procurement path)

---

## Data Readiness Assessment

### Case Classification

| Field | Total Closed Cases (last 18 months) | Non-Null Count | Completeness % | Go / No-Go |
|---|---|---|---|---|
| (e.g. Type) | | | | |
| (e.g. Priority) | | | | |
| (e.g. Reason) | | | | |

**Minimum threshold:** 1,000+ closed cases with >80% completeness per classified field.

**Decision:** Go / Defer — Reason: _______________

### Article Recommendations

- [ ] Salesforce Knowledge is enabled
- [ ] Published articles exist: count = ___
- [ ] Agents currently link articles to cases at resolution: Yes / No / Unknown

**Decision:** Go / Defer — Reason: _______________

### Reply Recommendations

- [ ] Active Messaging channel exists (Messaging for In-App and Web, SMS, WhatsApp, etc.)
- [ ] Estimated historical messaging session count: ___
- [ ] Meets minimum recommended threshold (several thousand sessions): Yes / No

**Decision:** Go / Defer — Reason: _______________

### Work Summaries

- [ ] Einstein Generative AI license confirmed
- [ ] Data Cloud entitlement confirmed
- [ ] Active Messaging or Voice channel confirmed
- [ ] Einstein Trust Layer active

**Decision:** Go / Defer — Reason: _______________

---

## Feature Readiness Matrix

| Feature | License Met | Data Threshold Met | Channel Prerequisite Met | Go / No-Go | Notes |
|---|---|---|---|---|---|
| Case Classification | | | N/A | | |
| Article Recommendations | | | N/A | | |
| Reply Recommendations | | | | | |
| Work Summaries | | | | | |
| Service Replies | | | N/A | | |

---

## Phased Activation Plan

### Phase 1 — Predictive AI Features (if prerequisites met)

- [ ] Assign `Service Cloud Einstein` or `Einstein for Service` permission sets to target users
- [ ] Enable Case Classification: Setup > Service > Einstein Classification Apps > Case Classification
  - Fields to classify: _______________
  - Mode: Suggestion (recommended for initial deployment)
- [ ] Enable Article Recommendations: Setup > Service > Einstein Article Recommendations
- [ ] Add Case Classification component to Case record page via Lightning App Builder
- [ ] Add Einstein Article Recommendations component to Case record page via Lightning App Builder
- [ ] Wait for model training (24–72 hours for initial training pass)
- [ ] Confirm model training status: Setup > Service > Einstein Classification Apps > View Model

**Phase 1 validation date:** _______________

### Phase 2 — Reply Recommendations (if prerequisites met)

- [ ] Enable Reply Recommendations: Setup > Service > Einstein Reply Recommendations
- [ ] Run Training Data job: Setup > Service > Einstein Reply Recommendations > Build Training Data
- [ ] Confirm Training Data job status = "Completed"
- [ ] Wait for model training to complete (additional 24–48 hours)
- [ ] Add Suggested Replies component to messaging console layout

**Phase 2 validation date:** _______________

### Phase 3 — Generative AI Features (if prerequisites met)

- [ ] Confirm Einstein Generative AI PSL and Data Cloud entitlement (final verification before enabling)
- [ ] Review Einstein Trust Layer configuration (data masking, audit log enabled)
- [ ] Enable Work Summaries: Setup > Service > Einstein Work Summaries
- [ ] Enable Service Replies: Setup > Service > Einstein Service Replies (if in scope)
- [ ] Test with a real interaction and verify output is generated

**Phase 3 validation date:** _______________

---

## Deferred Features

| Feature | Gap | Condition for Re-Assessment | Target Date |
|---|---|---|---|
| | | | |

---

## Post-Go-Live Checkpoints

- **30-day review:** Check Case Classification model accuracy in Setup > Einstein Classification Apps > View Model. Target: >75% precision per field. If below, review field selection and data completeness.
- **90-day review:** Assess Article Recommendations quality (are agents using suggested articles?). Review messaging transcript volume for Reply Recommendations quality.
- **Ongoing:** Ensure agents are trained to review and correct Case Classification suggestions, and to link Knowledge articles to resolved cases. These behaviors are required for ongoing model improvement.

---

## Notes and Deviations

(Record any deviations from the standard activation pattern and the rationale for each)
