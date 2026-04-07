# Experience Cloud Architecture Decision — Work Template

Use this template to document an architecture decision for an Experience Cloud digital experience.
Fill in every section. Incomplete sections are not acceptable as a final deliverable.

---

## Scope

**Skill:** `headless-vs-standard-experience`

**Request summary:** (describe what the stakeholder asked for)

**Decision date:** (YYYY-MM-DD)

**Decision owner:** (name or role)

---

## Context Gathered

Answer these questions before filling in the decision matrix.

### Current State

- **Existing site engine:** (Aura / LWR / None — greenfield)
- **Custom Aura component count:** (required if migrating from Aura)
- **AppExchange Aura-only components in use:** (list or "none")
- **Third-party JavaScript libraries in use:** (list names and versions)

### Team Skills

- **LWC proficiency:** (None / Basic / Proficient / Expert)
- **Full-stack web (React/Vue/Angular):** (None / Basic / Proficient / Expert)
- **Salesforce admin/declarative skills:** (None / Basic / Proficient / Expert)

### Requirements

- **Target audience:** (Authenticated users / Guest/public / Both)
- **Performance SLA:** (e.g., "sub-3s FCP on mobile 4G")
- **UX constraints:** (describe any design system, layout, or interaction requirements that may push toward headless)
- **Client type:** (Web browser / Native iOS / Native Android / Embedded WebView / Other)
- **Timeline:** (available months for migration or build)

---

## Decision Matrix

Score each option 1–5 on each dimension (5 = best fit). Add a note for any score below 3.

| Dimension | Aura | LWR | Headless | Notes |
|---|---|---|---|---|
| Performance (FCP, load time) | | | | |
| Development cost (initial build) | | | | |
| Development cost (ongoing maintenance) | | | | |
| Fit with team skills | | | | |
| UX flexibility required | | | | |
| Access to Salesforce roadmap features | | | | |
| Operational complexity | | | | |
| Migration cost from current state | | | | |
| **Total** | | | | |

---

## Hard Blockers

List any factors that immediately rule out an option, regardless of score.

| Option | Blocker | Impact |
|---|---|---|
| LWR | (e.g., "22 existing Aura components require rewrite, 6-month timeline not feasible") | Rules out LWR for this release |
| Headless | (e.g., "Team has no React skills and no budget for external developers") | Rules out Headless |
| Aura | (e.g., "New product feature requires LWR-only catalog component") | Rules out staying on Aura |

---

## Architecture Recommendation

**Chosen architecture:** (Aura / LWR / Headless)

**Primary rationale:** (1–3 sentences — what is the strongest reason for this choice)

**Secondary benefits:** (bullet points)

---

## Key Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| (e.g., LWR publish step missed in CI/CD) | Medium | High | Add publish to deploy checklist; automate via REST API |
| (e.g., Third-party library fails under LWS) | Low | Medium | Test in LWR sandbox before migration commit |
| (add rows as needed) | | | |

---

## LWR-Specific: Publish Workflow Plan

Complete this section if LWR is chosen or recommended.

- **How will the Publish action be triggered in production?**
  - [ ] Manual — Experience Builder admin clicks Publish
  - [ ] Automated — CI/CD pipeline calls `POST /connect/communities/{communityId}/publish`
  - [ ] Automated — Salesforce CLI `sf experience publish` step in pipeline

- **Who is responsible for triggering Publish after each deployment?**
  (name or role)

- **Is Publish confirmed in the deployment runbook?**
  - [ ] Yes — added to runbook
  - [ ] No — needs to be added

---

## Aura-to-LWR Migration Readiness

Complete this section if migrating from Aura to LWR.

### Aura Component Inventory

| Component Name | Type | LWC Equivalent Exists? | Rewrite Effort (S/M/L) | LWS Library Risk |
|---|---|---|---|---|
| (component name) | Custom / AppExchange | Yes / No | S / M / L | Low / Medium / High |
| (add rows) | | | | |

**Total rewrite effort estimate:** (person-days or sprint count)

### LWS Compatibility Check

| Library | Version | LWS Status | Action Required |
|---|---|---|---|
| (library name) | (version) | Compatible / Incompatible / Unknown | Test / Replace / None |

---

## Headless Architecture Sketch

Complete this section if Headless is chosen or recommended.

- **Frontend framework:** (React / Vue / Angular / React Native / Other)
- **Hosting:** (Vercel / Netlify / AWS / Azure / Other)
- **Auth mechanism:** (OAuth 2.0 PKCE / OAuth 2.0 Client Credentials / Other)
- **Connected App name:** (to be created)
- **Required OAuth scopes:** (list)
- **Primary data APIs:** (Connect REST / Apex REST / GraphQL / Other)
- **CMS content delivery:** (Yes — using headless channel / No)
- **CORS origins to allow:** (list)

---

## Conditions That Would Change This Recommendation

(List 1–3 circumstances that, if true, would flip the recommendation)

- If _____, we would recommend _____ instead because _____.
- If _____, we would recommend _____ instead because _____.

---

## Notes and Deviations

(Record any assumptions, constraints, or deviations from the standard pattern documented in SKILL.md)
