# Worked Examples — Self-Service Design

One design worksheet, filled in end to end, for the site that Acme Software puts in front of the
case-intake build in `skills/admin/case-management-setup/references/worked-example-case-intake.md`.
Every artefact here is copy-and-adapt shaped: the persona and licence line, the journey table, the
article visibility matrix, the case and comment exposure model, the deflection metrics with their
SOQL, the self-registration and login decisions, the moderation policy, the acceptance tests, and
the machine-readable YAML that `scripts/check_self_service_design.py` lints.

**Scenario.** Acme Software runs the Service Cloud intake built in the case-management worked
example: Email-to-Case on `support@acme.example` (~400/day) and `billing@acme.example`, a web form
(~60/day), three queues (`Tier_1_General`, `Tier_2_Support_Queue`, `Billing_Queue`), an escalation
rule and a Premier entitlement process. Roughly 9,600 cases a month reach a team of 18. Support Ops
wants a customer self-service site to take the repeat questions out of that flow — not to rebuild the
intake.

**What this page does not own.** The persona/licence catalogue belongs to
`skills/admin/portal-requirements-gathering` (`references/worked-examples.md` §1–§3, same Acme
account). The `Network` / `CustomSite` / `NavigationMenu` / `ExperienceBundle` deploy set belongs to
`skills/admin/experience-cloud-site-setup` (`references/metadata-examples.md`). The guest profile,
external OWD, guest sharing rules and route access belong to
`skills/admin/experience-cloud-guest-access` (`references/metadata-examples.md`, gates 0–6). Data
categories, record types and the publishing workflow belong to
`skills/admin/knowledge-base-administration`. Keyword lists and moderation rules belong to
`skills/admin/experience-cloud-moderation`. The XML below is here only where a *design* decision is
carried by a specific element; it cross-references those skills rather than restating them.

---

## 1. Personas and licence model (the line this design inherits)

The licence choice is made in `skills/admin/portal-requirements-gathering` and priced in
`skills/architect/experience-cloud-licensing-model`. Self-service design consumes it, because two
platform facts below make the licence a *design* input, not just a cost line.

| Persona | What they do on the site | Licence carried in from requirements | Design consequence that the guides ground |
|---|---|---|---|
| Anonymous visitor | Searches, reads articles, may open a case with no login | Guest user — consumes no user licence | Only `IsVisibleInPkb` articles reach them; every record they touch needs a `SharingGuestRule`, whose `accessLevel` "can be set only to `Read`" (api_meta.txt L129334) |
| End customer (support contact) | Reads articles, opens a case, tracks their own cases, comments | Customer Community Login | Contributes `Customer Community Login: 0` API calls per licence per 24 h (cheat sheet L534–L535) — a mobile or middleware caller acting *as this user* has no allocation of its own |
| Customer admin | Everything above, plus every case on their account | Customer Community Plus | `CommunitiesSettings.enablePowerCustomerCaseStatus` — "allows users with Customer Community Plus licenses to change case status" (api_meta.txt L112870–L112872). Case **status** editing by a portal user is a Plus-only capability; if the journey needs "customer closes their own case", the base licence cannot do it |
| Internal agent | Answers, publishes, moderates | Existing internal licence | Site member only via `Network.networkMemberGroups` plus `allowInternalUserLogin` (api_meta.txt L90695–L90697, L90963–L90971) |

Two design rules fall straight out of the table:

- **Do not design a "customer closes their own case" journey on a base Customer Community licence.**
  The org preference that permits it is scoped to Plus by its own description.
- **Do not design an API-backed companion app that authenticates as a Login-licence customer.** That
  licence row is `0`. Full allocation table: cheat sheet L525–L547 (Enterprise / Professional) and
  L555–L585 (Unlimited / Performance).

> Negative result worth recording: the App Limits Cheat Sheet has **no** rows for digital
> experiences, Knowledge, sites-per-org, deflection, or member counts. The only Experience Cloud
> numbers in that document are the per-licence API allocations above; it defers everything else with
> "For Experience Cloud limits, see Experience Cloud User Licenses" (L605). Do not quote a
> "max sites" or "max members" figure from it — it is not there.

---

## 2. Journeys

Five journeys, each with a persona, an entry point, and a success metric that can actually be
observed from a record or a stat object. A journey whose success metric cannot be queried is not a
journey — it is a hope.

| # | Journey | Persona | Entry point | Success metric (observable) | Friction level |
|---|---|---|---|---|---|
| J-01 | Find answer → deflect | anonymous-visitor | Search-engine result landing on an article URL | `KnowledgeArticleViewStat.ViewCount` where `Channel = 'Pkb'`, against contact volume for the same reason | none |
| J-02 | Search → deflect (logged in) | end-customer | Site search box | `KnowledgeArticleViewStat.ViewCount` where `Channel = 'Csp'` | none |
| J-03 | Log a case | end-customer | "Contact Support" after a search | Case created with `Origin = 'Web'`, article suggestions shown first | low — suggestions before fields |
| J-04 | Track a case | end-customer | "My Cases" list | Case detail opens for the case owner; no `INSUFFICIENT_ACCESS` | none |
| J-05 | Comment / escalate | end-customer | Case detail | `CaseComment` created by the portal user; agent reply visible when `IsPublished = true` | none |

