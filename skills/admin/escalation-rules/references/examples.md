# Examples — Escalation Rules

## Example 1: SLA Breach Notification for a Software Support Org

**Context:** A B2B software company has a 4-hour SLA for P1 cases. The support operations team needs to ensure that the support manager is notified when a P1 case is not updated within 4 hours, and that the case is reassigned to the escalations queue if it remains open at 8 hours.

**Problem:** Without escalation rules, cases slip past SLA thresholds silently. Support managers only discover breaches during weekly reviews, at which point the customer relationship is already damaged.

**Solution:**

1. Navigate to Setup > Service > Escalation Rules > New.
2. Name the rule "Case SLA Escalation" and check Active.
3. Add Rule Entry 1:
   - Criteria: `Priority equals P1`
   - Escalate Case When: Over 4 hours old
   - Business Hours: Use org default (24/7, since P1 is always-on)
   - Age Over Based On: Case Created Date
4. Add Escalation Action for Entry 1 at 4 hours:
   - Notify: Case Owner's Manager
   - Reassign To: (leave blank — notification only)
5. Add Escalation Action for Entry 1 at 8 hours:
   - Notify: Escalations Queue
   - Reassign To: Escalations Queue
6. Save and verify one P1 test case.

**Why it works:** Entry criteria `Priority = P1` ensures lower-priority cases are unaffected. Two time-layered actions on the same entry provide progressive escalation: warn first, reassign second. The 8-hour reassignment action guarantees a human takes ownership even if the original agent is unavailable.

---

## Example 2: Business-Hours-Aware Escalation for a Regional Service Team

**Context:** A US-based service team works Monday–Friday, 8 AM–6 PM Pacific. Standard cases must be resolved within 8 business hours. Without business hours configuration, cases created on Friday at 5 PM would trigger escalation early Saturday morning — when no one is available to act.

**Problem:** Escalation notifications landing outside business hours generate noise, erode trust in the system, and result in cases being escalated then never followed up on until Monday — making the escalation meaningless.

**Solution:**

1. Setup > Business Hours > New:
   - Name: "US Pacific Business Hours"
   - Check Active
   - Time Zone: Pacific Standard Time
   - Hours: Monday through Friday, 8:00 AM to 6:00 PM
   - Uncheck Saturday and Sunday
2. Setup > Escalation Rules > Edit active rule > Add Rule Entry:
   - Criteria: `Type equals Standard`
   - Escalate Case When: Over 8 hours old
   - Business Hours: Check "Use Business Hours" → select "US Pacific Business Hours"
   - Age Over Based On: Case Created Date
3. Add Escalation Action: notify case owner at the 8-hour mark.
4. Assign the Business Hours record to cases (the `BusinessHoursId` field or "Business Hours" field on Case).

**Why it works:** The escalation engine counts only hours that fall within the 8 AM–6 PM Monday–Friday window. A case created at 5 PM Friday has 1 hour of business time that day. It needs 7 more hours after 8 AM Monday — meaning escalation fires around 3 PM Monday. The notification lands when someone is actually available to act.

---

## Anti-Pattern: Multiple Active Escalation Rules for Different Case Types

**What practitioners do:** Attempt to create two escalation rules — one for "Sales Cases" and one for "Service Cases" — believing both will be active simultaneously to handle different SLA requirements.

**What goes wrong:** Salesforce only allows one active escalation rule per org. When you activate the second rule, the first is automatically deactivated. One set of cases stops escalating without any error message. The deactivation happens silently — there is no warning in the UI that the previous rule was turned off.

**Correct approach:** Use a single active escalation rule with multiple rule entries that differentiate by criteria. Entry 1: `Type = Sales Case` with Sales SLA thresholds. Entry 2: `Type = Service Case` with Service SLA thresholds. Both sets of criteria live within the one active rule, and each entry can have its own escalation time and actions.
