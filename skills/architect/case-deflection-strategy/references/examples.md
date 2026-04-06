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
- Deflection rate: 27% (Salesforce industry average)
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
