# Self-Service Design Brief

Use this template when designing or assessing a Salesforce self-service portal. Fill every section before beginning implementation. This brief is the input to portal configuration work — do not begin technical setup without completing Sections 1–4.

---

## Scope

**Skill:** `self-service-design`

**Request summary:** (fill in what the user asked for — e.g., "Design a self-service Help Center to reduce warranty case volume by 20%")

**Portal audience:** [ ] Authenticated community members  [ ] Unauthenticated public visitors  [ ] Both

**Primary goal:**
- [ ] Reduce case submission volume
- [ ] Improve time-to-resolution for self-service contacts
- [ ] Enable peer community support
- [ ] Replace an existing non-Salesforce self-service channel

---

## 1. Baseline Metrics (Required Before Design)

Complete this section from Case reports or Einstein Conversation Mining. Do not proceed to Section 2 without these figures.

| Metric | Value | Time Period |
|--------|-------|-------------|
| Total monthly case volume | | Last 90 days |
| Contact rate (cases per 1,000 portal sessions) | | Last 90 days |
| Top contact reason #1 | | % of total |
| Top contact reason #2 | | % of total |
| Top contact reason #3 | | % of total |
| Top contact reason #4 | | % of total |
| Top contact reason #5 | | % of total |

**Deflection target:** Reduce monthly case volume for top contact reasons by ___% within ___ months post-launch.

---

## 2. Article Coverage Assessment (Required Gate Before Portal Design)

For each top contact reason, verify the following before proceeding.

| Contact Reason | Article Exists? | Channel Assignment Correct? | Title Uses Customer Language? | Action Required |
|---|---|---|---|---|
| (reason 1) | Y / N | Y / N | Y / N | |
| (reason 2) | Y / N | Y / N | Y / N | |
| (reason 3) | Y / N | Y / N | Y / N | |
| (reason 4) | Y / N | Y / N | Y / N | |
| (reason 5) | Y / N | Y / N | Y / N | |

**Coverage gate decision:**
- [ ] Coverage is sufficient (>80% of top 5 contact reasons have a published, channel-assigned, customer-titled article). Proceed to Section 3.
- [ ] Coverage gaps identified. Block portal design work. Redirect to article authoring backlog below.

**Article authoring backlog (gaps to fill before launch):**
1.
2.
3.

---

## 3. Search UX Design

**Search bar placement:** (Describe placement and surrounding UI — e.g., "Full-width above-the-fold search bar on Help Center landing page, no competing navigation elements above the fold")

**Zero-results behavior:** (Describe what happens when search returns no results — e.g., "Display 'No results found' message followed immediately by a 'Contact Support' button that routes to the case submission flow")

**Article preview format in search results:** (e.g., "Article title + first 175 characters of body text + category label")

**Faceted filtering:** (e.g., "Product category filter available; disabled by default, visible via 'Filter results' toggle")

**Search bar behavior notes:**
-
-

---

## 4. Case Submission Flow Design

**Pre-deflection mechanism:**
- [ ] No pre-deflection (direct case form) — Justification: ___
- [ ] Article suggestions in Case Creation component (triggered after subject entry) — Friction level: low
- [ ] Mandatory search prompt with "I still need to submit" escape — Friction level: medium
- [ ] Required article acknowledgment before Submit activates — Friction level: medium-high — only use if article coverage for top reason >80%

**Number of article suggestions to display:** ___

**Friction calibration rationale:** (Why this friction level for this audience and article coverage state?)

**Abandonment monitoring plan:** (How will abandonment be measured separately from deflection? Define abandonment threshold that triggers friction reduction — e.g., ">15% abandonment rate triggers friction review")

**Case form fields (progressive disclosure decision):**
- [ ] All fields visible on form load
- [ ] Progressive disclosure: show subject + description first, reveal remaining fields after article suggestion dismissal

---

## 5. Deflection Measurement Setup

**Case Deflection component placement:** (Page name and position on page)

**Deflection rate reporting cadence:** (e.g., "Monthly review by Support Operations lead")

**Deflection rate measurement formula:**
- Primary: Case Deflection component rate = (article views during case creation that did not result in submission) / (total article views during case creation)
- Supplementary: Contact rate = total cases per 1,000 portal sessions (monthly trend)

**Reporting owner:**

**Intervention threshold:** (e.g., "If deflection rate does not reach 15% within 60 days post-launch, trigger article quality review for all contact reasons below 10% individual deflection rate")

---

## 6. Community Peer Support Assessment

**Community Q&A decision:**
- [ ] In scope for this launch
- [ ] Deferred — reason: ___

If in scope, confirm the following before launch:

| Readiness Criterion | Status | Owner | Due Date |
|---|---|---|---|
| 20+ pre-seeded Q&A pairs created from support content | | | |
| Q&A pairs use real customer question phrasings from case subjects | | | |
| Internal advocate coverage: 2–3 people assigned, 24hr response SLA | | | |
| Expert recognition mechanism configured (badges, reputation points) | | | |
| Moderation workflow documented and resourced | | | |
| Promoted-answer-to-Knowledge workflow defined | | | |

**Seeding content sources:** (e.g., "Top 20 support macros converted to Q&A pairs; 10 historical case subjects rewritten as community questions")

---

## 7. Launch Readiness Checklist

Run through these before go-live:

- [ ] Baseline metrics documented (Section 1 complete)
- [ ] Article coverage gate passed (Section 2 complete, no blocking gaps remaining)
- [ ] Article channel assignments verified from a guest/community member session (not internal admin session)
- [ ] Search UX designed and validated from a guest/community member session
- [ ] Case submission flow friction level documented and justified
- [ ] Abandonment monitoring instrumented and threshold defined
- [ ] Case Deflection component configured and verified to fire events
- [ ] Community Q&A either deferred (with reason) or all readiness criteria in Section 6 met
- [ ] Post-launch review date set: ___

---

## Notes

(Record any deviations from the standard patterns, stakeholder decisions that overrode design recommendations, or constraints that affected the design.)
