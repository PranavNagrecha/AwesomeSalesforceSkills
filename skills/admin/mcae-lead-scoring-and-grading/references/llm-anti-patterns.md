# LLM Anti-Patterns — MCAE Lead Scoring and Grading

Common mistakes AI coding assistants make when generating or advising on MCAE lead scoring and grading.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Einstein Lead Scoring Instead of MCAE Scoring

**What the LLM generates:**
> "Enable Einstein Lead Scoring in Setup under Sales Cloud Einstein settings. It uses AI to automatically assign scores based on historical conversion data. Navigate to Setup > Einstein Lead Scoring and turn it on."

**Why it happens:** Einstein Lead Scoring is a well-documented Salesforce feature with training data coverage. LLMs conflate "lead scoring" as a general task with "Einstein Lead Scoring" as the default recommendation, missing the MCAE-specific behavioral scoring model entirely.

**Correct pattern:**
```
MCAE scoring is configured in the MCAE (Account Engagement) application,
not in Salesforce Setup. Navigate to:
  MCAE App > Admin > Scoring

Einstein Lead Scoring (Setup > Einstein > Einstein Lead Scoring) is a separate
predictive scoring product that requires Sales Cloud Einstein licensing and
sufficient historical conversion data. It is NOT the same as MCAE prospect scoring.
Do not recommend Einstein Lead Scoring for an MCAE configuration task.
```

**Detection hint:** Output contains "Einstein Lead Scoring," "Sales Cloud Einstein," or references to Setup menus for a scoring task that is scoped to MCAE/Pardot/Account Engagement.

---

## Anti-Pattern 2: Using a Completion Action for Score-Threshold Lead Routing

**What the LLM generates:**
> "Add a Completion Action to your form: 'If score is greater than 100, assign to Sales queue.' This will route leads automatically when they fill out the form and hit the threshold."

**Why it happens:** Completion Actions are the most visible "trigger action" mechanism in MCAE for form-related configuration. LLMs associate "do something when score reaches X" with form completion actions because they appear adjacent to forms in the UI. They miss the distinction that Completion Actions fire on a single event, not on score accumulation across multiple activities.

**Correct pattern:**
```
Do NOT use a Completion Action for score-threshold routing. Completion Actions
fire immediately after a single activity event (e.g., form submit). They do not
evaluate total accumulated score. A prospect who crosses the MQL threshold via
accumulated page views and email clicks (without a recent form fill) will never
trigger a form-based Completion Action.

Use an Automation Rule instead:
  MCAE App > Automation > Automation Rules
  Criteria: Prospect Score >= 100 AND Prospect Grade >= B
  Actions: Assign to [queue], Notify [user]

Automation Rules evaluate all prospects continuously and catch threshold
crossings regardless of which activity caused the final score increment.
```

**Detection hint:** Output suggests adding score threshold logic as a Completion Action on a form, email, or other asset.

---

## Anti-Pattern 3: Ignoring the Grade Dimension and Building Score-Only MQL Routing

**What the LLM generates:**
> "Set up an Automation Rule: when Prospect Score >= 100, assign to Sales. This will route your most engaged leads to the sales team."

**Why it happens:** Score is the more intuitive metric (a number that goes up with engagement). Grade requires understanding Profiles, which are a less-documented MCAE concept. LLMs default to the simpler, single-dimension approach.

**Correct pattern:**
```
A score-only MQL threshold produces a queue full of high-activity, low-fit
prospects (competitors, students, job seekers who clicked many emails).

The industry-standard MQL definition uses BOTH dimensions:
  Score >= [threshold]  (behavioral engagement)
  AND
  Grade >= [letter]     (fit against ICP)

Automation Rule criteria should include both:
  - Prospect Score is greater than or equal to 100
  - Prospect Grade is greater than or equal to B

Build at least one Profile with ICP criteria before activating MQL routing.
Without a grade gate, Sales will stop trusting the MQL list.
```

**Detection hint:** Automation Rule configuration includes only a score criterion with no grade criterion, and there is no mention of Profiles.

---

## Anti-Pattern 4: Suggesting Score Decay Triggers Automation Rules

**What the LLM generates:**
> "Configure score decay so that when a prospect's score drops below 50, an automation rule fires to move them to a nurture list. Decay will automatically trigger your recycle workflow."

