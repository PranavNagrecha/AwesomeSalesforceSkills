# Gotchas — Well-Architected Review

---

## 1. Salesforce WAF Pillars (Trusted, Easy, Adaptable) Are Not the Same as AWS WAF or Salesforce CRM Analytics Pillars

The Salesforce Well-Architected Framework uses three top-level pillars: **Trusted**, **Easy**, and **Adaptable**. This is distinct from:

- **AWS Well-Architected Framework** which uses six pillars (Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization, Sustainability). AWS WAF pillar names appear in job descriptions, certifications, and team conversations. Do not conflate them with Salesforce WAF pillars.
- **Salesforce CRM Analytics (Tableau CRM)** has its own design best practices documentation that is unrelated to the WAF.
- **Older Salesforce architecture content** (pre-2022) sometimes uses different framing ("Build for scale", "Secure by default") that does not map cleanly to the current Trusted/Easy/Adaptable structure. Always use the current official WAF documentation as the reference.

When reviewing content written by others, confirm they are using the current Salesforce WAF definition before incorporating their ratings into your scorecard.

---

## 2. A Finding Without Severity and a Named Remediation Owner Is Not Actionable

A WAF review that lists findings without severity ratings and named owners produces no behaviour change. The most common failure mode is a review document that reads: "The org should improve its test coverage." Without: (a) a severity rating (Amber), (b) a specific current state (76%), (c) a target (85%), (d) a named owner (Delivery Lead), and (e) a target date (end of Q2), the finding will not be acted on.

Every finding in the review document must follow this structure:
- **Area:** What part of the org or solution is affected
- **Finding:** What the specific gap is, with a measurable current state where possible
- **Severity:** Red / Amber / Green
- **Recommendation:** A specific, actionable step — not "improve X" but "do Y by doing Z"
- **Owner:** A named role or individual, not "the team"
- **Target Date:** A specific date or quarter

A finding without all five fields is incomplete. Reviewers are frequently tempted to document what they found without telling anyone what to do about it. Resist this.

---

## 3. "Easy" Is the Most Overlooked Pillar — Orgs Obsess Over Security and Scalability While Adoption Silently Fails

Security gets board-level attention. Scalability gets attention after a governor limit incident. User experience gets attention only after adoption has already failed and the business is asking why the CRM data is unreliable.

"Easy" is frequently treated as a UX nicety rather than an architectural concern. It is not. Poor user experience is an architectural failure because it produces the same outcome as a system outage: users stop using the system. When users stop using Salesforce, they record data elsewhere (spreadsheets, email, personal notes), and the org becomes an unreliable system of record. Every downstream decision, report, and integration is then based on incomplete data.

During a WAF review, give the Easy pillar equal time. Specifically:
- Review page layouts for the two or three most-used objects with actual users present, not just admins
- Check field usage rates — a field with 0-5% population on a core object is a signal that something is wrong
- Ask users directly: "What do you do that takes the most time?" The answers are almost always Easy pillar findings
- Review whether automation is eliminating manual steps, not just automating existing ones

If stakeholders push back on spending review time on UX, explain: "An org that is secure and scalable but unusable is not a well-architected org. It is a well-locked-down liability."

---

## 4. WAF Reviews Go Stale — Build In a Re-Review Cadence From the Start

A WAF review conducted today reflects the org as it exists today. An org that is Green across all pillars in January can accumulate Amber and Red findings by December if development activity is high and no review gate is in place.

Recommend a re-review cadence as part of the review output:
- **Stable orgs (few releases per year):** Annual WAF review
- **Active orgs (releases monthly or more):** Semi-annual review, with a lightweight WAF checkpoint included in every major project sign-off
- **Post-incident:** Always conduct a focused WAF review after a production governor limit breach or security incident — the incident is evidence that the review cycle was too long

Document the next review date in the sign-off section of every WAF review deliverable. Assign a named owner for scheduling it. If no one is named, the review will not happen.

A WAF review without a follow-up date is a snapshot, not a governance process.

---

## Official Sources Used

- Salesforce Well-Architected Framework Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Well-Architected: Trusted — https://architect.salesforce.com/docs/architect/well-architected/guide/trusted.html
- Salesforce Well-Architected: Easy — https://architect.salesforce.com/docs/architect/well-architected/guide/easy.html
- Salesforce Well-Architected: Adaptable — https://architect.salesforce.com/docs/architect/well-architected/guide/adaptable.html
