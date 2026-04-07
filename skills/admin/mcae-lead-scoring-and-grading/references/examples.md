# Examples — MCAE Lead Scoring and Grading

## Example 1: Configuring a Combined MQL Automation Rule (Score >= 100 AND Grade >= B)

**Context:** A B2B SaaS company uses MCAE. Marketing has agreed with Sales that a Marketing Qualified Lead requires a score of at least 100 (behavioral engagement) and a grade of B or better (fit). Leads meeting both criteria should be assigned to the SDR queue in Salesforce and the SDR manager notified.

**Problem:** Without a grade gate, the SDR queue fills with high-activity low-fit prospects (competitors, students, job seekers) who waste SDR time. Without a score gate, high-fit cold prospects get routed before they've shown any interest.

**Solution:**

```
Automation Rule: MQL — Score and Grade Gate
Criteria (ALL must match):
  - Prospect Score is greater than or equal to 100
  - Prospect Grade is greater than or equal to B

Actions:
  1. Assign prospect to queue: SDR Queue
  2. Notify user: SDR Manager (email notification)
  3. Add to Salesforce Campaign: "MQL Routed — Q2 2026" (with status "Responded")

Rule settings:
  - Match type: Match ALL
  - Repeat: Yes — repeat rule when prospect score drops below 100 and rises again
  - Automation rule status: Active
```

**Why it works:** The AND logic ensures both dimensions are satisfied before routing. The "repeat" setting allows a previously recycled prospect to re-qualify if they re-engage and hit the threshold again. Tying to a Salesforce Campaign gives CRM-side reporting on MQL volume and conversion rate.

---

## Example 2: Score Decay Rules to Prevent Score Staleness

**Context:** A manufacturing company runs MCAE for an annual trade show season. After each event, prospects get high scores from form fills and webinar registrations. Six months later, many of those prospects are still "MQL eligible" on paper, but Sales knows they went cold. The SDR team is spending time on prospects who last engaged eight months ago.

**Problem:** Scores accumulated from old campaigns never reduce, so the MQL queue remains inflated with stale prospects. Sales stops trusting the MQL list.

**Solution:**

```
Score Decay Configuration (Admin > Scoring > Decay Scoring):

Rule 1:
  - Reduce score by: 10 points
  - After: 30 days of no activity

Rule 2:
  - Reduce score by: 20 points
  - After: 60 days of no activity

Effect on a prospect with score 100 who goes inactive:
  Day 30:  Score reduced by 10 → Score = 90
  Day 60:  Score reduced by 20 → Score = 70 (cumulative reduction: 30 points over 60 days)
  Day 90:  Rule 1 fires again if still inactive → Score = 60
  Day 120: Rule 2 fires again → Score = 40
  Score never goes below 0.
```

**Why it works:** Decay progressively signals that a prospect has gone cold without requiring any manual cleanup. Prospects who re-engage (click a new email, fill a new form) immediately earn fresh points on top of their decayed score, accurately reflecting new interest. After implementing decay, the MQL queue shrank by 40% within 90 days and SDR connect rates improved because remaining MQLs were genuinely recent engagers.

---

## Example 3: Multi-Segment Profile for Grading by ICP

**Context:** A HR tech company has two ICP segments: (1) Enterprise HR Directors at companies with 500+ employees in the US, and (2) SMB HR Managers at companies with 50–499 employees. Fit criteria differ between these segments, so a single Profile produces grades that don't match Sales' intuition.

**Solution:**

```
Profile 1: Enterprise ICP
Positive criteria (each worth grade points):
  - Job Title contains "Director" OR "VP" OR "CHRO" → +20 grade points
  - Industry = "Technology" OR "Financial Services" OR "Healthcare" → +15 grade points
  - Number of Employees >= 500 → +15 grade points
  - Country = "US" → +10 grade points

Negative criteria:
  - Job Title contains "Intern" OR "Coordinator" → -25 grade points
  - Industry = "Education" → -15 grade points
  - Number of Employees < 100 → -20 grade points

Profile 2: SMB ICP (default)
Positive criteria:
  - Job Title contains "Manager" OR "Director" → +20 grade points
  - Number of Employees between 50 and 499 → +20 grade points
  - Country = "US" OR "CA" → +10 grade points

Negative criteria:
  - Number of Employees < 50 → -20 grade points
  - Job Title contains "Intern" → -25 grade points

Set Profile 2 as the default (catches all prospects not matched by Profile 1 criteria).
```

**Why it works:** Each segment gets grade criteria calibrated to its specific ICP. A Director at a 1,000-person company matches Profile 1 criteria heavily and earns an A grade. An HR Manager at a 200-person SMB matches Profile 2 criteria and also earns an A — which is accurate for that segment. Both types of A-grade prospect + sufficient score will route to the appropriate SDR team.

---

## Anti-Pattern: Using Completion Actions for Score-Threshold Routing

**What practitioners do:** They add a Completion Action to a form: "If prospect submits this form AND score >= 100, assign to Sales queue." They expect this to route MQL leads automatically.

**What goes wrong:** Completion Actions fire immediately after the form submission event, at the moment of that specific activity. They do not re-evaluate the prospect's total accumulated score at that point reliably for threshold logic. More critically, completion actions only fire on that single form fill — a prospect who crosses the MQL threshold via accumulated email clicks and page views (no recent form fill) will never trigger the completion action. MQLs are missed.

**Correct approach:** Use an Automation Rule with the score and grade criteria, not a Completion Action. Automation Rules evaluate the entire prospect database continuously, catching threshold crossings regardless of which activity caused the final score increment.