Three platform facts constrain this table, and all three are the kind of thing a design gets wrong
once and then re-learns during UAT:

- **J-04 and J-05 need a record page that the Help Center template does not ship.** "The Help Center
  and LWR templates (Build Your Own and Microsites) don't include generic record pages. So if you
  create an object or global action type menu item that links to a Salesforce object, make sure that
  you also create the corresponding object pages. If you don't create the associated object pages,
  end users won't see anything if they click on the menu item." (api_meta.txt L90449–L90451.) A
  "Track my case" nav item on a Help Center site is a blank page until someone builds the Case page.
- **J-02, J-03, J-04 and J-05 need login, and the Help Center template does not support it.** See §6.
- **J-05's agent-visible-to-customer step is `CaseComment.IsPublished`, and it is the only field on
  that object the API can update after insert.** See §4.

---

## 3. Article visibility matrix

`Knowledge__kav` carries four independent required boolean flags, one per channel. They are not a
picklist, not a hierarchy, and not derived from each other.

| Channel | Field on `Knowledge__kav` | Properties (Object Reference L160929–L160955) | Acme value | Serves |
|---|---|---|---|---|
| Internal Articles tab | `IsVisibleInApp` | Required. **Defaulted on create, Filter, Group, Sort** — no `Create`, no `Update` | (platform-managed) | Agents |
| Public knowledge base | `IsVisibleInPkb` | Required. Create, Defaulted on create, Filter, Group, Sort, **Update** | `true` for the 22 deflection articles | J-01 anonymous-visitor |
| Customer Portal | `IsVisibleInCsp` | Required. Create, Defaulted on create, Filter, Group, Sort, **Update** | `true` for the same 22, plus 9 account-specific | J-02, J-03 end-customer |
| Partner portal | `IsVisibleInPrm` | Required. Create, Defaulted on create, Filter, Group, Sort, **Update** | `false` — no partner site in this release | — |

**How to read it**

- `IsVisibleInApp` is the odd one out: it is *Required* but its property list omits `Create` and
  `Update`, so a data load or Apex publish cannot set it. The three portal flags can be set, and
  default to `false`. "Articles are Internal-only by default" is the right conclusion for the wrong
  reason — the mechanism is that nobody ever set `IsVisibleInCsp`, not that anything assigned an
  Internal channel.
- The same four names reappear as the `Channel` picklist on `KnowledgeArticleViewStat` and
  `KnowledgeArticleVoteStat`: `AllChannels`, `App`, `Pkb`, `Csp`, `Prm` (Object Reference
  L162573–L162582, L162700–L162709). That is what makes §5's metrics work: the visibility flag you
  set and the channel you measure use one vocabulary.
- Data category visibility is a **second, independent** gate on top of these flags. An article with
  `IsVisibleInCsp = true` whose category is not visible to the portal profile still returns nothing.
  That gate is owned by `skills/admin/knowledge-base-administration` (`Profile.categoryGroupVisibilities`)
  and its "unclassified articles are invisible to standard users" gotcha; do not re-derive it here.

The article-summary switch that makes the search-result preview possible is org-level, not
site-level, and there is one per channel:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/settings/Knowledge.settings-meta.xml (excerpt) -->
<KnowledgeSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableKnowledge>true</enableKnowledge>
    <enableLightningKnowledge>true</enableLightningKnowledge>
    <defaultLanguage>en_US</defaultLanguage>

    <!-- Search-result previews. One switch per channel, all org-wide. -->
    <showArticleSummariesCustomerPortal>true</showArticleSummariesCustomerPortal>
    <showArticleSummariesPartnerPortal>false</showArticleSummariesPartnerPortal>
    <showArticleSummariesInternalApp>true</showArticleSummariesInternalApp>

    <!-- Search affordances. All three default to true (api_meta.txt L120561-L120590). -->
    <enableKnowledgeArticleTextHighlights>true</enableKnowledgeArticleTextHighlights>
    <enableKnowledgeTitleAutoComplete>true</enableKnowledgeTitleAutoComplete>
    <enableKnowledgeKeywordAutoComplete>true</enableKnowledgeKeywordAutoComplete>

    <!-- Pre-deflection: which Case fields feed article suggestion. -->
    <suggestedArticles>
        <useSuggestedArticlesForCase>true</useSuggestedArticlesForCase>
        <caseFields>
            <field><name>Subject</name></field>
            <field><name>Description</name></field>
        </caseFields>
    </suggestedArticles>

    <cases>
        <enableArticleCreation>true</enableArticleCreation>
        <!-- Names the Experience Cloud site(s) articles may be shared to from a Case. -->
        <articlePublicSharingCommunities>
            <site>Acme_Support_Help</site>
        </articlePublicSharingCommunities>
    </cases>
