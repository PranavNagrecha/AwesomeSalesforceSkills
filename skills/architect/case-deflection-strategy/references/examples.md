# Examples — Case Deflection Strategy

## Example 1: Retail Bank Reduces Inbound Chat Volume 31% Using ECM + Bot

**Context:** A retail bank running Service Cloud and Messaging for In-App and Web was receiving approximately 12,000 chat sessions per month. Agents were spending 40% of handle time on three topics: account balance inquiry, statement download instructions, and card block/unblock requests. An Einstein Conversation Mining report on six months of transcripts confirmed these three topics represented 38% of all chat volume.

**Problem:** Without topic-level data, the deflection program team had been building bot dialogs for topics they assumed were common (loan application help, fraud reporting) rather than the actual high-frequency topics. After two quarters, deflection rate was under 8%.

**Solution:**

```text
ECM Report Output (simplified):
| Topic Cluster              | Volume Share | Complexity | Automation Potential |
|----------------------------|--------------|------------|----------------------|
| Account balance inquiry    | 17%          | Low        | High                 |
| Statement download         | 12%          | Low        | High                 |
| Card block/unblock         | 9%           | Medium     | Medium               |
| Loan application questions | 5%           | High       | Low                  |
| Fraud reporting            | 4%           | High       | Low                  |

Wave 1 bot dialogs built:
1. Balance inquiry → API callout to core banking system, returns current balance
2. Statement download → guided navigation link to authenticated portal page
3. Card block/unblock → Flow-driven action via Financial Services Cloud API

KPI targets set:
- Deflection rate: 30% (derived: wave-1 topics are 38% of volume; assumes ~80% of those resolve in-bot)
- Goal completion rate: 60%
- Containment rate: 45%
```

**Why it works:** ECM replaced assumption-driven topic selection with volume-validated data. Building wave 1 around the actual top 3 topics (17% + 12% + 9% = 38% of volume) gave the bot a chance to impact the majority of inbound traffic in the first release.

---

## Example 2: SaaS Company Implements Search-First Portal to Cut Email Case Volume

**Context:** A B2B SaaS company was receiving 4,500 cases per month via Web-to-Case. Case classification showed 52% were how-to and documentation requests answerable by existing knowledge articles. The Experience Cloud portal had 200+ published articles but a Web-to-Case form was the first element on the support page — customers submitted cases without searching first.

**Problem:** The support team had invested heavily in knowledge authoring but was not measuring article-solved rate, and the portal layout drove customers to the form before ever seeing articles. Deflection rate was effectively 0% for web channel contacts.

**Solution:**

```text
Portal flow change:
1. Customer navigates to support page
2. Search bar renders first — case form is below the fold
3. As customer types a subject, federated search returns top 3 matching articles
4. If customer clicks an article and spends >60 seconds on the article page → session tagged as "article-solved"
5. Case form is still accessible but requires scrolling past article results

Data category fix:
- Previous state: 180 of 200 articles assigned to top-level "Products" category only
- Fixed state: articles assigned to product-specific child categories matching
  the Experience Cloud channel's Data Category Group visibility settings
- Result: search relevance score improved significantly; articles now surface
  for the correct product context

30-day post-launch results:
- Article-solved rate: 34% of support page sessions ended without case submission
- Web-to-Case volume: down 29% month-over-month
- Deflection rate (web channel): 29%
- Goal completion rate (survey): 58%
```

**Why it works:** The search-first layout created behavioral deflection — customers who had an answerable question found the answer before reaching the case form. The data category fix was the prerequisite that made article search results relevant enough to trust.

---

## Anti-Pattern: Launching a Deflection Bot Before the Knowledge Base Is Ready

**What practitioners do:** Deploy an Einstein Bot with NLU-driven article search as the primary resolution path before auditing whether articles exist and are readable for the target topics.

**What goes wrong:** The bot starts conversations, customers ask questions, the bot searches for articles, finds nothing or finds agent-facing content written in technical jargon, and the session ends in escalation. Containment rate is low, CSAT drops, and the business loses confidence in the deflection program. The knowledge investment that was needed before launch is now politically harder to fund because "the bot doesn't work."

**Correct approach:** Run the knowledge readiness assessment before bot go-live. For each deflection candidate topic, a customer-readable article must exist, be published, and be visible on the target channel. If fewer than 70% of wave 1 topics have compliant articles, defer bot launch and run a knowledge sprint first.

---

## Example 3: Worked Decision Record and Baseline Queries for a Deflection Program

**Context:** A Service Cloud Enterprise Edition org receives about 9,000 cases a month. Email is the largest origin. A Messaging for In-App and Web channel launched six months ago. Leadership asked for "a bot to cut volume".

**Step 1: baseline, before any design.** Run these in the Developer Console or `sf data query`. They read standard objects only.

