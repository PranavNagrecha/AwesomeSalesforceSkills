---
name: portal-requirements-gathering
description: "Use when gathering requirements for a customer portal, partner community, or self-service Experience Cloud site. Triggers: 'gathering requirements for customer portal', 'planning Experience Cloud site', 'what license for community portal', 'portal user journey mapping', 'self-service requirements'. NOT for building the site in Experience Builder — use admin/experience-cloud-site-setup. NOT for designing the deal-registration and MDF processes themselves — use admin/partner-community-requirements. More trigger keywords: portal persona licence matrix, which Experience Cloud licence do these requirements imply, external user needs a Contact and Account, sharing set vs sharing rule for a portal, self-registration vs SSO for a portal, portal requirements catalogue, handoff to Experience Cloud site setup."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
  - User Experience
triggers:
  - "gathering requirements for customer portal"
  - "planning Experience Cloud site"
  - "what license for community portal"
  - "portal user journey mapping"
  - "self-service requirements"
  - "which Experience Cloud licence do our portal requirements imply"
  - "partners need to see each other's deals — what does the portal requirement need"
  - "write a requirements catalogue for a customer self-service portal"
  - "do we need sharing sets or sharing rules for this portal requirement"
  - "should the portal use self-registration or SSO"
  - "portal users have no Contact record yet"
  - "what do I hand the team before they build the Experience Cloud site"
tags:
  - experience-cloud
  - portal
  - requirements-gathering
  - self-service
  - customer-community
  - partner-community
inputs:
  - "Existing support channel data: case volume, channel mix, top contact reasons (60–90 days minimum)"
  - "Audience definition: customer vs. partner vs. internal vs. public/anonymous"
  - "Business goal: deflection target, partner enablement, account self-service, or combination"
  - "Existing Salesforce org context: licenses owned, orgs in scope, connected systems"
outputs:
  - "Signed-off access architecture decision (public / authenticated / hybrid)"
  - "User license selection per audience segment with rationale"
  - "Top-3 high-volume job list with success criteria"
  - "Content taxonomy and ownership matrix"
  - "Feature scope document: in-scope, deferred, and out-of-scope items"
  - "Deflection baseline and measurable goal"
  - "Persona / licence matrix with the App Limits allocation line per persona"
  - "Requirements catalogue YAML (persona, licence implication, access mechanism, downstream owner)"
  - "Signed handoff checklist to admin/experience-cloud-site-setup"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-04
---

# Portal Requirements Gathering

This skill activates when a BA, admin, or architect needs to elicit, structure, and lock in the decisions required before building a Salesforce Experience Cloud portal. It covers contact reason analysis, access architecture, license selection, user journey definition, and content taxonomy. It does not cover site configuration, theme setup, or post-launch optimization.

---

## Before Starting

Gather this context before working on anything in this domain:

- Pull at minimum 60–90 days of support contact data segmented by channel (phone, email, chat, web form). Without this baseline, feature prioritization is opinion-driven rather than data-driven.
- Identify the distinct audience segments the portal must serve. A portal that tries to serve customers, partners, and anonymous visitors under a single access model will require major rework later because access architecture is set at the Experience Cloud site level and is difficult to change post-launch.
- Confirm which Salesforce licenses the org currently owns. License type determines what objects, features, and sharing configurations are available. Recommending a portal design that requires a license the org does not own creates a hard blocker at build time.

---

## Questions to Ask Before Configuring