</KnowledgeSettings>
```

- Field names, types and the sample shape: api_meta.txt `KnowledgeSettings` L120504–L120890
  (`showArticleSummaries*` L120597–L120614, `suggestedArticles` / `useSuggestedArticlesForCase`
  L120751–L120760, `caseFields` L120775–L120790, `articlePublicSharingCommunities` L120652–L120655).
- `useSuggestedArticlesForCase` — "Indicates whether case content is used to suggest articles for
  cases" — plus `caseFields` is the *org-level* half of pre-deflection article surfacing. It is
  deployable, testable, and independent of whichever site component renders the suggestions. Design
  against it, and record which case fields feed it; the field list is a design decision, not a
  default.
- Settings files do not accept a `*` wildcard in `package.xml`: "The wildcard character `*` … doesn't
  apply to metadata types for feature settings" (api_meta.txt L120884–L120887). Name `Knowledge`
  explicitly.

---

## 4. Case and comment exposure model

Every record the site shows must name one mechanism from the documented set. "The portal shows it"
is not a mechanism.

| Record the site exposes | Audience | Mechanism | Metadata type / field | Owned by |
|---|---|---|---|---|
| The customer's own Cases | end-customer | Record ownership (the portal user is `OwnerId`) | `CustomObject.externalSharingModel` = Private | `skills/admin/sharing-and-visibility` |
| Every Case on the account | customer-admin | Sharing set — `object` `Case`, `userField` `Account`, `objectField` `AccountId`, `accessLevel` `Read` | `SharingSet` / `AccessMapping` | `skills/admin/sharing-and-visibility` |
| Published `Knowledge__kav` | anonymous-visitor | Guest profile object access + data category visibility | `Profile.categoryGroupVisibilities` | `skills/admin/experience-cloud-guest-access` |
| A public status-page record | anonymous-visitor | Guest user sharing rule (`Read` only) | `SharingRules.sharingGuestRules` | `skills/admin/experience-cloud-guest-access` |
| Agent replies on a case | end-customer | `CaseComment.IsPublished = true` on a comment the user can already reach through the parent Case | `CaseComment` | this design |

**`Case.IsVisibleInSelfService` is not on that list, and that is deliberate.** The Object Reference
is unusually blunt about it (L62504–L62513): its properties are "Defaulted on create, Filter, Group,
Sort" — no `Create`, no `Update` — and its description says the field "is applied for case visibility
in the Partner Relationship Management, Customer Service Portal, and the earlier version of Self
Service Portal", then adds: "**The field does not alter sharing and will not prevent usage of a
direct URL to a case if a portal user has read or write access.**" A design that puts case visibility
on this flag has designed nothing. Sharing is the mechanism; this field is a legacy display filter
with no security effect. Read `standards/decision-trees/sharing-selection.md` before committing a row
in the Mechanism column.

**`CaseComment` is the customer-visible comment surface, and `IsPublished` is the switch.** The
Object Reference (L63015–L63022) defines it as "whether the CaseComment is visible to customers in
the Self-Service portal (`true`) or not (`false`)" and states, in the field entry itself, "**This is
the only CaseComment field that can be updated via the API.**" The Usage section repeats the
constraint from the other side (L63046–L63050): "CaseComment records can't be modified after
insertion unless the user has the 'Modify All Records' object-level permission for Cases or the
'Modify All Data' permission. If not, users can only update the `IsPublished` field, and can't delete
CaseComment."

Design consequences, in order of how often they bite:

1. **There is no edit-your-comment journey.** An agent who types the wrong thing into a published
   comment cannot fix it without Modify All Records; and cannot delete it at all. If the design needs
   correction, it needs a *new* comment plus a documented convention, or it needs `FeedItem` instead.
2. **`CaseComment` vs `FeedItem` is a real fork, not a styling choice.** `CaseComment` gives you the
   `IsPublished` gate and an email hook (`Network.caseCommentEmailTemplate`, api_meta.txt
   L90717–L90721 — "Email template used when notifying members when a case comment has been modified
   or added to a case", with the guide's own caveat "Lightning email templates aren't packageable. We
   recommend using a Classic email template"). `FeedItem` gives you moderation
   (`ModerationRule` targets `FeedItem.RawBody` and `FeedComment.RawCommentBody`, api_meta.txt
   L89598–L89604) and no per-post customer-visibility flag. Acme chose `CaseComment` for case
   correspondence and feed for the community layer, and wrote the reason down.
3. **`CaseArticle` cannot be part of a portal-facing journey.** "Customer Portal users can't access
   this object" (Object Reference L62842). It is an agent-side association only, so it can
   report on deflection *failure* (see §5) but cannot render on the site.

---

## 5. Deflection metrics, and the SOQL that computes them

Three metrics. Each is a query an internal user can run, not a component reading that has to be taken
on trust.

**M-1 — Portal article consumption by channel.** `KnowledgeArticleViewStat` is read-only, tracks
published and archived articles only (draft views are not tracked), and is scoped by the `Channel`
picklist (Object Reference L162554–L162620).

```sql
-- Which published articles the self-service channel is actually reading.
-- ViewCount is "the number of unique views a published or archived article has received
-- in the selected channel" (Object Reference L162624-L162628).
SELECT ParentId, Parent.Title, ViewCount, NormalizedScore
FROM   KnowledgeArticleViewStat
WHERE  Channel = 'Csp'
ORDER  BY ViewCount DESC
LIMIT  50
```

Swap `Channel = 'Pkb'` for the anonymous journey (J-01). `NormalizedScore` is relative, not absolute:
"The article with most views has a score of 100. Other article views are then calculated relative to
this highest view score" (L162596–L162597), and it is time-weighted — "The normalized score for an
article is calculated based on views over time, with more recent views earning a higher score"
(L162624–L162628). Report `ViewCount` to stakeholders; use `NormalizedScore` only to rank.

**M-2 — Article quality signal.** `KnowledgeArticleVoteStat` gives a weighted 1–5 rating per channel,
with the trap stated in the guide: "Articles without recent votes trend towards an average rating of
three stars" (Object Reference L162698–L162700). A three-star article is *unrated*, not *mediocre* —
do not build an intervention threshold at 3.

```sql
SELECT ParentId, Parent.Title, NormalizedScore
FROM   KnowledgeArticleVoteStat
WHERE  Channel = 'Csp'
AND    NormalizedScore < 3
ORDER  BY NormalizedScore ASC
```

**M-3 — Deflection failure: cases opened on a topic that already had an article.** This is the metric
that moves the article backlog, and it is the inverse of a deflection rate — it needs no component and
no instrumentation.

```sql
-- Cases where an agent had to attach an article that the customer could have read themselves.
-- CaseArticle is agent-side only; portal users can't query it (Object Reference L62842).
SELECT CaseId, Case.Subject, Case.Origin, KnowledgeArticleId
FROM   CaseArticle
WHERE  Case.CreatedDate = LAST_N_DAYS:90
AND    Case.Origin IN ('Web', 'Email')
```

Join the `KnowledgeArticleId` values back to `Knowledge__kav.IsVisibleInCsp`: any article that shows
up here with `IsVisibleInCsp = false` is a one-line fix, and any that shows up with
`IsVisibleInCsp = true` is a findability problem (title vocabulary, category, or search terms), not a
coverage problem. That distinction is the whole point of the metric.

**M-4 — Contact rate, the denominator that keeps the other three honest.** Cases created per month
from portal-capable origins, against the pre-launch baseline captured in
`templates/self-service-design-template.md` §1.

```sql
SELECT Origin, COUNT(Id) caseCount
FROM   Case
WHERE  CreatedDate = LAST_N_MONTHS:6
GROUP  BY Origin, CALENDAR_MONTH(CreatedDate)
```

`KnowledgeSettings.enableChatterQuestionKBDeflection` — "Indicates whether tracking for case
deflection via Chatter is enabled" (api_meta.txt L120532–L120534) — is the one deflection-tracking
switch these guides name. UNVERIFIED (2026-09-05): the Experience Builder **Case Deflection**
component and its "Did this article help?" prompt, which the rest of this skill describes, appear in
neither the Metadata API Developer Guide nor the Object Reference; help.salesforce.com cannot be
fetched to confirm its behaviour or its reporting surface. Design the measurement plan on M-1 to M-4,
which are queryable, and treat any component reading as corroboration.

---

## 6. Self-registration, login, and the template constraint

**The finding that reorders this design.** The `ExperienceBundle` field table marks three login
properties "Unsupported if the active Experience Builder template for the site doesn't support login
(**such as Help Center**)":

| Property | Line | Note |
|---|---|---|
| `loginAppPageId` | api_meta.txt L60139–L60141 | "Represents the ID of the login page." |
| `forgotPasswordRouteId` | api_meta.txt L60117–L60120 | "the route to use when a user forgets their password" |
| `selfRegistrationRouteId` | api_meta.txt L60161–L60164 | "the login route to use for self-registration" |

So the Help Center template — the one every self-service redesign reaches for, and the one this
skill's Pattern 1 names — is the template that cannot carry J-02 through J-05. Acme's site is
therefore built on **Customer Account Portal** (`templateName` "CPT Community Template", theme
`cpt`) with the Help Center search patterns applied to it, not on Help Center. Allowed
`templateName` values are listed at api_meta.txt L60480–L60487 and the matching theme
`developerName` values at L60600–L60610.

`authenticationType` (LWR sites; Aura uses `isAvailableToGuests`) takes `AUTHENTICATED`,
`AUTHENTICATED_WITH_PUBLIC_ACCESS_ENABLED`, or `UNAUTHENTICATED` (api_meta.txt L60098–L60116). Acme
needs both a public article surface and a login, so it takes
`AUTHENTICATED_WITH_PUBLIC_ACCESS_ENABLED` — which is also what the guide recommends outright:
"`UNAUTHENTICATED` isn't supported for LWR sites created after Winter '23 through Experience Builder
or Connect API. To allow guest user access, we recommend using
`AUTHENTICATED_WITH_PUBLIC_ACCESS_ENABLED`."

**Self-registration is two decisions, and both must be recorded.**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/networks/Acme_Support_Help.network-meta.xml
     Self-service DESIGN decisions only. The full Network deploy set - branding,
     navigation, custom domain, emailSenderAddress, status transitions - belongs to
     skills/admin/experience-cloud-site-setup/references/metadata-examples.md, and the
     guest switches (enableGuestChatter / enableGuestFileAccess /
     enableGuestMemberVisibility) to skills/admin/experience-cloud-guest-access. -->
<Network xmlns="http://soap.sforce.com/2006/04/metadata">
    <site>Acme_Support_Help</site>
    <status>Live</status>
    <urlPathPrefix>help</urlPathPrefix>
    <description>Acme customer self-service. Knowledge + case intake + case tracking.</description>

    <!-- Decision 1: is self-registration on at all? -->
    <selfRegistration>true</selfRegistration>
    <!-- Decision 2: which profile do self-registered users land on?
         "The profile assigned to users who self-register. This value is used only if
         selfRegistration is enabled for the site." (api_meta.txt L91035-L91038) -->
    <selfRegProfile>Acme Customer Community Login User</selfRegProfile>

    <!-- Site membership. Profiles/permission sets only; a Chatter customer assigned a
         permission set that is also associated with a site is NOT added to the site
         (api_meta.txt L90963-L90971, NetworkMemberGroup L91430-L91443). -->
    <networkMemberGroups>
        <profile>Acme Customer Community Login User</profile>
        <profile>Acme Customer Community Plus User</profile>
    </networkMemberGroups>

    <!-- Case correspondence. Classic template on purpose: "Lightning email templates
         aren't packageable. We recommend using a Classic email template."
         (api_meta.txt L90717-L90721, L90722-L90725, L91097-L91100) -->
    <caseCommentEmailTemplate>Support_Templates/Case_Comment_Added</caseCommentEmailTemplate>
    <welcomeTemplate>Support_Templates/Portal_Welcome</welcomeTemplate>
    <changePasswordTemplate>Support_Templates/Portal_Password_Changed</changePasswordTemplate>
    <sendWelcomeEmail>true</sendWelcomeEmail>

    <!-- Community layer, phase 2. Off at launch, declared so the decision is visible. -->
    <allowMembersToFlag>true</allowMembersToFlag>
    <enableKnowledgeable>false</enableKnowledgeable>
    <enableReputation>false</enableReputation>
    <enableDirectMessages>false</enableDirectMessages>
    <enablePrivateMessages>false</enablePrivateMessages>
    <enableTopicSuggestions>false</enableTopicSuggestions>
    <enableTopicAssignmentRules>true</enableTopicAssignmentRules>
    <enableUpDownVote>true</enableUpDownVote>
</Network>
```

