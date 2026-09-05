---
name: self-service-design
description: "Use this skill when designing the UX and content strategy for a Salesforce-powered self-service portal or help center — pre-deflection article surfacing, Help Center search UX, friction-calibrated case submission forms, community peer support layers, and deflection measurement. Trigger keywords: design self-service portal, case deflection strategy, help center UX design, reduce support volume with self-service, knowledge base search experience. NOT for picking which contact reasons to deflect and through which channel — use architect/case-deflection-strategy. NOT for building the Experience Cloud site itself — use admin/experience-cloud-site-setup. More trigger keywords: article visibility matrix IsVisibleInCsp IsVisibleInPkb, which articles show in the customer portal, case visibility for portal users, CaseComment IsPublished customer visible comment, self-registration profile and account for a portal, Help Center template does not support login, deflection metrics SOQL KnowledgeArticleViewStat, self-service journey map, moderation policy for a support community."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Operational Excellence
  - Reliability
triggers:
  - "design self-service portal for case deflection"
  - "reduce support volume with self-service help center"
  - "help center UX design and knowledge base search experience"
  - "case deflection strategy using knowledge article surfacing"
  - "friction-calibrated case submission form design"
  - "we're having issues with case deflection"
  - "which knowledge articles show up in the customer portal"
  - "portal users can't see their own cases"
  - "make an agent's case comment visible to the customer"
  - "design the journeys for a customer self-service site"
  - "how do we measure case deflection without guessing"
  - "should self-registration be on for our help centre"
  - "our help center has no login page"
  - "write a self-service design worksheet before we build the portal"
  - "let customers log and track cases on the portal"
tags:
  - self-service-design
  - case-deflection
  - help-center
  - knowledge
  - experience-cloud
  - customer-service
inputs:
  - "Current inbound case volume by contact reason (from Case reports or Einstein Conversation Mining)"
  - "Existing knowledge article inventory: count, category coverage, average age"
  - "Portal audience: authenticated customers vs. unauthenticated public visitors"
  - "Deflection goal: target reduction percentage or absolute case volume target"
  - "Available channels: Help Center, Community (peer support), Einstein Bot, email-to-case"
outputs:
  - "Self-service portal design brief covering UX structure, deflection mechanisms, and measurement plan"
  - "Pre-deflection article surfacing specification for case submission form"
  - "Friction calibration recommendation for the case submission flow"
  - "Deflection rate measurement setup using Case Deflection component"
  - "Community peer support readiness assessment"
  - "Self-service design YAML (journeys, exposed objects and their sharing mechanisms, article visibility matrix, self-registration and moderation decisions, metrics, acceptance tests)"
  - "Article visibility matrix mapping each channel to its Knowledge__kav flag"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# Self-Service Design