```soql
-- Q1. Volume by origin and reason, last 90 days (Case.Origin and Case.Reason are groupable picklists)
SELECT Origin, Reason, COUNT(Id) cases
FROM Case
WHERE CreatedDate = LAST_N_DAYS:90
GROUP BY Origin, Reason
ORDER BY COUNT(Id) DESC
LIMIT 50

-- Q2. Which articles customers already find (unique views per channel; drafts are not tracked)
SELECT ParentId, Channel, ViewCount, NormalizedScore
FROM KnowledgeArticleViewStat
WHERE Channel IN ('Pkb', 'Csp')
ORDER BY NormalizedScore DESC
LIMIT 50

-- Q3. Which articles agents attach to cases: the answers self-service failed to deliver
SELECT KnowledgeArticleId, COUNT(Id) attachments
FROM CaseArticle
WHERE CreatedDate = LAST_N_DAYS:90
GROUP BY KnowledgeArticleId
ORDER BY COUNT(Id) DESC
LIMIT 50

-- Q4. Readiness: published customer-facing articles missing a customer channel flag
SELECT Id, Title, IsVisibleInPkb, IsVisibleInCsp
FROM KnowledgeArticleVersion
WHERE PublishStatus = 'Online' AND Language = 'en_US'
  AND IsVisibleInPkb = false AND IsVisibleInCsp = false
```

UNVERIFIED (2026-10-03): which `KnowledgeArticleViewStat.Channel` value records views on an Experience Cloud site (`Csp` versus `Pkb`) is not stated in the Object Reference; check against a known article before trusting Q2. `CreatedDate` on `CaseArticle` is assumed from the standard audit fields; confirm with a describe call. Q4 filters `KnowledgeArticleVersion` by `PublishStatus` and `Language`, which that object requires.

**Step 2: the decision record.** It lives in the delivery repository at `docs/adr/0042-knowledge-led-deflection-before-bot.md`. It commits to metadata but deploys nothing itself; the metadata it names is listed with its `package.xml` type so the build team can scope the release.

```markdown
# ADR-0042: Knowledge-led, search-first deflection before an NLU bot

## Status
Accepted (2026-10-03), Service Design Authority

## Context
- Q1: Email 61%, Web 22%, Messaging 17% of 26,900 cases (90 days).
  Top five reasons = 41% of volume; four are informational.
- Messaging transcripts cover six months and one channel. Conversation
  Mining would see 17% of volume (Gotcha 2).
- Q3: 37 articles account for 70% of agent attachments. Q4: 22 of those
  37 have no customer channel flag (Gotcha 4).
- Knowledge is licensed: Enterprise Edition, Knowledge add-on.
- Customer-facing articles use two category groups (Product, Region).
  The guest profile has no Region visibility today (Gotcha 3).

## Decision
Wave 1 is a search-first help center on the existing Experience Cloud
site, gating the web case form behind article search for the four
informational reasons. Fix the 22 channel flags and grant guest and
customer visibility in the Region group before launch. Defer the NLU
bot to wave 2; reuse the messaging channel with a menu bot whose single
goal step is "article confirmed helpful".

## Consequences
### Positive
- Targets 41% of volume with no new licence.
### Negative
- Email volume (61%) is untouched until the auto-response links to
  articles in wave 2. Expect a smaller first-quarter drop than a bot
  vendor would promise.
- Two category groups double the visibility test matrix.

## Measurement (written before launch)
- Deflection rate = web help-center sessions with an article view and
  no case from the same contact within 72 hours / all help-center
  sessions. Containment is reported separately for the menu bot.
- Bot goal completion from the BotVersion goal step.

## Alternatives Considered
### NLU bot first on Messaging
Rejected: reaches 17% of volume; the transcript base is one channel.
### Agent-assisted deflection only (agents send articles)
Rejected: lowers handle time but not volume.

## Date
2026-10-03

## Deciders
- M. Okafor (Service Architect), J. Lind (Knowledge Lead), Service Design Authority
```

**Metadata the decision commits to** (for the release manifest; nothing here is generated by the ADR):

| What | Metadata API type | `package.xml` member form |
|---|---|---|
| Region and Product category groups | `DataCategoryGroup` | `<members>Region</members><name>DataCategoryGroup</name>` |
| Knowledge settings (if changed) | `KnowledgeSettings` | `<members>Knowledge</members><name>Settings</name>` |
| Help-center site pages | `ExperienceBundle` | `<members>Help_Center1</members><name>ExperienceBundle</name>` |
| Wave-2 menu bot with goal step | `Bot` (contains `BotVersion`) | `<members>Help_Bot</members><name>Bot</name>` |

The `Knowledge` member under `Settings` is grounded: the Metadata API Developer Guide says KnowledgeSettings "values are stored in a single file named Knowledge.settings" and that settings types "are accessed using the Settings name" in the manifest. The site and bot member names are placeholders for this org.

**Why it works:** the baseline queries turned "build a bot" into a ranked list grounded in the org's own objects. The record states the measurement before launch, names the visibility fixes that gate it, and records the cost (email untouched) that a later team would otherwise discover.

