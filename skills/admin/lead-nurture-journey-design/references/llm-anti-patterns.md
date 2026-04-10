# LLM Anti-Patterns — Lead Nurture Journey Design

Common mistakes AI coding assistants make when generating or advising on Lead Nurture Journey Design.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Designing the Journey Before Confirming a Content Inventory Exists

**What the LLM generates:** A fully specified Engagement Studio program with step-by-step email sends ("Send Email: Awareness Guide → Wait 5 days → Rule: clicked? → Send Case Study → ...") without first asking whether those assets exist or are mapped to the correct funnel stages.

**Why it happens:** LLMs treat program design as a configuration problem and jump directly to the configuration output. The prerequisite audit (content inventory) is not a Salesforce platform concept — it is a process gate — so it is underweighted in training data relative to platform configuration steps.

**Correct pattern:**

```
Step 0 (mandatory before any program design):
- Produce a content inventory table:
  | Stage        | Asset Name           | Type     | Has Form? |
  |--------------|----------------------|----------|-----------|
  | Awareness    | [Name]               | [Type]   | Yes/No    |
  | Consideration| [Name]               | [Type]   | Yes/No    |
  | Decision     | [Name]               | [Type]   | Yes/No    |

- Identify gaps: stages with zero assets must be flagged before proceeding.
- Only after every email send in the planned program has a corresponding row in this table
  does Engagement Studio configuration begin.
```

**Detection hint:** If the response jumps to Engagement Studio step configuration without first presenting a content inventory table or asking about existing assets, flag this anti-pattern.

---

## Anti-Pattern 2: Confusing Engagement Studio (MCAE) With Journey Builder (Marketing Cloud Engagement)

**What the LLM generates:** Instructions that reference "Journey Builder," "Entry Sources," "Decision Splits," "Wait Activities," "Email Studio," or "Contact Builder" when the user has asked about MCAE nurture journeys or Pardot lead nurturing. Alternatively, the LLM advises the user to "go to Marketing Cloud and set up a Journey" for a question about Engagement Studio.

**Why it happens:** Both MCAE and Marketing Cloud Engagement are Salesforce marketing products with overlapping terminology. Training data conflates "journey" language across both platforms. "Decision Split" is a Journey Builder concept; "Rule" is the Engagement Studio equivalent. LLMs frequently blend the two UIs and APIs.

**Correct pattern:**

```
MCAE Engagement Studio (Account Engagement / Pardot):
- Accessed from: Account Engagement app in Salesforce
- Program steps: Send Email, Wait, Rule (with Yes/No branches),
  Add to List, Notify User, Change Prospect Field, Create Task, Add Tag
- Branching: Rule steps using score, grade, email click, form submit,
  page visit, list membership
- Cadence: weekly execution schedule (not real-time)
- Data model: Prospects, Lists, Engagement Programs

Marketing Cloud Engagement Journey Builder (separate product):
- Accessed from: marketing.salesforce.com (separate org login)
- Steps: Decision Split, Wait, Send Email Activity, Update Contact Activity
- Data model: Contacts, Data Extensions
- NOT the same product. Never mix instructions.
```

**Detection hint:** If the response mentions "Journey Builder," "Decision Split," "Entry Source," "Email Studio," "Content Builder," or "marketing.salesforce.com" in response to a question about MCAE or Pardot nurture programs, this anti-pattern is present.

---

## Anti-Pattern 3: Assuming Engagement Studio Programs Execute in Real Time

**What the LLM generates:** Advice such as "set a 1-day Wait step so the prospect receives the follow-up email the next day after clicking" or "the rule will fire immediately after the prospect submits the form" — without disclosing that programs evaluate on a weekly cadence, not per-event.

**Why it happens:** Drip email tools in other marketing platforms (HubSpot Workflows, Marketo Smart Campaigns) do evaluate triggers in near-real-time. LLMs trained on broad marketing automation content assume Engagement Studio operates similarly.

**Correct pattern:**

```
Engagement Studio programs: weekly evaluation cadence.
- A 1-day Wait step does NOT guarantee next-day execution.
  The prospect will be evaluated at the next weekly program run.
- For real-time follow-up after a prospect action:
  → Use Completion Actions on the form, email, or file (fires immediately at event time)
  → Use Automation Rules (near-real-time, evaluates all prospects continuously)
  → Reserve Engagement Studio programs for the multi-week behavioral journey

Correct framing: "The program will evaluate this rule at the next weekly run
after the Wait period has elapsed — typically within 7 days."
```