Use this skill when designing how customers or partners will find answers and optionally submit cases on a Salesforce-powered self-service portal. It activates when the goal is to reduce inbound case volume through deliberate UX design: article surfacing placement, search experience quality, case form friction calibration, and peer community engagement — not through technical Experience Cloud configuration.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Contact reason breakdown:** Pull current case volume by contact reason from Case reports or Einstein Conversation Mining. Without topic-level volume you cannot prioritize which knowledge gaps to close first or measure deflection meaningfully.
- **Article inventory baseline:** Count existing knowledge articles, their category coverage, and average last-modified date. Self-service only deflects if findable, accurate articles exist for the top contact reasons. Designing UX before fixing content gaps produces cosmetic improvements with no deflection impact.
- **Portal audience type:** Authenticated community members have persistent identity; unauthenticated visitors cannot. This determines whether you can personalize article suggestions, track case submission history, or measure per-user deflection patterns.
- **Existing deflection mechanisms already in place:** Check whether the org already uses Einstein Search for Experts, Einstein Bot, or a pre-submission search prompt. Design should layer on existing mechanisms, not duplicate them.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which of these journeys must work when the visitor is *not* logged in, and which require a login?" | The Help Center template does not support login: `loginAppPageId`, `forgotPasswordRouteId` and `selfRegistrationRouteId` are all "Unsupported if the active Experience Builder template for the site doesn't support login (such as Help Center)". Picking the template before answering this is picking it wrong | The template decision, made once, with the authenticated journeys on a template that can carry them |
| "For each channel we open — public, customer, partner — which articles are in it?" | `Knowledge__kav` carries three independent, Required, `false`-by-default flags (`IsVisibleInPkb`, `IsVisibleInCsp`, `IsVisibleInPrm`). Nothing inherits; an article visible internally is invisible to every portal until one of these is set | The article visibility matrix, one row per channel, with a count and an owner |
| "Which records does the site show, and by what mechanism does each customer get access to theirs?" | `Case.IsVisibleInSelfService` looks like the answer and is not: "The field does not alter sharing and will not prevent usage of a direct URL to a case if a portal user has read or write access." Access is ownership, a sharing set, or a guest sharing rule | The exposed-object table with one named mechanism per row, and the sibling skill that builds each |
| "Do customers need to see agent replies, and must they be able to correct their own?" | `CaseComment.IsPublished` is the customer-visibility switch and "the only CaseComment field that can be updated via the API" — comments cannot be edited or deleted without Modify All Records | The comment model, and an explicit decision between `CaseComment` and feed |
| "What number will tell us in 90 days whether this worked, and can we query it today?" | Deflection rate is not derivable from a component alone. `KnowledgeArticleViewStat` (per `Channel`) and `CaseArticle` are queryable now; a baseline taken after launch is not a baseline | The metric set with its SOQL, its owner, and a pre-launch baseline reading |
| "Is self-registration on, and if so which profile and which account do new users land on?" | `selfRegistration` deploys happily without `selfRegProfile`, and self-registering users are "required to be associated with an account, which the admin must specify" — one account per site | The profile, the holding account, and the named owner of the duplicate-contact cleanup that follows |
| "Who moderates member content, and how much of the org's moderation budget is already spent?" | Keyword lists and moderation rules are capped at 30 each **per org, not per site** — a late-arriving site can find the budget gone | A moderation owner, a rule count, and the org-wide switches escalated to the platform owner |

What a proper configuration adds over just building a help centre: every journey has a persona, an access mechanism and a queryable success metric; the article and case visibility decisions are written down as flags and sharing mechanisms rather than assumed; and the design fails the checker before it fails UAT.

---

## Core Concepts

### Pre-Deflection Article Surfacing

Pre-deflection is the primary lever for reducing case volume. It works by surfacing relevant knowledge articles to the customer before they submit a case — specifically during or immediately before the case submission form. The Salesforce implementation uses Knowledge search embedded in the Case Creation component on Experience Cloud sites. When a customer types a subject or description, the component queries published Knowledge articles and displays up to five suggested results inline. If the customer finds an answer, they abandon the form without submitting a case. UNVERIFIED (2026-09-05): the “five” figure and the Case Creation component itself appear in neither the Metadata API Developer Guide nor the Object Reference, and help.salesforce.com cannot be fetched. What *is* deployable and testable is the org-level half: `KnowledgeSettings.suggestedArticles.useSuggestedArticlesForCase` plus the `caseFields` list that feeds it — design against that and record which Case fields are in it.

The effectiveness of pre-deflection depends entirely on article quality and findability:
- Articles must be published to the channel used by the portal, which means the matching `Knowledge__kav` boolean is `true`: `IsVisibleInCsp` for the Customer Portal channel, `IsVisibleInPkb` for the public knowledge base, `IsVisibleInPrm` for partner. All three are Required and default to `false`.
- Article titles must use natural-language, customer-facing terminology — not internal support agent terminology.
- Search relevance is driven by the Knowledge search index, which weights title matches more heavily than body content. UNVERIFIED (2026-09-05): the relative weighting is not stated in the Metadata API Developer Guide or the Object Reference. The grounded, deployable adjacent levers are `KnowledgeSettings.enableKnowledgeTitleAutoComplete`, `enableKnowledgeKeywordAutoComplete` and `enableKnowledgeArticleTextHighlights`, all three of which default to `true`.