**How to read it**

- `selfRegistration` / `selfRegProfile` is a *pair*, and only one half is enforced. The guide states
  the dependency one-way — `selfRegProfile` "is used only if `selfRegistration` is enabled" — and
  says nothing about the reverse, which is why `selfRegistration` `true` with no `selfRegProfile`
  deploys clean and produces a registration form that cannot create a user.
  `skills/admin/experience-cloud-site-setup` gotcha 12 documents that failure; the checker in this
  skill fails the pair so the design never reaches deploy.
- **The profile is not the whole story: self-registration also needs an account.** The
  `NetworkSelfRegistration` object exists precisely for this — "Self-registering users in an
  Experience Cloud site are **required** to be associated with an account, which the admin must
  specify while setting up self-registration for the site. If an account isn't specified, Salesforce
  creates person accounts (when enabled) for self-registering users" (Object Reference
  L188832–L188838). And it is one account per site: "You can use only one account per Experience
  Cloud site to assign self-registering users" (L188899–L188902). For Acme's B2B model that single
  holding account is a design decision with a cleanup consequence — see §8's AT-06.
- `enableTopicAssignmentRules` earns its place in a self-service design: it "enables the org to use
  rules to automatically assign topics to articles in a site. After it's enabled, admins set up rules
  to map topics to Salesforce Knowledge data categories" (api_meta.txt L90893–L90897). That is the
  bridge between the browse taxonomy the visitor sees and the data categories the knowledge base is
  organised by, and it means the browse tree does not have to be maintained twice.