**Detection hint:** Any claim that a program step will execute "immediately," "in real time," "the next day," or "within 24 hours" without referencing Completion Actions or Automation Rules as the real-time mechanism.

---

## Anti-Pattern 4: Recommending Score-Only MQL Thresholds Without Grade Gating

**What the LLM generates:** An Automation Rule or program step configured as "Prospect Score >= 100 → Assign to Sales" with no grade criterion — treating score alone as sufficient for MQL qualification.

**Why it happens:** Score is the more visible and frequently discussed MCAE metric. Grade (fit dimension based on demographic/firmographic criteria) is less prominent in surface-level MCAE documentation. LLMs default to the simpler single-criterion rule.

**Correct pattern:**

```
MQL definition requires BOTH dimensions:
- Score measures behavioral engagement (interest level)
- Grade measures fit against the Ideal Customer Profile

Automation Rule criteria (both required):
  Criterion 1: Prospect Score >= [threshold, e.g., 100]
  Criterion 2: Prospect Grade is [B or better]  ← mandatory fit gate

Why: Score-only MQL floods Sales with high-engagement, low-fit records
(competitors researching the product, students, wrong geography, wrong job title).
The grade gate ensures Sales receives prospects who are both interested AND a fit.
```

**Detection hint:** Any MQL Automation Rule or program handoff step that specifies only a score criterion with no grade (or equivalent fit) criterion. Look for "Score >= X → Assign to Sales" without a "Grade >= Y" companion criterion.

---

## Anti-Pattern 5: Omitting a Standalone MQL Automation Rule and Relying Only on Program-Internal Steps

**What the LLM generates:** A nurture program design where the only MQL handoff is a "Notify User" or "Create Task" step inside the Engagement Studio program. The design assumes that all prospects who become MQL will be in the program when they cross the threshold.

**Why it happens:** The Engagement Studio canvas is visually intuitive and the "Notify User" step appears to solve the handoff problem completely. LLMs do not model the universe of prospects who reach MQL threshold outside the program (via direct form fills, event registration, other programs, or manual activity).

**Correct pattern:**

```
Dual-layer MQL handoff architecture:

Layer 1 (inside the program):
  Rule: Prospect score >= 100 AND grade >= B
    YES → Notify User (Sales Rep) + Create Task "MQL: [Prospect Name]"

Layer 2 (standalone Automation Rule, always-on, outside the program):
  Criteria: Prospect Score >= 100 AND Prospect Grade >= B
  Actions: Assign to [Sales Queue], Notify User, Add to [MQL Campaign]
  Schedule: Repeat (re-evaluates continuously)

Layer 2 covers:
  - Prospects who reach MQL through direct form fills (not in the program)
  - Prospects in other programs that don't have a handoff step
  - Prospects who score up mid-week before the program's weekly run

Without Layer 2, Sales misses every prospect who becomes MQL through
any channel other than the specific program with the notify step.
```

**Detection hint:** A nurture program design that includes a "Notify User" step for MQL but no mention of a companion Automation Rule. Ask: "Where does the MQL handoff happen for prospects who are not currently in this program?"

---

## Anti-Pattern 6: Placing Decision-Stage Content Early in the Program Without Engagement Gates

**What the LLM generates:** A program flow where the first or second email step is a "Book a Demo" or "Request Pricing" CTA, with no prior Awareness or Consideration content and no behavioral gate (rule step) before the Decision-stage send.

**Why it happens:** Conversion-focused CTAs are the stated business goal of nurture programs. LLMs shortcut to the outcome without modeling the trust-building sequence that makes the CTA effective. Also occurs when the LLM conflates "nurture program" with "promotional email campaign."

**Correct pattern:**

```
Correct stage sequence (enforce with behavioral gates):
1. Awareness content first (educational, no sales pressure)
   → Rule: Engagement signal before advancing?
2. Consideration content second (comparative, differentiating)
   → Rule: Intent signal before advancing?
3. Decision content only after demonstrated Consideration engagement

Do NOT send Decision-stage content (demo CTAs, pricing pages, trial offers)
until the prospect has engaged with at least one Awareness AND one Consideration asset,
or has reached a score threshold that indicates sustained engagement.

Premature Decision-stage sends:
- Produce low click rates (prospect is not ready)
- Inflate unsubscribes (prospect perceives the send as irrelevant or pushy)
- Waste high-value conversion assets on cold prospects
```

**Detection hint:** Any program design where a demo request, trial offer, or pricing CTA appears as the first or second email step without a preceding behavioral rule gate confirming engagement at an earlier stage.
