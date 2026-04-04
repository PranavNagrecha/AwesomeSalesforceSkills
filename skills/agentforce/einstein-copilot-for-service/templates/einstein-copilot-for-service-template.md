# Einstein Copilot for Service — Work Template

Use this template when enabling, reviewing, or troubleshooting Einstein for Service AI features in a Service Cloud org. Fill in each section before beginning work.

---

## Scope

**Skill:** `einstein-copilot-for-service`

**Request summary:** (fill in what the user or project asked for)

**Features in scope for this engagement:**

- [ ] Case Classification
- [ ] Article Recommendations
- [ ] Reply Recommendations
- [ ] Work Summary (After-Visit Summary)
- [ ] Service Replies with Einstein
- [ ] Einstein Auto-Routing (requires Omni-Channel)
- [ ] Einstein Conversation Mining

---

## License Confirmation

Fill this in before any feature scoping discussion.

| License / Entitlement | Present? | Location Confirmed |
|---|---|---|
| Service Cloud Einstein add-on OR Einstein 1 Service | | Setup > Company Information > Feature Licenses |
| Einstein Generative AI entitlement (required for Work Summary, Service Replies) | | Setup > Company Information > Feature Licenses |

**Notes on license gaps:**

---

## Context Gathered

Answer these before beginning feature configuration:

**Case Classification data readiness:**
- Total closed cases with Closed Date in the last 12 months: ___
- Null rate for Case Type field on closed cases: ___%
- Null rate for Priority field on closed cases: ___%
- Null rate for Case Reason field on closed cases: ___%
- Fields selected for classification (only those with <20% null rate): ___

**Knowledge base readiness (for Article Recommendations and Service Replies):**
- Knowledge enabled in org: Yes / No
- Published article count: ___
- Agents currently linking articles to cases at resolution: Yes / No / Inconsistent
- Average article age (years since last review): ___

**Omni-Channel status (for Auto-Routing):**
- Omni-Channel enabled and configured: Yes / No
- Queues defined for relevant case types: Yes / No / Partial
- Routing configurations active: Yes / No

**Reply Recommendations readiness:**
- Messaging channels in scope: ___
- Historical messaging transcript volume (last 12 months): ___
- Training Data job previously run: Yes / No / Unknown

---

## Approach

**Which pattern from SKILL.md applies?**

- [ ] Mode 1: Enable and configure from scratch
- [ ] Mode 2: Improve Case Classification quality
- [ ] Mode 3: Troubleshoot Article Recommendations not appearing
- [ ] Other (describe): ___

**Rationale:**

---

## Enablement Sequence

Follow this sequence to avoid dependency failures. Check off each step only after validating the outcome.

**Phase 1 — Prerequisites**
- [ ] License confirmed for all features in scope
- [ ] Permission sets identified (`Service Cloud Einstein` or `Einstein for Service`)
- [ ] Case field null rate report run and qualifying fields identified
- [ ] Knowledge articles confirmed published (if Article Recommendations or Service Replies in scope)
- [ ] Omni-Channel confirmed active (if Auto-Routing in scope)

**Phase 2 — ML Feature Enablement (Case Classification, Article Recommendations, Reply Recommendations)**
- [ ] Case Classification enabled; fields selected based on data quality audit
- [ ] Case Classification set to suggestion mode (not auto-populate) for initial rollout
- [ ] Classification component added to Case record page / service console layout
- [ ] Article Recommendations enabled; component added to Case record page
- [ ] Agents briefed on article-linking habit (link article to case when it helps resolve it)
- [ ] Reply Recommendations enabled (if in scope)
- [ ] Training Data job initiated for Reply Recommendations; status confirmed "Complete"
- [ ] Model training status checked (24–72 hours post-enablement): Active / In Progress / Insufficient Data

**Phase 3 — Generative AI Feature Enablement (Work Summary, Service Replies)**
- [ ] Einstein Generative AI entitlement confirmed (re-check)
- [ ] Einstein Trust Layer settings reviewed
- [ ] Work Summary enabled (if in scope)
- [ ] Service Replies enabled and Knowledge grounding confirmed (if in scope)
- [ ] Agents briefed: AI outputs are suggestions — edit or reject as needed

**Phase 4 — Auto-Routing (if in scope)**
- [ ] Case Classification model validated in suggestion mode (accuracy sampled over 2–4 weeks)
- [ ] Per-field classification accuracy at acceptable threshold (80%+) before enabling Auto-Routing
- [ ] Auto-Routing enabled on pilot case type or channel
- [ ] Routing outcomes monitored for 1 week before expanding

**Phase 5 — Einstein Conversation Mining (if in scope)**
- [ ] Bot has been live 30+ days with sufficient transcript volume
- [ ] ECM enabled
- [ ] Review cadence scheduled (monthly or quarterly)

---

## Classification Mode Decision

| Field | Classification Mode | Rationale |
|---|---|---|
| Case Type | Suggestion / Auto-populate | |
| Priority | Suggestion / Auto-populate | |
| Case Reason | Suggestion / Auto-populate | |
| (custom field) | Suggestion / Auto-populate | |

---

## Review Checklist

Copy from SKILL.md and tick items as confirmed:

- [ ] Service Cloud Einstein or Einstein 1 Service license confirmed
- [ ] Einstein Generative AI entitlement confirmed (if generative features in scope)
- [ ] Permission sets assigned to all target agents
- [ ] Case Classification model status: Active (not In Progress or Insufficient Data)
- [ ] Classified fields have >80% data completeness validated via Case report
- [ ] Case Classification component on Case record page or service console layout
- [ ] Knowledge published; agents trained on article-linking habit
- [ ] Article Recommendations component on Case record page
- [ ] Reply Recommendations Training Data job completed (if in scope)
- [ ] Work Summary enabled with Trust Layer reviewed (if in scope)
- [ ] Service Replies enabled with Knowledge grounding confirmed (if in scope)
- [ ] Omni-Channel active before Auto-Routing enabled (if in scope)
- [ ] Classification accuracy validated before Auto-Routing enabled (if in scope)

---

## Notes and Deviations

Record any deviations from the standard pattern and the reason for the deviation.

---

## Known Issues / Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Case field null rate too high for reliable classification | | |
| Einstein Generative AI license not provisioned | | |
| Agents not adopting article-linking habit | | |
| Auto-Routing errors due to early classification inaccuracy | | |