- The browse tree has a hard ceiling. `ManagedTopics` `position` takes "a number between 0 and 24.
  (**The maximum amount of navigational or featured topics is 25.**)" (api_meta.txt L86774–L86775),
  and "Only navigational topics support parent-child relationships" (L86755). A 40-item category tree
  cannot become a 40-item navigational topic menu. Acme's browse tree is 8 top-level topics.
- `Network.status` is required and takes `Live`, `DownForMaintenance`, or `UnderConstruction`, and
  the last of these is one-way: "After a site is published, it can never be in this status again"
  (api_meta.txt L91053–L91072). That is a release-plan constraint, not a design one — see
  `skills/admin/experience-cloud-site-setup` gotcha 7.

---

## 7. Moderation policy

Acme launches the community layer in phase 2, but writes the policy in phase 1 because two of the
platform limits are org-wide and shared with everything else the org moderates.

| Policy line | Metadata that carries it | Grounded constraint |
|---|---|---|
| Block profanity in posts, comments, link URLs, titles and poll choices | `ModerationRule` `action` `Block` over `FeedItem.RawBody`, `FeedComment.RawCommentBody`, `FeedItem.LinkUrl`, `FeedItem.Title`, `FeedPollChoice.ChoiceBody` | `RawBody` / `RawCommentBody` "aren't available in any other API" (api_meta.txt L89598–L89604) |
| Review first three posts from a new member | `ModerationRule` `action` `Review` + `userCriteria` | Rules run in order Block → Review → Replace → Flag; "If two or more rules perform the same action, the oldest rule runs first" (api_meta.txt L89492–L89494) |
| Members may flag | `Network.allowMembersToFlag` | "Flagged items are sent to a moderator for review" (api_meta.txt L90699–L90705); flags surface as `NetworkModeration` records with `ModerationType` `FlagAsInappropriate` / `FlagAsSpam` and `Visibility` `SelfAndModerators` / `ModeratorsOnly` (Object Reference L188697–L188760) |
| One shared keyword list | `KeywordList` | "Your org can have up to **30** keyword list criteria. This limit is **per org, not per Experience Cloud site**. A keyword list can have up to 2,000 keywords." (api_meta.txt L82185–L82186) |
| Budget the rule count | `ModerationRule` | "Your org can have up to **30** rules. This limit is per org, not per site. This limit includes both content rules and rate rules. Each rule can have up to three keyword criteria." (api_meta.txt L89484–L89485) |