Pre-deflection is measured by the Case Deflection component, a standard Experience Cloud component that displays a "Did this article help?" prompt and tracks whether the customer proceeded to submit a case after viewing a suggested article. UNVERIFIED (2026-09-05): neither guide names this component or its prompt; the only deflection-tracking switch either guide carries is `KnowledgeSettings.enableChatterQuestionKBDeflection`, “tracking for case deflection via Chatter”. Build the measurement plan on the queryable metrics in `references/worked-examples.md` §5 and treat any component reading as corroboration.

### The Article Visibility Matrix

Portal visibility is not a channel assignment, a picklist, or a hierarchy. `Knowledge__kav` carries four independent Required boolean fields, and the three portal ones default to `false`:

| Channel | Field | Can a deploy or load set it? |
|---|---|---|
| Internal Articles tab | `IsVisibleInApp` | No — properties are Defaulted on create, Filter, Group, Sort |
| Public knowledge base | `IsVisibleInPkb` | Yes — Create and Update |
| Customer Portal | `IsVisibleInCsp` | Yes — Create and Update |
| Partner portal | `IsVisibleInPrm` | Yes — Create and Update |

Those same four names reappear as the `Channel` picklist on `KnowledgeArticleViewStat` and `KnowledgeArticleVoteStat` — `App`, `Pkb`, `Csp`, `Prm`, plus `AllChannels` for the total, which is what makes the measurement plan work: the flag you set and the channel you measure share one vocabulary. Data category visibility is a second, independent gate on top of these flags — see `admin/knowledge-base-administration`. The matrix, filled in, is in `references/worked-examples.md` §3.

### Record Exposure: Mechanisms, Not Flags

Every record the site shows needs one named mechanism: record ownership, a `SharingSet` access mapping, a `SharingGuestRule` (whose `accessLevel` "can be set only to `Read`"), data category visibility, or parent-record control. `Case.IsVisibleInSelfService` is none of these — its own field entry says it "does not alter sharing and will not prevent usage of a direct URL to a case if a portal user has read or write access", and its properties list carries neither Create nor Update. Agent replies reach the customer through `CaseComment.IsPublished`, which is "the only CaseComment field that can be updated via the API". Read `standards/decision-trees/sharing-selection.md` before committing a mechanism; the exposed-object table is in `references/worked-examples.md` §4.

### Help Center Search UX

The Help Center template on Experience Cloud provides a search-first landing experience — and does not support login. `ExperienceBundle` marks `loginAppPageId`, `forgotPasswordRouteId` and `selfRegistrationRouteId` all “Unsupported if the active Experience Builder template for the site doesn't support login (such as Help Center)”. Any journey past “read an article” belongs on Customer Account Portal (`templateName` “CPT Community Template”, theme `cpt`) or another login-capable template; see `references/gotchas.md` gotcha 6. The primary UX pattern is a prominent full-page search bar that queries both Knowledge articles and, optionally, community questions and answers. Design decisions for search UX:

- **Search bar placement:** Above the fold, without competing UI elements. Every additional nav item or promotional banner above the search bar reduces search usage.
- **Zero-results handling:** When search returns no results, the portal should immediately offer a case submission link — not a dead end. Unhandled zero-result states are a primary driver of customer frustration and channel escalation.
- **Faceted filtering:** Article category or product filters help customers narrow results when initial queries are broad, but should not be the primary navigation pattern. Most customers search rather than browse.
- **Article previews in search results:** The preview is an org-level switch per channel — `KnowledgeSettings.showArticleSummariesCustomerPortal`, `showArticleSummariesPartnerPortal`, `showArticleSummariesInternalApp`. Turn on the one matching the channel you opened. Displaying roughly the first 150–200 characters of body lets customers assess relevance before clicking, reducing pogo-sticking. UNVERIFIED (2026-09-05): the character count is a design convention; neither guide states a summary length.

