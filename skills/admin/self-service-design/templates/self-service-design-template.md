# Self-Service Design Brief

Use this template when designing or assessing a Salesforce self-service portal. Fill every section before beginning implementation. This brief is the input to portal configuration work — do not begin technical setup without completing Sections 1–4.

A filled-in copy of every section below, for one realistic org, is in `references/worked-examples.md`; its section 9 is the machine-readable form that `scripts/check_self_service_design.py --file <design>.yaml` lints. Fill this document for the human review, then transcribe sections 2A, 3A, 4A and 6 into the YAML for the checker.

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

## 2A. Journeys and Template Capability

Every journey needs a persona, an entry point, a friction level, and a success metric that can be
written as a query today. A journey whose metric cannot be queried goes back to the requester.

| # | Journey | Persona | Authenticated? | Entry point | Success metric (as SOQL, or the record it lands on) | Friction |
|---|---|---|---|---|---|---|
| J-01 | | | Y / N | | | none / low / medium |
| J-02 | | | Y / N | | | |
| J-03 | | | Y / N | | | |
| J-04 | | | Y / N | | | |
| J-05 | | | Y / N | | | |

**Template capability gate.** If any journey above is marked authenticated, the Help Center template
is out: `loginAppPageId`, `forgotPasswordRouteId` and `selfRegistrationRouteId` are unsupported on
templates that do not support login, Help Center among them. Help Center and the LWR starters also
ship no generic record pages, so a "track my case" menu item needs a Case page built for it.

- [ ] All journeys anonymous → Help Center template is viable
- [ ] One or more journeys authenticated → template selected: ___________ (Customer Account Portal /
      Customer Service / Build Your Own / other)
- [ ] Record pages required for: ___________ (or "none")

Template selection is permanent once the site is created — confirm with
`admin/experience-cloud-site-setup` before the site exists.

---

## 2B. Article Visibility Matrix

Three independent, Required, `false`-by-default boolean fields on `Knowledge__kav`. Nothing inherits.
`IsVisibleInApp` is Required but cannot be set by a deploy or a load — leave it alone.

| Channel | `Knowledge__kav` flag | Open for this design? | Article count in scope | Owner |
|---|---|---|---|---|
| Public knowledge base | `IsVisibleInPkb` | Y / N | | |
| Customer Portal | `IsVisibleInCsp` | Y / N | | |
| Partner portal | `IsVisibleInPrm` | Y / N | | |

- [ ] Every persona with a journey has at least one channel open for it
- [ ] Data category visibility confirmed for the portal profile(s) with
      `admin/knowledge-base-administration` — the flags alone do not make an article findable

---

## 2C. Record Exposure Model

One row per record the site shows. "The portal shows it" is not a mechanism, and
`Case.IsVisibleInSelfService` is not a mechanism either — it "does not alter sharing and will not
prevent usage of a direct URL to a case if a portal user has read or write access".

| Record / object | Audience | Sharing mechanism | Built by (skill) |
|---|---|---|---|
| | | ownership / sharing-set / guest-sharing-rule / data-category-visibility / parent-record-controlled / role-hierarchy / apex-managed-sharing | |
| | | | |
| | | | |

- [ ] Mechanism column routed through `standards/decision-trees/sharing-selection.md`
- [ ] Agent-reply visibility decided: `CaseComment.IsPublished` (customer-visible switch, and the
      only field on that object the API can update after insert) **or** feed. Chosen: ___________
- [ ] Correction convention written down, because a published `CaseComment` cannot be edited or
      deleted without Modify All Records

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

**Queryable metrics (take the M-4 baseline before anything ships):**

| # | Metric | Source | Query owner | Baseline reading | Date taken |
|---|---|---|---|---|---|
| M-1 | Portal article consumption by channel | `KnowledgeArticleViewStat` (`Channel` = `Csp` / `Pkb`) | | | |
| M-2 | Article quality signal | `KnowledgeArticleVoteStat` — note that unrated articles trend to 3 stars, so do not set a threshold at 3 | | | |
| M-3 | Deflection failure (article attached to a case anyway) | `CaseArticle`, internal user only | | | |
| M-4 | Contact rate | `Case` grouped by `Origin` and month | | | |

The SOQL for each is in `references/worked-examples.md` §5.

---

## 5A. Self-Registration and Login Policy

Three decisions, recorded together. `selfRegistration` deploys clean without either of the other two.

| Decision | Value | Notes |
|---|---|---|
| `Network.selfRegistration` | on / off | |
| `Network.selfRegProfile` | | Required in practice; the platform does not enforce the pair |
| `NetworkSelfRegistration.AccountId` | | One account per site. If unset, person accounts are created (when enabled) |
| Duplicate-contact / re-parenting cleanup owner | | Self-registered users land on the holding account, not the Contact's real one |
| Login method(s) | password / SSO / passwordless | |
| `Network.allowInternalUserLogin` | on / off | |

---

## 5B. Moderation Policy

Both ceilings below are **per org, not per site** — count what is already in use before claiming any.

| Item | Value |
|---|---|
| Members may flag (`Network.allowMembersToFlag`) | Y / N |
| Keyword lists this design claims (org ceiling: 30) | ___ of 30 already used: ___ |
| Moderation rules this design claims (org ceiling: 30, content + rate combined) | ___ of 30 already used: ___ |
| Moderation owner and response SLA | |
| `CommunitiesSettings.canModerateAllFeedPosts` / `canModerateInternalFeedPosts` | unchanged / escalated to platform owner |

Rule and keyword XML is authored by `admin/experience-cloud-moderation`; reputation and recognition
by `admin/community-engagement-strategy`.

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
- [ ] `python3 scripts/check_self_service_design.py --file <design>.yaml --manifest-dir <metadata dir>` exits 0

---

## 8. Acceptance Tests

Given / When / Then, every one run from an **external-user** sandbox session, never from an internal
admin login. The eight worked tests are in `references/worked-examples.md` §8; AT-02 (channel flags
are independent) and AT-04 (cross-account case by direct URL) are the two that most often fail late.

| # | Journey | Given | When | Then | Owner | Result |
|---|---|---|---|---|---|---|
| AT-01 | | | | | | pass / fail |
| AT-02 | | | | | | pass / fail |
| AT-03 | | | | | | pass / fail |
| AT-04 | | | | | | pass / fail |

---

## Notes

(Record any deviations from the standard patterns, stakeholder decisions that overrode design recommendations, or constraints that affected the design.)