Two org-level switches decide the *blast radius* of the policy, and they live in
`Communities.settings`, not on the site:

- `canModerateAllFeedPosts` — "allows moderation features, such as flags and rules, to be set on all
  feed posts **including** posts that are visible in Experience Cloud sites. When set to `false`,
  only feed posts in sites can be moderated. Default is `false`." (api_meta.txt L112809–L112813)
- `canModerateInternalFeedPosts` — "allows moderation features … to be set on record feed posts
  created by internal users. Such posts can also be visible in multiple sites. Default is `false`."
  (api_meta.txt L112814–L112818)

Both default `false`. Turning either on extends moderation over internal Chatter, which is an
org-wide decision that a self-service design does not get to make alone — flag it to the platform
owner. The rule and keyword XML itself is owned by `skills/admin/experience-cloud-moderation`;
the reputation and recognition model by `skills/admin/community-engagement-strategy`.

The 30-rule and 30-keyword-list ceilings are the reason the policy is written before the community
launches: they are org budgets, and a self-service site that arrives late finds them already spent.

---

## 8. Acceptance tests

Given / When / Then, each naming the sandbox persona and the observation. Run every one from an
external-user session, never from an internal admin session — the whole point is the audience that
cannot see what the admin sees.

| # | Given | When | Then |
|---|---|---|---|
| AT-01 | A Full or Partial sandbox with the site `Live`, and an article with `IsVisibleInPkb = true` | An anonymous browser opens the site search and queries the article's customer-phrased title | The article appears; `KnowledgeArticleViewStat` for `Channel = 'Pkb'` shows a `ViewCount` increment for that `ParentId` |
| AT-02 | The same article with `IsVisibleInCsp = false` | A logged-in Customer Community Login user searches the same phrase | Zero results — proving the two flags are independent, not inherited |
| AT-03 | `KnowledgeSettings.useSuggestedArticlesForCase = true` with `caseFields` = Subject, Description | A customer types a known contact reason into Subject on the case form | Suggestions render before the customer submits; a case created anyway is the M-3 population |
| AT-04 | A case owned by customer A's contact | Customer B's contact opens customer A's case by direct URL | `INSUFFICIENT_ACCESS`. If it opens, the design leaned on `Case.IsVisibleInSelfService`, which "does not alter sharing and will not prevent usage of a direct URL" (Object Reference L62512–L62513) |
| AT-05 | An agent adds a comment with `IsPublished = false`, then a second with `IsPublished = true` | The case contact opens the case in the portal | Only the second comment is visible; the agent then finds they cannot edit or delete either (Object Reference L63046–L63050) |
| AT-06 | `selfRegistration = true`, `selfRegProfile` set, `NetworkSelfRegistration.AccountId` pointing at the holding account | A new visitor self-registers with an email that already exists as a Contact | A user is created against the holding account, **not** the existing Contact's account. Confirm the duplicate-contact cleanup owner named in the design YAML — see `skills/admin/portal-requirements-gathering` gotcha 10 |
| AT-07 | `selfRegProfile` removed, `selfRegistration` left `true` | Deploy the `Network` | The deploy succeeds and the registration form fails at runtime. This is the case `scripts/check_self_service_design.py` exists to catch before deploy |
| AT-08 | A nav item pointing at Case on a Help Center-template site | A member clicks "My Cases" | A blank page, because "The Help Center and LWR templates … don't include generic record pages" (api_meta.txt L90449–L90451). Passing this test means the Case page was built, or the template was changed |

