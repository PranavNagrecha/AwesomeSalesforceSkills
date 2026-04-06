# LLM Anti-Patterns — Escalation Rules

Common mistakes AI coding assistants make when generating or advising on Salesforce Case Escalation Rules.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Expecting escalation to fire in real time

**What the LLM generates:** "Set the escalation rule to fire after 2 hours. The case will be escalated exactly 2 hours after creation."

**Why it happens:** LLMs describe escalation timing as precise. The Salesforce time-based workflow engine that evaluates escalation rules runs approximately every hour. A case that hits its 2-hour threshold at 3:05 PM may not escalate until the next engine run around 4:00 PM. Escalation is not real-time.

**Correct pattern:**

```
Escalation timing is approximate, not exact:
1. The time-based engine evaluates escalation rules approximately
   every 60 minutes (not configurable).
2. A case with a 2-hour SLA may not escalate until up to ~3 hours
   after creation (2 hours + up to 1 hour engine cycle).
3. Plan SLA commitments with this latency in mind:
   - If the business expects escalation within 2 hours,
     set the rule to 1 hour to account for engine delay.
4. For near-real-time escalation, use a scheduled Flow with a
   shorter polling interval or a time-based Flow trigger.
```

**Detection hint:** If the output describes escalation timing as exact (e.g., "exactly 2 hours"), the engine cycle delay is being ignored. Search for `exactly` or `precisely` near escalation time settings.

---

## Anti-Pattern 2: Creating multiple active escalation rules

**What the LLM generates:** "Create an escalation rule for High priority cases and another for Critical priority cases. Activate both."

**Why it happens:** LLMs treat escalation rules like sharing rules where multiple can be active. Only ONE escalation rule can be active per org. Use multiple rule entries within the single active rule to handle different priorities.

**Correct pattern:**

```
Only one escalation rule can be active per org.
Use ordered rule entries within the single active rule:
  Escalation Rule: Case Escalation (Active)
    Entry 1: Priority = 'Critical' → escalate after 1 hour.
    Entry 2: Priority = 'High' → escalate after 4 hours.
    Entry 3: Priority = 'Medium' → escalate after 8 hours.
    Entry 4: (No criteria — catch-all) → escalate after 24 hours.

Entries are evaluated top-to-bottom; first match wins.
Order from most urgent to least urgent.
```

**Detection hint:** If the output suggests activating multiple escalation rules, the one-active-rule limit is being violated. Search for `activate both` or multiple `escalation rule` creation instructions.

---

## Anti-Pattern 3: Ignoring the "Escalated" checkbox and its interaction with escalation rules

**What the LLM generates:** "The escalation rule will keep escalating the case at each tier until it is resolved."

**Why it happens:** LLMs describe escalation as a continuous process. When a case is escalated, Salesforce checks the IsEscalated checkbox. The escalation rule's behavior after the initial escalation depends on the configuration. If the "case is not escalated" auto-response is set, re-escalation requires resetting the checkbox or configuring additional escalation actions.

**Correct pattern:**

```
Escalation behavior details:
1. When an escalation action fires, the Case's IsEscalated checkbox
   is set to TRUE.
2. The escalation rule entry has an "Age Over" setting that determines
   when escalation fires relative to creation or last modification.
3. For multi-tier escalation within one rule entry:
   - Add multiple Escalation Actions with increasing time thresholds:
     Action 1: After 2 hours → email to team lead.
     Action 2: After 4 hours → reassign to manager, email to director.
4. Once a case meets the "stop escalation" criteria (e.g., Status = Closed),
   the case exits escalation. Configure the criteria carefully.
```

**Detection hint:** If the output describes multi-tier escalation without using multiple Escalation Actions within a single rule entry, the multi-tier setup is being misunderstood. Search for `Escalation Actions` (plural) with time thresholds.

---

## Anti-Pattern 4: Not configuring Business Hours for escalation timing

**What the LLM generates:** "Set the escalation rule to fire after 8 hours. It will escalate based on elapsed clock time."

**Why it happens:** LLMs default to 24/7 clock time. Most service teams have defined business hours (e.g., 9 AM - 5 PM, Mon-Fri). Escalation rules can be configured to count only business hours. An 8-hour SLA with business hours means the case escalates the next business day if submitted at 4 PM, not at midnight.

**Correct pattern:**

```
Configure Business Hours for escalation:
1. Setup → Business Hours → define hours per day and time zone.
2. In the escalation rule entry:
   - "Business Hours": select the applicable business hours record.
   - "Escalation times are based on": choose "When Case is Created"
     or "When Case was Last Modified."
   - Time calculations will respect the business hours schedule.
3. For 24/7 support: create a "24/7" business hours record
   (all hours, all days).
4. For different SLAs by region: create multiple business hours
   records and use different rule entries per region.
```

**Detection hint:** If the output sets an escalation time without mentioning Business Hours configuration, the escalation may fire outside working hours or miscalculate SLA timing. Search for `Business Hours` in the escalation rule setup.

---

## Anti-Pattern 5: Forgetting that resolved or closed cases can still escalate

**What the LLM generates:** "The escalation rule will only fire on open cases."

**Why it happens:** LLMs assume escalation rules automatically exclude closed cases. The escalation rule entry criteria define which cases are eligible. If the criteria do not explicitly exclude Status = 'Closed' or Status = 'Resolved', a case that was closed after the escalation timer started may still escalate.

**Correct pattern:**

```
Ensure escalation criteria exclude resolved/closed cases:
1. In each rule entry, add criteria:
   Status NOT EQUAL TO 'Closed'
   AND Status NOT EQUAL TO 'Resolved'
   AND Status NOT EQUAL TO 'Closed - Duplicate'
2. Or use a formula-based criterion:
   ISPICKVAL(Status, 'New') || ISPICKVAL(Status, 'Working')
   → only escalate cases in active statuses.
3. When a case is closed, if it matched an escalation entry,
   closing it removes it from the escalation queue
   ONLY IF the closed status is excluded by the rule entry criteria.
4. Test: create a case, wait for escalation timer, close it,
   and verify it does NOT escalate after closure.
```

**Detection hint:** If the escalation rule entry criteria do not explicitly filter out Closed/Resolved statuses, closed cases may escalate. Search for `Closed` or `Resolved` in the rule entry criteria.
