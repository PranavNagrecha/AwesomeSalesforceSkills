# Examples — Entitlements and Milestones

## Example 1: Platinum/Gold/Standard Three-Tier SLA Process

**Context:** A B2B SaaS company sells support tiers as line items on their contracts. Platinum customers get 1-hour response / 4-hour resolution during 24/7 coverage. Gold gets 4-hour response / 1-business-day resolution during business hours. Standard gets next-business-day response / 3-business-day resolution.

**Problem:** Without entitlement processes, agents have no visibility into how much time remains on SLA commitments. Escalation rules fire too broadly (they do not distinguish between tiers) and cannot pause for business hours.

**Solution:**

Three entitlement processes are created in Setup > Entitlement Processes:

```
Entitlement Process: "Platinum SLA"
  Business Hours: 24/7 (process level)
  Version: 1
  Start: Case Created
  Exit: Case Closed

  Milestone 1: First Response
    Time Limit: 1 hour
    Recurrence: No Recurrence
    Business Hours: (inherit process — 24/7)
    Warning Actions:
      30 min (50%): Email alert → Case Owner
      45 min (75%): Email alert → Case Owner + Support Manager
    Violation Actions:
      60 min (100%): Email alert → VP Support; Field Update: Case.SLA_Breached__c = true
    Success Actions:
      On Completion: Field Update: Case.First_Response_Met__c = Now()

  Milestone 2: Resolution
    Time Limit: 4 hours
    Recurrence: No Recurrence
    Business Hours: (inherit process — 24/7)
    Warning Actions:
      2 hr (50%): Email alert → Case Owner
      3 hr (75%): Email alert → Case Owner + Support Manager
    Violation Actions:
      4 hr (100%): Email alert → VP Support; Field Update: Case.Resolution_Breached__c = true
```

The Gold and Standard processes follow the same structure with adjusted time limits and a "Business Hours: M–F 8am–5pm" assignment at the process level.

Each entitlement record is created on the customer's Account, referencing the correct process. When a case is created for the account, a Record-Triggered Flow populates `Case.EntitlementId` by querying the active entitlement for that account.

**Why it works:** Milestone timers respect the process-level business hours assignment, so Gold and Standard timers pause automatically outside M–F 8–5. Platinum timers run 24/7. The action system handles agent notification without custom Apex, and the field updates enable standard reports to track SLA breach rates by tier.

---

## Example 2: Independent Recurrence for Ongoing Response SLA

**Context:** A managed services provider commits to responding to every new comment on an open case within 2 business hours. Customers frequently add comments throughout the day expecting rapid responses. The business wants to track each comment response as a separate SLA commitment.

**Problem:** Using No Recurrence on the response milestone means that once the first response is logged, the milestone is complete and subsequent customer comments have no SLA timer attached.

**Solution:**

```
Entitlement Process: "MSP Ongoing Response"
  Business Hours: M–F 8am–6pm

  Milestone: Customer Comment Response
    Time Limit: 2 hours
    Recurrence: Independent
    Reset Event: Case Comment Added (when contact is the author)
    Business Hours: M–F 8am–6pm (milestone-level override to be explicit)
    Warning Actions:
      1 hr (50%): Email alert → Assigned Agent
      1.5 hr (75%): Email alert → Assigned Agent + Queue Manager
    Violation Actions:
      2 hr (100%): Email alert → Customer Success Manager; Field Update: Case.Ongoing_Response_Breached__c = true
```

A Flow also stamps `Case.Last_Customer_Comment__c` each time a contact adds a comment, which feeds a report showing average response time per agent.

**Why it works:** Independent recurrence restarts the milestone timer each time the reset event fires, regardless of whether the prior instance was completed. This means every customer comment opens a new 2-hour SLA window. Warning and violation actions fire independently per instance.

---

## Anti-Pattern: Applying Entitlements but Forgetting the Case Lookup

**What practitioners do:** Enable Entitlement Management, create entitlement processes and entitlement records, then go live — but never populate the `EntitlementId` field on cases created via Email-to-Case or Web-to-Case.

**What goes wrong:** Milestone processes are only triggered when `Case.EntitlementId` is populated. Cases without an entitlement lookup have no process, no milestone timers, and no SLA tracking — silently. Agents see no Milestone Tracker on the case. No warning or violation actions fire. The org believes entitlements are running when they are not.

**Correct approach:** Build a Record-Triggered Flow on Case creation (Before Save for performance) that queries `Entitlement` WHERE `AccountId = triggerCase.AccountId` AND `Status = 'Active'` and stamps the result into `Case.EntitlementId`. For cases without an account (anonymous web submissions), define a fallback default entitlement (e.g., "Standard SLA — No Account") so at minimum baseline tracking applies.