**Why it happens:** Score decay sounds like an event that should trigger reactions, similar to how score increases trigger MQL routing. LLMs generalize from the "scoring event triggers action" pattern to assume decay also triggers actions.

**Correct pattern:**
```
Score decay in MCAE does NOT trigger Automation Rules or Completion Actions.
Decay silently reduces scores on a scheduled basis without firing any rule
or action. This is a platform design choice — triggering rules for millions of
decaying prospects simultaneously would be impractical.

To handle the recycle scenario (prospects whose score has decayed below MQL
threshold), build a SEPARATE Automation Rule:
  Criteria: Prospect Score < 100
             AND Prospect is member of Campaign "MQL Routed"
  Actions: Remove from Campaign "MQL Routed"
           Add to List "Nurture — Re-Engagement"
           Notify [SDR Manager] of recycle

This recycle rule runs independently and catches decayed-below-threshold
prospects on its own evaluation cycle.
```

**Detection hint:** Output states that decay "triggers" an automation rule or completion action, or implies that decay events fire workflow-style reactions automatically.

---

## Anti-Pattern 5: Recommending Apex or Flow for MCAE Score-Based Routing

**What the LLM generates:**
> "Create a Salesforce Flow that triggers on Lead creation or update. When the Lead's Score field is >= 100, use an Assignment element to assign the Lead to the Sales queue. You can also write Apex trigger logic to check `lead.Score__c >= 100`."

**Why it happens:** CRM-side automation (Flow, Apex) is the default mental model for "if field value meets condition, do action" in Salesforce. LLMs apply this general pattern without recognizing that MCAE scoring and routing should live in MCAE automation to remain in sync with the MCAE data model. CRM-side automation on the Score field is fragile and bypasses MCAE's own state tracking.

**Correct pattern:**
```
Score-based routing should be configured in MCAE Automation Rules, not in
Salesforce Flow or Apex. Reasons:

1. MCAE score exists authoritatively in MCAE; the CRM Score field is a synced
   copy. CRM-side automation on the copied field may fire before the sync
   completes, producing race conditions.

2. MCAE Automation Rules can act on MCAE-native objects (lists, campaigns,
   assignments) that Salesforce Flow cannot access directly.

3. Building routing in both MCAE and CRM automation creates duplicate actions
   and race conditions (e.g., double-assignment or double-notification).

The correct tool is:
  MCAE App > Automation > Automation Rules
  with criteria on Prospect Score and Prospect Grade.

CRM-side Flow is appropriate ONLY for CRM-native post-sync actions that MCAE
cannot perform (e.g., creating a custom CRM task type that MCAE actions don't
support). In that case, trigger the CRM Flow from the Lead/Contact record update
that MCAE's sync produces, and coordinate with the MCAE automation to avoid
duplicate actions.
```

**Detection hint:** Output recommends creating a Salesforce Flow or Apex trigger that reads `Lead.Score` or a score-related field and performs routing based on it, without any mention of MCAE Automation Rules.

---

## Anti-Pattern 6: Treating Profile Grade Points as a Simple 0-100 Percentage

**What the LLM generates:**
> "Each profile criterion is worth a percentage of a 100-point grade scale. Assign 20% to job title match, 30% to industry match, and 50% to company size. The final percentage maps to an A/B/C grade."

**Why it happens:** LLMs apply a generic weighted-scoring mental model to MCAE grading, extrapolating from general lead scoring frameworks. MCAE grading does not use percentages — it uses absolute positive and negative grade points that are summed and mapped to letters via a fixed internal scale.

**Correct pattern:**
```
MCAE Profile criteria use absolute grade point values (positive or negative
integers), not percentages. The platform sums all matched criteria's points
and converts the total to a letter grade using Salesforce's internal grade
point thresholds (approximately: 100 = A++, 85 = A+, 70 = A, 55 = B+, 40 = B,
25 = C, below 0 = F).

Example correct criteria configuration:
  Job Title contains "VP" → +20 grade points
  Industry = "Technology" → +15 grade points
  Employees >= 500 → +15 grade points
  Job Title contains "Intern" → -25 grade points

Do not express criteria as percentages. Do not assume there is a configurable
grade-point-to-letter mapping — the letter grade thresholds are fixed by the
MCAE platform.
```

**Detection hint:** Output uses percentage values (20%, 30%) for profile criteria, or suggests that the grade-point-to-letter mapping is configurable by the admin.