Ask these before writing a single requirement. Each one exists because skipping it produces a document that reads fine and cannot be built from; the gotcha it traces to is named in the last column of `references/gotchas.md`.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which records must an external user see that they do not own — and are those records related to their Account or their Contact?" | This is the sentence that picks the access mechanism. Related-to-my-account is a sharing set; related-to-a-person-below-me is a role hierarchy; neither is a sharing rule | The `object` / `userField` / `objectField` / `accessLevel` values for each sharing-set row, ready for `admin/sharing-and-visibility` |
| "Does any external persona need to see records owned by another external user beneath them?" | Role-hierarchy access belongs to specific portal user types, not to every Experience Cloud licence — a yes moves that persona onto a different licence and a different cost | A licence per persona that survives contact with the build team, instead of one licence for the whole portal |
| "Will any page be reachable without logging in, and which objects would the guest user then read?" | The guest identity is created by the site, not chosen; whatever it can read, the internet can read | A named security reviewer per guest-facing row and an explicit list of what the guest may not touch |
| "Does every intended portal user already exist as a Contact, on an Account?" | An external user record cannot be created otherwise. A persona with no natural Account is a data-model requirement wearing a portal requirement's clothes | The Contact/Account shape per persona, or a flagged data-model decision before build starts |
| "How does each persona get credentials: self-registration, admin provisioning, or SSO from the customer's own IdP?" | Self-registration is one switch for the entire site and every self-registered user lands on one profile | A duplicate control named per self-registration row and an IdP onboarding path per SSO row |
| "Are we buying per named user or per login, and how often will each persona actually log in?" | The two variants are separate allocation rows with different API allocations, so the choice reaches integrations, not just the invoice | The cheat-sheet allocation line beside each persona, and an answer to "does anything call the API as this user?" |
| "Which of this content is a record, which is Knowledge, and which is CMS?" | The three are governed by different mechanisms — sharing, data category visibility, and channel publishing — and only one of them is a sharing question at all | A content column in the catalogue that routes each row to the right downstream skill instead of to the sharing model by default |

What a proper requirements pass adds over just writing user stories: every row names the persona it serves, the licence that row implies, the mechanism that satisfies it, and the skill or person who builds it — so the build team starts without a single open question, and the licence decision is made while it is still free to change.

---

## Core Concepts

### Contact Reason Analysis (Answers / Status / Actions Framework)

Before defining any portal features, categorize 60–90 days of support contacts into three buckets:

- **Answers** — contacts where the customer needed information (e.g., "How do I reset my password?", "What is my contract end date?"). These are deflectable via knowledge articles and FAQ content.
- **Status** — contacts where the customer needed to check on something (e.g., "Where is my order?", "What is the status of my open case?"). These are deflectable via self-service visibility into records.
- **Actions** — contacts where the customer needed to do something (e.g., "I need to update my billing address", "I want to raise a return request"). These require transactional self-service capabilities.

The ratio of Answers : Status : Actions determines the portal's feature priority stack. A portal heavy in Answers needs a strong knowledge base. A portal heavy in Actions needs a robust case management and record-update layer. Skipping this analysis results in building features that do not reduce support volume.

### Access Architecture Decision

Experience Cloud sites have three access models:

- **Public / Unauthenticated** — any visitor can see content without logging in. Appropriate for knowledge bases, product documentation, and community forums with no personalization.
- **Authenticated** — visitors must log in to access the site. Required for any personalized content, record visibility, or transactional self-service.
- **Hybrid** — some pages are public, others require login. Requires careful sharing rule and page-level access design to avoid accidental data exposure.

This decision must be locked before any other design work begins. It governs the license model, the sharing architecture, the guest user profile configuration, and the data exposure risk posture. Changing from authenticated to hybrid after launch is a significant rework.

### License Type Selection Per Audience

Experience Cloud user licenses determine which standard and custom objects users can access and what features are available. The primary license types for portal use are:

| License | Use case |
|---|---|
| Customer Community | Suitable for B2C self-service portals. Provides access to standard Case, Contact, and Knowledge objects. Does not support Leads or Opportunities. |
| Customer Community Plus | Adds advanced sharing (criteria-based and manual sharing on custom objects), reports, and dashboards. Required when customers need to view or manage complex data sets. |
| Partner Community | Designed for indirect sales and PRM. Includes access to Leads, Opportunities, and partner-specific features. Required for deal registration and pipeline visibility use cases. |
| External Apps | The most flexible license for custom portal experiences; provides object access comparable to internal users at higher cost. Use when none of the community licenses cover the required object set. |

License selection is difficult and costly to change after user records are provisioned at scale. It must be locked during requirements, not during build.

### Top-3 High-Volume Jobs Model

Rather than building a feature list from wishlist conversations, the requirements process should identify the top 3 jobs customers most frequently need to complete. A "job" is defined as a task the customer is trying to accomplish, not a feature. Example jobs:

