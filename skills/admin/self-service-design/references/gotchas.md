# Gotchas — Self-Service Design

Non-obvious Salesforce platform behaviors and design failures that cause real production problems in this domain.

## Gotcha 1: Deflection Rate Is a Lagging Metric — Design for Article Findability First

**What happens:** Teams launch a redesigned Help Center, enable the Case Deflection component, and see no improvement in deflection rate for weeks or months despite increased portal traffic. The UX redesign is correctly implemented but produces no measurable deflection impact.

**When it occurs:** When the portal UX is improved without first auditing and fixing the article inventory. The Case Deflection component can only record deflections for articles that are found and read. If articles are not published to the correct Knowledge channel, use internal jargon in their titles, or are not indexed by the Knowledge search engine, no UX improvement will surface them. The deflection rate metric reports on outcomes; it cannot improve until the upstream article quality inputs are correct.

**How to avoid:** Make article coverage and findability a prerequisite gate before portal UX work begins. For each top contact reason: verify at least one article is published, assign it to the correct channel (Customer Community, Partner Community, or Public Knowledge Base), and confirm the article title uses the exact natural-language phrasing customers use in search queries. Run test searches from an unauthenticated or guest user session to verify articles appear in results before committing to UX design work.

---

## Gotcha 2: Friction in the Case Form Must Be Calibrated — Too Much Friction Drives Abandonment, Not Deflection

**What happens:** The org implements a multi-step pre-deflection workflow that requires customers to rate every suggested article, confirm they searched, and explain in a text field why no article answered their question. Form abandonment rate spikes above 30%. UNVERIFIED (2026-09-05): the >30%% figure is attributed to unnamed customer-service research; no Salesforce guide states an abandonment threshold. Treat it as a working heuristic and replace it with your own measured abandonment rate as soon as one exists. The deflection rate metric shows a modest improvement, but total unresolved customer contacts increase because abandoned sessions migrate to phone and email. Support cost per contact increases.

**When it occurs:** When friction is added to the case submission flow without measuring abandonment separately from deflection. Practitioners treat any case form exit as a deflection success. Customers who abandon the form out of frustration are not deflected — they are unresolved contacts who escalate to higher-cost channels. The Case Deflection component does not distinguish between satisfied deflection and frustrated abandonment.

**How to avoid:** Always instrument both metrics: deflection rate (customer found an answer) and form abandonment rate (customer left without submitting or finding an answer). Define abandonment as: customer started the case creation flow but did not complete a submission or click "This answered my question." Set a threshold — if abandonment exceeds 15–20%, reduce friction. Use progressive disclosure (low friction) or the mandatory search prompt with a clearly visible "I still need to submit" escape hatch rather than multi-step article rating requirements.

---

## Gotcha 3: Community Peer Support Requires Active Seeding — An Empty Forum Produces No Deflection and Suppresses Future Engagement

**What happens:** The org launches Experience Cloud Q&A or a Chatter Questions component expecting organic peer support to develop. The forum has zero content at launch. Early visitors see no activity, assume the channel is unused, and do not post questions. Within two weeks, posting rates drop to near zero. The community never recovers organic engagement because social proof (answered questions visible to new visitors) never accumulates.

**When it occurs:** When community peer support is planned as a deflection channel but the content seeding and community management requirements are scoped out of the launch plan as "Phase 2." In practice, Phase 2 never occurs for unseeded communities because the deflection data never supports investment in a channel that appears to have zero usage.

**How to avoid:** Treat community seeding as a launch prerequisite, not a post-launch activity. Before go-live: create 20–50 Q&A pairs using real customer question phrasings from historical case subjects, marked as best-answered. Assign two internal advocates with a 24-hour response SLA for the first 30 days. Set an expert recognition mechanism (reputation points, top contributor badges) active from day one. If these resources cannot be committed, defer community Q&A to a later phase rather than launching an unseeded forum.

---

## Gotcha 4: Article Channel Assignment Must Match the Portal Audience Type

**What happens:** Knowledge articles are published and visible to internal users but do not appear in Experience Cloud portal search results. The portal search returns zero results for queries that internal agents would answer immediately using the same Knowledge articles.

**When it occurs:** The mechanism is a field default, not a channel assignment. `Knowledge__kav` carries four independent Required booleans — `IsVisibleInApp`, `IsVisibleInCsp`, `IsVisibleInPkb`, `IsVisibleInPrm` — and the three portal ones are `false` until someone sets them. (`IsVisibleInApp` is the odd one: it is Required but its properties are "Defaulted on create, Filter, Group, Sort", with no Create and no Update, so no deploy or data load can touch it.) Articles authored for internal use therefore sit at `IsVisibleInCsp = false` by default. Experience Cloud portals surface articles only from channels explicitly assigned to the portal's audience: Customer Community for Customer Community portals, Partner Community for partner portals, or Public Knowledge Base for unauthenticated portals. An article assigned only to "Internal App" is invisible to all portal search, including the pre-deflection article suggestions in the Case Creation component.

