# LLM Anti-Patterns — SLA Design and Escalation Matrix

Common mistakes AI coding assistants make when generating or advising on SLA design and escalation matrix work in Salesforce Service Cloud. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Configuring Business Hours on the Entitlement Process Alone

**What the LLM generates:** Instructions that say "set Business Hours on the Entitlement Process to restrict SLA tracking to working hours" — without mentioning that escalation rule entries also require independent Business Hours configuration.

**Why it happens:** LLMs see entitlement process as the primary SLA object and treat it as the single configuration point for business hours. The dual-path enforcement model (entitlement process milestone clock + escalation rule time-based evaluation) is a Salesforce-specific nuance that is underrepresented in training data.

**Correct pattern:**

```
Step 1: Set Business Hours on the Entitlement Process record.
Step 2: Set Business Hours on EACH Escalation Rule entry that covers the same cases.
Both configurations are required and are independent of each other.
If only one is set, the other enforcement path runs on calendar hours 24/7.
```

**Detection hint:** If the output mentions Business Hours only in the context of entitlement process configuration and does not mention escalation rule entries, flag it for review.

---

## Anti-Pattern 2: Recommending "Default" Business Hours Without Verification

**What the LLM generates:** Instructions to "use the Default Business Hours record" for restricting SLA tracking to business hours, or configuration steps that reference "Default" as a working-hours record.

**Why it happens:** LLMs interpret "Default" as a sensible baseline (Mon–Fri 9–5), when in fact the Salesforce Default Business Hours record is configured as 24/7 out of the box.

**Correct pattern:**

```
Do not reference "Default" Business Hours without first verifying its configuration.
Go to Setup > Business Hours > Default and confirm the day/time settings.
If it is 24/7, create a new Business Hours record with the correct restricted hours.
Name it descriptively: "US Support M-F 8am-6pm PT" not "Default."
```

**Detection hint:** Search for "Default" in any output that references Business Hours configuration. If "Default" appears without a verification step or caveat, the output is likely incorrect.

---

## Anti-Pattern 3: Designing Milestones With OR Criteria

**What the LLM generates:** A milestone entry criteria design like "Priority equals High OR Priority equals Critical" as a single milestone condition, expecting the milestone to start when the case priority is either High or Critical.

**Why it happens:** OR logic is a natural conditional design pattern that works in most systems. Salesforce milestone entry criteria are AND-only declaratively — this is a counter-intuitive platform constraint that is easy to miss.

**Correct pattern:**

```
Milestone: First Response - Critical
  Entry Criteria: Priority equals Critical

Milestone: First Response - High
  Entry Criteria: Priority equals High

Each priority level requires its own milestone with its own entry criteria.
One milestone cannot cover multiple priority levels using OR conditions.
```

**Detection hint:** If the output shows a single milestone with criteria covering multiple field values (e.g., Priority in (Critical, High)), or if it does not create separate milestones per priority level, flag for review.

---

## Anti-Pattern 4: Treating Milestone Timing as Precise to the Minute

**What the LLM generates:** SLA matrix designs with sub-30-minute targets (e.g., "send a pre-breach notification at 90% of a 20-minute P1 window — at 18 minutes"), implying Salesforce milestone actions will fire at that exact moment.

**Why it happens:** LLMs understand milestone percentage thresholds as mathematical calculations and do not model the batch-based execution latency of the Salesforce time-based workflow engine.

**Correct pattern:**

```
Declarative milestone actions are batch-processed by Salesforce's time-based workflow engine.
The engine runs approximately every 15–60 minutes; precise sub-hour timing is not guaranteed.
For SLA windows under 1 hour, design a custom solution:
  - Apex Schedulable job with short polling interval
  - Platform Events triggered by field change at case creation
  - OR document explicitly that notification timing has up to 60-minute variance.
Declarative milestones are appropriate for SLA windows of 2 hours or more.
```

**Detection hint:** If the output contains milestone action timing for SLA targets under 60 minutes without mentioning batch processing latency, flag it.

---

## Anti-Pattern 5: Recommending a Single Escalation Rule Entry for All SLA Tiers

**What the LLM generates:** A single escalation rule entry with no tier differentiation — e.g., "escalate after 4 hours" — that applies to all cases regardless of tier (Enterprise, Professional, Basic) or priority.

**Why it happens:** LLMs model escalation rules as simple time-based triggers and do not reason through the implication that a single entry applies to all matching cases equally, regardless of the tier-specific SLA commitments defined in the escalation matrix.

**Correct pattern:**

```
Create separate escalation rule entries per tier-priority combination.
Each entry should have criteria that match on the entitlement name, account tier field, or case priority.

Example entries:
  Entry 1: Type = Enterprise, Priority = P1, Age = 1 hour, Business Hours = Enterprise 24/5
  Entry 2: Type = Enterprise, Priority = P2, Age = 4 hours, Business Hours = Enterprise 24/5
  Entry 3: Type = Professional, Priority = P1, Age = 4 hours, Business Hours = Professional M-F 8-6
  ...

A single "escalate after 4 hours" entry will fire for Enterprise P1 AND Basic P4 at the same time.
This floods managers with notifications and produces meaningless SLA data.
```

**Detection hint:** If the output produces fewer escalation rule entries than tier-priority combinations defined in the escalation matrix, the entries are likely under-differentiated.

---

## Anti-Pattern 6: Omitting the Design Artifact Layer Entirely

**What the LLM generates:** Direct Salesforce configuration steps for entitlement processes and milestones without first producing a tier definition table, escalation matrix document, or business hours mapping table.

**Why it happens:** LLMs default to answering "how to configure" questions with step-by-step Setup instructions, skipping the design and documentation phase that makes the configuration reviewable, auditable, and maintainable.

**Correct pattern:**

```
Before any Salesforce configuration:
1. Produce the Tier Definition Table (tier x priority x time target x business hours).
2. Produce the Escalation Matrix Document (tier x priority x threshold x notification target x action).
3. Produce the Business Hours Mapping Table (every entitlement process and every escalation
   rule entry with the Business Hours record each must reference).
4. Review and get sign-off on these artifacts.
5. THEN proceed to Salesforce configuration.

The design artifacts are not optional documentation — they are the specification.
```

**Detection hint:** If the output jumps directly to "Go to Setup > Entitlements" without producing a tier definition table or escalation matrix first, prompt for the design artifact phase before configuration.