### Friction-Calibrated Case Submission

Case form friction is a design lever, not an accident. The goal is to require just enough steps to confirm the customer has attempted self-service before submitting a case — without causing abandonment by customers who have a legitimate transactional or complex need.

Calibration model:
1. **Mandatory search prompt (low friction):** Display a search step before showing the case form fields. Requires one interaction but does not block submission. Appropriate for most orgs as a baseline.
2. **Required article acknowledgment (medium friction):** Customer must click through a suggested article before the Submit button activates. Increases deflection rate but also increases abandonment. Use only when article coverage for the top contact reason is high (>80% of cases have a matching article).
3. **Progressive disclosure (medium friction):** Show only subject and description fields first. Surface article suggestions. Only reveal category, priority, and attachment fields after the customer dismisses the suggestions. Balances deflection opportunity with form completion.
4. **No friction (baseline):** Direct case form with no pre-deflection. Appropriate only when the org has no published Knowledge base or when the portal audience is exclusively authenticated partners with time-sensitive transactional requests.

High friction designs — multi-step wizards requiring customers to confirm they searched, rate articles, and explain why no article helped — consistently produce abandonment rather than deflection. Abandoned sessions are not deflected cases; they are unresolved customer needs that resurface through phone or email channels.

### Community Peer Support Layer

A community forum layer (Chatter Q&A or Experience Cloud Questions component) enables customers to answer each other's questions, extending the effective knowledge base without requiring internal article authoring for every topic. Design requirements for a functional community peer support layer:

- **Active seeding is required at launch:** A community with zero answered questions produces zero deflection. Before launch, seed the community with 20–50 realistic Q&A pairs using internal content (converted from existing support macros, email templates, or FAQ documents). Unseeeded communities generate a "ghost town" perception that suppresses customer engagement.
- **Expert recognition:** Visible reputation indicators (badges, answer counts, top contributor labels) drive ongoing community participation. Without recognition, high-quality contributors stop answering after initial engagement.
- **Moderation queue:** Community content requires moderation to prevent misinformation from deflecting customers to incorrect answers. Plan for a moderation workflow before enabling community Q&A for public deflection.
- **Answer promotion:** Promoting community answers to Knowledge articles for high-traffic topics creates a compounding deflection effect. This requires a workflow connecting Community question resolution to the Knowledge authoring process.

### Deflection Rate Measurement

The Case Deflection component on Experience Cloud sites tracks article views during case creation and records whether the customer submitted a case after viewing an article. The standard metric is:

**Case Deflection Rate = (Article Views During Case Creation that Did Not Result in a Case Submission) / (Total Article Views During Case Creation)**

That ratio depends on a component reading. Four metrics that do not — portal article consumption by `Channel` from `KnowledgeArticleViewStat`, article quality from `KnowledgeArticleVoteStat`, deflection *failure* from `CaseArticle`, and contact rate from `Case` — are written out with their SOQL in `references/worked-examples.md` §5. Compute both; report the queryable set.

Measurement design requirements:
- Deflection rate is a lagging metric. It does not improve until article quality and findability improve. Design for article findability first; measure deflection rate as a validation signal, not a primary leading indicator.
- Baseline contact volume must be established before portal launch. Without a pre-launch baseline, you cannot demonstrate deflection impact to stakeholders.
- Track deflection by contact reason, not just aggregate. Aggregate deflection rate masks which topic areas are working and which need article investment.
- Distinguish between deflection (customer found answer) and abandonment (customer gave up). The Case Deflection component's "Did this article help?" prompt captures intent, but low response rates to that prompt mean the metric is an approximation.

---

## Common Patterns

### Pattern: Search-First Help Center with Pre-Submission Article Surfacing

**When to use:** The org has a published Knowledge base covering the top 5–10 contact reasons, and the goal is to reduce inbound email-to-case or web-to-case volume.

