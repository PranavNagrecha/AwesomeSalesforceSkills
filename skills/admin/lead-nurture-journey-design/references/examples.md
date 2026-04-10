# Examples — Lead Nurture Journey Design

## Example 1: B2B SaaS — Stage-Gated Program with Behavioral Advancement

**Context:** A B2B SaaS company with a documented content library (3 awareness guides, 2 case studies, 1 demo CTA page) wants to nurture mid-funnel prospects who have scored between 25–75 but have not yet reached the MQL threshold of Score >= 100 AND Grade >= B. Prospects were previously receiving the same three emails in fixed order regardless of engagement.

**Problem:** The previous approach was a flat drip sequence. Every prospect received the demo CTA email as the third email in the sequence regardless of whether they had opened the first two emails. The demo CTA to cold prospects produced a 0.8% click rate and generated Sales complaints about low-quality leads.

**Solution:**

```
Program Entry List: Dynamic list "Score 25-75, Grade C or better, not MQL, opted in"
Suppression List: "Existing Customers," "Competitors," "Opted Out"

Step 1 — Send Email: Awareness Guide ("5 Signs You Need a Better [Category] Tool")
Step 2 — Wait: 5 days
Step 3 — Rule: Did prospect click Step 1 email?
  YES path:
    Step 4a — Send Email: Case Study ("How [Customer] Reduced Costs by 40%")
    Step 5a — Wait: 5 days
    Step 6a — Rule: Did prospect submit the case study download form?
      YES path:
        Step 7a — Change Prospect Field: Nurture Stage = "Decision"
        Step 8a — Send Email: Demo Request CTA ("See it in action — book your demo")
        Step 9a — Wait: 3 days
        Step 10a — Rule: Prospect score >= 100 AND grade >= B?
          YES path: Notify User (Sales Rep), Create Task "Follow up MQL — demo CTA clicked"
          NO path: Add to list "Long-term Nurture," Exit program
      NO path:
        Step 7b — Send Email: Alternative Case Study (different vertical)
        Step 8b — Wait: 5 days
        Step 9b — Rule: Any email engagement in last 14 days?
          YES path: Route to Decision track (Step 7a above)
          NO path: Add to list "Long-term Nurture," Exit program
  NO path:
    Step 4c — Send Email: Second Awareness asset ("Industry Benchmark Report")
    Step 5c — Wait: 7 days
    Step 6c — Rule: Any engagement (open or click)?
      YES path: Advance to Consideration track (Step 4a above)
      NO path: Add to list "Re-engagement Sequence," Exit program
```

**Why it works:** Behavioral branching ensures the demo CTA only reaches prospects who have demonstrated engagement at earlier stages. Prospects who never open Awareness emails are routed to a re-engagement program rather than receiving a high-value conversion asset prematurely. The Case Study form submission is the key intent signal — it requires an active action, not just a passive open, before the prospect advances to Decision content.

---

## Example 2: Manufacturing — Re-engagement Program Before Database Suppression

**Context:** A manufacturing org with 12,000 prospects in MCAE has 4,800 records that have not engaged with any marketing asset in 90+ days. Their average score is 8. Marketing is about to suppress all of them, but Sales flagged several as previously warm accounts.

**Problem:** Bulk suppression of 4,800 records with no re-engagement attempt would permanently remove prospects who might respond to the right content, including contacts at accounts Sales considers strategic. The org had no structured process for distinguishing recoverable cold prospects from truly dead records.

**Solution:**

```
Program Entry List: Dynamic list "Last activity > 90 days, score <= 15, opted in, not customer"
Suppression List: "Current Customers," "Opted Out," "Competitor Domains"

Step 1 — Wait: 2 days  (allow list to stabilize before first send)
Step 2 — Send Email: Re-engagement email — Subject: "[First Name], is this still relevant?"
  Body: Brief value proposition recap + link to top-performing resource from last 6 months
Step 3 — Wait: 7 days
Step 4 — Rule: Did prospect open or click Step 2 email?
  YES path:
    Step 5a — Remove from List: "Cold Prospects Q1"
    Step 6a — Add to List: "Awareness Nurture — Reactivated"
    Step 7a — Change Prospect Field: Nurture Stage = "Awareness (Reactivated)"
    Step 8a — Exit program (prospect enters standard nurture program)
  NO path:
    Step 5b — Send Email: Final re-engagement — Subject: "Last chance to stay in touch"
      Body: Stronger offer (free assessment, exclusive webinar registration)
    Step 6b — Wait: 7 days
    Step 7b — Rule: Any engagement?
      YES path: Route to reactivated track (Step 5a above)
      NO path:
        Step 8b — Change Prospect Field: Marketing Status = "Dormant"
        Step 9b — Add to List: "Suppression — Dormant Q1"
        Step 10b — Exit program
```

**Why it works:** The two-step approach recovers re-engageable prospects before suppression while creating a clean, auditable "Dormant" status for records that did not respond to either outreach. Sales can export the "Dormant" list for account-level review before final suppression. The Change Prospect Field step creates a reporting field that distinguishes suppressed records from opted-out records in future pipeline analysis.

---

## Anti-Pattern: Building the Program Before the Content Inventory Exists

**What practitioners do:** Open Engagement Studio, create the program shell with placeholder "Send Email" steps, and plan to fill in the email templates later. They map out the branching logic before knowing what content exists for each stage.

**What goes wrong:** When the content inventory is finally audited, it becomes clear that there is no Consideration-stage content at all (or only one asset). The branching logic has to be rebuilt from scratch because paths that were designed around multiple Consideration assets now have dead ends. More commonly, Decision-stage content (demo CTAs) ends up being placed after only one Awareness email — not because of a design decision, but because there is nothing else to send. The result is a program that sends a hard sales pitch to prospects who are not yet qualified.

**Correct approach:** Run the content inventory audit as step zero. Produce a table:

```
Stage        | Asset Name                        | Type          | CTA / Form?
-------------|-----------------------------------|---------------|-------------
Awareness    | "5 Signs You Need X" Guide        | PDF/Gated     | Yes — form
Awareness    | Industry Benchmark Report 2025    | Ungated blog  | No
Consideration| Customer Case Study — Healthcare  | PDF/Gated     | Yes — form
Consideration| ROI Calculator                    | Web tool      | No
Decision     | Demo Request Page                 | Landing page  | Yes — form
```

Only after every program step has a corresponding asset does Engagement Studio configuration begin. Gaps in the inventory are escalated to Marketing for content creation before the program launches.