**How to avoid:** Before portal launch, run a Knowledge article channel audit. Filter articles by the target contact reasons and verify each article has the correct Experience Cloud channel assigned. For articles authored internally and repurposed for the portal, the channel assignment requires explicit update in the article record — it does not carry over automatically when articles are published or promoted. Validate from a guest user or community member session, not from an internal admin session.

---

## Gotcha 5: The Case Deflection Component Undercounts True Deflection

**What happens:** The Case Deflection component reports a deflection rate of 12%. Leadership interprets this as the portal's total deflection impact and considers it insufficient. In reality, a large portion of portal-driven deflection occurs before customers reach the case creation flow — customers who search, find an answer, and leave without opening the case form at all are not counted by the component.

**When it occurs:** When the Case Deflection component metric is treated as the complete self-service deflection measurement rather than one instrument in a broader measurement set. The component only fires when a customer views a suggested article during case creation. It cannot observe customers who were deflected at the Help Center search page and never initiated case creation.

**How to avoid:** Supplement Case Deflection component data with contact rate trend analysis: total cases submitted per 1,000 portal sessions, tracked monthly before and after portal redesign. A declining contact rate with stable or growing portal traffic is a stronger signal of true deflection impact than the Case Deflection component metric alone. Report both metrics to stakeholders and be explicit about what each measures.

---

## Gotcha 6: The Help Center Template Cannot Carry a Login, and That Is Not a Configuration Problem

**What happens:** A self-service redesign picks the Help Center template — the one whose name matches the goal — and builds the anonymous search experience on it. Then the authenticated half of the scope arrives: My Cases, case comments, self-registration. There is no login page to configure, no forgot-password route, and no self-registration route. The project either rebuilds the site on a different template or ships a public-only portal that was scoped as a customer portal.

**When it occurs:** Whenever template selection precedes the journey list. The `ExperienceBundle` field table states the constraint three separate times, once per property: `loginAppPageId` ("Represents the ID of the login page"), `forgotPasswordRouteId`, and `selfRegistrationRouteId` are each annotated "Unsupported if the active Experience Builder template for the site doesn't support login (**such as Help Center**)". It is stated as a property-level note, not as a template limitation headline, which is why it is routinely missed. The same section's `templateName` list gives the login-capable alternatives: `CPT Community Template` (Customer Account Portal), `PRM Community Template` (Partner Central), and the Build Your Own / Microsite LWR starters.

**How to avoid:** Write the journey list first (see `worked-examples.md` §2) and mark each journey authenticated or anonymous. If any journey is authenticated, the template is not Help Center. Template selection is also permanent once the site is created — see `admin/experience-cloud-site-setup` gotcha 1 — so this is a decision with no cheap reversal.

---

## Gotcha 7: `Case.IsVisibleInSelfService` Is Not a Security Control, and the Object Reference Says So Outright

**What happens:** A design specifies "cases are visible to the portal when `IsVisibleInSelfService` is true". A portal user is then handed, or guesses, the URL of another account's case — and it opens.

**When it occurs:** Whenever the flag is treated as an access mechanism rather than a legacy display filter. The Object Reference is unusually direct: the field "is applied for case visibility in the Partner Relationship Management, Customer Service Portal, and the earlier version of Self Service Portal", and then — "**The field does not alter sharing and will not prevent usage of a direct URL to a case if a portal user has read or write access.**" Its property list carries neither Create nor Update, so a data load or Apex cannot set it either. The same trap has a benign twin on `Task` and `Event`, where `IsVisibleInSelfService` *is* Create/Update-able and does control whether an activity shows to an external user — which is exactly why the Case one looks like it should work the same way.

**How to avoid:** Name the real mechanism for every record the site exposes: record ownership, a `SharingSet` access mapping, a guest user sharing rule, or parent-record control. Route the choice through `standards/decision-trees/sharing-selection.md`. Then run acceptance test AT-04 in `worked-examples.md` §8 — one portal user opening another account's case by direct URL — from an external-user session, and expect `INSUFFICIENT_ACCESS`.

---

## Gotcha 8: A Case Comment Cannot Be Corrected, Only Added To

**What happens:** An agent publishes a case comment containing the wrong figure, or internal wording, to a customer. They open the case to edit it and cannot. They try to delete it and cannot.

**When it occurs:** On every org that has not granted Modify All Records on Case. The Object Reference states the constraint twice, from both directions. On the field: `IsPublished` "indicates whether the CaseComment is visible to customers in the Self-Service portal … **This is the only CaseComment field that can be updated via the API.**" In Usage: "CaseComment records can't be modified after insertion unless the user has the 'Modify All Records' object-level permission for Cases or the 'Modify All Data' permission. If not, users can only update the `IsPublished` field, and can't delete CaseComment." So the one repair available to a normal agent is to flip `IsPublished` back to `false` — which un-publishes it but does not un-send the notification, if `Network.caseCommentEmailTemplate` is configured.