**How it works:**
1. Build the portal on a login-capable template — Customer Account Portal (`templateName` "CPT Community Template") or Customer Service — unless *every* journey in scope is anonymous, in which case Help Center is fine. Help Center cannot carry a login page, a forgot-password route, or self-registration, and ships no generic record pages, so "track my case" is a blank menu item on it.
2. Place the search bar as the primary above-the-fold element with no competing UI.
3. Add the Case Creation component to the Contact Support page and enable Knowledge article suggestions in the component settings. Configure the component to display suggestions after the customer enters a subject.
4. Add the Case Deflection component to track whether customers who viewed a suggestion submitted a case.
5. Configure zero-results search behavior to show a "Contact Support" call-to-action immediately below the empty results message.
6. Set article view targets: any article with fewer than 50 views per month in a portal with 500+ monthly case submissions is likely not surfaced effectively — investigate search index positioning and title terminology.

**Why not the alternative:** Relying on article browsing (category navigation) instead of search-first design produces lower deflection rates because customers with urgent questions do not browse — they search. Category navigation serves customers exploring a product; search serves customers with a specific problem.

### Pattern: Friction Gate with Mandatory Search Before Case Submission

**When to use:** Article coverage for the top three contact reasons is high, but customers are bypassing the Help Center and submitting cases directly through bookmarked URLs or email.

**How it works:**
1. Remove direct links to the case submission form from portal navigation and email footers.
2. Route all case submission entry points through a search landing page that requires one search query before the case form link appears.
3. Use Experience Cloud page visibility rules or a custom LWC component to conditionally show the case form link only after a search interaction event fires.
4. Monitor the abandonment rate at the search gate separately from the deflection rate. If abandonment spikes, the gate friction is too high for the audience.

**Why not the alternative:** Embedding the case form directly on the search results page (low-friction pattern) is appropriate when article coverage is incomplete. The mandatory search gate is only appropriate when coverage is high; applying it prematurely frustrates customers who correctly know no article exists for their issue.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Article base covers fewer than 50% of top contact reasons | Invest in article authoring before portal redesign | UX improvements cannot compensate for missing content |
| Portal is primarily authenticated community members | Enable Case Deflection component + community Q&A with seeded content | Authenticated users produce better deflection measurement and can participate in peer support |
| Any journey in scope requires a login | Do not use the Help Center template | `loginAppPageId`, `forgotPasswordRouteId` and `selfRegistrationRouteId` are unsupported on templates that do not support login, Help Center among them |
| The journey is "customer closes or re-opens their own case" | Requires Customer Community **Plus** | `CommunitiesSettings.enablePowerCustomerCaseStatus` "allows users with Customer Community Plus licenses to change case status" |
| Self-registration is requested | Decide the profile *and* the account in the same conversation | `selfRegistration` deploys without `selfRegProfile`; self-registering users must be tied to one account per site, or person accounts are created |
| Portal audience is unauthenticated public visitors | Search-first Help Center with pre-submission article surfacing only; no community Q&A | Unauthenticated visitors cannot participate in community; focus on Knowledge search quality |
| Org has Einstein Bot already handling first-contact deflection | Layer Help Center design to handle post-bot escalation path | Avoid duplicating deflection logic; portal is the fallback for cases the bot does not resolve |
| Stakeholder requires deflection metrics before launch | Establish baseline contact volume and contact reason distribution first | No baseline = no provable deflection impact post-launch |
| High-volume topic with no matching article | Prioritize article creation for that topic before adding friction | Adding friction when no article exists drives abandonment, not deflection |

---

## Recommended Workflow