Run `scripts/check_self_service_design.py --file <design>.yaml --manifest-dir force-app/main/default`
before AT-01. It catches AT-07 and the article-visibility inconsistencies behind AT-02 statically.

---

## 9. The design artefact

The machine-readable form of everything above. `scripts/check_self_service_design.py --file` lints it.

```yaml
# acme-self-service-design.yaml
design: acme-support-help-centre
network_api_name: Acme_Support_Help
site_api_name: Acme_Support_Help
url_path_prefix: help
template: CPT Community Template            # NOT Help Center Template - see worked-examples.md section 6
authentication_type: AUTHENTICATED_WITH_PUBLIC_ACCESS_ENABLED
baseline_period: "2026-06-01 to 2026-08-31"
baseline_monthly_cases: 9600
upstream_requirements: skills/admin/portal-requirements-gathering

personas:
  - id: anonymous-visitor
    licence: guest
    owner: "Priya Raman (Support Ops)"
  - id: end-customer
    licence: customer-community-login
    owner: "Priya Raman (Support Ops)"
  - id: customer-admin
    licence: customer-community-plus
    owner: "Priya Raman (Support Ops)"

journeys:
  - id: J-01
    name: find-answer-and-deflect-anonymous
    persona: anonymous-visitor
    entry: "Search-engine result landing on a public article URL"
    success_metric: "KnowledgeArticleViewStat.ViewCount where Channel = 'Pkb', by contact reason"
    friction: none
    owner: "Priya Raman (Support Ops)"
    status: approved
  - id: J-02
    name: find-answer-and-deflect-authenticated
    persona: end-customer
    entry: "Site search box on the authenticated home page"
    success_metric: "KnowledgeArticleViewStat.ViewCount where Channel = 'Csp', by contact reason"
    friction: none
    owner: "Priya Raman (Support Ops)"
    status: approved
  - id: J-03
    name: log-a-case
    persona: end-customer
    entry: "Contact Support, reached after a search"
    success_metric: "Case created with Origin = 'Web' after suggestions were rendered"
    friction: low
    owner: "Priya Raman (Support Ops)"
    status: approved
  - id: J-04
    name: track-a-case
    persona: end-customer
    entry: "My Cases list on the authenticated home page"
    success_metric: "Case detail opens for the record owner with no INSUFFICIENT_ACCESS"
    friction: none
    owner: "Dan Ochieng (Service Delivery)"
    status: approved
  - id: J-05
    name: comment-and-escalate
    persona: end-customer
    entry: "Case detail page"
    success_metric: "CaseComment created by the portal user; agent reply visible when IsPublished = true"
    friction: none
    owner: "Dan Ochieng (Service Delivery)"
    status: approved

exposed_objects:
  - object: Knowledge__kav
    audience: anonymous-visitor
    sharing_mechanism: data-category-visibility
    built_by: skills/admin/experience-cloud-guest-access
  - object: Knowledge__kav
    audience: end-customer
    sharing_mechanism: data-category-visibility
    built_by: skills/admin/knowledge-base-administration
  - object: Case
    audience: end-customer
    sharing_mechanism: ownership
    built_by: skills/admin/sharing-and-visibility
  - object: Case
    audience: customer-admin
    sharing_mechanism: sharing-set
    built_by: skills/admin/sharing-and-visibility
  - object: CaseComment
    audience: end-customer
    sharing_mechanism: parent-record-controlled
    built_by: skills/admin/case-management-setup

article_visibility:
  - channel: pkb
    flag: IsVisibleInPkb
    value: true
    audience: anonymous-visitor
  - channel: csp
    flag: IsVisibleInCsp
    value: true
    audience: end-customer
  - channel: prm
    flag: IsVisibleInPrm
    value: false
    audience: none

self_registration:
  enabled: true
  self_reg_profile: "Acme Customer Community Login User"
  account_assignment: "NetworkSelfRegistration.AccountId -> Acme Self Service Holding"
  duplicate_contact_owner: "Priya Raman (Support Ops)"
  login_policy: "Password login plus SSO for customer-admin personas; internal login disabled"

moderation:
  members_may_flag: true
  keyword_lists_used: 1
  moderation_rules_used: 2
  moderator_owner: "Sara Novak (Community)"
  org_wide_switches_reviewed_by: "Platform Owner"

deflection_metrics:
  - id: M-1
    name: portal-article-consumption
    query: "SELECT ParentId, ViewCount FROM KnowledgeArticleViewStat WHERE Channel = 'Csp'"
    owner: "Priya Raman (Support Ops)"
  - id: M-3
    name: deflection-failure
    query: "SELECT CaseId, KnowledgeArticleId FROM CaseArticle WHERE Case.CreatedDate = LAST_N_DAYS:90"
    owner: "Priya Raman (Support Ops)"

acceptance_tests:
  - id: AT-01
    journey: J-01
    expect: "Public article returned to an anonymous session; Pkb ViewCount increments"
    owner: "Dan Ochieng (Service Delivery)"
  - id: AT-04
    journey: J-04
    expect: "Cross-account case URL returns INSUFFICIENT_ACCESS"
    owner: "Dan Ochieng (Service Delivery)"
  - id: AT-07
    journey: J-03
    expect: "Checker fails a Network with selfRegistration true and no selfRegProfile"
    owner: "Priya Raman (Support Ops)"
```