- "Check the status of my open support case"
- "Download my invoice"
- "Request a change to my service plan"

Each job should have a measurable success criterion (e.g., "customer can complete task without contacting support") and a baseline deflection target. Defer social features, gamification, idea exchanges, and community forums until the three core jobs are delivered and the deflection loop is validated.

---

## Common Patterns

### B2C Self-Service Support Portal

**When to use:** The primary goal is to reduce inbound support contact volume by enabling customers to find answers, check case status, and raise new cases without calling or emailing.

**How it works:**
1. Run contact reason analysis. Identify top 10 contact reasons; categorize as Answers, Status, or Actions.
2. Map each top contact reason to an Experience Cloud capability: Knowledge (Answers), case feed visibility (Status), web-to-case or case management (Actions).
3. Define authenticated access model. Customers log in with a Customer Community or Customer Community Plus license.
4. Set deflection baseline (current self-service containment rate) and target.
5. Defer idea exchange, chatter, and gamification to phase 2 after deflection goal is validated.

**Why not the alternative:** Building from a feature wishlist (search, FAQ, chat, forums, notifications) without contact reason grounding produces a portal with high feature count but low actual deflection, because the features do not map to the real reasons customers contact support.

### Partner Relationship Management (PRM) Portal

**When to use:** The portal must support indirect channel: deal registration, pipeline visibility, MDF requests, partner onboarding, or co-selling.

**How it works:**
1. Define partner tiers and what each tier needs to see and do (different job sets per tier).
2. Select Partner Community license. Confirm org has Sales Cloud enabled; PRM requires access to Lead and Opportunity objects.
3. Map access architecture: partners must be authenticated. Determine if partner account hierarchy is required (child partner accounts under master partner account).
4. Define content taxonomy: product enablement, partner agreements, co-marketing assets, deal registration forms.
5. Lock sharing model early — Partner Community uses role hierarchy and sharing rules. Confirm partner users should NOT see each other's opportunities (the default is account-scoped sharing).

**Why not the alternative:** Using Customer Community Plus for a PRM use case lacks Lead and Opportunity access, forcing workarounds that create data model debt and break standard Salesforce partner reporting.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| B2C customers need to view cases, download invoices, update contact info | Customer Community or Customer Community Plus | Standard objects covered; no Lead/Opp access needed |
| B2C customers need to share reports with each other or see complex custom object data | Customer Community Plus | Advanced sharing (manual + criteria-based on custom objects) required |
| Indirect sales channel: deal registration, pipeline, MDF | Partner Community | Lead and Opportunity access mandatory for PRM |
| Portal requires access to objects beyond standard community object set | External Apps license | Most flexible; evaluate cost vs. object coverage gap |
| Portal will have anonymous (non-logged-in) visitors AND authenticated users | Hybrid access model | Requires careful guest user profile lockdown; plan sharing rules for both populations |
| Deflection is primary goal; gamification/forums in scope | Defer social features | Validate deflection loop first; gamification adds scope without improving core self-service |
| Less than 60 days of contact reason data available | Delay feature scoping | Feature decisions made without data will misalign with actual customer needs |

---

## Recommended Workflow

