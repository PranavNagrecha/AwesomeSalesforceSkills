# LLM Anti-Patterns — FSL Scheduling Optimization Design

Common mistakes AI coding assistants make when generating or advising on FSL Scheduling Optimization Design.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Conflating Service Objective Weights with Appointment Priority Score

**What the LLM generates:** Advice to increase the "ASAP" service objective weight to 100% in order to make high-priority appointments schedule first, or guidance that reducing the "Minimize Travel" weight will fix priority ordering.

**Why it happens:** LLMs conflate two distinct scoring mechanisms. Service objectives (ASAP, Minimize Travel, etc.) rank candidate time slots within a filtered set. The optimizer priority score (derived from the Priority field and DueDate) determines which appointments the optimizer attempts to schedule first in a constrained run. Training data mixes these concepts because both affect "what gets scheduled" — but they operate at different layers and cannot substitute for each other.

**Correct pattern:**

```
To control which appointments get scheduled first in a constrained run:
  → Set ServiceAppointment.Priority (1 = highest, ~25,500 pts; lower priority = fewer pts)
  → Set ServiceAppointment.DueDate to reflect urgency

To control how candidates are ranked after work rule filtering:
  → Adjust service objective weights in the Scheduling Policy
  → ASAP, Minimize Travel, Preferred Resource, Skill Level, etc.

These are independent levers. Do not substitute one for the other.
```

**Detection hint:** Any suggestion to "increase ASAP weight to fix priority ordering" or "lower travel weight so critical appointments go first" is applying a service objective to an appointment prioritization problem.

---

## Anti-Pattern 2: Recommending Global Optimization for Same-Day Disruption Response

**What the LLM generates:** When a same-day cancellation leaves a schedule gap, the LLM suggests triggering a Global Optimization run to fill it.

**Why it happens:** LLMs know Global Optimization as the primary optimizer type and generalize it as the solution to all optimization problems. The distinction between Global (multi-day bulk), In-Day (same-day disruption), and Resource Schedule (single resource) requires precise awareness of FSL's three distinct optimizer modes.

**Correct pattern:**

```
Same-day cancellation / gap:          → In-Day Optimization
Pre-day bulk scheduling:              → Global Optimization (1–7 day horizon)
Single technician resequencing:       → Resource Schedule Optimization

Global Optimization during an active workday risks:
  - Rescheduling confirmed appointments
  - 10–30 minute run times (too slow for gap response)
  - Cross-day disruption to future confirmed schedules
```

**Detection hint:** Any recommendation of Global Optimization in response to "cancellation," "gap," "same-day," or "disruption" phrases is applying the wrong optimizer type.

---

## Anti-Pattern 3: Assuming Street-Level Routing Is Included in Field Service License

**What the LLM generates:** Advice to "enable Street-Level Routing in Setup > Field Service Settings" without noting that this is a paid add-on requiring a separate license, or instructions that treat road-network routing as the default behavior.

**Why it happens:** LLMs trained on general Salesforce documentation know that Street-Level Routing exists as a feature, but the distinction between "available" and "licensed by default" is often lost. Aerial mode is free and the default; Street-Level Routing costs extra.

**Correct pattern:**

```
Default travel mode: Aerial (straight-line, free, no license required)
Street-Level Routing: Paid add-on — requires separate license activation
  - Provides road-network travel time
  - Supports predictive traffic data
  - Must be explicitly licensed and enabled in Setup

Before recommending Street-Level Routing:
  → Confirm the org has the add-on license
  → Confirm it is enabled in Setup > Field Service Settings > Routing
```

**Detection hint:** Any instruction to configure Street-Level Routing without a licensing confirmation step is missing a prerequisite check.

---

## Anti-Pattern 4: Treating Priority 1 as a General "Important" Label

**What the LLM generates:** Guidance to set all customer-facing or time-sensitive appointments to `Priority = 1` as a blanket rule, or to default all appointments to priority 1 in automation because "all customers are equally important."

**Why it happens:** LLMs mirror common business language where "priority 1" means "important" rather than understanding the technical consequence: every appointment at priority 1 generates the same optimizer score (~25,500 points), eliminating the optimizer's ability to differentiate scheduling order.

**Correct pattern:**

```
Priority 1 (~25,500 pts):  Emergency / SLA breach imminent (<4 hours response window)
Priority 2–3:              Urgent — next available slot required
Priority 4–5:              Standard customer appointment
Priority 6–7:              Routine maintenance, planned work
Priority 8–10:             Lowest urgency — bulk/background tasks

Rule: Priority 1 must be rare. If >20% of appointments are priority 1,
      the tier model is misconfigured.

DueDate must also be set — null DueDate + any priority = lowest effective score.
```

**Detection hint:** Any automation that sets `Priority = 1` for all or most appointments, or any guidance using "priority 1 = customer-facing" as the rule, is over-assigning the highest priority tier.

---

## Anti-Pattern 5: Ignoring DueDate Null Check Before Optimizer Guidance

**What the LLM generates:** Optimization configuration and tuning advice without asking about or checking `ServiceAppointment.DueDate` population. The LLM proceeds to tune scheduling policy or objective weights while the real problem is that many appointments have null `DueDate`.

**Why it happens:** LLMs focus on the optimizer configuration surface (scheduling policy, objective weights, travel mode) because those are the visible settings. The data quality prerequisite — that `DueDate` and `Priority` must be populated — is a less prominent constraint that is easy to overlook when the prompt focuses on configuration rather than data.

**Correct pattern:**

```
Before any optimizer tuning or troubleshooting:

Step 0: Run data quality check
  SELECT Id, Subject, DueDate, Priority 
  FROM ServiceAppointment 
  WHERE Status NOT IN ('Completed', 'Cancelled')
    AND (DueDate = null OR Priority = null)

If this returns records: fix data quality first.
Optimizer tuning on dirty data produces misleading results.

Null DueDate = optimizer treats appointment as lowest priority
Null Priority = optimizer cannot differentiate urgency
```

**Detection hint:** Any optimizer troubleshooting guidance that proceeds directly to policy/objective configuration without first confirming DueDate and Priority data quality is missing the prerequisite check.

---

## Anti-Pattern 6: Recommending Manual Dispatcher Scheduling as an Alternative to the Optimizer

**What the LLM generates:** When the optimizer is complex to configure, the LLM suggests "dispatchers can manually assign appointments in the Gantt as an alternative to using the optimizer."

**Why it happens:** LLMs avoid complex configuration topics by suggesting simpler alternatives. Manual scheduling is a valid FSL feature, and suggesting it is not technically wrong — but it is architecturally wrong for any operation above small scale. The optimizer is designed to solve the combinatorial routing problem at scale; manual scheduling cannot replicate it.

**Correct pattern:**

```
Manual dispatcher scheduling: appropriate for
  - Small teams (<10 technicians)
  - Exception handling after optimization runs
  - Overriding specific optimizer assignments

FSL Optimizer: required for
  - Territory-wide sequencing (10+ technicians)
  - Multi-day planning
  - Consistent travel minimization across the workforce

Do not recommend manual scheduling as an alternative to optimization at scale.
```

**Detection hint:** Any guidance that suggests manual Gantt assignment as the primary scheduling approach for a field service operation with more than 10–15 technicians is substituting manual labor for a purpose-built optimization engine.