**How to avoid:** Decide `CaseComment` versus feed deliberately rather than by default. `CaseComment` buys the `IsPublished` gate and the email hook; feed buys moderation (`ModerationRule` targets `FeedItem.RawBody` and `FeedComment.RawCommentBody`) and editability, at the cost of a per-post customer-visibility flag. If `CaseComment` wins, write the correction convention into the agent runbook — a new comment that supersedes, never a silent un-publish — and make sure the console layout shows `IsPublished` before the agent types, not after.

---

## Gotcha 9: `selfRegistration` Deploys Without a Profile and Without an Account, and Fails at Both Layers

**What happens:** Self-registration is turned on for the site. The deploy is green. A visitor fills in the registration form and gets an error, or — worse — succeeds and lands on an account nobody expected, duplicating a Contact that already existed.

**When it occurs:** Two independent halves are missing, and neither is enforced at deploy time.

- **The profile.** `Network.selfRegProfile` is "the profile assigned to users who self-register. This value is used only if `selfRegistration` is enabled for the site." The dependency runs one way only; nothing states that `selfRegistration` requires `selfRegProfile`, and nothing rejects the file when it is absent.
- **The account.** Self-registration also needs an account, and it lives on a separate object entirely: `NetworkSelfRegistration`. "Self-registering users in an Experience Cloud site are **required** to be associated with an account, which the admin must specify while setting up self-registration for the site. **If an account isn't specified, Salesforce creates person accounts (when enabled) for self-registering users.**" And there is no per-domain or per-segment routing: "You can use only one account per Experience Cloud site to assign self-registering users."

For a B2B portal that single holding account is a design decision with a tail: every self-registered user starts on the wrong account and needs re-parenting, and the Contact they arrive as may duplicate one that already exists (see `admin/portal-requirements-gathering` gotcha 10).

**How to avoid:** Treat self-registration as three decisions recorded together — on/off, `selfRegProfile`, and the `NetworkSelfRegistration.AccountId` holding account — plus a named owner for the duplicate-contact and re-parenting cleanup. `scripts/check_self_service_design.py` fails the `Network` file on the unpaired case and fails the design YAML when `self_registration.enabled` is true without both a profile and an account assignment.

---

## Gotcha 10: The Moderation Budget Is Org-Wide, and a Late Site Finds It Spent

**What happens:** The community layer of a new self-service site is designed with six moderation rules and two keyword lists. The deploy fails, or Setup refuses to save, because the org is already at its ceiling from other sites.

**When it occurs:** When the design assumes moderation limits are per site. Both are stated per org, in the guide's own emphasis. `KeywordList`: "Your org can have up to **30** keyword list criteria. This limit is **per org, not per Experience Cloud site**. A keyword list can have up to 2,000 keywords." `ModerationRule`: "Your org can have up to **30** rules. This limit is per org, not per site. This limit includes both content rules and rate rules. Each rule can have up to three keyword criteria." Two further behaviours surprise people who budget only the counts: rules run in a fixed order regardless of authoring order — "Rules that block content run first, followed by rules to review and approve content, then rules that replace content, and last by rules that flag content. If two or more rules perform the same action, the oldest rule runs first" — and "Rules to replace content don't run when the content also applies to a review rule."

**How to avoid:** Count the org's existing `ModerationRule` and `KeywordList` components before designing the moderation policy, and record the budget you are claiming in the design YAML (`moderation.keyword_lists_used`, `moderation.moderation_rules_used`). Share one keyword list across sites rather than cloning it. The rule and keyword XML belongs to `admin/experience-cloud-moderation`; this skill only sets the policy and the budget.

---

## Gotcha 11: The Browse Tree Caps at 25 Topics, and Only Navigational Topics Nest

**What happens:** A knowledge taxonomy of 40 data categories is handed over as the browse structure for the site. Roughly two thirds of it goes in; the rest silently has nowhere to sit.

**When it occurs:** When the site's navigational topic tree is treated as a mirror of the data category tree. `ManagedTopics` `position` "arranges the Topics menu in the Experience Cloud site" and takes "a number between 0 and 24. (**The maximum amount of navigational or featured topics is 25.**)" The second constraint is on nesting: `parentName` names a parent topic, and "**Only navigational topics support parent-child relationships**" — featured topics are flat by construction. A third catch is deploy ordering: "The related Experience Cloud site must exist before you deploy managed topics."

**How to avoid:** Design the browse tree as a deliberate 8–12 top-level selection over the *highest-volume* contact reasons, with subtopics beneath the navigational ones, and let search carry the long tail. Then turn on `Network.enableTopicAssignmentRules`, which "enables the org to use rules to automatically assign topics to articles in a site … admins set up rules to map topics to Salesforce Knowledge data categories" — so the browse tree and the category tree stay connected without being maintained twice.