1. **Pull the contact-reason baseline** — 60–90 days of support contacts, ranked by volume and split into Answers / Status / Actions. The SOQL that produces it, and the two ways the output is misleading, are in `references/examples.md` example 1. Nothing below is worth doing on stakeholder opinion.
2. **Build the persona / licence matrix** — one row per persona with a distinct record-visibility need, using section 8 of `templates/portal-requirements-gathering-template.md`. Record the App Limits allocation line beside each licence; the worked matrix is `references/worked-examples.md` section 1. Licence *selection* between login and member variants belongs to `architect/experience-cloud-licensing-model` — hand it this matrix rather than deciding here.
3. **Resolve each visibility requirement to one access mechanism** — read `standards/decision-trees/sharing-selection.md` first, then fill the implications table (`references/worked-examples.md` section 2). Sharing-set rows carry `object` / `userField` / `objectField` / `accessLevel`; role-hierarchy rows carry the partner account shape. Do not author the XML here — that is `admin/sharing-and-visibility`.
4. **Record the authentication decision per persona** — self-registration, SSO, admin-provisioned, login-only, or guest, with what each obliges downstream. `references/worked-examples.md` section 4 shows the four decisions and their consequences. Every self-registration row names its duplicate control before it can be signed.
5. **Write the requirements catalogue and lint it** — copy the YAML skeleton from section 9 of the template, then run `python3 scripts/check_portal_requirements_gathering.py --file <portal>-requirements.yaml`. It fails on rows missing a persona, licence, mechanism or downstream owner, on licence or status values outside the allowed set, on unresolvable repo paths, and on guest-facing rows with no named reviewer. Lint the narrative workshop doc separately with `--doc`.
6. **Walk the gotchas against the finished catalogue** — `references/gotchas.md` is written as a review pass, not background reading. Rows most likely to fail it: any sharing-set row whose licence is not on the `SharingSet` Special Access Rules list, any persona with no Contact, and any Knowledge row with no data category named.
7. **Run the handoff checklist and hand over** — `references/worked-examples.md` section 6. Requirements are complete when a builder can start without asking a question; the receiving skill is `admin/experience-cloud-site-setup` and the receiving agent is `/design-experience-cloud`.

---

## Review Checklist

Run through these before marking requirements complete:

- [ ] Contact reason analysis completed with 60–90 days of real data
- [ ] Each top contact reason categorized as Answers, Status, or Action
- [ ] Access architecture decision documented and signed off (public / authenticated / hybrid)
- [ ] License type selected and confirmed as owned by the org for each audience segment
- [ ] Top-3 high-volume jobs defined with measurable success criteria
- [ ] Deflection baseline and target recorded
- [ ] Content taxonomy documented with content owners named
- [ ] Deferred features listed explicitly (social, gamification, idea exchange)
- [ ] Out-of-scope items recorded to prevent scope creep at build time
- [ ] Requirements document reviewed with at least one technical stakeholder
- [ ] Persona / licence matrix complete: every persona names its Contact and Account shape
- [ ] Requirements catalogue passes `check_portal_requirements_gathering.py --file`
- [ ] Every guest-facing catalogue row names a security reviewer in `guest_review`
- [ ] Every `auth: self-registration` row names its Contact duplicate control
- [ ] Handoff checklist in `references/worked-examples.md` section 6 walked with the build team

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **License selection is a one-way door at scale** — Once thousands of partner or customer users are provisioned under a given license type, changing the license requires reprovisioning every user record. This is a bulk DML operation with significant risk and effort. The license decision must be final before any user provisioning begins.
2. **Guest user profile is shared across all public pages** — In a hybrid access model, the guest user profile applies to every public page on the site. Overly permissive guest user object access (e.g., read access on Account) creates data exposure risk that is invisible during requirements if access architecture is not locked early.
3. **Customer Community does not support manual sharing or role hierarchy on custom objects** — Teams that choose Customer Community and later discover they need to share custom object records selectively must upgrade to Customer Community Plus. This surprises teams who assumed all community licenses had equivalent sharing capabilities.
4. **Contact reason analysis is almost never done** — The most common failure mode in portal projects is skipping the data pull and jumping directly to feature selection. The result is a portal with search, chat, and a knowledge base that does not contain answers to the actual questions customers ask, achieving near-zero deflection.
5. **Gamification and social features defer deflection validation** — Adding idea exchange, chatter, and leaderboards to phase 1 shifts engineering effort away from the core self-service loop. Deflection is measurable; community engagement metrics are vanity metrics at the requirements stage.
6. **An external user record cannot exist without a Contact that already sits on an Account** — a persona described by job title rather than by its record shape blocks user creation at build time, and a B2C persona with no natural Account is a data-model decision that has to be made in requirements.
7. **Sharing sets are restricted to a named licence list** — one that is neither "Customer Community only" nor "all of them". A requirement that pairs a mechanism with a licence without checking the two against each other is unbuildable in both directions: it can over-scope the licence, and it can miss a sharing set that would have worked.
8. **Self-registration is one switch for the whole site** — every self-registered user lands on the single self-registration profile, and a person who already exists as a Contact registers a second time under a different spelling, splitting their history.