Lint it, together with the `Network` file, before anything is built:

```bash
python3 skills/admin/self-service-design/scripts/check_self_service_design.py \
    --file acme-self-service-design.yaml \
    --manifest-dir force-app/main/default
```

---

## Source lines used on this page

All line numbers are into the extracted text of the Summer '26 / v62 PDFs.

| Claim | Source | Lines |
|---|---|---|
| `Network` self-registration pair, member groups, email templates, topic and community switches, `status` enum | Metadata API Developer Guide, `Network` | api_meta.txt L90671–L91110 |
| `NetworkMemberGroup` profile / permission set, Chatter-customer exclusion | Metadata API Developer Guide | api_meta.txt L91430–L91443 |
| `ExperienceBundle` login properties unsupported on Help Center; `authenticationType`; template and theme names | Metadata API Developer Guide, `ExperienceBundle` | api_meta.txt L60098–L60164, L60480–L60487, L60600–L60610 |
| Help Center / LWR templates have no generic record pages | Metadata API Developer Guide, `NavigationMenu` | api_meta.txt L90449–L90451 |
| `ManagedTopics` 25-topic ceiling; navigational-only parent/child | Metadata API Developer Guide | api_meta.txt L86721–L86790 |
| `KeywordList` 30-per-org / 2,000-keyword ceilings | Metadata API Developer Guide | api_meta.txt L82177–L82190 |
| `ModerationRule` 30-per-org ceiling, action ordering, `RawBody` / `RawCommentBody` | Metadata API Developer Guide | api_meta.txt L89469–L89494 |
| `CommunitiesSettings` moderation blast radius; Plus-only case status | Metadata API Developer Guide | api_meta.txt L112766–L112818 |
| `KnowledgeSettings` article summaries, search affordances, suggested articles, site sharing | Metadata API Developer Guide | api_meta.txt L120504–L120890 |
| `SharingGuestRule` `accessLevel` `Read` only | Metadata API Developer Guide, `SharingRules` | api_meta.txt L129322–L129345 |
| `SharingSet` / `AccessMapping` licence list and mapping fields | Metadata API Developer Guide | api_meta.txt L130365–L130470 |
| `Knowledge__kav` `IsVisibleInApp` / `Csp` / `Pkb` / `Prm` properties | Object Reference | object_reference.txt L160929–L160955 |
| `KnowledgeArticleViewStat` / `VoteStat` channels, `ViewCount`, `NormalizedScore` | Object Reference | object_reference.txt L162554–L162720 |
| `Case.IsVisibleInSelfService` does not alter sharing | Object Reference, `Case` | object_reference.txt L62504–L62513 |
| `CaseComment.IsPublished` is the only API-updatable field; no delete | Object Reference | object_reference.txt L63015–L63050 |
| `CaseArticle` inaccessible to Customer Portal users | Object Reference | object_reference.txt L62831–L62842 |
| `NetworkSelfRegistration` account requirement, one account per site | Object Reference | object_reference.txt L188832–L188902 |
| `NetworkModeration` flag types and visibility | Object Reference | object_reference.txt L188697–L188760 |
| Per-licence API allocations for community licences | Salesforce App Limits Cheat Sheet | salesforce_app_limits_cheatsheet.txt L525–L547, L555–L585, L605 |

PDF sources: <https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf>,
<https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf>.
