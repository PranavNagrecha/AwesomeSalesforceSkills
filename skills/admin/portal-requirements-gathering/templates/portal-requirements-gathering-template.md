# Portal Requirements Gathering — Requirements Workshop Template

Use this template to document and lock portal requirements before any design or build work begins. Fill in every section. Do not proceed to build until Sections 1–6 have sign-off.

---

## Project Header

| Field | Value |
|---|---|
| Project name | |
| Portal type | Customer Self-Service / Partner Community / Hybrid / Other |
| Primary business goal | Deflection / Partner Enablement / Account Self-Service / Other |
| Stakeholder lead | |
| Technical lead | |
| Requirements owner | |
| Workshop date | |
| Sign-off date | |

---

## Section 1: Contact Reason Analysis

**Data period covered:** _____ to _____ (minimum 60–90 days)

**Data sources pulled:**
- [ ] Case records (closed/resolved)
- [ ] Phone/email/chat activity logs
- [ ] Web form submissions
- [ ] Other: ___________________

### Top 10 Contact Reasons by Volume

| Rank | Contact Reason | Monthly Volume | Category (Answers / Status / Action) | Currently Deflectable? |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |
| 6 | | | | |
| 7 | | | | |
| 8 | | | | |
| 9 | | | | |
| 10 | | | | |

**Summary counts:**
- Answers (information): ___
- Status (check on something): ___
- Actions (do something): ___

**Current self-service containment rate (baseline):** ____ %

---

## Section 2: Audience Segments

Define each distinct audience the portal must serve. Add rows as needed.

| Audience Segment | Access Type | Example Users | Key Jobs | License Type |
|---|---|---|---|---|
| | Authenticated / Public | | | |
| | Authenticated / Public | | | |
| | Authenticated / Public | | | |

**License confirmation:**
- [ ] Licenses required have been confirmed as owned by the org
- [ ] License procurement request submitted if new licenses are needed

---

## Section 3: Access Architecture Decision

**Decision:** (circle one) **Public** | **Authenticated** | **Hybrid**

**Rationale:**

**If Hybrid — Public pages list:**

| Page Name | Content | Guest User Profile Permissions Required |
|---|---|---|
| | | |
| | | |

**Guest user profile lockdown assigned to:** ____________________

**Technical sign-off from:** ____________________ **Date:** ____________

---

## Section 4: Top-3 High-Volume Jobs

Document the three highest-volume customer jobs this portal must support in phase 1.

### Job 1

**Job statement:** "As a [audience segment], I need to [action] so that [outcome]."

**Contact reasons addressed:** (from Section 1 rank list)

**Success criterion:** Customer can complete this task without contacting support via phone/email/chat.

**Deflection target:** Reduce contacts for this reason by ____% within ____ months of launch.

**Portal capabilities required:**

---

### Job 2

**Job statement:** "As a [audience segment], I need to [action] so that [outcome]."

**Contact reasons addressed:**

**Success criterion:**

**Deflection target:**

**Portal capabilities required:**

---

### Job 3

**Job statement:** "As a [audience segment], I need to [action] so that [outcome]."

**Contact reasons addressed:**

**Success criterion:**

**Deflection target:**

**Portal capabilities required:**

---

## Section 5: Content Taxonomy and Ownership

List every content type the portal will surface. Assign an owner and review cadence to each.

| Content Type | Description | Content Owner | Review Cadence | Publication Workflow |
|---|---|---|---|---|
| Knowledge Articles | Self-service answers to top contact reasons | | Quarterly | Draft → SME Review → Publish |
| | | | | |
| | | | | |
| | | | | |

**Top-level taxonomy categories (max 7 for usability):**

1.
2.
3.
4.
5.

---

## Section 6: Feature Scope

### In Scope — Phase 1

Features that directly support the top-3 jobs and deflection goal.

| Feature | Addresses Job(s) | Salesforce Capability | Notes |
|---|---|---|---|
| | | | |
| | | | |
| | | | |

### Deferred — Phase 2 (gate: phase 1 deflection target met)

| Feature | Reason for Deferral |
|---|---|
| Idea Exchange | Social engagement; does not contribute to core deflection loop |
| Community Forums / Chatter | Social engagement; deferred until core loop validated |
| Gamification (badges, leaderboards) | Engagement feature; deferred until deflection proven |
| | |

### Out of Scope

| Item | Reason |
|---|---|
| | |
| | |

---

## Section 7: Deflection Measurement Plan

**Baseline self-service containment rate:** ____% (from Section 1)

**Phase 1 target containment rate:** ____% by ________________ (date)

**Measurement method:**

| Metric | How Measured | Reporting Cadence |
|---|---|---|
| Self-service containment rate | Cases closed without agent contact / total cases | Monthly |
| Portal page views per contact reason | Experience Cloud analytics | Monthly |
| Search zero-result rate | Site search analytics | Bi-weekly |
| | | |

**Reporting owner:** ____________________

---

## Sign-Off

| Section | Decision Summary | Approver | Date |
|---|---|---|---|
| Access Architecture | | | |
| License Selection | | | |
| Top-3 Jobs | | | |
| Phase 1 Feature Scope | | | |
| Content Ownership | | | |

**Requirements document version:** 1.0

**Status:** Draft / Under Review / Signed Off
