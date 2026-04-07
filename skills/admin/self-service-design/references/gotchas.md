# Gotchas — Self-Service Design

Non-obvious Salesforce platform behaviors and design failures that cause real production problems in this domain.

## Gotcha 1: Deflection Rate Is a Lagging Metric — Design for Article Findability First

**What happens:** Teams launch a redesigned Help Center, enable the Case Deflection component, and see no improvement in deflection rate for weeks or months despite increased portal traffic. The UX redesign is correctly implemented but produces no measurable deflection impact.

**When it occurs:** When the portal UX is improved without first auditing and fixing the article inventory. The Case Deflection component can only record deflections for articles that are found and read. If articles are not published to the correct Knowledge channel, use internal jargon in their titles, or are not indexed by the Knowledge search engine, no UX improvement will surface them. The deflection rate metric reports on outcomes; it cannot improve until the upstream article quality inputs are correct.

**How to avoid:** Make article coverage and findability a prerequisite gate before portal UX work begins. For each top contact reason: verify at least one article is published, assign it to the correct channel (Customer Community, Partner Community, or Public Knowledge Base), and confirm the article title uses the exact natural-language phrasing customers use in search queries. Run test searches from an unauthenticated or guest user session to verify articles appear in results before committing to UX design work.

---

## Gotcha 2: Friction in the Case Form Must Be Calibrated — Too Much Friction Drives Abandonment, Not Deflection

**What happens:** The org implements a multi-step pre-deflection workflow that requires customers to rate every suggested article, confirm they searched, and explain in a text field why no article answered their question. Form abandonment rate spikes above 30%. The deflection rate metric shows a modest improvement, but total unresolved customer contacts increase because abandoned sessions migrate to phone and email. Support cost per contact increases.

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

**When it occurs:** Knowledge articles authored for internal use are assigned to the "Internal App" channel by default. Experience Cloud portals surface articles only from channels explicitly assigned to the portal's audience: Customer Community for Customer Community portals, Partner Community for partner portals, or Public Knowledge Base for unauthenticated portals. An article assigned only to "Internal App" is invisible to all portal search, including the pre-deflection article suggestions in the Case Creation component.

**How to avoid:** Before portal launch, run a Knowledge article channel audit. Filter articles by the target contact reasons and verify each article has the correct Experience Cloud channel assigned. For articles authored internally and repurposed for the portal, the channel assignment requires explicit update in the article record — it does not carry over automatically when articles are published or promoted. Validate from a guest user or community member session, not from an internal admin session.

---

## Gotcha 5: The Case Deflection Component Undercounts True Deflection

**What happens:** The Case Deflection component reports a deflection rate of 12%. Leadership interprets this as the portal's total deflection impact and considers it insufficient. In reality, a large portion of portal-driven deflection occurs before customers reach the case creation flow — customers who search, find an answer, and leave without opening the case form at all are not counted by the component.

**When it occurs:** When the Case Deflection component metric is treated as the complete self-service deflection measurement rather than one instrument in a broader measurement set. The component only fires when a customer views a suggested article during case creation. It cannot observe customers who were deflected at the Help Center search page and never initiated case creation.

**How to avoid:** Supplement Case Deflection component data with contact rate trend analysis: total cases submitted per 1,000 portal sessions, tracked monthly before and after portal redesign. A declining contact rate with stable or growing portal traffic is a stronger signal of true deflection impact than the Case Deflection component metric alone. Report both metrics to stakeholders and be explicit about what each measures.
