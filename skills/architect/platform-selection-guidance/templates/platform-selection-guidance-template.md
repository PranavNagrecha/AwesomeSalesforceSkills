# Platform Feature Selection — Decision Document

**Prepared by:**
**Date:**
**Org / Project:**
**Skill reference:** `architect/platform-selection-guidance`

---

## 1. Requirement Statement

Describe the business or technical requirement driving this decision. Be specific about:
- What behavior or outcome is needed
- What triggers the behavior (user action, record change, schedule, external event)
- What data is read, created, or modified
- Who the end users or consuming systems are

> _Example: "The service team needs routing rules that map Case origin + language to an assignment queue. Rules change ~4 times per year. They must be identical across all sandboxes and production. Rules are read by a Record-Triggered Flow on Case before-save."_

---

## 2. Candidate Features

List 2–3 platform features that could address this requirement. For each, summarize the pros, cons, and any license requirements.

| Feature | Pros | Cons | License Required |
|---|---|---|---|
| | | | |
| | | | |
| | | | |

---

## 3. Decision Criteria

Rate each candidate against the criteria relevant to this requirement. Mark N/A if the criterion does not apply.

| Criterion | Why It Matters for This Requirement | Candidate 1 | Candidate 2 | Candidate 3 |
|---|---|---|---|---|
| Deployable via Metadata API / change sets | Config must travel with releases | | | |
| Per-user or per-profile override needed | Behavior varies by user or profile | | | |
| Data volume (rows) | Expected record count now and at 3–5 year scale | | | |
| Relationship to other Salesforce records needed | Config references Queue IDs, User IDs, etc. | | | |
| Formula or validation rule access needed | Config read in declarative formula context | | | |
| Team skill fit | Admin team vs. developer team | | | |
| Strategic platform investment | Feature is actively developed vs. legacy | | | |
| License included in org | No additional cost vs. add-on required | | | |
| Runtime performance for high-transaction use | Config read in high-volume trigger context | | | |

---

## 4. Recommendation and Rationale

**Recommended platform feature:**

**Rationale** (2–5 sentences explaining why this feature best meets the criteria above):

**Tradeoffs accepted** (what you are giving up by choosing this feature over the alternatives):

---

## 5. Migration Path (if replacing a legacy feature)

Complete this section only if this decision involves migrating away from an existing implementation.

**Current implementation:**
**Target implementation:**

**Migration steps:**

| Step | Description | Owner | Target Date |
|---|---|---|---|
| 1 | | | |
| 2 | | | |
| 3 | | | |

**Parallel run period** (how long both old and new run side by side before the old is retired):

**Rollback plan** (what happens if the new implementation has a production incident):

---

## 6. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| | Low / Medium / High | Low / Medium / High | |
| | | | |
| | | | |

**Common risks by feature type — check applicable ones:**

- [ ] Custom Metadata Types: data volume may grow past the ~5,000-record practical limit → monitor record count; plan migration to Custom Object if volume grows
- [ ] Custom Metadata Types: configuration references Salesforce record IDs stored as text → IDs are org-specific; implement runtime resolution by developer name
- [ ] Custom Settings: values not deploying via Metadata API → post-deploy data seeding script required for every sandbox/production deploy
- [ ] LWC: team lacks JavaScript skills → allocate training/spike time before first sprint
- [ ] Aura migration: application events require LMS redesign → design LMS channel before beginning migration
- [ ] Platform Events: external subscriber offline beyond 72-hour replay window → design replay strategy; consider fallback reconciliation job
- [ ] CDC with Shield: 7-day retention requires Shield Event Monitoring license → confirm license availability before design commitment
- [ ] OmniStudio: license may not be included in production org → verify license before beginning OmniScript design

---

## 7. Implementation Skill References

Based on the recommendation above, the next skills to use for implementation:

| Decision | Implementation Skill |
|---|---|
| Custom Metadata Types chosen | `admin/custom-metadata-types`, `apex/custom-metadata-in-apex` |
| LWC chosen | `lwc/` skill suite |
| Platform Events chosen | `integration/platform-events` |
| Change Data Capture chosen | (search `scripts/search_knowledge.py "change data capture"`) |
| OmniStudio chosen | `omnistudio/omniscript-design-patterns` |
| Automation tool decision still needed | `admin/process-automation-selection` |

---

## 8. Sign-Off

| Role | Name | Date | Approved |
|---|---|---|---|
| Architect | | | [ ] |
| Tech Lead | | | [ ] |
| Product Owner | | | [ ] |