Each of these, plus data category visibility for external Knowledge and the login-vs-member API allocation split, is written up with its source lines in `references/gotchas.md`.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Contact Reason Analysis | Spreadsheet or document showing top 10 contact reasons, volume, and Answers/Status/Actions classification |
| Access Architecture Decision Record | Single-page document recording the access model decision, rationale, and technical sign-off |
| License Selection Matrix | Table mapping each audience segment to a license type with cost and coverage rationale |
| Top-3 Jobs Document | Three customer jobs with success criteria, deflection baseline, and target |
| Content Taxonomy and Ownership Matrix | List of content types, owners, and review cadence |
| Portal Requirements Scope Document | Full requirements document: in-scope features, deferred features, out-of-scope items |
| Persona / Licence Matrix | One row per persona: records they must see, licence implied, login vs member, and the App Limits allocation line for that licence |
| Requirements Catalogue (YAML) | The machine-readable artefact: id, statement, persona, licence implication, access mechanism, content type, auth, downstream owner, status. Linted by `scripts/check_portal_requirements_gathering.py --file` |
| Handoff Checklist | The signed list that closes requirements and opens `admin/experience-cloud-site-setup` |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/worked-examples.md` | You need the artefacts filled in: the persona/licence matrix, the access-model implications table, the requirements catalogue YAML, the authentication decision, the grounded NFRs, and the handoff checklist |
| `references/examples.md` | You are running the workshop itself — two full agendas (B2C support portal, PRM portal), the contact-reason SOQL, and how partner tiers become catalogue rows |
| `references/gotchas.md` | Reviewing a finished catalogue, or a requirement resolved to a mechanism suspiciously fast — ten platform behaviours that turn a signed document into an unbuildable one |
| `references/well-architected.md` | Justifying the licence and access-model tradeoffs to an architect, and for the grounded source list behind every platform claim in this package |
| `references/llm-anti-patterns.md` | An AI assistant produced the requirements — check its output against the failure modes it is most likely to have hit |
| `templates/portal-requirements-gathering-template.md` | Starting from a blank page: the nine-section workshop document, including the persona matrix and the catalogue YAML skeleton |
| `scripts/check_portal_requirements_gathering.py` | Before every handoff — `--file` / `--manifest-dir` lint the catalogue, `--doc` lints the narrative workshop document |

---

## Related Skills

- `admin/experience-cloud-site-setup` — the receiving skill: template choice, branding, navigation, domain. Everything this skill locks is its input
- `admin/sharing-and-visibility` — owns external OWD, sharing rules and the deployable `SharingSet` XML; every access-mechanism row in the catalogue is built there
- `admin/experience-cloud-guest-access` — owns guest profile lockdown and public-page object visibility; every guest-facing catalogue row hands off here
- `admin/experience-cloud-member-management` — owns adding external users, self-registration configuration and login page customisation
- `admin/experience-cloud-cms-content` — owns CMS workspaces and channels; catalogue rows with `content_type: cms` or `file` land here
- `admin/experience-cloud-moderation` — required before any user-generated-content requirement is released from deferred
- `admin/community-engagement-strategy` — reputation, ideation and recognition; where the deferred social rows go once the deflection gate is met
- `admin/partner-community-requirements` — the deal-registration, MDF and partner-tier process design this skill only records as personas
- `admin/duplicate-management` — matching and duplicate rules on Contact, mandatory for any self-registration row
- `admin/knowledge-base-administration` — Knowledge taxonomy and data categories behind the external data category visibility decision
- `admin/requirements-gathering-for-sf` — general Salesforce requirements practice; this skill is its portal-specific extension
- `architect/experience-cloud-licensing-model` — owns the login-vs-member and licence-tier selection this skill's persona matrix feeds
- `security/experience-cloud-security` — the site-level security posture the locked access model has to be reviewed against
- `security/guest-user-security` — the guest user's own record-access model, which the guest reviewer named in the catalogue signs against
- `security/sso-configuration` — the IdP onboarding path behind every `auth: sso` catalogue row
