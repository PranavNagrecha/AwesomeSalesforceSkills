# Examples — SLA Design and Escalation Matrix

## Example 1: Three-Tier SLA Matrix for an Enterprise Software Company

**Context:** A B2B SaaS company has three support tiers: Enterprise (large accounts, 24/5 coverage), Professional (mid-market, Mon–Fri 8am–6pm), and Basic (self-serve, Mon–Fri 9am–5pm). The company needs to design the SLA tier definition table and escalation matrix before the Salesforce admin configures entitlement processes.

**Problem:** Without a design artifact, the admin configures milestones ad hoc — setting 4-hour first-response on Enterprise P1 but forgetting to attach Enterprise Business Hours to the escalation rule entries. The milestone clock correctly tracks business hours, but escalation rules fire at 4 calendar hours, sending the manager a breach email at 3 AM on Saturday.

**Solution — Tier Definition Table:**

```
| Tier         | Priority | First Response | Resolution | Business Hours       |
|--------------|----------|----------------|------------|----------------------|
| Enterprise   | P1       | 1 hour         | 4 hours    | Enterprise 24/5      |
| Enterprise   | P2       | 4 hours        | 1 day      | Enterprise 24/5      |
| Enterprise   | P3       | 8 hours        | 3 days     | Enterprise 24/5      |
| Enterprise   | P4       | 1 day          | 5 days     | Enterprise 24/5      |
| Professional | P1       | 4 hours        | 1 day      | Professional M-F 8-6 |
| Professional | P2       | 1 day          | 3 days     | Professional M-F 8-6 |
| Professional | P3       | 2 days         | 5 days     | Professional M-F 8-6 |
| Professional | P4       | 3 days         | 7 days     | Professional M-F 8-6 |
| Basic        | P1       | 1 day          | 3 days     | Basic M-F 9-5        |
| Basic        | P2       | 2 days         | 5 days     | Basic M-F 9-5        |
| Basic        | P3       | 3 days         | 7 days     | Basic M-F 9-5        |
| Basic        | P4       | 5 days         | 10 days    | Basic M-F 9-5        |
```

**Solution — Escalation Matrix excerpt for Enterprise P1:**

```
| Threshold | Notification Target     | Automated Action                        |
|-----------|-------------------------|-----------------------------------------|
| 50%       | Assigned Agent          | Email Alert: "Enterprise P1 at 50%"    |
| 75%       | Team Lead               | Email Alert: "Enterprise P1 at 75%"    |
| 90%       | Support Manager         | Email Alert + Task: "Pre-breach P1"    |
| 100%      | VP of Support + Manager | Email Alert + Field Update (Violated=true) |
```

**Solution — Business Hours Mapping Table excerpt:**

```
| Object                              | Business Hours Record    |
|-------------------------------------|--------------------------|
| Entitlement Process: Enterprise     | Enterprise 24/5          |
| Entitlement Process: Professional   | Professional M-F 8-6     |
| Entitlement Process: Basic          | Basic M-F 9-5            |
| Escalation Rule Entry: Enterprise P1| Enterprise 24/5          |
| Escalation Rule Entry: Professional | Professional M-F 8-6     |
| Escalation Rule Entry: Basic        | Basic M-F 9-5            |
```

**Why it works:** The business hours mapping table ensures both enforcement paths (milestone clock on the entitlement process, time-based action on the escalation rule entry) reference the same Business Hours record. The tier definition table gives the admin an unambiguous specification — no interpretation required.

---

## Example 2: Designing for a Mixed 24/7 and Business-Hours SLA Model

**Context:** A cloud infrastructure provider has Platinum tier customers who require 24/7 SLA coverage (response within 15 minutes for P1) and Gold tier customers who require Mon–Fri 9–5 coverage (response within 2 hours for P1). A single admin is configuring entitlements and cannot recall which tier gets which business hours record.

**Problem:** The admin attaches "Default" Business Hours (24/7) to both entitlement processes, assuming that is correct for Platinum. For Gold, the milestone clock continues running overnight and on weekends, so a P1 case filed at 5 PM Friday hits the 2-hour resolution milestone by 7 PM Friday even though no Gold agents work on weekends. Gold customers receive automated breach notifications on Friday evenings for work the team has not even seen yet.

**Solution — Design the Business Hours mapping explicitly:**

```
Platinum Tier:
  Entitlement Process Business Hours: 24/7 All Hours (explicitly created record, confirmed as 24/7)
  Escalation Rule Entries for Platinum: 24/7 All Hours
  Note: Do NOT use "Default" — verify Default is 24/7 in Setup > Business Hours before referencing it.

Gold Tier:
  Entitlement Process Business Hours: Gold Support M-F 9am-5pm (custom record, restricted to Mon-Fri 09:00-17:00)
  Escalation Rule Entries for Gold: Gold Support M-F 9am-5pm (same record)
  Note: Create a named record with a descriptive name. "Default" is ambiguous — its hours may change.
```

**Why it works:** By naming business hours records descriptively and listing them explicitly in the design artifact, the admin configuration becomes deterministic. The design review catches the "Default" anti-pattern before it reaches production. Platinum customers get genuine 24/7 milestone tracking. Gold customers' milestones pause outside business hours — a P1 filed Friday at 5 PM does not start the 2-hour clock until Monday at 9 AM.

---

## Anti-Pattern: Configuring Milestones Without an Escalation Matrix Document

**What practitioners do:** Jump directly into Salesforce Setup to configure entitlement processes and milestones without a written escalation matrix. Time values come from a Slack message or verbal conversation. Notification targets are guessed based on current user records rather than defined roles.

**What goes wrong:** Three months after go-live, the support manager is no longer with the company. The milestone action sends breach notifications to a deactivated user. The team discovers this only when an Enterprise P1 case goes unescalated for 6 hours. Additionally, the Professional tier milestones were configured with the wrong time targets (2 hours instead of 4 hours) because two people interpreted the same verbal agreement differently.

**Correct approach:** Produce the tier definition table and escalation matrix as formal documents before any Salesforce configuration begins. Use queue-based or role-based email alerts rather than user-specific ones — so escalation notifications survive personnel changes. Review the escalation matrix with support operations leadership for sign-off. Treat the document as a versioned artifact that is updated when SLA commitments change.