1. **Inherit the persona and licence line.** Read the requirements catalogue produced by `admin/portal-requirements-gathering` (or run it first). Do not re-derive personas or licences here — but do read the two licence constraints in `references/worked-examples.md` §1, because they veto journeys.
2. **Write the journeys.** Fill `templates/self-service-design-template.md` §3. Every journey gets a persona, an entry point, a friction level and a success metric you can write as SOQL today. A journey whose metric cannot be queried goes back to the requester, not into the design.
3. **Fill the article visibility matrix and the exposed-object table.** One row per channel with its `Knowledge__kav` flag; one row per record the site shows, each naming a mechanism from the documented set. Route the mechanism choice through `standards/decision-trees/sharing-selection.md`, and hand the XML to `admin/experience-cloud-guest-access` or `admin/sharing-and-visibility` — this skill decides, it does not author.
4. **Decide self-registration, login and moderation.** Profile plus account for self-registration; template capability for login; moderation owner and rule budget. The worked shapes and their grounded constraints are in `references/worked-examples.md` §6–§7.
5. **Set the measurement plan.** Take the pre-launch baseline reading of M-4 (contact rate) *before* anything ships, then M-1 to M-3 from `references/worked-examples.md` §5. Name the owner and the intervention threshold.
6. **Lint the design, then the metadata.** Run `python3 scripts/check_self_service_design.py --file <design>.yaml --manifest-dir <metadata dir>`. It fails on unresolvable personas, undocumented sharing mechanisms, channel/flag mismatches, `IsVisibleInApp` rows, an unpaired `selfRegistration`, and skill paths that do not exist.
7. **Run the acceptance tests from an external-user session.** The eight in `references/worked-examples.md` §8, in a sandbox, never from an internal admin login. AT-02 and AT-04 are the two that most often fail late.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Baseline case volume by contact reason documented with pre-launch figures
- [ ] Knowledge article coverage confirmed for top 5 contact reasons (titles use customer-facing terminology, correct channel assignment)
- [ ] Search bar is the primary above-the-fold element with no competing navigation
- [ ] Zero-results search behavior routes to case submission, not a dead end
- [ ] Case submission flow includes pre-deflection article surfacing with calibrated friction level documented and justified
- [ ] Case Deflection component is configured and deflection rate measurement plan is defined
- [ ] Community Q&A either deferred (with documented reason) or launched with seeded content, moderation workflow, and expert recognition
- [ ] Every journey names a persona, an entry point and a success metric that is written as a query, not a hope
- [ ] Article visibility matrix filled: one row per channel, flag matched to channel, no attempt to set `IsVisibleInApp`
- [ ] Every exposed record names one sharing mechanism; nothing relies on `Case.IsVisibleInSelfService`
- [ ] Template choice checked against the login-bearing journeys before anything is built
- [ ] `selfRegistration` paired with `selfRegProfile` and an account assignment, with the duplicate-contact cleanup owner named
- [ ] `python3 scripts/check_self_service_design.py --file <design>.yaml --manifest-dir <metadata dir>` exits 0

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Deflection rate is a lagging metric — design for findability first.** The Case Deflection component reports on outcomes, not inputs. A portal can have well-designed UX and still show 0% deflection if articles are not published to the correct channel, use internal jargon in titles, or are not indexed by the Knowledge search engine. Practitioners who optimize UX before auditing article quality waste implementation effort on a metric that will not move.

2. **Article channel assignment must match the portal audience.** Knowledge articles must be explicitly assigned to the Customer Community, Partner Community, or Public Knowledge Base channel — whichever the portal uses. An article published to the wrong channel will not appear in portal search results even if it exists in the org and is visible to internal users. This is a common post-launch surprise when knowledge articles were authored for internal use and not re-assigned before portal go-live.

3. **Friction in the case form must be calibrated — too much friction drives abandonment, not deflection.** Multi-step pre-submission wizards that require customers to rate articles, confirm they searched, and explain why no article helped consistently produce form abandonment rates above 30% in customer service research. UNVERIFIED (2026-09-05): the >30%% figure is attributed to unnamed customer-service research; no Salesforce guide states an abandonment threshold. Treat it as a working heuristic and replace it with your own measured abandonment rate as soon as one exists. Abandoned sessions represent unresolved customer needs that migrate to higher-cost channels (phone, email escalation), not genuinely deflected cases. Measure abandonment separately from deflection and treat high abandonment as a friction miscalibration signal.

