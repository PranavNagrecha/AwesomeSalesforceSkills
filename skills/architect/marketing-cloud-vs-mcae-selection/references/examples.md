# Examples — Marketing Cloud vs. MCAE Selection

## Example 1: B2C E-Commerce Company Selecting MCE

**Context:** A national retail brand sells directly to consumers through an e-commerce site. They have a subscriber list of 2.3 million opted-in customers. Marketing needs include promotional email campaigns, abandoned cart journeys, SMS alerts for order status, and paid advertising retargeting using customer purchase data. The brand has a small inside sales team for business accounts but the dominant motion is self-serve consumer.

**Problem:** The marketing team initially assumed "Salesforce Marketing Cloud" referred to a single product. A vendor proposed MCAE (Account Engagement) as the solution. MCAE's prospect limit at the Premium edition is 75,000 records — the brand's 2.3 million subscriber list would require a non-standard, cost-prohibitive license. Additionally, MCAE does not support SMS or advertising audiences, which are core requirements.

**Solution:**

```
Platform selected: Marketing Cloud Engagement (MCE)

Edition: Marketing Cloud Advanced (includes Email Studio, MobileConnect, Advertising Studio)
Channels in scope: Email, SMS, Advertising (Facebook/Google retargeting)

Data model:
- Sendable Data Extension: "All_Subscribers" (EmailAddress PK)
- Behavioral DEs populated via Automation Studio jobs
- Contact Builder relationships for purchase history

Journey Builder use:
- Abandoned cart journey (triggered by data event on cart DE)
- Post-purchase follow-up series
- Re-engagement series for lapsed subscribers

MC Connect: Configured to sync opt-outs to Salesforce for the small B2B accounts segment

MCAE: Not purchased
```

**Why it works:** MCE's Data Extension model handles subscriber volumes in the millions without record limits. Journey Builder supports the cross-channel (email + SMS + advertising) orchestration the brand requires. MCAE's prospect model and edition limits would have been a structural mismatch from day one.

---

## Example 2: B2B SaaS Company Selecting MCAE

**Context:** A mid-market SaaS company sells a project management platform to enterprise customers. The sales cycle is 30–90 days, involves multiple stakeholders per account, and the SDR team needs to prioritize outreach based on prospect engagement. Marketing generates leads through webinars, gated content, and paid search. The Salesforce Sales Cloud org is the system of record for all pipeline activity.

**Problem:** The marketing team considered MCE because they had heard it was "more powerful." An architect evaluated the requirements and found that the core needs — real-time CRM sync, lead scoring, automated sales alerts on hot prospects, and Engagement Studio nurture sequences — are all native MCAE capabilities. MCE would require significant custom development to approximate any of these, and would not have bidirectional field sync with Salesforce Leads and Contacts out of the box.

**Solution:**

```
Platform selected: Marketing Cloud Account Engagement (MCAE), Advanced Edition

Edition rationale: Advanced supports up to 10K prospects, B2B AI features (Einstein Lead Scoring),
and advanced analytics. Current prospect database is ~6,000 records with 18-month growth
projected to 9,500 — within Advanced limits.

Scoring model:
- +10 email open, +20 email click, +50 form submission, +100 demo request
- Score decay: -5 per week of inactivity after 30 days

Grading criteria:
- Job title: VP/Director/C-level = A; Manager = B; Individual Contributor = C
- Company size: 500+ employees = A modifier; 100–499 = B; <100 = C
- Industry match: Target verticals receive upgrade; non-target receive downgrade

Engagement Studio programs:
- MQL nurture (triggered when score >= 75, grade >= B-)
- Recycled leads re-engagement (triggered by CRM field Recycle_Reason__c)
- Event follow-up series

Sales alerts: Pardot Automation Rule fires Salesforce task when prospect reaches score 100+

MCE: Not purchased
```

**Why it works:** MCAE's native CRM sync eliminates the need for custom integration. Scoring and grading automate pipeline prioritization that would otherwise require manual SDR review. Engagement Studio's prospect-level logic maps directly to the multi-step, rule-based nurture sequences the marketing team runs. The prospect volume is within MCAE Advanced limits.

---

## Anti-Pattern: Selecting MCAE for a High-Volume Consumer Email Program

**What practitioners do:** A practitioner recommends MCAE because the customer already has a Salesforce CRM and wants "tight integration." The use case is a weekly promotional email to 800,000 opted-in consumer subscribers with no sales team involvement.

**What goes wrong:** MCAE's prospect record limit at Premium edition is 75,000. An 800,000-subscriber list would require a non-standard enterprise contract at costs far exceeding what MCE would cost for the same volume. Additionally, MCAE lacks the batch sending infrastructure, deliverability tooling (IP warming, dedicated sending domains at scale), and suppression list management that MCE provides for consumer programs at this volume. Attempting to send 800K emails through MCAE would create deliverability and performance problems.

**Correct approach:** Select MCE for any consumer-facing, high-volume email program. Use MCE's Data Extensions to manage the subscriber list. If Salesforce CRM integration is needed for opt-out sync, configure Marketing Cloud Connect. Reserve MCAE for B2B prospect management and sales alignment use cases.