4. **Community peer support requires active seeding — an empty forum produces no deflection.** Experience Cloud Q&A launches with zero content. Portals that launch community forums without seeded Q&A content produce a "ghost town" perception that suppresses customer posting behavior. The deflection contribution from peer community is zero until answered questions accumulate. Plan for internal seeding (20–50 realistic Q&A pairs from existing support content) before launch.

5. **Case Deflection component only measures deflection during case creation — it does not capture self-service sessions that never reached the case form.** A customer who searches, finds an answer, and leaves without opening the case form at all is not counted by the Case Deflection component. Total deflection impact is higher than what the component reports. Supplement with contact rate trend analysis (total cases per 1,000 portal sessions month-over-month) for a more complete deflection picture.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Self-service design brief | UX structure, deflection mechanism specification, friction calibration decision, and measurement plan for the portal |
| Article coverage gap report | List of top contact reasons with no matching published Knowledge article, formatted as a backlog for the knowledge team |
| Deflection measurement plan | Case Deflection component configuration, reporting cadence, deflection rate baseline, and threshold for intervention |
| Community readiness assessment | Go/defer recommendation for peer community Q&A with seeding plan if proceeding |
| Self-service design YAML | The machine-readable design (`references/worked-examples.md` §9): journeys, exposed objects with their sharing mechanisms, article visibility matrix, self-registration and moderation decisions, metrics, acceptance tests — linted by `scripts/check_self_service_design.py` |
| Article visibility matrix | One row per channel with its `Knowledge__kav` flag, article count and owner — the handoff to `admin/knowledge-base-administration` |
| Acceptance test set | Given/When/Then tests runnable from an external-user sandbox session, including the cross-account case URL test |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/worked-examples.md` | Filling in the design — one Acme site worked end to end: personas and licence vetoes, five journeys, the article visibility matrix, the case and comment exposure model, four deflection metrics with SOQL, the self-registration and login decisions, the moderation policy, eight acceptance tests, and the YAML the checker lints |
| `references/gotchas.md` | An article, a case, a comment or a login does not appear where the design said it would — eleven platform behaviours behind those symptoms |
| `references/examples.md` | Working a real deflection problem end to end: a Help Center retitle, a partner-portal pre-submission gate, and the unseeded-community anti-pattern |
| `references/llm-anti-patterns.md` | Reviewing AI-generated self-service advice, especially "add the Case Deflection component" offered as a measurement plan |
| `references/well-architected.md` | Framing the article-quality-versus-UX and moderation-cost tradeoffs, and locating the source behind each claim |
| `templates/self-service-design-template.md` | Workflow step 2, and again at review time as the one-page record of every decision |
| `scripts/check_self_service_design.py` | Before the design leaves your hands, and again before the `Network` deploys |

---

## Related Skills

- `architect/case-deflection-strategy` — Use for org-wide deflection program design across all channels (bot, portal, email, chat). This skill focuses on portal UX design specifically; the architect skill covers cross-channel strategy, Einstein Bot integration, and Einstein Conversation Mining analysis.
- `admin/portal-requirements-gathering` — Run before this skill. Owns the persona / licence matrix, the requirements catalogue and the access-architecture decision that this design consumes.
- `admin/experience-cloud-site-setup` — Owns the `Network`, `CustomSite`, `NavigationMenu` and `ExperienceBundle` deploy set, template selection mechanics, branding and custom domain.
- `admin/experience-cloud-guest-access` — Owns the guest profile, external OWD, guest user sharing rules and route-level page access for every anonymous journey in this design.
- `admin/knowledge-base-administration` — Owns data categories, record types, the publishing workflow and category visibility, which gate article findability on top of the visibility flags.
- `admin/case-management-setup` — Owns the intake this site sits in front of: Web-to-Case, assignment, auto-response, escalation and the case model the portal exposes.
- `admin/experience-cloud-moderation` — Owns the `KeywordList` and `ModerationRule` metadata behind the moderation policy §7 sets.
- `admin/community-engagement-strategy` — Owns reputation levels, recognition and the contribution model behind the peer-support layer.
